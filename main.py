import sqlite3
import re
import os
import time
import sys
import json

import mechanize

# Hipinion
LOGIN_PAGE = 'http://forums.hipinion.com/ucp.php'
USER_LIST_TEMPLATE = 'http://forums.hipinion.com/memberlist.php?sk=d&sd=d&start={}'
USER_PROFILE_TEMPLATE = 'http://forums.hipinion.com/memberlist.php?mode=viewprofile&u={}'
# TODO: parameterize number of users to fetch
PAGES_OF_BOARDERS = 1 # each page = 50 boarders

def parse_boarder_profile(profile_html):
    boarder = {}
    # TODO: this is bad
    next_span_user = False
    next_img_av = False
    next_dd_posts = False
    next_joined = False
    profile_html = profile_html.split('\n')
    for l in profile_html:
        if l.find("<dl class=\"left-box\">") > 0:
            next_img_av = True
        if l.find("<img src=") > 0 and next_img_av:
            boarder['avatar_html'] = "<" + l.strip().lstrip("<dt>").rstrip("</dt>").strip() + ">"
            boarder['avatar_url'] = re.search(r".*src=\"(?P<url>.*?)\"", l).groupdict()['url']
            if boarder['avatar_url'][0] == '.':
                old_url = boarder['avatar_url']
                new_url = "http://forums.hipinion.com" + old_url[1:]
                boarder['avatar_html'] = boarder['avatar_html'].replace(old_url, new_url)
                boarder['avatar_url'] = new_url
            next_img_av = False
        if l.find("<dt>Username:</dt>") > 0:
            next_span_user = True
        if l.find("span") > 0 and next_span_user:
            boarder['username_html'] =  l.strip()
            boarder['username'] = re.search(r"<span.*?>(?P<username>.*?)</span>", boarder['username_html']).groupdict()['username']
            next_span_user = False
            next_img_av = False
        if l.find("<dt>Location:</dt>") > 0:
            start = l.find("<dd>")
            stop = l.find("</dd>")
            boarder['location'] = l[start+4:stop]
            l = l[stop+5:]
        if l.find("<dt>Age:</dt>") >= 0:
            start = l.find("<dd>", l.find("<dt>Age:</dt>"))
            stop = l.find("</dd>", l.find("<dt>Age:</dt>"))
            boarder['age'] = int(l[start+4:stop])
        if l.find("<dt>Website:</dt>") > 0:
            start = l.find("<dd>", l.find("<dt>Website:</dt>"))
            stop = l.find("</dd>", l.find("<dt>Website:</dt>"))
            boarder['website_html'] = l[start+4:stop]
            boarder['website_url'] = re.search(r".*href=\"(?P<url>.*?)\"", boarder['website_html']).groupdict()['url']
        if l.find("<dt>Joined:</dt>") >= 0:
            next_joined = True
        if l.find("<dd>") > 0 and next_joined:
            boarder['joined_date'] = re.search(r"<dd>(?P<joined_date>.*?)</dd>", l.strip()).groupdict()['joined_date']
            next_joined = False
        if l.find("<dt>Total posts:</dt>") >= 0:
            next_dd_posts = True
        if l.find("<dd>") > 0 and next_dd_posts:
            boarder['post_count'] = int(l.split("|")[0].strip().lstrip("<dd>").strip())
            next_dd_posts = False
        if l.find('% of all posts') >= 0:
            boarder['posts_per_day'] = float(
                re.search(r"of all posts / (?P<posts_per_day>[0-9\.]+) posts per day", l.strip()).groupdict()['posts_per_day'])
        if l.find("class=\"signature\"") > 0:
            boarder['signature'] = l.strip()

    return boarder


def get_boarder_profile(browser, boarder_id):
    browser.open(USER_PROFILE_TEMPLATE.format(boarder_id))
    return browser.response().get_data()


def get_boarder(browser, boarder_id):
    html = get_boarder_profile(browser, boarder_id)
    info = parse_boarder_profile(html)
    info['id'] = boarder_id
    return info

def get_top_boarder_ids(browser):
    user_ids = []
    for i in range(PAGES_OF_BOARDERS):
        browser.open(USER_LIST_TEMPLATE.format(i*50))
        page = browser.response().get_data()
        user_ids += re.findall(r"memberlist.php\?mode=viewprofile&amp;u=(?P<id>\d+)", page)
    return map(int, user_ids)

def fill_out_login_form(browser, username, password, answer=None):
    flist = browser.forms()
    for f in flist:
        if str(f).find("login") > 0:
            browser.form = f
    browser['username'] = username
    browser['password'] = password
    if answer:
        browser['qa_answer'] = answer
    return browser


def get_hipinion(username, password):
    """Logs into hipinion.

    If presented with a challenge,
    presents challenge to user on stdout
    and captures answer on stdin.

    Returns a mechanize.Browser.
    """
    browser = mechanize.Browser()
    browser.open(LOGIN_PAGE)
    browser = fill_out_login_form(browser, username, password)
    browser.submit()
    response = browser.response().get_data()
    if 'You exceeded the maximum allowed number of login attempts.' in response:
        for line in response.split("\n"):
            if 'This question is a means of preventing' in line:
                print line
                break
        answer = raw_input('Enter captcha answer: ')
        browser = fill_out_login_form(browser, username, password, answer)
        browser.submit()
    return browser


def dump_to_file(filename, data):
    with open(filename, 'w') as fh:
        json.dump(data, fh, indent=2)


def main():
    # TODO: use argparse
    if len(sys.argv) < 3:
        print "Give your username and password as arguments"

    # Output to boarders.json by default
    output_file = 'boarders.json'
    if len(sys.argv) == 4:
        output_file = sys.argv[3]

    browser = get_hipinion(sys.argv[1], sys.argv[2])

    # Get a list of the top boarders by post count
    user_ids = get_top_boarder_ids(browser)
    boarder_list = []

    # Fetch profiles
    for user_id in user_ids:
        try:
            boarder_info = get_boarder(browser, user_id)
            print boarder_info
            boarder_list.append(boarder_info)
            dump_to_file(output_file, boarder_list)
        except Exception, e:
            print e
            pass
        time.sleep(2)


if __name__ == '__main__':
    main()

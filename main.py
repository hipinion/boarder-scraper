import sqlite3
import re
import os
import time
import sys
import json

import mechanize

# Hipinion
HIPINION_LOGIN_PAGE = 'http://forums.hipinion.com/ucp.php'
HIPINION_USER_PAGE = 'http://forums.hipinion.com/memberlist.php?mode=viewprofile&u={}'
NUMBER_OF_BOARDERS = 2614

def parse_boarder_profile(profile_html):
    av_link = ""
    dname = ""
    location = ""
    num_posts = ""
    next_span_user = False
    next_img_av = False
    next_dd_posts = False
    # TODO: what the hell?
    profile_html = profile_html.split('\n')
    for l in profile_html:
        if l.find("<dl class=\"left-box\">") > 0:
            next_img_av = True
        if l.find("<img src=") > 0 and next_img_av == True:
            av_link = "<" + l.strip().lstrip("<dt>").rstrip("</dt>").strip() + ">"
            next_img_av = False
        if l.find("<dt>Username:</dt>") > 0:
            next_span_user = True
        if l.find("span") > 0 and next_span_user == True:
            dname =  l.strip()
            next_span_user = False
            next_img_av = False
        if l.find("<dt>Location:</dt>") > 0:
            start = l.find("<dd>")
            stop = l.find("</dd>")
            location = l[start+4:stop]
        if l.find("<dt>Total posts:</dt>") > 0:
            next_dd_posts = True
        if l.find("<dd>") > 0 and next_dd_posts == True:
            num_posts = l.split("|")[0].strip().lstrip("<dd>").strip()
            next_dd_posts = False

    return {"av_link":av_link, "dname":dname, "location":location, "num_posts":num_posts}


def get_boarder_profile(browser, boarder_id):
    browser.open(HIPINION_USER_PAGE.format(boarder_id))
    return browser.response().get_data()


def get_hipinion(username, password):
    browser = mechanize.Browser()
    browser.open(HIPINION_LOGIN_PAGE)
    flist = browser.forms()
    for f in flist:
        if str(f).find("login") > 0:
            browser.form = f
    browser['username'] = username
    browser['password'] = password
    browser.submit()
    return browser


def dump_to_file(filename, data):
    with open(filename, 'w') as fh:
        fh.write(json.dump(data))


def main():
    if len(sys.argv < 3):
        print "Hey, give your username and password as arguments"

    last_boarder_retrieved = 1
    output_file = 'boarders.json'
    boarder_list = []
    if len(sys.argv == 4):
        output_file = sys.argv[4]
        with open(output_file) as boarder_file:
            boarder_list = json.load(boarder_file)
            last_board_retrieved = len(boarder_json) - 1


    browser = get_hipinion(sys.argv[1], sys.argv[2])
    print br.title()
    print br.geturl()
    while last_boarder_retrieved < NUMBER_OF_BOARDERS:
        boarder_info = parse_boarder_profile(
            get_boarder_profile(browser, last_boarder_retrieved))
        print boarder_info
        boarder_list.append(boarder_info)
        with open(output_file, 'w') as fh:
            fh.write(json.dump(boarder_list))
        last_boarder_retrieved += 1
        time.sleep(3)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3.6
import exifread, mwclient, mwparserfromhell, sys, re, configparser, json, pathlib
from time import sleep
number_saved = 0

def call_home(site_obj):
    page = site_obj.Pages['User:TheSandBot/status']
    text = page.text()
    data = json.loads(text)["run"]["exif_resolver"]
    if str(data) == str(True):
        return True
    return False


def get_valid_filename(s):
    """
    Turns a regular string into a valid (sanatized) string that is safe for use
    as a file name.
    Method courtesy of cowlinator on StackOverflow
    (https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename)
    @param s String to convert to be file safe
    @return File safe string
    """
    assert(s is not "" or s is not None)
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def save_edit(page, utils, text):
    config = utils[0]

    site = utils[1]
    original_text = text

    if not call_home(site):
        raise ValueError("Kill switch on-wiki is false. Terminating program.")
    time = 0
    edit_summary = """[[Commons:Bots/Requests/TheSandBot|Task 1]]: Fixed inaccurate use of [[Template:According to Exif data]]. Questions? [[User talk:TheSandDoctor|msg TSD!]]"""
    while True:
        if time == 1:
            text = site.Pages["File:" + page.page_title].text()
        try:
            content_changed, text = process("File:" + page.page_title,site)

        except ValueError as e:
            print(e)
            pathlib.Path('./errors').mkdir(parents=False, exist_ok=True)
            title = get_valid_filename("File:" + page.page_title)
            text_file = open("./errors/err " + title + ".txt", "w")
            text_file.write("Error present: " +  str(e) + "\n\n\n\n\n" + text)
            text_file.close()
            text_file = open("./errors/error_list.txt", "a+")
            text_file.write("File:" + page.page_title + "\n")
            text_file.close()
            text_file = open("./errors/wikified_error_list.txt", "a+")
            text_file.write("#[[" + "File:" + page.page_title + "]]" + "\n")
            text_file.close()
            return
        try:
            if content_changed:
                page.save(text,summary=edit_summary,bot=False,minor=True)
                print("Saved page")
                global number_saved
                number_saved += 1
                if time == 1:
                    time = 0
                break
            else:
                print("Content not changed, no need to save")
                break
        except [[EditError]]:
            print("Error")
            time = 1
            sleep(5)   # sleep for 5 seconds before trying again
            continue
        except [[ProtectedPageError]]:
            print('Could not edit ' + page.page_title + ' due to protection')
        break


def process(page_name,site):
    image_page = site.Pages["""""" + str(page_name) + """"""]#'File:Taiwan white caterpillar2018.jpg']
    wikicode = mwparserfromhell.parse(image_page.text())
    dict_results = {}
    content_changed = False
    for template in wikicode.filter_templates():
        if template.name.matches("Information") and template.has("date"):
            date = template.get("date").value
            for template in date.filter_templates():
                if template.name.matches("According to EXIF data") and len(template.params) == 1:
                    dict_results["template"] = template.params[0] # Get template date value
                    with open('Example.jpg', 'wb') as fd:
                        image_page.download(fd)

                    # Open image file for reading (binary mode)
                    with open("./Example.jpg",'rb') as f:
                        tags = exifread.process_file(f)

                    # Get Exif tags
                    if "EXIF DateTimeOriginal" in tags:
                        dict_results["original"] = re.sub("[:]","-",str(tags["EXIF DateTimeOriginal"])[0:10])
                        print("Checking")
                        # Results don't match, so original takes precedence
                        if dict_results["original"] != dict_results["template"]:
                            wikicode.replace(template,str("{{According to EXIF data|" + dict_results["original"] + "}}"))
                            content_changed = True
                            print("Replaced instance")
                        print("Checked")
    return [content_changed,str(wikicode)]


def run(utils):
    site = utils[1]
    offset = utils[2]
    limit = utils[3]
    global number_saved
    for page in site.Categories["Uploaded with Mobile/Android"]:
        if offset > 0:
            offset -= 1
            print("Skipped due to offset config")
            continue
        print("Working with: " + page.name)
        print(number_saved)
        if number_saved < limit:
            text = page.text()
            try:
                save_edit(page, utils, text)
            except ValueError:
                raise
        else:
            return  # run out of pages in limited run


def main():
    site = mwclient.Site(('https','commons.wikimedia.org'),'/w/')
    config = configparser.RawConfigParser()
    config.read('credentials.txt')
    try:
        site.login(config.get('enwiki_sandbot','username'), config.get('enwiki_sandbot', 'password'))
    except errors.LoginError as e:
        print(e)
        raise ValueError("Login failed.")
    offset = 1  # must be 1 to avoid the sub category
    limit = 2
    utils = [config,site,offset,limit]
    run(utils)


if __name__ == "__main__":
    main()

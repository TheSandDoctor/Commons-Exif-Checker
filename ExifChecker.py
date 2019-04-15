#!/usr/bin/env python3.6
import exifread, mwclient, mwparserfromhell, sys, re, configparser, json, pathlib


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
    dry_run = utils[2]
    original_text = text

    # print("{}".format(dry_run))
    code = mwparserfromhell.parse(text)

    if not call_home(site):#config):
        raise ValueError("Kill switch on-wiki is false. Terminating program.")
    time = 0
    edit_summary = """Corrected use of [[Template:According to Exif data]] using [[User:""" + config.get('enwiki_sandbot','username') + "| " + config.get('enwiki_sandbot','username') + """]]. Questions? [[User talk:TheSandDoctor|msg TSD!]] (please mention that this is task #1! [[Commons:Bots/Requests/TheSandBot|BRFA trial 1]])"""
    while True:
        # text = page.edit()
        if time == 1:
            text = site.Pages[page.page_title].text()
        try:
            content_changed, text = process(page.page_title)

        except ValueError as e:
            print(e)
            pathlib.Path('./errors').mkdir(parents=False, exist_ok=True)
            title = get_valid_filename(page.page_title)
            text_file = open("./errors/err " + title + ".txt", "w")
            text_file.write("Error present: " +  str(e) + "\n\n\n\n\n" + text)
            text_file.close()
            text_file = open("./errors/error_list.txt", "a+")
            text_file.write(page.page_title + "\n")
            text_file.close()
            text_file = open("./errors/wikified_error_list.txt", "a+")
            text_file.write("#[[" + page.page_title + "]]" + "\n")
            text_file.close()
            return
        try:
            if dry_run:
                print("Dry run")
                #Write out the initial input
                title = get_valid_filename(page.page_title)
                text_file = open("./tests/in " + title + ".txt", "w")
                text_file.write(original_text)
                text_file.close()
                #Write out the output
                if content_changed:
                    title = get_valid_filename(page.page_title)
                    text_file = open("./tests/out " + title + ".txt", "w")
                    text_file.write(text)
                    text_file.close()
                else:
                    print("Content not changed, don't print output")
                break
            else:
                #print("Would have saved here")
                if content_changed:
                    page.save(text,summary=edit_summary,bot=False,minor=True)
                    print("Saved page")
                    if time == 1:
                        time = 0
                    break
                else:
                    print("Would have saved here")
                    break
        except [[EditError]]:
            print("Error")
            time = 1
            sleep(5)   # sleep for 5 seconds before trying again
            continue
        except [[ProtectedPageError]]:
            print('Could not edit ' + page.page_title + ' due to protection')
        break


def process(page_name):
    image_page = site.Pages[page_name]#'File:Taiwan white caterpillar2018.jpg']
    wikicode = mwparserfromhell.parse(image_page.text())
    dict_results = {}
    content_changed = False
    for template in wikicode.filter_templates():
        if(template.name.matches("Information") and template.has("date")):
            date = template.get("date").value
            for template in date.filter_templates():
                if(template.name.matches("According to EXIF data") and len(template.params) == 1):
                    dict_results["template"] = template.params[0]
                    #print(template.params[0])
                    with open('Example.jpg', 'wb') as fd:
                        image_page.download(fd)


    # Open image file for reading (binary mode)
    #f = open('./Tabby_cat_with_blue_eyes-3336579.jpg', 'rb')
                    with open("./Example.jpg",'rb') as f:
                        tags = exifread.process_file(f)
                    #f = open('./Example.jpg', 'rb')
                    # Return Exif tags
                    #tags = exifread.process_file(f)
                    #f.close()
                    #dict_results = {}
                    if "EXIF DateTimeOriginal" in tags:
                        dict_results["original"] = re.sub("[:]","-",str(tags["EXIF DateTimeOriginal"])[0:10])

                        #print(tags["EXIF DateTimeOriginal"])
                        #dict_results["digitized"] = tags["EXIF DateTimeDigitized"]
                        #print(tags["EXIF DateTimeDigitized"])
                        print(dict_results["original"])
                        print(dict_results["template"])
                        if dict_results["original"] != dict_results["template"]:
                            #print(dict_results["original"])
                            #print("N")
                            #print("T")
                            #print(wikicode)
                            #print(dict_results["template"])
                            wikicode.replace(template,str("{{According to EXIF data|" + dict_results["original"] + "}}"))
                            #template.replace("date",dict_results["original"])
                            #template.get("date").value = dict_results["original"]
                            #print(template.get("date").value)
                            #template.params[0] = dict_ori
                            #print(wikicode)
                            content_changed = True
                            print("Replaced instance")
    return [content_changed,str(wikicode)]


def run(utils):
    site = utils[1]
    offset = utils[2]
    limit = utils[3]
    counter = 0
    for page in site.Categories["Uploaded with Mobile/Android"]:
        if offset > 0:
            offset -= 1
            print("Skipped due to offset config")
            continue
        print("Working with: " + page.name + " " + str(counter))
        if counter < limit:
            counter += 1
            text = page.text()
            try:
                save_edit(page, utils, text)#config, api, site, text, dry_run)#, config)
            except ValueError:# as err:
                raise
        #print(err)
            else:
                return  # run out of pages in limited run

site = mwclient.Site(('https','commons.wikimedia.org'),'/w/')
config = configparser.RawConfigParser()
config.read('credentials.txt')
try:
    #pass
    site.login(config.get('enwiki_sandbot','username'), config.get('enwiki_sandbot', 'password'))
except errors.LoginError as e:
    #print(e[1]['reason'])
    print(e)
    raise ValueError("Login failed.")
offset = 0
limit = 1
utils = [config,site,offset, limit]
run(utils)



#if "EXIF DateTimeDigitized" in tags:
#	dict_results["digitized"] = tags["EXIF DateTimeDigitized"]
#	print(tags["EXIF DateTimeDigitized"])

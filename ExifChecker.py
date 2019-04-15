import exifread, mwclient, mwparserfromhell, sys, re

site = mwclient.Site(('https','commons.wikimedia.org'),'/w/')
image_page = site.Pages['File:Taiwan white caterpillar2018.jpg']
wikicode = mwparserfromhell.parse(image_page.text())
templates = wikicode.filter_templates()
dict_results = {}
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
				f = open('./Example.jpg', 'rb')
				# Return Exif tags
				tags = exifread.process_file(f)
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
						print(wikicode)
						#print(dict_results["template"])
						wikicode.replace(template,str("{{According to EXIF data|" + dict_results["original"] + "}}"))
						#template.replace("date",dict_results["original"])
						#template.get("date").value = dict_results["original"]
						#print(template.get("date").value)
						#template.params[0] = dict_ori
						print(wikicode)
		
#if "EXIF DateTimeDigitized" in tags:
#	dict_results["digitized"] = tags["EXIF DateTimeDigitized"]
#	print(tags["EXIF DateTimeDigitized"])
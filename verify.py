import exifread
with open("./Example.jpg",'rb') as f:
    tags = exifread.process_file(f)

# Get Exif tags
if "EXIF DateTimeOriginal" in tags:
    print(tags["EXIF DateTimeOriginal"])

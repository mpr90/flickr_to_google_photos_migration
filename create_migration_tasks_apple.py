from celery_migration_app import migrate_photo_to_apple
from migration_util import *
from pathlib import Path
import pickle
import os
import sys
import osxphotos
from osxphotos.fingerprint import fingerprint
import subprocess

def migrate_photo_to_apple_immediate(photo_title, photo_url, album_title, photo_tags, dryrun):
    
    # osxphotos has a bug that it won't allow commas in album names. Just remove rather than dealing with OSXPhotos templates (https://rhettbull.github.io/osxphotos/template_help.html)
    album_title = album_title.replace(',', '')

    # Download photo from flickr if not already on disk
    photo_filename = set_image_type_extension_if_missing(f"images/{album_title}/{photo_title}", "JPG")
    if not os.path.isfile(photo_filename):
        print("Downloading photo to '" + photo_filename + "'")
        if download:
            Path(f"./images/{album_title}").mkdir(parents=True, exist_ok=True)
            photo_data = get_photo_from_flickr(photo_url)
            with open(photo_filename, "wb") as f:
                f.write(photo_data.getbuffer())

    # Create or retrieve album
    if not dryrun:
        album = osxphotos.PhotosAlbum(album_title)

    # Try to find existing photo with same title (filename)
    results = photosdb.query(osxphotos.QueryOptions(name=[photo_title]))

    # Check fingerprints
    found = False
    if len(results) > 0:
        print("Found " + str(len(results)) + " matches for '" + photo_title + "', checking fingerprints")
        if os.path.isfile(photo_filename):
            fp = fingerprint(photo_filename)
            for p in results:
                print(f"  Checking search result fp '{p.fingerprint}' against file fp '{fp}'")
                if fp == p.fingerprint:
                    print("  Found a fingerprint match, adding existing photo to album")
                    found = True
                    if not dryrun:
                        album.add(p)

    # If existing photo not found, then add the downloaded file
    if not found:
        print(f"Photo {photo_title} not found in library, adding")
        if not dryrun:
            sp = subprocess.run(["osxphotos", "import", photo_filename, "-N", "--album", album_title], check=True, capture_output=True)
            s = sp.stdout.decode('utf-8').rstrip()
            print(f"  {s}")
            return True
        else:
            return True

####################################################################################################

dryrun = False
download = True

if len(sys.argv) > 1:
    if sys.argv[1] == "-n":
        dryrun = True

print("Migrating Apple Photos...")
if dryrun:
    print("  dryrun mode")
    photosdb = None

print("open photos DB")
photosdb = osxphotos.PhotosDB()

for file in os.listdir("photosets/"):
    if file.endswith(".pickle"):

        with open(f"photosets/{file}", "rb") as photo_tasks_file:
            my_photos = pickle.load(photo_tasks_file)
            print("  Processing file 'photosets/%s' with %d photos" % (file, len(my_photos)))

        for photo in my_photos:
            migrate_photo_to_apple_immediate(
                photo['photoTitle'],
                photo['photoUrl'],
                album_name_adjust(photo['album']),
                photo['photoTags'] or photo['photoTitle'],
                dryrun,
            )

        os.rename(f"photosets/{file}", f"photosets-complete/{file}")


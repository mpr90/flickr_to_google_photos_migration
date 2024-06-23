from celery_migration_app import migrate_photo_to_google
import pickle
import os
import sys

dryrun = False

if len(sys.argv) > 1:
    if sys.argv[1] == "-n":
        dryrun = True

print("Creating Google Photos migration tasks...")
if dryrun:
    print("  dryrun mode")

for file in os.listdir("photosets/"):
    if file.endswith(".pickle"):

        with open(f"photosets/{file}", "rb") as photo_tasks_file:
            my_photos = pickle.load(photo_tasks_file)
            print("  Processing file 'photosets/%s' with %d photos" % (file, len(my_photos)))

        for photo in my_photos:
            migrate_photo_to_google.delay(
                photo['photoTitle'],
                photo['photoUrl'],
                photo['album'],
                photo['photoTags'] or photo['photoTitle'],
                dryrun,
            )

        os.rename(f"photosets/{file}", f"photosets-complete/{file}")


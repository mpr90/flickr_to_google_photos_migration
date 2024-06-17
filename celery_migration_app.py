from celery import Celery
from migration_util import *
from pathlib import Path
from requests.exceptions import RequestException
from googleapiclient.errors import HttpError

app = Celery(__name__)
app.conf.update({
    'result_backend': f'file://{(Path.cwd() / "celery" / "results").resolve().as_posix()}',
    'broker_url': 'filesystem://',
    'broker_transport_options': {
        'data_folder_in': 'celery/out',
        'data_folder_out': 'celery/out',
        'data_folder_processed': 'celery/processed',
        'processed_folder': 'celery/processed',
        'store_processed': True
    },
    'imports': ('celery_migration_app',),
    'result_persistent': True,
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json']})

r = redis.Redis(host='0.0.0.0', port=6379, db=0, decode_responses=True)


@app.task(autoretry_for=(RequestException, HttpError),
          retry_backoff=True,
          retry_kwargs={'max_retries': 20})
def migrate_photo(photo_title, photo_url, album_title, photo_tags, dryrun):
    google_creds = authorize_with_google()
    service = get_google_photos_service(google_creds)

    with r.lock("find-album"):
        album_id = find_album_on_google(album_title)
        if album_id is None:
            print("Creating new album " + album_title)
            if not dryrun:
                album_id = create_album_on_google(service, album_title)

    with r.lock("find-photo"):
        photo_id = find_photo_on_google(photo_title)
        if photo_id is None:
            photo_id = find_photo_on_google(photo_title + ".JPG")
        if photo_id is None:
            photo_id = find_photo_on_google(photo_title + ".HEIC")
    
    if True: #photo_id is None:
        print("Downloading photo " + photo_title + " and uploading to album " + album_title)
        rv = True
        if not dryrun:
            photo_data = get_photo_from_flickr(photo_url)
            return upload_photo_to_google(google_creds, service, album_id, photo_data,
                                        photo_title, photo_tags)
        else:
            return True
    else:   # This doesn't work due to this app needing to own photos that you want to add to the album. So just always download/upload
        print("Adding existing photo " + photo_title + " to album " + album_title)
        if not dryrun:
            return add_existing_photo_to_google_album(service, album_id, photo_id)
        else:
            return True


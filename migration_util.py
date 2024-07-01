from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import requests
import urllib
from io import BytesIO
from pathlib import Path
import redis
import os
import re

r = redis.Redis(host='0.0.0.0', port=6379, db=0, decode_responses=True)


def authorize_with_google():
    store = file.Storage((Path().parent / "auth/google_token.json").resolve().as_posix())
    return store.get()


def get_google_photos_service(google_creds):
    return build('photoslibrary', 'v1',
                 http=google_creds.authorize(Http()),
                 cache_discovery=False,
                 static_discovery=False)


def find_album_on_google(album_title):
    return r.get(album_title)


def find_photo_on_google(photo_filename):
    return r.get(photo_filename)


def create_album_on_google(service, album_title):
    albums = service.albums()
    new_album = albums.create(body={"album": {"title": album_title}}).execute()
    r.set(album_title, new_album.get('id', None))
    return new_album.get("id", None)


def upload_photo_to_google(google_auth, service, album_id, photo_data,
                           photo_title, photo_tags):
    media_items = service.mediaItems()

    url = 'https://photoslibrary.googleapis.com/v1/uploads'
    authorization = 'Bearer ' + google_auth.access_token
    headers = {
        "Authorization": authorization,
        'Content-type': 'application/octet-stream',
        'X-Goog-Upload-File-Name': photo_title,
        'X-Goog-Upload-Protocol': 'raw',
    }

    upload_response = requests.post(url, headers=headers, data=photo_data)
    upload_token = upload_response.text

    if upload_token is not None:
        payload = {
            "albumId": album_id,
            "newMediaItems": [{
                "description": photo_tags,
                "simpleMediaItem": {
                    "uploadToken": upload_token
                }
            }]
        }

        add_photo_req = media_items.batchCreate(body=payload)
        add_photo_resp = add_photo_req.execute()

        return add_photo_resp


def add_existing_photo_to_google_album(service, album_id, photo_id):
    albums = service.albums()

    add_photo_req = albums.batchAddMediaItems(albumId=album_id, body=dict(mediaItemIds=photo_id))
    add_photo_resp = add_photo_req.execute()

    return add_photo_resp


def get_photo_from_flickr(photo_url):
    photo_url_obj = urllib.request.urlopen(photo_url)
    return BytesIO(photo_url_obj.read())


def set_image_type_extension_if_missing(file_path, new_extension):
    base_name, ext = os.path.splitext(file_path)
    if not ext.upper() in ['.JPG', '.JPEG', '.HEIC', '.PNG', '.TIF', '.TIFF', '.GIF']:
        new_file_path = file_path + "." + new_extension
    else:
        new_file_path = file_path
    return new_file_path


# if album name ends with <space>+<digits> (i.e. year), move digits to beginning of name
def album_name_adjust(name):
    res = re.search(r' \d+$', name)
    if bool(res):
        match = res.group()
        new_name = match[1:] + " " + name[:-len(match)]
        return new_name
    else:
        return name


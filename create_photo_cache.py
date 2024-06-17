import redis
from migration_util import authorize_with_google, get_google_photos_service


r = redis.Redis(host='0.0.0.0', port=6379, db=0, decode_responses=True)


def build_photo_cache(service):
    photos = service.mediaItems()
    photo_list_req = photos.list(pageSize=50, fields="nextPageToken,mediaItems")
    while photo_list_req is not None:
        photo_list_resp = photo_list_req.execute()
        photo_list = photo_list_resp.get('mediaItems', [])
        print("Adding ", len(photo_list), " photos...")
        for photo in photo_list:
            print("  Caching photo " + photo['filename'] + " created " + photo['mediaMetadata']['creationTime'])
            if r.get(photo['filename']) is None:
                r.set(photo['filename'],  photo['id'])

        photo_list_req = photos.list_next(photo_list_req, photo_list_resp)

if __name__ == '__main__':
    creds = authorize_with_google()
    service = get_google_photos_service(creds)
    build_photo_cache(service)

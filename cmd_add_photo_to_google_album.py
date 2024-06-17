import sys
import redis
from migration_util import authorize_with_google, get_google_photos_service, add_existing_photo_to_google_album


if __name__ == '__main__':
    if len(sys.argv) >= 3:
        album_id = sys.argv[1]
        photo_id = sys.argv[2]
        if album_id is not None and photo_id is not None:
            creds = authorize_with_google()
            service = get_google_photos_service(creds)
            photo_ids = [photo_id]
            add_existing_photo_to_google_album(service, album_id, photo_ids)
    else:
        print("Error: Missing argument(s)")
        print("Usage: cmd album_id photo_id")

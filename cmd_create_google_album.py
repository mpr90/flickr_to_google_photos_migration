import sys
import redis
from migration_util import authorize_with_google, get_google_photos_service, create_album_on_google


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        album_title = sys.argv[1]
        if album_title is not None:
            creds = authorize_with_google()
            service = get_google_photos_service(creds)
            album_id = create_album_on_google(service, album_title)
            print("Created new album '" + album_title + "' with ID ", album_id)
    else:
        print("Error: Missing argument(s)")
        print("Usage: cmd album_title")

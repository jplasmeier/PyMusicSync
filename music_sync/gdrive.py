# Google Drive functionality 

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def get_file_ext_type(drive_file):
    """ 
    Gets the file extension type from a GoogleDriveFile object instance.
    Uses the MIME type.
    Options are:
    folder - u'mimeType': u'application/vnd.google-apps.folder',
    other - u'mimeType': u'text/plain'
    audio - u'mimeType': u'audio/mp3'
    """
    raw_mimeType = drive_file.metadata['mimeType']
    if 'google-apps.folder' in raw_mimeType:
        return 'folder'
    if 'audio' in raw_mimeType:
        return 'audio'
    else:
        return 'other'

def list_folder(drive, folder_id):
    # folder_id: GoogleDriveFile['id']
    _q = {'q': "'{}' in parents and trashed=false".format(folder_id)}
    return drive.ListFile(_q).GetList()

def get_artist_size(drive_collection, album_cache, drive, artist):
    """
    artist: GoogleDriveFile of an artist folder
    """
    albums = list_folder(drive, artist['id'])
    size = 0
    album_list = drive_collection[artist['title']]
    for album in albums:
        file_extension_type = get_file_ext_type(album)
        if album['title'] not in album_list and file_extension_type is 'folder':
            album_list.append(album['title'])
        if file_extension_type is 'audio' and artist['title'] not in audio_in_artist:
            audio_in_artist.append(artist['title'])
        album_size = get_album_size_cache(album_cache, album['id'])
        if album_size is None:
            album_size = get_album_size_drive(drive, album['id'])
        if album_size is not None:
            size += album_size
    return size, drive_collection

def get_album_size_cache(album_cache, album_id):
    """
    Turns out getting the size of each album_id thru drive takes forever
    So we're caching them.
    album_id: string containing GoogleDriveFile id of an album_id folder
    Returns None if not found in cahce
    """
    if album_id in album_cache:
        return album_cache[album_id]
    else:
        return None

def get_album_size_drive(drive, album_id):
    """
    album_id: string containing GoogleDriveFile id of an album_id folder
    """
    tracks = list_folder(drive, album_id)
    size = 0
    for track in tracks:
        file_size = int(track["quotaBytesUsed"])
        if file_size is not None:
            size += file_size
    album_cache[album_id] = size
    return size

def login():
    '''
    Login via Google Auth
    If there is a credentials file present, use it.
    Otherwise, use Local Webserver Auth
    Returns the gauth object
    '''
    gauth = GoogleAuth()
    # Try to load saved client credentials
    gauth.LoadCredentialsFile("mycreds.txt")
    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()
    # Save the current credentials to a file
    gauth.SaveCredentialsFile("mycreds.txt")
    return gauth

def get_file_size_recursive(drive_collection, album_cache, drive, folder):
    size = 0
    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    for file1 in file_list:
        if file1['title'] == folder:
            artists = list_folder(drive, file1['id'])
            i = 0.0
            for artist in artists:
                drive_collection[artist['title']] = []
                print "Getting Filesize: {0}%".format((i/len(artists))*100)
                i += 1
                size_add, drive_collection = get_artist_size(drive_collection, album_cache,  drive, artist)
                size += size_add
    return size, drive_collection


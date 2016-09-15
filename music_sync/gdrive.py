# Google Drive functionality 
from pydrive.auth import GoogleAuth
import cannery
import datetime


def get_file_ext_type(drive_file):
    """
    :param drive_file: The GoogleDriveFile to get the file type of
    Uses the MIME type.
    Options are:
    folder - u'mimeType': u'application/vnd.google-apps.folder',
    other - u'mimeType': u'text/plain'
    audio - u'mimeType': u'audio/mp3'
    """
    raw_mime_type = drive_file.metadata['mimeType']
    if 'google-apps.folder' in raw_mime_type:
        return 'folder'
    if 'audio' in raw_mime_type:
        return 'audio'
    else:
        return 'other'


def list_folder(drive, folder_id):
    """
    Lists contents of a GoogleDriveFile that is a folder
    :param drive: Drive object to use for getting folders
    :param folder_id: The id of the GoogleDriveFile
    :return: The GoogleDriveList of folders
    """
    _q = {'q': "'{}' in parents and trashed=false".format(folder_id)}
    return drive.ListFile(_q).GetList()


# TODO: Dead Code?
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
    cannery.add_album_to_cache(album_id, size, datetime.datetime.now())
    return size


# Collection Filling

def fill_google_drive_collection(google_drive_collection, drive, folder):
    """
    :param google_drive_collection: GoogleDriveCollection object to fill with metadata from Google Drive
    :param drive: the GoogleDrive object to pull metadata from Google Drive
    :param folder: the name of the folder to pull metadata from. Currently must be in the root folder
    """
    # Check last mod by date for music folder and fill from cache if possible
    cache_collection = cannery.get_cached_drive_colleciton(folder)
    artists = list_folder(drive, folder['id'])
    for artist in artists:
        # Check last mod by date for artist and fill from cache if possible
        google_drive_collection.add_artist(artist['title'])
        fill_albums_for_artist(google_drive_collection, drive, artist)
    return google_drive_collection


def fill_albums_for_artist(google_drive_collection, drive, artist):
    """
    :param google_drive_collection: The GoogleDriveCollection
    :param drive: The GoogleDrive object to use
    :param artist: GoogleDriveFile of an artist
    :return: Size of artist
    """
    # Check last mod by date and fill from cache if possible
    albums = list_folder(drive, artist['id'])
    album_list = google_drive_collection.get_albums_for_artist(artist['title'])
    audio_in_artist = []
    size = 0
    for album in albums:
        file_extension_type = get_file_ext_type(album)
        if album['title'] not in album_list and file_extension_type is 'folder':
            google_drive_collection.add_album_for_artist(album['title'], artist['title'])
            google_drive_collection.set_album_size(album['title'], artist['title'],
                                                   get_album_size_drive(drive, album['id']))
        if file_extension_type is 'audio' and artist['title'] not in audio_in_artist:
            audio_in_artist.append(artist['title'])
        # album_size = cannery.get_album_size_from_cache(album['id'])
        # if not album_size:
        #     album_size = get_album_size_drive(drive, album['id'])
        # if album_size:
        #    size += album_size

    if audio_in_artist:
        print "Heads up, you have audio files directly in the following artists."
        print "You should put them in a folder by album instead."
        print sorted(audio_in_artist)

# Drive Utilities


def login():
    """
    Login via Google Auth
    If there is a credentials file present, use it.
    Otherwise, use Local Webserver Auth
    Returns the gauth object
    """
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
    # TODO: Encryption???
    gauth.SaveCredentialsFile("mycreds.txt")
    return gauth


def get_file_from_root(drive, file_title):
    """
    Returns the file(s)/director(y/ies) as a GoogleDriveFile with the given title.
    :param drive: GoogleDrive object to use to pull file from
    :param file_title: Title to return file for
    :return: List of GoogleDriveFiles matching file_title
    """
    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    title_matches = []
    for file1 in file_list:
        if file1['title'] == file_title:
            title_matches.append(file1)
    return title_matches


def get_folder_from_root(drive, file_title):
    """
    Returns the file/directory as a GoogleDriveFile with the given title.
    :param drive: GoogleDrive object to use to pull file from
    :param file_title: Title to return file for
    :return: First GoogleDriveFile matching file_title found
    """
    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    for file1 in file_list:
        if file1['title'] == file_title:
            return file1

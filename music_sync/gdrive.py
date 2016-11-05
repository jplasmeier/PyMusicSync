# Google Drive functionality 
from pydrive.auth import GoogleAuth
import cannery
import music_sync_utils

raw_metadata_artists_path = 'raw_metadata_artists.p'
raw_metadata_albums_path = 'raw_metadata_albums.p'


class DriveArtistItem(music_sync_utils.ArtistItem):

    def get_albums_for_artist(self, drive, drive_artist):
        """
        Given an ArtistItem, find its albums in Drive and return a list of them
        :param drive: The GoogleDrive object
        :param drive_artist: The Drive Artist to get new albums from
        :return: A list of albums. Should include existing albums and new ones.
        """
        audio_in_artist = []
        drive_albums_added = []
        drive_albums = list_folder(drive, drive_artist['id'])
        for drive_album in drive_albums:
            drive_album_name = drive_album['title']
            if drive_album_name not in self.albums and get_file_ext_type(drive_album) is 'folder':
                album_size = get_album_size_drive(drive, drive_album['id'])
                new_album = music_sync_utils.AlbumItem(drive_album_name, album_size)
                self.albums.append(new_album)
                drive_albums_added.append(drive_album)
            elif get_file_ext_type(drive_album) is 'audio':
                audio_in_artist.append(drive_album_name)
        if audio_in_artist:
            print "Heads up, you have some audio files directly under an artist: ", audio_in_artist
        return drive_albums_added


# Collection Filling

# This needs to be a bound method in a Google Drive subclass of the CollectionItem.
def get_google_drive_collection(drive, folder):
    """
    :param drive: the GoogleDrive object to pull metadata from Google Drive
    :param folder: the name of the folder to pull metadata from. Currently must be in the root folder
    """

    # These are currently being dumped to disk
    # But they aren't useful after execution so should keep them in memory
    raw_metadata_artists = {}
    raw_metadata_albums = {}

    filled_collection = {}
    drive_artists = list_folder(drive, folder['id'])

    for drive_artist in drive_artists:
        drive_artist_name = drive_artist['title']
        raw_metadata_artists[drive_artist_name] = drive_artist
        if drive_artist_name not in raw_metadata_albums:
            raw_metadata_albums[drive_artist_name] = []
        # Artist not in collection yet
        if drive_artist_name not in filled_collection:
            new_artist = DriveArtistItem(drive_artist_name)
            drive_albums = new_artist.get_albums_for_artist(drive, drive_artist)
            raw_metadata_albums[drive_artist_name] = drive_albums
            filled_collection[drive_artist_name] = new_artist
            print "Added Artist: {}".format(drive_artist_name)
            for drive_album in drive_albums:
                print "----Added Album: {}".format(drive_album['title'])

    cannery.pickle_something(raw_metadata_artists, raw_metadata_artists_path)
    cannery.pickle_something(raw_metadata_albums, raw_metadata_albums_path)
    return filled_collection


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


# TODO: Fix this hacky code
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


# TODO: Bind this method to the DriveArtist class
def get_artist_size(drive, artist):
    albums = list_folder(drive, artist['id'])
    size = 0
    for album in albums:
        size += int(album['quotaBytesUsed'])
    return size


# TODO: Bind this method to the DriveAlbum class
def get_album_size_drive(drive, album_id):
    """
    Gets the size of an album in Drive.
    album_id: string containing GoogleDriveFile id of an album_id folder
    """
    tracks = list_folder(drive, album_id)
    size = 0
    for track in tracks:
        file_size = int(track["quotaBytesUsed"])
        if file_size is not None:
            size += file_size
    return size



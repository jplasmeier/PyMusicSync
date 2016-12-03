from pydrive.auth import GoogleAuth
import config
import logger
import music_sync_utils
import os
import sys


class GoogleDriveLibrary(music_sync_utils.MediaLibrary):
    def __init__(self, drive, root_folder_name):
        super(GoogleDriveLibrary, self).__init__()
        self.init_google_drive_collection(drive, root_folder_name)
        self.clean_unicode()

    def init_google_drive_collection(self, drive, folder):
        """
        :param drive: the GoogleDrive object to pull metadata from Google Drive
        :param folder: the name of the folder to pull metadata from. Currently must be in the root folder
        """
        if self.collection is None:
            self.collection = {}

        drive_artists = list_folder(drive, folder['id'])
        len_drive_artists = len(drive_artists)
        for idx, drive_artist in enumerate(drive_artists):
            drive_artist_name = drive_artist['title']
            # Artist not in collection yet
            if drive_artist_name not in self.collection:
                new_artist = DriveArtistItem(drive_artist_name, drive_artist)
                new_artist.get_albums_for_artist(drive, drive_artist)
                self.collection[drive_artist_name] = new_artist
                # This will update the same line with the new percentage.
                sys.stdout.write("\rDownloading Google Drive Metadata: {}".format(idx / float(len_drive_artists) * 100))
                sys.stdout.flush()
        return self


class DriveArtistItem(music_sync_utils.ArtistItem):
    def __init__(self, name, drive_file):
        super(DriveArtistItem, self).__init__(name)
        self.drive_file = drive_file

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
                new_album = DriveAlbumItem(drive_album_name, album_size, drive_album)
                self.albums.append(new_album)
                drive_albums_added.append(drive_album)
            elif get_file_ext_type(drive_album) is 'audio':
                audio_in_artist.append(drive_album_name)
        if audio_in_artist:
            for audio in audio_in_artist:
                logger.log_warning("Heads up, you have some audio files directly under an artist: {}".format(audio))
                print "\rHeads up, you have some audio files directly under an artist: {}".format(audio)
        return drive_albums_added


class DriveAlbumItem(music_sync_utils.AlbumItem):
    def __init__(self, name, file_size, drive_file):
        super(DriveAlbumItem, self).__init__(name, file_size)
        self.drive_file = drive_file


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


# TODO: Implement
def get_root_folder(drive):
    """
    Returns the GoogleDriveFile of the root.
    :param drive:
    :return:
    """
    raise NotImplementedError


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


# Download

def download_recursive(drive, folder, download_to):
    """
    Given a Drive folder, recursively download that folder and it's children
    :param drive: The drive object
    :param folder: The folder to download
    :param download_to: The path to download to
    :return: None
    """
    children = list_folder(drive, folder['id'])
    if children is None:
        return
    for child in children:
        file_type = get_file_ext_type(child)
        if file_type is 'folder':
            new_dir = os.path.join(download_to, child['title'])
            if not os.path.isdir(new_dir):
                os.mkdir(new_dir)
            download_recursive(drive, child, new_dir)
        elif file_type is 'audio':
            download_file(child, download_to)
    return


def download_file(child, download_to):
    download_path = os.path.join(download_to, child['title'])
    print 'Downloading file {0} to: {1}'.format(child['title'].encode('utf-8'), download_path.encode('utf-8'))
    child.GetContentFile(download_path)
    return


# Upload

# TODO: Test and then use to upload instead.
def upload_recursive(drive, upload_name, upload_path, upload_to):
    """
    Given a Drive folder, recursively download that folder and it's children
    :param drive: The drive object
    :param upload_path: The path of the content to upload
    :param upload_to: The GoogleDriveFile to upload to
    :return: None
    """
    if os.path.isdir(upload_path):
        # This is a directory. Make a GDrive folder and recurse
        drive_parent = create_folder(drive, upload_name, upload_to['id'])
        for item_name in os.listdir(upload_path):
            item_path = os.path.join(upload_path, item_name)
            upload_recursive(drive, item_name, item_path, drive_parent)
    else:
        # This is a file. Upload it to the parent folder and return.
        upload_file(drive, upload_name, upload_path, upload_to)
        return
    return


def upload_file(drive, file_name, file_path, parent):
    """
    Uploads a file with a given parent.
    :param file_name: The name of the file to upload
    :param file_path: The local path of the file being uploaded.
    :param parent: The GoogleDriveFile of the parent
    :return:
    """
    print 'Uploading file {0} to: {1}'.format(file_path, parent['title'])
    new_drive_file = drive.CreateFile({'title': file_name, 'parents': [{'id': parent['id']}]})
    new_drive_file.SetContentFile(file_path)
    new_drive_file.Upload()
    return


# TODO: Deprecate and remove once recursive version is done.
def upload_album(drive, artist_name, album_path, album_name, collection):
    """
    Upload an album to Google Drive.
    :param drive
    :param artist_name
    :param album_path
    :param album_name
    """
    # Using the artist name see if it exists in the cache (on GDrive)
    # If it does, create a folder under it, and upload tracks from album_path
    # Else, Create a folder for the artist name. Then create the album under it and add the tracks
    if collection is not None and artist_name in collection:
        drive_artist = collection[artist_name].drive_file
    else:
        # we need the root folder of artists for this
        music_folder = get_folder_from_root(drive, config.load_google_drive_test_folder_name())
        drive_artist = create_folder(drive, artist_name, music_folder['id'])
    print "Uploading Album: {0} to Artist: {1}".format(album_path, artist_name)

    # We now have an Artist Folder, now upload an album folder.
    drive_album = create_folder(drive, album_name, drive_artist['id'])

    # Now create tracks under the folder
    for track_file_name in os.listdir(album_path):
        print "Uploading file: ", track_file_name
        track_path = os.path.join(album_path, track_file_name)
        if os.path.isdir(track_path):
            sub_dir = create_folder(drive, track_file_name, drive_album['id'])
            for sub_track in os.listdir(track_path):
                if not os.path.isdir(sub_track):
                    print "Uploading sub file: ", sub_track
                    sub_track_path = os.path.join(track_path, sub_track)
                    track = drive.CreateFile({'title': sub_track, 'parents': [{'id': sub_dir['id']}]})
                    track.SetContentFile(sub_track_path)
                    track.Upload()
        else:
            track = drive.CreateFile({'title': track_file_name, 'parents': [{'id': drive_album['id']}]})
            track.SetContentFile(track_path)
            track.Upload()
    return drive_album


def create_folder(drive, folder_name, parent_id):
    drive_folder = drive.CreateFile({'title': folder_name,
                                    "parents": [{"id": parent_id}],
                                     "mimeType": "application/vnd.google-apps.folder"})
    drive_folder.Upload()
    return drive_folder

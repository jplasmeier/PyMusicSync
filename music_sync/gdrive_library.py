import gdrive
import music_sync_utils
import logger
import sys


class GoogleDriveLibrary(music_sync_utils.MediaLibrary):
    def __init__(self, drive, root_folder_name):
        super(GoogleDriveLibrary, self).__init__()
        self.init_google_drive_collection(drive, root_folder_name)

    def init_google_drive_collection(self, drive, folder):
        """
        :param drive: the GoogleDrive object to pull metadata from Google Drive
        :param folder: the name of the folder to pull metadata from. Currently must be in the root folder
        """
        if self.collection is None:
            self.collection = {}

        drive_artists = gdrive.list_folder(drive, folder['id'])
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
        self.drive_file = drive_file
        super(DriveArtistItem, self).__init__(name)

    def get_albums_for_artist(self, drive, drive_artist):
        """
        Given an ArtistItem, find its albums in Drive and return a list of them
        :param drive: The GoogleDrive object
        :param drive_artist: The Drive Artist to get new albums from
        :return: A list of albums. Should include existing albums and new ones.
        """
        audio_in_artist = []
        drive_albums_added = []
        drive_albums = gdrive.list_folder(drive, drive_artist['id'])
        for drive_album in drive_albums:
            drive_album_name = gdrive.clean_unicode_title(drive_album)
            if drive_album_name not in self.albums and gdrive.get_file_ext_type(drive_album) is 'folder':
                new_album = DriveAlbumItem(drive, drive_album_name, drive_album)
                self.albums.append(new_album)
                drive_albums_added.append(drive_album)
            elif gdrive.get_file_ext_type(drive_album) is 'audio':
                audio_in_artist.append(drive_album_name)
        if audio_in_artist:
            for audio in audio_in_artist:
                logger.log_warning("Heads up, you have some audio files directly under an artist: {}".format(audio))
                print("\rHeads up, you have some audio files directly under an artist: {}".format(audio))
        return drive_albums_added


class DriveAlbumItem(music_sync_utils.AlbumItem):
    def __init__(self, drive, name, drive_file):
        file_size = gdrive.get_folder_size_drive(drive, drive_file['id'])
        super(DriveAlbumItem, self).__init__(name, file_size, drive_file)
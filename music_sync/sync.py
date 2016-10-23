# Do the actual sync in this module
import gdrive
import os
import subprocess

MYDIR = os.path.dirname(__file__)


def get_gdrive_albums_from_collection(drive, music_folder, collection):
    gdrive_artists = {}
    gdrive_albums = []
    for artist_name in collection:
        # find the folder with this name
        gdrive_artists[artist_name] = []
        drive_artists = gdrive.list_folder(drive, music_folder['id'])
        for d_a in drive_artists:
            if d_a['title'] == artist_name:
                drive_albums = gdrive.list_folder(drive, d_a['id'])
                for drive_album in drive_albums:
                    if drive_album['title'] in collection[artist_name].albums:
                        gdrive_albums.append(drive_album)
                        gdrive_artists[artist_name].append(drive_album)
    return gdrive_albums  # [gdrive_albums[g]['title'] for g in gdrive_albums]


def get_gdrive_artists_from_collection(drive, music_folder, collection):
    gdrive_artists = {}
    gdrive_albums = []
    for artist_name in collection:
        # find the folder with this name
        gdrive_artists[artist_name] = []
        drive_artists = gdrive.list_folder(drive, music_folder['id'])
        for d_a in drive_artists:
            if d_a['title'] == artist_name:
                drive_albums = gdrive.list_folder(drive, d_a['id'])
                for drive_album in drive_albums:
                    if drive_album['title'] in collection[artist_name].albums:
                        gdrive_albums.append(drive_album)
                        gdrive_artists[artist_name].append(drive_album)
    return gdrive_artists  # [gdrive_albums[g]['title'] for g in gdrive_albums]


def download_gdrive_locally(drive, music_folder, collection):
    # collection is a dict of artist_name - GDriveArtistItem object kvps
    artist_albums = get_gdrive_artists_and_albums_from_collection(drive, music_folder, collection)
    temp_music_dir = os.path.join(MYDIR, 'temp_music')
    os.mkdir(temp_music_dir)
    for artist in artist_albums:
        new_dir_artist = os.path.join(temp_music_dir, artist)
        os.mkdir(new_dir_artist)
        for album in artist_albums[artist]:
            tracks = gdrive.list_folder(drive, album['id'])
            new_dir_album = os.path.join(new_dir_artist, album['title'])
            os.mkdir(new_dir_album)
            print 'made dir ', new_dir_album
            for track in tracks:
                # Parameter is the filepath to download to. Let's try to use the USB path, eh?
                print 'Saving to: ', new_dir_album + '/' + track['title']
                track.GetContentFile('/{0}/'.format(new_dir_album) + track['title'])
    return temp_music_dir


def sync_music_from_temp_to_USB(usb_path, temp_music_path):
    artists = os.listdir(temp_music_path)
    for artist in artists:
        artist_path = os.path.join(usb_path, artist)
        temp_music_artist_path = os.path.join(temp_music_path, artist)
        if not os.path.isdir(artist_path):
            os.mkdir(artist_path)
        for album in os.listdir(temp_music_artist_path):
            temp_album_path = os.path.join(temp_music_artist_path, album)
            usb_album_path = os.path.join(artist_path,album)
            # Sync album from temp to usb
            folder_arguments = ['-r', temp_album_path, artist_path]
            print 'calling it yo ', ["rsync"] + folder_arguments
            returncode = subprocess.call(["rsync"] + folder_arguments)

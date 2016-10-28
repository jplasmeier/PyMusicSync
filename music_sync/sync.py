# Do the actual sync in this module
import gdrive
import os
import sys
import subprocess
import cannery
from subprocess import check_output, CalledProcessError
from collections import deque

raw_metadata_artists_path = 'raw_metadata_artists.p'
raw_metadata_albums_path = 'raw_metadata_albums.p'

MYDIR = os.path.dirname(__file__)
boot_disc_path = '/dev/disk1'


def check_df_output():
    try:
        return check_output(["df", "-k"]).split("\n")
    except CalledProcessError as err:
        print "Error making DF call: {}".format(err)
        sys.exit(1)


def get_free_space_on_local():
    df_output = check_df_output()
    for line in df_output:
        tokens = line.split()
        if tokens[0] == boot_disc_path:
            return int(tokens[3])/1024


def get_size_of_syncing_collection(drive, gdrive_collection):
    collection_cache = cannery.get_cached_independent_drive_collection()
    gdrive_sync_size = 0
    for gdrive_artist in gdrive_collection:
        if gdrive_artist in collection_cache:
            print 'Found artist {0} in cache!'.format(gdrive_artist)
            gdrive_sync_size += collection_cache[gdrive_artist].get_file_size_of_albums()
        else:
            print 'Artist not in cache.'
            gdrive_sync_size += gdrive.get_artist_size(drive, gdrive_artist['id'])

    gdrive_sync_size = gdrive_sync_size / 1024.0 / 1024.0
    return gdrive_sync_size


def get_gdrive_albums_from_collection(drive, music_folder, collection):
    gdrive_artists = {}
    gdrive_albums = []
    for artist_name in collection:
        # find the folder with this name
        gdrive_artists[artist_name] = []

        drive_artists = cannery.load_something(raw_metadata_albums_path)
        if artist_name in drive_artists:
            print "Found artist {0} in the cache.".format(artist_name)
            drive_albums = drive_artists[artist_name]
        else:
            print "Looking for artist {0} on GDrive".format(artist_name)
            for d_a in gdrive.list_folder(drive, music_folder['id']):
                if d_a['title'] == artist_name:
                    drive_albums = gdrive.list_folder(drive, d_a['id'])
                else:
                    drive_albums = []

        for drive_album in drive_albums:
            if drive_album['title'] in collection[artist_name].albums:
                gdrive_albums.append(drive_album)
                gdrive_artists[artist_name].append(drive_album)
    return gdrive_albums  # [gdrive_albums[g]['title'] for g in gdrive_albums]


#@profile
def get_gdrive_artists_from_collection(drive, music_folder, collection):
    albums_cache = cannery.load_something(raw_metadata_albums_path)
    if albums_cache is None:
        albums_cache = {}
    gdrive_artists = {}
    for artist_name in collection:
        # find the folder with this name
        gdrive_artists[artist_name] = []
        if artist_name in albums_cache:
            gdrive_artists[artist_name] = albums_cache[artist_name]
        else:
            drive_artists = gdrive.list_folder(drive, music_folder['id'])
            for d_a in drive_artists:
                if d_a['title'] == artist_name:
                    drive_albums = gdrive.list_folder(drive, d_a['id'])
                    for drive_album in drive_albums:
                        if drive_album['title'] in collection[artist_name].albums:
                            gdrive_artists[artist_name].append(drive_album)
    return gdrive_artists


def download_gdrive_locally(drive, music_folder, collection):
    # collection is a dict of artist_name - GDriveArtistItem object kvps
    artist_albums = get_gdrive_artists_from_collection(drive, music_folder, collection)
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


def sync_artist_from_temp_to_USB_and_delete(artist_path, temp_music_artist_path):
    for album in os.listdir(temp_music_artist_path):
        temp_album_path = os.path.join(temp_music_artist_path, album)
        usb_album_path = os.path.join(artist_path,album)
        # Sync album from temp to usb
        folder_arguments = ['-r', temp_album_path, artist_path]
        print 'calling it yo ', ["rsync"] + folder_arguments
        returncode = subprocess.call(["rsync"] + folder_arguments)
    # Delete shit
    delete_arguments = ['-rf', temp_music_artist_path]
    returncode2 = subprocess.call(["rm"] + delete_arguments)


def buffered_sync_gdrive_to_usb(drive, gdrive_collection, usb_path):
    """
    Laptop doesn't have enough space to store all of the music that needs to go from Drive to USB
    So we need to sync some stuff then delete it.
    :param drive:
    :param gdrive_collection: the return from get_gdrive_artist TBH (artist_name: list of gdrive albums
    :param usb_file_path:
    :return:
    """
    # Get the size of the next album? artist? to download
    # Get size of local
    # If there's enough space, sync
    # Else, Rsync buffer to USB

    # Collection is artist ->
    artist_queue = deque()
    artist_queue.extend(gdrive_collection.keys())
    collection_cache = cannery.get_cached_independent_drive_collection()
    temp_music_dir = os.path.join(MYDIR, 'temp_music')
    if not os.path.isdir(temp_music_dir):
        os.mkdir(temp_music_dir)

    while artist_queue:
        artist_name = artist_queue.popleft()
        artist_path = os.path.join(usb_path, artist_name)

        new_dir_artist = os.path.join(temp_music_dir, artist_name)
        if not os.path.isdir(new_dir_artist):
            os.mkdir(new_dir_artist)
        space_on_local = get_free_space_on_local()
        if artist_name in collection_cache:
            artist_size = collection_cache[artist_name].get_file_size_of_albums()
        else:
            # Do it the shitty way
            artist_size = 9999999999999
        if artist_size < space_on_local:
            for album in gdrive_collection[artist_name]:
                tracks = gdrive.list_folder(drive, album['id'])
                new_dir_album = os.path.join(new_dir_artist, album['title'])
                os.mkdir(new_dir_album)
                print 'made dir ', new_dir_album
                for track in tracks:
                    # Parameter is the filepath to download to. Let's try to use the USB path, eh?
                    print 'Saving to: ', new_dir_album + '/' + track['title']
                    track.GetContentFile('/{0}/'.format(new_dir_album) + track['title'])

        # Artist downloaded to client machine, now sync
        sync_artist_from_temp_to_USB_and_delete(artist_path, new_dir_artist)

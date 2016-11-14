# Do the actual sync in this module
import gdrive
import os
import sys
import subprocess
from subprocess import check_output, CalledProcessError
from collections import deque, OrderedDict


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


def get_size_of_syncing_collection(sync_collection, drive_collection):
    """
    Gets the size of the files to be sync'd.
    :param sync_collection: The albums to sync.
    :param drive_collection: The whole Google Drive collection
    :return:
    """
    gdrive_sync_size = 0
    for gdrive_artist in sync_collection:
        gdrive_sync_size += drive_collection[gdrive_artist].get_file_size_of_albums()

    gdrive_sync_size = gdrive_sync_size / 1024.0 / 1024.0
    return gdrive_sync_size


# TODO: Remove. Can just use sync_collection directly...
def get_gdrive_artists_from_collection(sync_collection, drive_collection):
    """
    This skips the ArtistItem and Album objects and returns a dict of artist_name: [drive_album] kvps.
    :param sync_collection: The collection of things to sync of artist_name: ArtistItem kvps
    :param drive_collection: The collection of artist_name: ArtistItem kvps.
    :return:
    """
    gdrive_artists = {}
    for artist_name in sync_collection:
        # find the folder with this name
        gdrive_artists[artist_name] = [a.drive_file for a in drive_collection[artist_name].albums]
    return gdrive_artists


def sync_artist_from_temp_to_usb_and_delete(artist_path, temp_music_artist_path):
    for album in os.listdir(temp_music_artist_path):
        temp_album_path = os.path.join(temp_music_artist_path, album)
        # Sync album from temp to usb
        folder_arguments = ['-r', temp_album_path, artist_path]
        print 'Syncing: ', ["rsync"] + folder_arguments
        returncode = subprocess.call(["rsync"] + folder_arguments)
    # Delete shit
    delete_arguments = ['-rf', temp_music_artist_path]
    returncode2 = subprocess.call(["rm"] + delete_arguments)
    return

# TODO: What the hell? Fix this crap
def delete_folder(folder=None):
    if folder is None:
        folder = os.path.join(MYDIR, 'temp_music')
    delete_arguments = ['-rf', folder]
    return subprocess.call(["rm"] + delete_arguments)


def buffered_sync_gdrive_to_usb(drive, sync_collection, usb_path, drive_collection):
    """`
    Local machine doesn't have enough space to store all of the music that needs to go from Drive to USB.
    Also can't download directly to USB for some reason.
    So we need to sync some stuff then delete it.
    :param drive:
    :param sync_collection: artist_name: list of drive_albums
    :param usb_path: the path to the root of the USB device
    :param drive_collection: the whole collection of artist_name: ArtistItem objects
    :return: None.
    """
    # Get the size of the next album? artist? to download
    # Get size of local
    # If there's enough space, sync
    # Else, Rsync buffer to USB

    print 'Syncing collection to USB Path: ', usb_path
    artist_queue = deque()
    artist_queue.extend(sync_collection.keys())
    temp_music_dir = os.path.join(MYDIR, 'temp_music')
    if not os.path.isdir(temp_music_dir):
        os.mkdir(temp_music_dir)

    while artist_queue:
        artist_name = artist_queue.popleft()
        usb_artist_path = os.path.join(usb_path, artist_name)
        print 'Syncing artist {0} to path {1}'.format(artist_name, usb_artist_path)
        new_dir_artist = os.path.join(temp_music_dir, artist_name)
        if not os.path.isdir(new_dir_artist):
            os.mkdir(new_dir_artist)
        space_on_local = get_free_space_on_local()
        artist_size = drive_collection[artist_name].get_file_size_of_albums()/1024/1024
        print 'Artist {0} is size {1}.'.format(artist_name, artist_size)
        print 'We have {0} mb left on local machine.'.format(space_on_local)
        if artist_size < space_on_local:
            for album_item in sync_collection[artist_name].albums:
                new_dir_album = os.path.join(new_dir_artist, album_item.name)
                if not os.path.isdir(new_dir_album):
                    os.mkdir(new_dir_album)
                print "Going to recursively download album: {0} to path: {1}".format(album_item.name, new_dir_album)
                gdrive.download_recursive(drive, album_item.drive_file, new_dir_album)
        # Artist downloaded to client machine, now sync
        sync_artist_from_temp_to_usb_and_delete(usb_artist_path, new_dir_artist)

    # delete temp music
    delete_folder(temp_music_dir)

    return


def remove_extra_bins(bins, min_size):
    for idx, bin in enumerate(bins):
        if bin[1] - bin[0] < min_size:
            # Check if bin below and get size
            if idx - 1 >= 0:
                below_size = bins[idx-1][1] - bins[idx-1][0]
            if idx + 1 < len(bins):
                above_size = bins[idx+1][1] - bins[idx+1][0]


def bin_folder(path):
    """
    Given a path containing only folders, group the folders into a fixed number of bins by alphabet.
    :param path: The path containing folders to put into bins.
    :return: Fuck if I know
    """

    # Okay well I guess we should get a list of the directories to bin
    sub_dirs = []

    dir_contents = os.listdir(path)
    for item in dir_contents:
        item_path = os.path.join(path,item)
        if os.path.isdir(item_path) and '.' != item_path.startswith('.'):
            sub_dirs.append(item)
    print dir_contents
    # So now we need to figure out how to bin these folders.
    # At current scale (260 artist), as few as 5 bins is good.
    # I'm going to say auto mode is floor of num of artists divided by a bin size 50.
    bin_size = 50
    num_bins = len(sub_dirs) / bin_size

    # Now that we have the number of bins, we need to make the bins
    # Make a dict of the index of the last Artist starting with that character.
    char_index = OrderedDict()
    rev_char_index = OrderedDict()

    sub_dirs = sorted(sub_dirs)
    incoming_char = sub_dirs[0][0]
    for idx, artist in enumerate(sub_dirs):
        c_0 = artist[0]
        if c_0 != incoming_char:
            # new char
            rev_char_index[idx-1] = incoming_char
            char_index[incoming_char] = idx - 1
            incoming_char = c_0

    # Cool, now we just need to assign the bins.
    # First bin needs to start at 0 and last bin needs to end at len - 1 of course
    bins = []
    incoming_bin_idx = 0
    j = 0
    lagging_char = ''
    for i in range(0, num_bins-1):
        for char in char_index:
            target_end = incoming_bin_idx + bin_size
            print 'Bin {0}. Target folder idx is {1}. Checking char {2} w index {3}'.format(i, target_end, char, char_index[char])
            if char_index[char] > target_end and lagging_char and char_index[lagging_char] > incoming_bin_idx:
                print 'That\'s it for this bin. Including up to folder at idx {0}'.format(char_index[lagging_char])
                bins.append((incoming_bin_idx, char_index[lagging_char]))
                incoming_bin_idx = char_index[lagging_char]
            lagging_char = char

    bins.append((char_index[sorted(char_index.keys())[-2:][0]], char_index[char_index.keys()[-1:][0]]))
    print 'bins ', bins

    # Trim any tins bins (less than half spec size)
    remove_extra_bins(bins, bin_size/2)


def upload_collection_to_gdrive(drive, sync_collection, usb_path, drive_collection):
    for artist_name in sync_collection:
        artist_path = os.path.join(usb_path, artist_name)
        for album_item in sync_collection[artist_name].albums:
            album_path = os.path.join(artist_path, album_item.name)
            gdrive.upload_album(drive, artist_name, album_path, album_item.name, drive_collection)

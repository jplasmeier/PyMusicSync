# Do the actual sync in this module
import config
import copy
import gdrive
import gdrive_folder
import general_sync_utils
import os
import sys
import usb
from subprocess import getoutput, CalledProcessError, call
from collections import deque, OrderedDict

BIN_SIZE = 40
MYDIR = os.path.dirname(__file__)
boot_disc_path = config.load_boot_disk_path()


# General Sync

def one_way(source, destination, clean_unicode):
    pass


def one_way_delete(source, destination, clean_unicode):
    pass


def two_way(drive, drive_root, usb_root, usb_path, clean_unicode):
    """
    Omni-directional sync across two or more devices.
    Sets each device equal to the union of all devices.
    First we construct the union.
    Then we diff each device against the union.
    Then, copy the difference from the union to that device.
    :param sources: A list of general_sync_utils.Folder objects.
    :param clean_unicode: If true, clean unicode names on Drive folders/files.
    :return: The union? Maybe a status code?
    """
    union_folder = union([drive_root, usb_root])
    missing_from_drive = subtraction(union_folder, drive_root)
    missing_from_usb = subtraction(union_folder, usb_root)

    # do this to not download "Difference Root"
    for item in missing_from_usb.contents:
        gdrive_folder.download_contents(drive, item, usb_path)

    usb.upload_contents(drive, missing_from_drive, drive_root)


def two_way_delete(drive, drive_root, usb_root, usb_path, clean_unicode):
    """
    TODO: Implement this. First need to implement delete on both Folder subclasses.
    :param drive:
    :param drive_root:
    :param usb_root:
    :param usb_path:
    :param clean_unicode:
    :return:
    """
    pass


def subtraction(a, b, difference_root=None):
    """
    Subtract folder from union_folder and return the difference.
    :param a:
    :param b:
    :return:
    """
    if difference_root is None:
        difference_root = general_sync_utils.Folder("Difference Root")
    if isinstance(a, general_sync_utils.File):
        difference_root.contents.append(a)
        return difference_root
    elif isinstance(a, general_sync_utils.Folder):
        for item in a.contents:
            if isinstance(item, general_sync_utils.File) and item not in b.contents:
                difference_root.contents.append(item)
            elif isinstance(item, general_sync_utils.Folder):
                if item in b.contents:
                    folder_item = b.contents_map[item.name]
                    if folder_item is None:
                        print("contents map didn't work???")
                        folder_item = next(i for i in b.contents if i == item)
                else:
                    folder_item = general_sync_utils.Folder("Folder Item")  # make a dummy folder to subtract against
                sub_folder = general_sync_utils.Folder(item.name)
                difference_subfolder = subtraction(item, folder_item, sub_folder)
                if difference_subfolder.contents:
                    difference_root.contents.append(difference_subfolder)
        return difference_root
    else:
        return difference_root


def union(folders):
    """
    Given a list of folders, that is, general_sync_utils.Folder objects
    Return the union of all folders.
    :param folders: A list of general_sync_utils.Folder objects
    :return:
    """
    # We allow devices to have different roots. Keep the contents of each root in Union Root.
    union_root = general_sync_utils.Folder("Union Root")
    for root in folders:
        # Omit the root folder
        for folder in root.contents:
            union_root = add_contents_recursive(union_root, folder)
    return union_root


def intersection(folders, intersection_root=None):
    """
    Given a list of folders, that is, general_sync_utils.Folder objects
    Return the intersection of all folders.
    :param folders: A list of general_sync_utils.Folder objects
    :return:
    """
    if intersection_root is None:
        intersection_root = general_sync_utils.Folder("Intersection Root")
    for root in folders:
        # Omit the root
        for item in root.contents:
            cousins = [] # items in other folders with same name
            for folder in folders:
                if item in folder.contents:
                    cousin, = [i for i in folder.contents if i == item]
                    cousins.append(cousin)
            if len(cousins) == len(folders) and item not in intersection_root.contents:
                if isinstance(item, general_sync_utils.File):
                    intersection_root.contents.append(item)
                elif isinstance(item, general_sync_utils.Folder):
                    subfolder = general_sync_utils.Folder(item.name)
                    intersection_root.contents.append(intersection(cousins, subfolder))
    return intersection_root


def add_contents_recursive(destination, source):
    """
    Add the contents of source to destination, recursively.
    :param destination:
    :param source:
    :return:
    """
    if isinstance(source, general_sync_utils.File):
        if source not in destination.contents:
            destination.contents.append(source)
        return destination
    else:
        if source not in destination.contents:
            new_folder = copy.deepcopy(source)
            new_folder.contents = []
            destination.contents.append(new_folder)
            for item in source.contents:
                add_contents_recursive(new_folder, item)
            return destination
        else:
            source_in_destination, = [d for d in destination.contents if d.name == source.name]
            for item in source.contents:
                add_contents_recursive(source_in_destination, item)
            return destination

# Legacy Sync


def check_df_output():
    try:
        return getoutput("df -k").split("\n")
    except CalledProcessError as err:
        print("Error making DF call: {}".format(err))
        sys.exit(1)


def get_free_space_on_local():
    df_output = check_df_output()
    for line in df_output:
        tokens = line.split()
        if tokens[0] == boot_disc_path:
            return int(tokens[3]) / 1024


def sym_link_artist_from_temp_to_usb_and_delete(artist_path, temp_music_artist_path):
    if not os.path.isdir(artist_path):
        os.mkdir(artist_path)
    # Symlink album from temp to usb
    folder_arguments = ['-s', temp_music_artist_path, artist_path]
    print('Symlinking: ', ["ln"] + folder_arguments)
    returncode = call(["ln"] + folder_arguments)
    # Delete shit
    #delete_arguments = ['-rf', temp_music_artist_path]
    #returncode2 = subprocess.call(["rm"] + delete_arguments)
    return


# TODO: Fix this crap
def sync_artist_from_temp_to_usb_and_delete(artist_path, temp_music_artist_path):
    if not os.path.isdir(artist_path):
        os.mkdir(artist_path)
    for album in os.listdir(temp_music_artist_path):
        temp_album_path = os.path.join(temp_music_artist_path, album)
        # Sync album from temp to usb
        folder_arguments = ['-r', temp_album_path, artist_path]
        print('Syncing: ', ["rsync"] + folder_arguments)
        returncode = call(["rsync"] + folder_arguments)
    # Delete shit
    delete_arguments = ['-rf', temp_music_artist_path]
    returncode2 = call(["rm"] + delete_arguments)
    return


# TODO: What the hell? Fix this crap
def delete_folder(folder=None):
    if folder is None:
        folder = os.path.join(MYDIR, 'temp_music')
    delete_arguments = ['-rf', folder]
    return call(["rm"] + delete_arguments)


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

    print('Syncing collection to USB Path: ', usb_path)
    artist_queue = deque()
    artist_queue.extend(list(sync_collection.keys()))
    temp_music_dir = os.path.join(MYDIR, 'temp_music')
    if not os.path.isdir(temp_music_dir):
        os.mkdir(temp_music_dir)

    while artist_queue:
        artist_name = artist_queue.popleft()
        usb_artist_path = os.path.join(usb_path, artist_name)
        print('Syncing artist {0} to path {1}'.format(artist_name, usb_artist_path))
        new_dir_artist = os.path.join(temp_music_dir, artist_name)
        if not os.path.isdir(new_dir_artist):
            os.mkdir(new_dir_artist)
        space_on_local = get_free_space_on_local()
        artist_size = drive_collection[artist_name].get_file_size_of_albums() / 1024 / 1024
        print('Artist {0} is size {1}.'.format(artist_name, artist_size))
        print('We have {0} mb left on local machine.'.format(space_on_local))
        if artist_size < space_on_local:
            for album_item in sync_collection[artist_name].albums:
                new_dir_album = os.path.join(new_dir_artist, album_item.name)
                if not os.path.isdir(new_dir_album):
                    os.mkdir(new_dir_album)
                print("Going to recursively download album: {0} to path: {1}".format(album_item.name, new_dir_album))
                gdrive.download_recursive(drive, album_item.drive_file, new_dir_album)
        # Artist downloaded to client machine, now sync
        sync_artist_from_temp_to_usb_and_delete(usb_artist_path, new_dir_artist)

    # delete temp music
    delete_folder(temp_music_dir)

    return


def unbin_folder(folder_path):
    """
    The inverse of bin_folder.
    :param folder_path:
    :return:
    """
    bin_paths = [os.path.join(folder_path, p) for p in os.listdir(folder_path) if not p.startswith('.') and '-' in p]
    bin_dirs = [p for p in bin_paths if os.path.isdir(p)]
    for bin_path in bin_dirs:
        bin_contents = os.listdir(bin_path)
        for artist_name in bin_contents:
            new_artist_path = os.path.join(folder_path, artist_name)
            old_artist_path = os.path.join(bin_path, artist_name)
            sym_link_artist_from_temp_to_usb_and_delete(new_artist_path, old_artist_path)
        delete_folder(bin_path)


def bin_folder(folder_path):
    """
    Given a path, take its contents and put those items into buckets, alphabetically.

    Given a bin size, we aim to minimize the sum of square residuals,
    Where the residual is the difference between the expected end index of the next bin
    And the closest available index.

    :param folder_path: The path to bin
    :return: Dict of index: bin_size pairs
    """
    # Get folders to bin
    folders = get_folders_from_path(folder_path)

    # Get idx: char ordered dict
    boundaries = get_character_boundaries(folders)
    # The list of indicies which should end each bin.
    bin_indicies = sorted(get_bin_indicies(boundaries, 0, len(folders)))
    print('bin indicies', bin_indicies)

    # bin_name: [] of names
    bin_dict = {}
    boundary = True
    lag_char_idx = 0
    for char_idx in boundaries:
        if boundary:
            # start of bin
            boundary = False
            new_bin_name = str(boundaries[char_idx].upper() + ' - ')

        if char_idx in bin_indicies:
            # end of bin
            boundary = True
            new_bin_name = new_bin_name + boundaries[char_idx].upper()
            bin_dict[new_bin_name] = folders[lag_char_idx:char_idx+1]
            lag_char_idx = char_idx+1

    for bin_name in bin_dict:
        print('Bin: {0} has contents: \n{1}'.format(bin_name, bin_dict[bin_name]))

    for bin_name in bin_dict:
        # make a directory
        bin_path = os.path.join(folder_path, bin_name)
        print('Processing bin at: ', bin_path)
        if not os.path.isdir(bin_path):
            os.mkdir(bin_path)
        for artist_name in bin_dict[bin_name]:
            new_artist_path = os.path.join(bin_path, artist_name)
            old_artist_path = os.path.join(folder_path, artist_name)
            sym_link_artist_from_temp_to_usb_and_delete(new_artist_path, old_artist_path)


def get_bin_indicies(boundaries, current_index, last_index, bin_indicies=None):
    """
    Get the indicies to end each bin at.
    Works pretty well so far, but need to fix last tiny bin.
    :param boundaries: The ends of each character
    :param current_index: The current index
    :param last_index: The value of the last index.
    :param bin_indicies: The list of indicies to fill and return.
    :return: bin_indicies
    """
    if bin_indicies is None:
        bin_indicies = []

    target_index = current_index + BIN_SIZE

    # We don't want the last bin to be less than half of BIN_SIZE
    if target_index + (BIN_SIZE / float(2)) > last_index or target_index > last_index:
        bin_indicies.append(last_index)
        return bin_indicies
    else:
        closest_index = get_closest_index(boundaries, target_index)
        bin_indicies.append(closest_index)
        return get_bin_indicies(boundaries, closest_index, last_index, bin_indicies)


def get_closest_index(boundaries, target_index):
    boundary_indicies = list(boundaries.keys())
    closest_val = abs(target_index - boundary_indicies[0])
    closest_key_idx = 0
    for idx in boundaries:
        if abs(target_index - idx) < closest_val:
            closest_val = abs(target_index - idx)
            closest_key_idx = idx
    return closest_key_idx


def get_character_boundaries(items):
    """
    Given a list of names, return the indicies which are a boundary between characters.
    So the entry 12: A would mean that the entry at index 12 is the last entry for A.
    :param items: list of folders
    :return: dict of (idx: character)
    """
    boundaries = OrderedDict()
    start = 0
    char = items[start][0].lower()
    for idx, item in enumerate(items):
        if item[0].lower() != char:
            boundaries[idx - 1] = char
            char = item[0].lower()
    boundaries[len(items)] = items[-1:][0][0].lower()
    for idx in boundaries:
        print('Index : \'{0}\' is the end of character {1}.'.format(idx, boundaries[idx]))

    return boundaries


def get_folders_from_path(path):
    sub_dirs = []
    dir_contents = os.listdir(path)
    for item in dir_contents:
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path) and not item.startswith('.'):
            sub_dirs.append(item)
    return sorted(sub_dirs, key=lambda s: s.lower())

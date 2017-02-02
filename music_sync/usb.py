# usb.py
# A module to find and save USB device information on a Mac.
# Author: J. Plasmeier | jplasmeier@gmail.com
# License: MIT License
from subprocess import CalledProcessError, getoutput
import general_sync_utils
import gdrive
import logger
import music_sync_utils
import os
import sys


class USBLibrary(music_sync_utils.MediaLibrary):
    """
    USB Device specific collection. Includes file path of device.
    """
    def __init__(self, path):
        super(USBLibrary, self).__init__(os.path.getmtime(path))
        self.file_path = path
        self.get_usb_collection()

    def get_usb_collection(self):
        """
        Get a collection of Artist names and objects from the path selected before.
        """
        if self.collection is None:
            self.collection = {}
        artist_names = get_folder_names(self.file_path)
        for artist_name in artist_names:
            # Create an ArtistItem
            artist_path = os.path.join(self.file_path, artist_name)
            artist_item = music_sync_utils.ArtistItem(artist_name, get_last_mod_by(artist_path))
            self.collection[artist_name] = artist_item

            # Now get the albums
            album_items = get_album_items(artist_path)
            # If there aren't any, log a warning.
            if album_items is None:
                logger.log_warning("Artist {0} has no albums.".format(artist_name))
            else:
                self.collection[artist_name].albums = album_items
        return self


class USBAlbumItem(music_sync_utils.AlbumItem):
    def __init__(self, album_name, album_path):
        file_size = get_directory_size(album_path)
        super(USBAlbumItem, self).__init__(album_name, file_size)


class USBFolder(general_sync_utils.Folder):

    def __init__(self, path):
        name = os.path.basename(path)
        super(USBFolder, self).__init__(name)
        self.path = path

    def __str__(self):
        return self.name


class USBFile(general_sync_utils.File):

    def __init__(self, path):
        if os.path.isdir(path):
            raise os.error("Error: cannot create file from directory, silly")
        name = os.path.basename(path)
        size = os.path.getsize(path)
        super(USBFile, self).__init__(name, size)
        self.path = path

    def __str__(self):
        return self.name


def build_folder(path):
    """
    Return the contents of a folder, recursively
    :param path:
    :return:
    """
    if not os.path.isdir(path):
        return USBFile(path)
    else:
        usb_folder = USBFolder(path)
        drive_folder_contents = os.listdir(path)
        for item in drive_folder_contents:
            print("Processing: ", item)
            usb_folder.contents.append(build_folder(os.path.join(path, item)))
    return usb_folder


def upload_contents(drive, usb_folder, drive_folder):
    """
    Upload the contents of the given usb folder to Google Drive.
    :param drive:
    :param usb_folder:
    :param drive_folder:
    :return:
    """
    if isinstance(usb_folder, USBFile):
        gdrive.upload_file(drive, usb_folder.name, usb_folder.path, drive_folder)
        return usb_folder
    elif isinstance(usb_folder, general_sync_utils.Folder):
        for item in usb_folder.contents:
            if isinstance(item, general_sync_utils.Folder):
                if not item in drive_folder.contents:
                    new_folder = gdrive.create_folder(drive, item.name, drive_folder.drive_file['id'])
                else:
                    new_folder, = [f for f in drive_folder.contents if f == item]
                upload_contents(drive, item, new_folder)
            elif isinstance(item, USBFile):
                gdrive.upload_file(drive, item.name, item.path, drive_folder.drive_file)
        return drive_folder
    return drive_folder


class DFDevice:
    """
    Class to store information about a device from df
    """
    def __init__(self, df_tokens):
        self.filesystem = df_tokens[0]
        self.size = df_tokens[1]
        self.used = df_tokens[2]
        self.avail = int(df_tokens[3])
        self.capacity = df_tokens[4]
        self.iused = df_tokens[5]
        self.ifree = df_tokens[6]
        self.pct_iused = df_tokens[7]
        self.mounted_on = df_tokens[8]

    def get_free_space(self):
        return self.avail

    def __str__(self):
        return self.mounted_on


# check_output calls


def check_df_output():
    try:
        # Skip the first item, it's just the headers.
        return getoutput("df -k -T exfat").split("\n")[1:]
    except CalledProcessError as err:
        print("Error making DF call: {}".format(err))
        sys.exit(1)


# os calls
# we ensure that file paths still exist in case we are on a flaky FS


def get_last_mod_by(artist_path):
    try:
        return os.path.getmtime(artist_path)
    except OSError as err:
        print('Artist path {0} no longer exists: {1}'.format(artist_path, err))
        sys.exit(1)


def get_directory_size(album_path):
    try:
        if os.path.isdir(album_path):
            return os.path.getsize(album_path)
        else:
            return
    except OSError as err:
        print('Directory at {0} no longer exists: {1}'.format(album_path, err))
        sys.exit(1)


def get_folder_names(device_path):
    try:
        folder_paths = []
        # Get non-hidden contents
        contents = [f for f in os.listdir(device_path) if not f.startswith('.')]

        # Only return directories
        for item_name in contents:
            item_path = os.path.join(device_path, item_name)
            if os.path.isdir(item_path):
                folder_paths.append(item_name)
        return folder_paths
    except OSError as err:
        print("Error accessing USB device: ", err)
        sys.exit(1)


def get_folder_paths(device_path):
    try:
        folder_paths = []
        # Get non-hidden contents
        contents = [f for f in os.listdir(device_path) if not f.startswith('.')]

        # Only return directories
        for item in contents:
            item_path = os.path.join(device_path, item)
            if os.path.isdir(item_path):
                folder_paths.append(item_path)
        return folder_paths
    except OSError as err:
        print("Error accessing USB device: ", err)
        sys.exit(1)


def get_df_devices():
    """
    Should return a list of DF objects.
    """
    exfat_devices = check_df_output()
    df_objects = []
    for exfat_device in exfat_devices:
        tokens = exfat_device.split()
        if len(tokens) >= 9:
            df_objects.append(DFDevice(tokens))
    return df_objects


def get_df_info_for_device(device_path):
    df_devices = get_df_devices() 
    if len(df_devices) <= 0:
        raise Exception("No USB Device Connected.")
    for df_device in df_devices:
        if df_device.mounted_on == device_path:
            return df_device
    raise Exception("Could not find an exfat device in df with path: {0}".format(device_path))


def get_album_items(artist_path):
    album_items = []
    album_names = get_folder_names(artist_path)
    for album_name in album_names:
        album_path = os.path.join(artist_path, album_name)
        album_items.append(USBAlbumItem(album_name, album_path))
    return album_items

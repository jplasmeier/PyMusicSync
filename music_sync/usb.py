# usb.py
# A module to find and save USB device information on a Mac.
# Author: J. Plasmeier | jplasmeier@gmail.com
# License: MIT License
from subprocess import check_output, CalledProcessError
import logger
import os
import pprint
import re
import sys
import music_sync_utils


class USBLibrary(music_sync_utils.MediaLibrary):
    """
    USB Device specific collection. Includes file path of device.
    """
    def __init__(self, path):
        super(USBLibrary, self).__init__(os.path.getmtime(path))
        self.file_path = path
        self.get_usb_collection()
        self.clean_unicode()

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


class DFDevice:
    """
    Class to store information about a device from df
    Might not need this........?
    """

    # def __init__(self, filesystem, size, used, avail, capacity, iused, ifree, pct_iused, mounted_on):
    #    self.filesystem = filesystem
    #    self.size = size
    #    self.used = used
    #    self.avail = avail
    #    self.capacity = capacity
    #    self.iused = iused
    #    self.ifree = ifree
    #    self.pct_iused = pct_iused
    #    self.mounted_on = mounted_on
    
    def __init__(self, identifier):
        self.identifier = identifier

    # wtf is this shit
    def set_df_info(self, df_list):
        self.filesystem = df_list[0] 
        self.size = df_list[1]
        self.used = df_list[2]
        self.avail = df_list[3]
        self.capacity = df_list[4]
        self.iused = df_list[5]
        self.ifree = df_list[6]
        self.pct_iused = df_list[7]
        self.mounted_on = df_list[8]

    def get_free_space(self):
        return self.avail

    def __str__(self):
        return self.mounted_on


# check_output calls


# ship
def check_df_output():
    try:
        return check_output(["df", "-k", "-T", "exfat"]).split("\n")
    except CalledProcessError as err:
        print "Error making DF call: {}".format(err)
        sys.exit(1)


# ship
def check_ioreg_output():
    try:
        return check_output(["ioreg", "-p", "IOUSB", "-l", "-w", "0"]).split("+-o")
    except CalledProcessError as err:
        print "Error making IOREG call: {}".format(err)
        sys.exit(1)


# os calls
# we ensure that file paths still exist in case we are on a flaky NFS


# ship
def get_last_mod_by(artist_path):
    try:
        return os.path.getmtime(artist_path)
    except OSError as err:
        print 'Artist path no longer exists'
        sys.exit(1)


# ship
def get_album_list(artist_path):
    try:
        return os.listdir(artist_path)
    except OSError as err:
        print 'Artist path no longer exists: ', err
        sys.exit(1)


# ship
def get_directory_size(album_path):
    try:
        if os.path.isdir(album_path):
            return os.path.getsize(album_path)
        else:
            return
    except OSError as err:
        print 'Directory at {0} no longer exists: {1}'.format(album_path, err)
        sys.exit(1)


# ship
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
        print "Error accessing USB device: ", err
        sys.exit(1)


# ship
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
        print "Error accessing USB device: ", err
        sys.exit(1)


# TODO: Refactor this shit show
def get_ioreg_devices():
    devices = check_ioreg_output()
    ioreg_info = {}
    for dev in devices:
        lines = dev.split("\n")
        this_device = {}
        for line in lines:
            if "sessionID" in line:
                sessionID = re.search(r'\d+',line).group(0)
            if "USB Vendor Name" in line:
                usb_vendor_name = line
            if "USB Product Name" in line:
                usb_product_name = line
            if "USB Serial Number" in line:
                usb_serial_number = line
        try: 
            this_device["USB Vendor Name"] = usb_vendor_name
            this_device["USB Product Name"] = usb_product_name
            this_device["USB Serial Number"] = usb_serial_number
            # We use sessionID as the key
            ioreg_info[sessionID] = this_device
        except Exception, err:
            print "Error while reading from IOReg: {}".format(err)
    return ioreg_info


def get_df_devices():
    """
    Should return a list of DF objects.
    """
    df_info = {}
    results = check_df_output()
    df_objects = []
    for res in results[1:]:
        tokens = res.split()
        if len(tokens) >= 9:
            df_obj = DFDevice(tokens[8])
            df_obj.set_df_info(tokens)
            df_objects.append(df_obj)
    return df_objects


def print_dict_list(dict_to_print):
    for key in dict_to_print:
            print dict_to_print[key], '\n'


# Expose these functions to main
# TODO: Actually give the user a choice...
def pick_from_df():
    df_devices = get_df_devices() 
    if len(df_devices) >= 1:
        return df_devices[0]
    else:
        raise Exception("No USB Device Connected.")


# TODO: Actually give the user a choice...
def pick_from_ioreg():
    ioreg_devices = get_ioreg_devices() 
    for idx, dev in enumerate(ioreg_devices):
        print "Device {0}: ".format(idx)
        ioreg_devices[dev]["Device"] = idx
        pprint.pprint(ioreg_devices[dev])
    # prompt user selection
    choice = int(raw_input("Enter the number of the device which you would like to sync:"))
    return [ioreg_devices[dev] for dev in ioreg_devices if ioreg_devices[dev]["Device"] == choice]


def get_album_items(artist_path):
    album_items = []
    album_names = get_folder_names(artist_path)
    for album_name in album_names:
        album_path = os.path.join(artist_path, album_name)
        album_items.append(music_sync_utils.AlbumItem(album_name, album_path))
    return album_items

# usb.py
# A module to find and save USB device information on a Mac.
# Author: J. Plasmeier | jplasmeier@gmail.com
# License: MIT License
from subprocess import check_output, CalledProcessError
import os
import re
import pprint
import sys
import music_sync_utils

# TODO: Refactor globals
df_info = {}
device_info = {}


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


class USB_Device:
    """
    Class to keep track of USB device information.
    Might not need this........?
    The reason we had this originally was to be able to save devices
    But since we can't tie DF and IOREG together, what's the point? most likely we will just pick each time.
    But for caching, we want to give a unique ID for each player. Use IOREG sn + getmtime for custom etag?
    """
    
    def __init__(self, nickname):
        self.IOReg_info = {}
        self.DF_info = {}
        self.nickname = nickname

    def get_free_space(self):
        return self.DF_info['Avail']


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
        print 'Artist path no longer exists.'
        sys.exit(1)


# ship
def get_album_size(album_path):
    try:
        if os.path.isdir(album_path):
            return os.path.getsize(album_path)
        else:
            return
    except OSError as err:
        print 'Album candidate no longer exists.'
        sys.exit(1)


# ship
def get_artists(device_path):
    try:
        return os.listdir(device_path)
    except OSError as err:
        print "Error accessing USB device: {}".format(err)
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


# ship!
def get_usb_collection(device_path):
    """
    Get a collection of Artist names and objects from the path selected before.
    """
    usb_collection = {} 
    artists = get_artists(device_path)
    for artist in artists:
        # TODO: Replace with artist_path = os.path.join(device_path, artist) on successful test
        artist_path = device_path + '/' + artist

        # Only grab directories and non-hidden files
        # They are hidden for chrissakes
        if os.path.isdir(artist_path) and not artist.startswith('.'):
            artist_item = music_sync_utils.ArtistItem(artist, get_last_mod_by(artist_path))
            usb_collection[artist] = artist_item
            album_list = get_album_items(artist_path)
            if album_list is not None:
                usb_collection[artist].albums = album_list
    return usb_collection


# ship
def get_album_item_from_path(album_path, album_candidate):
    album_size = get_album_size(album_path)
    if album_size is not None:
        return music_sync_utils.AlbumItem(album_candidate, album_size)
    else:
        return


# ship
def get_album_items(artist_path):
    album_items = []
    albums_and_files = get_album_list(artist_path)
    for album_candidate in albums_and_files:
        album_path = artist_path + '/' + album_candidate
        album = get_album_item_from_path(album_path, album_candidate)
        if album is not None:
            album_items.append(album)
    return album_items

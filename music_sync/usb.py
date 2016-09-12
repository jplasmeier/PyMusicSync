# usb.py
# A module to find and save USB device information on a Mac.
# Author: J. Plasmeier | jplasmeier@gmail.com
# License: MIT License
from subprocess import call, check_output
import os, re, pprint

df_info = {}
device_info = {}

class DF_Device:
    """
    Class to store information about a device from df
    """

    #def __init__(self, filesystem, size, used, avail, capacity, iused, ifree, pct_iused, mounted_on):
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
    """
    
    def __init__(self, nickname):
        self.IOReg_info = {}
        self.DF_info = {}
        self.nickname = nickname

    def get_free_space(self):
        return self.DF_info['Avail']

def get_usb_devices_ioreg():
    result = check_output(["ioreg", "-p", "IOUSB", "-l", "-w", "0"])
    results = result.split("+-o")
    return results 

# TODO: Refactor this shit show
def get_ioreg_devices():
    devices = get_usb_devices_ioreg()
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
    result = check_output(["df", "-k", "-T", "exfat"]) 
    results = result.split("\n")
    df_objects = []
    for res in results[1:]:
        tokens = res.split()
        if len(tokens) >= 9:
            df_obj = DF_Device(tokens[8])
            df_obj.set_df_info(tokens)
            df_objects.append(df_obj)
    return df_objects

def print_dict_list(dict_to_print):
    for key in dict_to_print:
            print dict_to_print[key], '\n'


# Expose these functions to main
def pick_from_df():
    df_devices = get_df_devices() 
    if len(df_devices) == 1:
        return df_devices[0]
    else:
        # not implemented yet
        return df_devices[0]


def pick_from_ioreg():
    ioreg_devices = get_ioreg_devices() 
    for idx, dev in enumerate(ioreg_devices):
        print "Device {0}: ".format(idx)
        ioreg_devices[dev]["Device"] = idx
        pprint.pprint(ioreg_devices[dev])
    # prompt user selection
    choice = int(raw_input("Enter the number of the device which you would like to sync:"))
    return [ioreg_devices[dev] for dev in ioreg_devices if ioreg_devices[dev]["Device"] == choice]


def get_usb_collection(device_path):
    """
    Get the dict of Artist - Album[] pairs from the path selected before.
    TODO: Refactor this 6 indents shit
    """
    usb_collection = {} 
    try:
        artists = os.listdir(device_path)
    except:
        print "Error accessing USB device."

    for artist in artists:
        artist_path = device_path + '/' + artist
        # Only grab directories and non-hidden files
        if os.path.isdir(artist_path) and not artist.startswith('.'):
            albums_and_files = os.listdir(artist_path)
            for album_candidate in albums_and_files:
                if os.path.isdir(artist_path + '/' + album_candidate):
                    if artist not in usb_collection:
                        usb_collection[artist] = [] 
                    usb_collection[artist].append(album_candidate)
    return usb_collection

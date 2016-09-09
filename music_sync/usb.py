# usb.py
# A module to find and save USB device information on a Mac.
# Author: J. Plasmeier | jplasmeier@gmail.com
# License: MIT License
from subprocess import call, check_output
import os, re, pprint

df_info = {}
device_info = {}

def get_usb_devices_ioreg():
    result = check_output(["ioreg", "-p", "IOUSB", "-l", "-w", "0"])
    results = result.split("+-o")
    return results 

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
    df_info = {}
    #result = check_output(["df", "-h"]) 
    result = check_output(["df", "-h", "-T", "exfat"]) 
    results = result.split("\n")
    for res in results:
        tokens = res.split()
        if tokens != [] and tokens[0] != 'Filesystem':
            df_info[tokens[0]] = tokens
    return df_info

def print_dict_list(dict_to_print):
    for key in dict_to_print:
            print dict_to_print[key], '\n'

# Expose these functions to main
def pick_from_df():
    df_devices = get_df_devices() 
    if len(df_devices) == 1:
        for dev in df_devices:
            return df_devices[dev][-1]
    else:
        # not implemented yet
        return df_devices

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

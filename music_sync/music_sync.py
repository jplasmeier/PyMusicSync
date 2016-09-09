# -*- coding: utf-8 --
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import usb, cannery, gdrive, music_sync_utils
import codecs
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# Global Variables
# IOREG device info pickle file
ioreg_file = "ioreg_file.p"

# Your music collection
# key: str - artist 
# value: list - albums
drive_collection = {}
usb_collection = {}

# If you have audio files under an artist (and not in an album folder)
# Add the culprit artist to this list and let the user know 
audio_in_artist = []

# Load cached JSON object of album size
drive_album_size_cache = "album_cache.p"
album_cache = cannery.load_album_cache(drive_album_size_cache)
###############################################

def main():
    # Drive Stuff
    gauth = gdrive.login()
    drive = GoogleDrive(gauth)
    folder = 'Music'
    drive_collection = {}
    drive_size, drive_collection = gdrive.get_file_size_recursive(drive_collection, album_cache, drive, folder)
    print("Your music takes up {0} Kib, {1} Gb of space.".format(drive_size/1024/1024,drive_size/1000/1000/1000)) 
    
    #USB Stuff
    ioreg_device = cannery.load_ioreg(ioreg_file)
    if not ioreg_device:
        ioreg_device = usb.pick_from_ioreg()
    df_device = usb.pick_from_df()

    print "You picked this device from IOREG: {}".format(ioreg_device)
    print "You picked this device from DF: {}".format(df_device)
    usb_collection = music_sync_utils.clean_unicode(usb.get_usb_collection(df_device))
 
    drive_collection= music_sync_utils.clean_unicode(drive_collection)
    
    missing_from_usb = music_sync_utils.check_drive_not_in_usb_collection(drive_collection, usb_collection) 
    missing_from_drive = music_sync_utils.check_usb_not_in_drive_collection(drive_collection, usb_collection)
    
    missing_from_usb, missing_from_drive = music_sync_utils.find_possible_duplicate_albums(missing_from_usb, missing_from_drive)

    print "The following are missing from your USB device"
    music_sync_utils.print_collection(missing_from_usb)
    print "The following are missing from your Drive"
    music_sync_utils.print_collection(missing_from_drive)

    # Epilogue
    if audio_in_artist:
        print "Heads up, you have audio files directly in the following artists."
        print "You should put them in a folder by album instead."
        print sorted(audio_in_artist)

    # We can pickle the IOREG stuff because its serial no. is invariant, but we can't be sure that its mount point in df will be the same.
    # Need to research if there's a (reliable) link between df and IOREG
    cannery.pickle_ioreg(ioreg_device, ioreg_file)
    cannery.pickle_album_cache(drive_album_size_cache, album_cache)

if __name__ == '__main__':
    main() 

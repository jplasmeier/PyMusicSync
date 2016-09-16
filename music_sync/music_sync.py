# -*- coding: utf-8 --
from pydrive.drive import GoogleDrive
import usb
import cannery
import gdrive
import music_sync_utils
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# TODO: Clear out these globals
# IOREG device info pickle file
ioreg_file = "ioreg_file.p"


# Load cached JSON object of album size
drive_album_size_cache = "album_cache.p"
album_cache = cannery.load_album_cache(drive_album_size_cache)


def main():
    # Drive Setup Stuff
    gauth = gdrive.login()
    drive = GoogleDrive(gauth)
    folder_name = 'Music'

    # Create, fill, and clean GoogleDriveCollection
    google_drive_collection = music_sync_utils.GoogleDriveCollection()
    music_folder = gdrive.get_folder_from_root(drive, folder_name)
    google_drive_collection.etag = music_folder.metadata['etag']
    gdrive.fill_google_drive_collection(google_drive_collection, drive, music_folder)
    print google_drive_collection.collection
    google_drive_collection.collection = music_sync_utils.clean_unicode(google_drive_collection.collection)

    print("Your Drive music takes up {0} Mib, {1} Gb of space.".format(google_drive_collection.get_collection_size()/1024/1024, google_drive_collection.get_collection_size()/1000/1000/1000))
    cannery.pickle_collection_cache(google_drive_collection)

    # USB Setup Stuff
    ioreg_device = cannery.load_ioreg(ioreg_file)
    if not ioreg_device:
        ioreg_device = usb.pick_from_ioreg()
    df_device = usb.pick_from_df()

    # These two print statements should probably go elsewhere/nowhere
    print "You picked this device from IOREG: {}".format(ioreg_device)
    print "You picked this device from DF: {}".format(df_device)

    # Create, fill, and clean USBCollection
    usb_collection = music_sync_utils.USBCollection(df_device.mounted_on)
    usb_collection.collection = usb.get_usb_collection(usb_collection.file_path)
    usb_collection = music_sync_utils.clean_unicode(usb_collection)

    print "Free space on USB (kb)", df_device.avail

    # TODO: Refactor to use class functions - or something
    missing_from_usb = music_sync_utils.check_drive_not_in_usb_collection(google_drive_collection, usb_collection)
    missing_from_drive = music_sync_utils.check_usb_not_in_drive_collection(google_drive_collection, usb_collection)
    
    missing_from_usb, missing_from_drive = music_sync_utils.find_possible_duplicate_albums(missing_from_usb, missing_from_drive)

    print "The following are missing from your USB device"
    music_sync_utils.print_collection(missing_from_usb)
    print "The following are missing from your Drive"
    music_sync_utils.print_collection(missing_from_drive)

    # We can pickle the IOREG stuff because its serial no. is invariant,
    # But we can't be sure that its mount point in df will be the same.
    # Need to research if there's a (reliable) link between df and IOREG
    cannery.pickle_ioreg(ioreg_device, ioreg_file)
    cannery.pickle_album_cache(drive_album_size_cache, album_cache)
    cannery.pickle_collection_cache(google_drive_collection)

if __name__ == '__main__':
    main() 

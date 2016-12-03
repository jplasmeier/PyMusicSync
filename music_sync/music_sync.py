# -*- coding: utf-8 -*-
from pydrive.drive import GoogleDrive
import config
import gdrive
import music_sync_utils
import os
import pickle
import sync
import sys
import usb
import imp
imp.reload(sys)


def main():
    # Drive Setup
    gauth = gdrive.login()
    drive = GoogleDrive(gauth)
    folder_name = config.load_google_drive_folder_name()
    music_folder = gdrive.get_folder_from_root(drive, folder_name)
    if os.path.isfile('gdl_temp.p'):
        with open('gdl_temp.p', 'rb') as fp:
            google_drive_library = pickle.load(fp)
    else:
        # Initialize GoogleDriveLibrary
        google_drive_library = gdrive.GoogleDriveLibrary(drive, music_folder)
    print("Your Drive music takes up {0} Mib, {1} Gb of space.".format(google_drive_library.get_collection_size()/1024/1024, google_drive_library.get_collection_size()/1000/1000/1000))

    with open('gdl_temp.p', 'wb') as fp:
        pickle.dump(google_drive_library, fp)

    # USB Setup
    usb_device_path = config.load_usb_device_path()
    usb_device_df_info = usb.get_df_info_for_device(usb_device_path)
    print("You are using the USB Device at path: {}".format(usb_device_df_info.mounted_on))
    print("Your USB Device has {0} mb free". format(int(usb_device_df_info.avail) / float(1024)))

    # Initialize USBLibrary
    usb_music_library = usb.USBLibrary(usb_device_path)

    # Compare libraries
    missing_from_usb = google_drive_library.get_subtracted_collection_elements(usb_music_library)
    missing_from_drive = usb_music_library.get_subtracted_collection_elements(google_drive_library)

    missing_from_drive_less = music_sync_utils.find_duplicate_albums(missing_from_usb, missing_from_drive)

    print("The following are missing from your USB device")
    music_sync_utils.print_collection(missing_from_usb.collection)
    print("The following are missing from your Drive")
    music_sync_utils.print_collection(missing_from_drive_less.collection)

    gdrive_sync_size = missing_from_usb.get_collection_size()
    print('Size of GDrive files to be added (mb): ', gdrive_sync_size)

    free_space_usb = usb_device_df_info.avail

    print("Free space on USB (mb)", free_space_usb)
    if free_space_usb < gdrive_sync_size:
        print("Not enough space on USB Device. Skipping...")
    free_space_pc = sync.get_free_space_on_local()
    print("Free space on PC  (mb)", free_space_pc)
    sync.buffered_sync_gdrive_to_usb(drive, missing_from_usb.collection, usb_music_library.file_path, google_drive_library.collection)

    print('Upload to Drive')
    sync.upload_collection_to_gdrive(drive, missing_from_drive_less.collection, usb_music_library.file_path, google_drive_library.collection)

if __name__ == '__main__':
    main() 

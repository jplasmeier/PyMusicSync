from pydrive.drive import GoogleDrive
import config
import gdrive
import gdrive_folder
import os
import pickle
import sync
import sys
import usb


cache_drive = config.cache_drive_metadata()
timing_mode = config.timing_mode()


def general(drive, drive_folder, usb_device_path, sync_mode):
    """
    A more general approach to syncing.
    Instead of forcing Library => Artist => Albums => content
    Just use a generic recursive diff/sync.
    Also supports one-way and two-way sync.
    :return:
    """
    print("General sync mode selected.")
    cache_path = config.load_general_cache_path()

    if cache_drive is True and os.path.isfile(cache_path):
        with open(cache_path, 'rb') as fp:
            google_drive_folder = pickle.load(fp)
    else:
        print("Building list of Google Drive files...")
        google_drive_folder = gdrive_folder.build_folder(drive, drive_folder)

    with open(cache_path, 'wb') as fp:
        pickle.dump(google_drive_folder, fp)
    print("Google Drive Folder: ", google_drive_folder)

    usb_folder = usb.build_folder(usb_device_path)
    print("USB Folder: ", usb_folder)

    clean_unicode = config.load_option_clean_unicode()
    delete = config.load_option_delete()

    if sync_mode == "one-way":
        source = google_drive_folder
        destination = usb_folder
        if delete:
            sync.one_way_delete(source, destination, clean_unicode)
        else:
            sync.one_way(source, destination, clean_unicode)
    elif sync_mode == "two-way":
        sync.two_way(drive, google_drive_folder, usb_folder, usb_device_path, clean_unicode)


def main(folder_name=None, usb_device_path=None, sync_mode=None):
    
    if folder_name is None:
        folder_name = config.load_general_drive_folder_name()

    if usb_device_path is None:
        usb_device_path = config.load_general_usb_device_path()

    if folder_name is None and usb_device_path is None and len(sys.argv) < 3:
        raise Exception("Source and destination must be specified.")
    elif len(sys.argv) >= 4:
        if sync_mode is None:
            sync_mode = sys.argv[3]
    else:
        if folder_name is None:
            folder_name = sys.argv[1]
        if usb_device_path is None:
            usb_device_path = sys.argv[2]

    # default sync mode is two-way
    if sync_mode is None:
        sync_mode = "two-way"

    # Drive Setup
    gauth = gdrive.login()
    drive = GoogleDrive(gauth)
    music_folder = gdrive.get_folder_from_root(drive, folder_name)

    general(drive, music_folder, usb_device_path, sync_mode)


if __name__ == '__main__':
    main() 

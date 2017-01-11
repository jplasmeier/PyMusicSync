from pydrive.drive import GoogleDrive
import config
import gdrive
import gdrive_folder
import gdrive_library
import music_sync_utils
import os
import pickle
import sync
import usb

cache_drive = config.load_option_cache()


def trad(drive, music_folder, usb_device_path):
    print("Traditional sync mode selected.")
    cache_path = config.load_trad_cache_path()

    if cache_drive is True and os.path.isfile(cache_path):
        with open(cache_path, 'rb') as fp:
            google_drive_library = pickle.load(fp)
    else:
        # Initialize GoogleDriveLibrary
        google_drive_library = gdrive_library.GoogleDriveLibrary(drive, music_folder)
    print("Your Drive music takes up {0} Mib, {1} Gb of space.".format(google_drive_library.get_collection_size()/1024/1024, google_drive_library.get_collection_size()/1000/1000/1000))

    with open(cache_path, 'wb') as fp:
        pickle.dump(google_drive_library, fp)

    # USB Setup
    usb_device_df_info = usb.get_df_info_for_device(usb_device_path)
    print("You are using the USB Device at path: {}".format(usb_device_df_info.mounted_on))
    print("Your USB Device has {0} mb free". format(int(usb_device_df_info.avail) / float(1024)))

    # Initialize USBLibrary
    usb_music_library = usb.USBLibrary(usb_device_path)

    # Compare libraries
    missing_from_usb = google_drive_library.get_subtracted_collection_elements(usb_music_library)
    missing_from_drive = usb_music_library.get_subtracted_collection_elements(google_drive_library)

    missing_from_drive_less = music_sync_utils.find_duplicate_albums(missing_from_usb, missing_from_drive)

    if missing_from_usb.collection:
        print("The following are missing from your USB device")
        print(missing_from_usb)

    if missing_from_drive_less.collection:
        print("The following are missing from your Drive")
        print(missing_from_drive_less)

    gdrive_sync_size = missing_from_usb.get_collection_size()
    print('Size of GDrive files to be added (mb): ', gdrive_sync_size)

    free_space_usb = usb_device_df_info.avail

    print("Free space on USB (mb)", free_space_usb)
    if free_space_usb < gdrive_sync_size:
        print("Not enough space on USB Device. Skipping...")
    free_space_pc = sync.get_free_space_on_local()
    print("Free space on PC  (mb)", free_space_pc)
    sync.buffered_sync_gdrive_to_usb(drive, missing_from_usb.collection, usb_music_library.file_path, google_drive_library.collection)

    if missing_from_drive_less.collection:
        print('Uploading to Drive')
        sync.upload_collection_to_gdrive(drive, missing_from_drive_less.collection, usb_music_library.file_path, google_drive_library.collection)


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
        sources = [google_drive_folder, usb_folder]
        sync.two_way(sources, clean_unicode)


def main(mode=None, sync_mode=None):
    # Load from config
    if mode is None:
        mode = config.load_mode()

    if mode == "trad":
        folder_name = config.load_google_drive_folder_name()
        usb_device_path = config.load_usb_device_path()
    elif mode == "general":
        folder_name = config.load_general_drive_folder_name()
        usb_device_path = config.load_general_usb_device_path()
    elif mode == "general_test":
        folder_name = config.load_general_test_drive_folder_name()
        usb_device_path = config.load_general_test_usb_device_path()
    else:
        raise Exception("Invalid Mode")

    if sync_mode is None:
        sync_mode = config.load_sync_mode()

    # Drive Setup
    gauth = gdrive.login()
    drive = GoogleDrive(gauth)
    music_folder = gdrive.get_folder_from_root(drive, folder_name)

    if mode == "trad":
        trad(drive, music_folder, usb_device_path)
    elif mode == "general" or mode == "general_test":
        general(drive, music_folder, usb_device_path, sync_mode)


if __name__ == '__main__':
    main() 

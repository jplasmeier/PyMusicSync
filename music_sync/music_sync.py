# -*- coding: utf-8 --
from pydrive.drive import GoogleDrive
import usb
import gdrive
import music_sync_utils
import sync
import sys
reload(sys)
sys.setdefaultencoding('utf8')


def main():
    # Drive Setup
    gauth = gdrive.login()
    drive = GoogleDrive(gauth)
    # TODO: Pull this out and into a config file
    folder_name = 'Music'
    music_folder = gdrive.get_folder_from_root(drive, folder_name)

    # Create GoogleDriveCollection
    google_drive_library = music_sync_utils.MusicLibrary(music_folder.metadata['etag'])

    google_drive_library.collection = gdrive.get_google_drive_collection(drive, music_folder)
    google_drive_library.collection = google_drive_library.clean_unicode()

    print("Your Drive music takes up {0} Mib, {1} Gb of space.".format(google_drive_library.get_collection_size()/1024/1024, google_drive_library.get_collection_size()/1000/1000/1000))

    # USB Setup Stuff
    df_device = usb.pick_from_df()

    # These two print statements should probably go elsewhere/nowhere
    print "You picked this device from DF: {}".format(df_device)

    # Create, fill, and clean USBCollection
    usb_music = music_sync_utils.USBLibrary(df_device.mounted_on)
    usb_music.collection = usb.get_usb_collection(usb_music.file_path)
    usb_music.collection = music_sync_utils.clean_unicode(usb_music.collection)

    missing_from_usb = google_drive_library.get_subtracted_collection_elements(usb_music)
    missing_from_drive = usb_music.get_subtracted_collection_elements(google_drive_library)

    missing_from_drive_less = music_sync_utils.find_duplicate_albums(missing_from_usb, missing_from_drive)

    print "The following are missing from your USB device"
    music_sync_utils.print_collection(missing_from_usb.collection)
    print "The following are missing from your Drive"
    music_sync_utils.print_collection(missing_from_drive_less.collection)

    # Get albums to sync. Need artists too.
    sync_to_usb_collection = sync.get_gdrive_artists_from_collection(missing_from_usb.collection, google_drive_library.collection)
    # gdrive_collection is a dict of artist_name: [drive_album]
    gdrive_sync_size = sync.get_size_of_syncing_collection(sync_to_usb_collection, google_drive_library.collection)
    print 'Size of GDrive files to be added (mb): ', gdrive_sync_size
    # watch out that size is hard coded against the df call - can return different things
    free_space_usb = int(df_device.avail)/1024.0
    print "Free space on USB (mb)", free_space_usb
    if free_space_usb < gdrive_sync_size:
        print "Not enough space on USB Device. Skipping..."
    free_space_pc = sync.get_free_space_on_local()
    print "Free space on PC  (mb)", free_space_pc
    sync.buffered_sync_gdrive_to_usb(drive, sync_to_usb_collection, usb_music.file_path, google_drive_library.collection)

    print 'Upload to Drive'
    sync.upload_collection_to_gdrive(drive, missing_from_drive_less.collection, usb_music.file_path)

if __name__ == '__main__':
    main() 

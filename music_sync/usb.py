# usb.py
# A module to find and save USB device information on a Mac.
# Author: J. Plasmeier | jplasmeier@gmail.com
# License: MIT License
import config
import general_sync_utils
import gdrive
import gdrive_folder
import os


class USBFolder(general_sync_utils.Folder):

    def __init__(self, path):
        name = os.path.basename(path)
        super(USBFolder, self).__init__(name)
        self.path = path

    def __str__(self):
        return self.name


class USBFile(general_sync_utils.File):

    def __init__(self, path):
        if os.path.isdir(path):
            raise os.error("Error: cannot create file from directory, silly")
        name = os.path.basename(path)
        size = os.path.getsize(path)
        super(USBFile, self).__init__(name, size)
        self.path = path

    def __str__(self):
        return self.name


def build_folder(path):
    """
    Return the contents of a folder, recursively
    :param path:
    :return:
    """
    if not os.path.isdir(path):
        return USBFile(path)
    else:
        usb_folder = USBFolder(path)
        drive_folder_contents = os.listdir(path)
        for item in drive_folder_contents:
            if config.ignore_dotfiles() and item.startswith('.'):
                continue
            else:
                print("processing:" , item)
                new_usb_folder = build_folder(os.path.join(path, item))
                usb_folder.contents_map[new_usb_folder.name] = new_usb_folder
                usb_folder.contents.append(build_folder(os.path.join(path, item)))
    return usb_folder


def upload_contents(drive, usb_folder, drive_folder):
    """
    Upload the contents of the given usb folder to Google Drive.
    :param drive:
    :param usb_folder:
    :param drive_folder:
    :return:
    """
    if not isinstance(drive_folder, gdrive_folder.DriveFolder):
        return
    if isinstance(usb_folder, USBFile):
        gdrive.upload_file(drive, usb_folder.name, usb_folder.path, drive_folder.drive_file)
        return usb_folder
    elif isinstance(usb_folder, general_sync_utils.Folder):
        for item in usb_folder.contents:
            # Why wasn't this isintance(item, g_s_u.Folder)?
            if isinstance(item, general_sync_utils.Folder):
                if not item in drive_folder.contents:
                    print("Creating folder: ", item.name)
                    drive_file = gdrive.create_folder(drive, item.name, drive_folder.drive_file['id'])
                    new_folder = gdrive_folder.DriveFolder(drive_file)
                    # but what about its contents? i think its ok to be empty at initialization- it is empty
                    # but what about as it's being filled?
                else:
                    # this nonsense should be: new_folder = drive_folder.contents.get(item)
                    new_folder, = [f for f in drive_folder.contents if f == item]
                    if item not in drive_folder.contents:
                        drive_folder.contents.add(item)
                upload_contents(drive, item, new_folder)
            elif isinstance(item, USBFile):
                gdrive.upload_file(drive, item.name, item.path, drive_folder.drive_file)
        return drive_folder
    return drive_folder

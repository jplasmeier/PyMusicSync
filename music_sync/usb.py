# usb.py
# A module to find and save USB device information on a Mac.
# Author: J. Plasmeier | jplasmeier@gmail.com
# License: MIT License
from subprocess import CalledProcessError, getoutput
import general_sync_utils
import gdrive
import os
import sys


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
            print("Processing: ", item)
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
    if isinstance(usb_folder, USBFile):
        gdrive.upload_file(drive, usb_folder.name, usb_folder.path, drive_folder)
        return usb_folder
    elif isinstance(usb_folder, general_sync_utils.Folder):
        for item in usb_folder.contents:
            if isinstance(item, general_sync_utils.Folder):
                if not item in drive_folder.contents:
                    new_folder = gdrive.create_folder(drive, item.name, drive_folder.drive_file['id'])
                else:
                    new_folder, = [f for f in drive_folder.contents if f == item]
                upload_contents(drive, item, new_folder)
            elif isinstance(item, USBFile):
                gdrive.upload_file(drive, item.name, item.path, drive_folder.drive_file)
        return drive_folder
    return drive_folder

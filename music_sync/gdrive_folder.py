import gdrive
import general_sync_utils
import os


class DriveFolder(general_sync_utils.Folder):

    def __init__(self, drive_file):
        super(DriveFolder, self).__init__(drive_file['title'])
        self.drive_file = drive_file

    def __str__(self):
        return self.drive_file["title"]





class DriveFile(general_sync_utils.File):

    def __init__(self, drive_file):
        super(DriveFile, self).__init__(drive_file['title'], drive_file['quotaBytesUsed'])
        self.drive_file = drive_file

    def __str__(self):
        return self.drive_file['title']


def build_folder(drive, drive_file):
    """
    Return the contents of a folder, recursively
    :param drive:
    :param drive_file:
    :return:
    """
    drive_file_type = gdrive.get_file_ext_type(drive_file)
    if drive_file_type != "folder":
        return DriveFile(drive_file)
    else:
        drive_folder = DriveFolder(drive_file)
        drive_folder_contents = gdrive.list_folder(drive, drive_file["id"])
        for item in drive_folder_contents:
            print("Processing: ", item['title'])
            drive_folder.contents.append(build_folder(drive, item))
    return drive_folder


def download_contents(drive, drive_folder, destination):
    """
    Downloads the contents of this Drive Folder.
    This will only download files present within this object,
    so files on Drive not present in self.contents will not be downloaded.
    :param destination: Ideally, a filepath of a place to put your Drive files
    :return:
    """
    if isinstance(drive_folder, general_sync_utils.File):
        gdrive.download_file(drive_folder.drive_file, destination)
        return drive_folder
    elif isinstance(drive_folder, general_sync_utils.Folder):
        for item in drive_folder.contents:
            new_folder = os.path.join(destination, drive_folder.name)
            if not os.path.isdir(new_folder):
                os.mkdir(os.path.join(destination, drive_folder.name))
            download_contents(drive, item, new_folder)
        return drive_folder
    return drive_folder
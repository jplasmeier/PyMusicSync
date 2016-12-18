import gdrive
import general_sync_utils


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

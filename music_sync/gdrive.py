# gdrive.py
# Google Drive Utilities
from pydrive.auth import GoogleAuth
import os


def clean_unicode_title(drive_file):
    clean_name = clean_unicode(drive_file['title'])
    if clean_name != drive_file['title']:
        drive_file['title'] = clean_name
        drive_file.Upload()
    return clean_name


def login():
    """
    Login via Google Auth
    If there is a credentials file present, use it.
    Otherwise, use Local Webserver Auth
    Returns the gauth object
    """
    gauth = GoogleAuth()
    # Try to load saved client credentials
    gauth.LoadCredentialsFile("mycreds.txt")
    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()
    # Save the current credentials to a file
    # TODO: Encryption???
    gauth.SaveCredentialsFile("mycreds.txt")
    return gauth


def get_file_from_root(drive, file_title):
    """
    Returns the file(s)/director(y/ies) as a GoogleDriveFile with the given title.
    :param drive: GoogleDrive object to use to pull file from
    :param file_title: Title to return file for
    :return: List of GoogleDriveFiles matching file_title
    """
    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    title_matches = []
    for file1 in file_list:
        if file1['title'] == file_title:
            title_matches.append(file1)
    return title_matches


def get_folder_from_root(drive, file_title):
    """
    Returns the file/directory as a GoogleDriveFile with the given title.
    :param drive: GoogleDrive object to use to pull file from
    :param file_title: Title to return file for
    :return: First GoogleDriveFile matching file_title found
    """
    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    for file1 in file_list:
        if file1['title'] == file_title:
            return file1


def get_folders_from_root(drive):
    """
    Returns the files in your root Google Drive directory
    :param drive:
    :return:
    """
    return drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()


def get_file_ext_type(drive_file):
    """
    :param drive_file: The GoogleDriveFile to get the file type of
    Uses the MIME type.
    Options are:
    folder - u'mimeType': u'application/vnd.google-apps.folder',
    other - u'mimeType': u'text/plain'
    audio - u'mimeType': u'audio/mp3'
    """
    raw_mime_type = drive_file.metadata['mimeType']
    if 'google-apps.folder' in raw_mime_type:
        return 'folder'
    if 'audio' in raw_mime_type:
        return 'audio'
    else:
        return 'other'


def list_folder(drive, folder_id):
    """
    Lists contents of a GoogleDriveFile that is a folder
    :param drive: Drive object to use for getting folders
    :param folder_id: The id of the GoogleDriveFile
    :return: The GoogleDriveList of folders
    """
    _q = {'q': "'{}' in parents and trashed=false".format(folder_id)}
    return drive.ListFile(_q).GetList()


# Download

def download_recursive(drive, folder, download_to):
    """
    Given a Drive folder, recursively download that folder and it's children
    :param drive: The drive object
    :param folder: The folder to download
    :param download_to: The path to download to
    :return: None
    """
    children = list_folder(drive, folder['id'])
    if children is None:
        return
    for child in children:
        file_type = get_file_ext_type(child)
        if file_type is 'folder':
            new_dir = os.path.join(download_to, child['title'])
            if not os.path.isdir(new_dir):
                os.mkdir(new_dir)
            download_recursive(drive, child, new_dir)
        elif file_type is 'audio':
            download_file(child, download_to)
    return


def clean_unicode(name):
    """
    Clean bad unicode strings from Drive and upload the change.
    Currently this means adding combining marks to reflect the directory name upon directory creation.
    :param name: The name to clean
    :return: The clean name
    """
    if u"\u00E4" in name or u"\u00E1" in name:
        temp_unicode_dir_path = os.path.join(os.path.curdir, 'temp_unicode_dir')
        if not os.path.isdir(temp_unicode_dir_path):
            os.mkdir(temp_unicode_dir_path)
        dirty_path = os.path.join(temp_unicode_dir_path, name)
        if not os.path.isdir(dirty_path):
            os.mkdir(dirty_path)
        clean_name = os.listdir(temp_unicode_dir_path).pop()
        os.rmdir(dirty_path)
        return clean_name
    else:
        return name


# Why child??
def download_file(child, download_to):
    download_path = os.path.join(download_to, child['title'])
    print('Downloading file {0} to: {1}'.format(child['title'], download_path))
    child.GetContentFile(download_path)
    return


# Upload


def upload_recursive(drive, upload_name, upload_path, upload_to):
    """
    Given a Drive folder, recursively download that folder and it's children
    :param drive: The drive object
    :param upload_name: The name of the object
    :param upload_path: The path of the object to upload
    :param upload_to: The GoogleDriveFile to upload to
    :return: None
    """
    if os.path.isdir(upload_path):
        # This is a directory. Make a GDrive folder and recurse
        drive_parent = create_folder(drive, upload_name, upload_to['id'])
        for item_name in os.listdir(upload_path):
            item_path = os.path.join(upload_path, item_name)
            upload_recursive(drive, item_name, item_path, drive_parent)
    else:
        # This is a file. Upload it to the parent folder and return.
        upload_file(drive, upload_name, upload_path, upload_to)
        return
    return


def upload_file(drive, file_name, file_path, parent_drive_file):
    """
    Uploads a file with a given parent.
    :param file_name: The name of the file to upload
    :param file_path: The local path of the file being uploaded.
    :param parent_drive_file: The GoogleDriveFile of the parent
    :return:
    """
    print('Uploading file {0} to: {1}'.format(file_path, parent_drive_file['title']))
    new_drive_file = drive.CreateFile({'title': file_name, 'parents': [{'id': parent_drive_file['id']}]})
    new_drive_file.SetContentFile(file_path)
    try:
        new_drive_file.Upload()
    except Exception as ex:
        print("Exception of type {0} thrown: \n".format(type(ex), ex))
        print("File name: ", file_name)
    return


def create_folder(drive, folder_name, parent_id):
    drive_folder = drive.CreateFile({'title': folder_name,
                                    "parents": [{"id": parent_id}],
                                     "mimeType": "application/vnd.google-apps.folder"})
    drive_folder.Upload()
    return drive_folder

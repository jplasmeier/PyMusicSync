from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def list_folder(drive, folder_id):
    # folder_id: GoogleDriveFile['id']
    _q = {'q': "'{}' in parents and trashed=false".format(folder_id)}
    return drive.ListFile(_q).GetList()

def get_artist_size(drive, artist):
    albums = list_folder(drive, artist['id'])
    size = 0
    for album in albums:
        album_size = get_album_size(drive, album)
        if album_size is not None:
            size += album_size
    return size 

def get_album_size(drive, album):
    tracks = list_folder(drive, album['id'])
    size = 0
    for track in tracks:
        file_size = int(track["quotaBytesUsed"])
        if file_size is not None:
            size += file_size
    return size

def login():
    '''
    Login via Google Auth
    If there is a credentials file present, use it.
    Otherwise, use Local Webserver Auth
    Returns the gauth object
    '''
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
    gauth.SaveCredentialsFile("mycreds.txt")
    return gauth
    

def get_file_size_recursive(drive, folder):
    size = 0
    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    for file1 in file_list:
        if file1['title'] == folder:
            artists = list_folder(drive, file1['id'])
            i = 0.0
            for artist in artists:
                print "Getting Filesize: {0}%".format((i/len(artists))*100)
                i += 1
                size += get_artist_size(drive, artist)
    return size

def main():
    gauth = login()
    drive = GoogleDrive(gauth)
    folder = 'Music'
    drive_size = get_file_size_recursive(drive, folder)
    print("Your music takes up {0} Kib, {1} Gb of space.".format(drive_size/1024/1024,drive_size/1000/1000/1000)) 

if __name__ == '__main__':
   main() 

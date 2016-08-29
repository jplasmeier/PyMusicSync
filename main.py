from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import pickle
import os.path
import usb

# Global Variables
ioreg_file = "ioreg_file.p"

# Load cached JSON object of album size
cache_file = "album_cache.p"
try:
    if os.path.isfile(cache_file):
        with open(cache_file, "rb") as fp:
            album_cache = pickle.load(fp)
    else:
        album_cache = {}
except Exception, err:
    print "Cache error: {}".format(err)

def pickle_albums():
    """
    Why is this a separate function and the above code is not?
    Because I'm shit at code and need to make sure that load happens at the beginning in global scope
    And dumping happens at the end of main
    """
    with open(cache_file, "wb") as fp:
        pickle.dump(album_cache, fp)

def pickle_ioreg(ioreg_device):
    with open(ioreg_file, "wb") as fp:
        pickle.dump(ioreg_device, fp)

def load_ioreg():
    if os.path.isfile(ioreg_file):
        with open(ioreg_file, "rb") as fp:
            ioreg_device = pickle.load(fp)
        return ioreg_device
    else:
        return None

def list_folder(drive, folder_id):
    # folder_id: GoogleDriveFile['id']
    _q = {'q': "'{}' in parents and trashed=false".format(folder_id)}
    return drive.ListFile(_q).GetList()

def get_artist_size(drive, artist_id):
    """
    artist_id: string containing GoogleDriveFile id of an artist_id folder
    """
    albums = list_folder(drive, artist_id)
    size = 0
    for album in albums:
        album_size = get_album_size_cache(album['id'])
        if album_size is None:
            album_size = get_album_size_drive(drive, album['id'])
        if album_size is not None:
            size += album_size
    return size 

def get_album_size_cache(album_id):
    """
    Turns out getting the size of each album_id thru drive takes forever
    So we're caching them.
    album_id: string containing GoogleDriveFile id of an album_id folder
    Returns None if not found in cahce
    """
    if album_id in album_cache:
        return album_cache[album_id]
    else:
        return None
    
def get_album_size_drive(drive, album_id):
    """
    album_id: string containing GoogleDriveFile id of an album_id folder
    """
    tracks = list_folder(drive, album_id)
    size = 0
    for track in tracks:
        file_size = int(track["quotaBytesUsed"])
        if file_size is not None:
            size += file_size
    album_cache[album_id] = size
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
                size += get_artist_size(drive, artist['id'])
    return size

def main():
    # Drive Stuff
    gauth = login()
    drive = GoogleDrive(gauth)
    folder = 'Music'
    #drive_size = get_file_size_recursive(drive, folder)
    #print("Your music takes up {0} Kib, {1} Gb of space.".format(drive_size/1024/1024,drive_size/1000/1000/1000)) 
    
    #USB Stuff
    ioreg_device = load_ioreg()
    if not ioreg_device:
        ioreg_device = usb.pick_from_ioreg()
    df_device = usb.pick_from_df()

    print "You picked this device from IOREG: {}".format(ioreg_device)
    print "You picked this device from DF: {}".format(df_device)

    # We can pickle the IOREG stuff because it's invariant
    # But we can't be sure that df will be the same.
    # We could guess at the filesize but that's risky
    # Need to research if there's a (reliable) link between df and IOREG
    pickle_ioreg(ioreg_device)
    # do this at the end of the program
    pickle_albums()

if __name__ == '__main__':
   main() 

# -*- coding: utf-8 --
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import pickle
import os.path
import usb
import codecs
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# Global Variables
# IOREG device info pickle file
ioreg_file = "ioreg_file.p"

# Your music collection
# key: str - artist 
# value: list - albums
drive_collection = {}
usb_collection = {}

# If you have audio files under an artist (and not in an album folder)
# Add the culprit artist to this list and let the user know 
audio_in_artist = []

# Load cached JSON object of album size
drive_album_size_cache = "album_cache.p"
try:
    if os.path.isfile(drive_album_size_cache):
        with open(drive_album_size_cache, "rb") as fp:
            album_cache = pickle.load(fp)
    else:
        album_cache = {}
except Exception, err:
    print "Cache error: {}".format(err)

###############################################

def get_file_ext_type(drive_file):
    """
    Gets the file extension type from a GoogleDriveFile object instance.
    Uses the MIME type.
    Options are:
    folder - u'mimeType': u'application/vnd.google-apps.folder',
    other - u'mimeType': u'text/plain'
    audio - u'mimeType': u'audio/mp3'
    """
    raw_mimeType = drive_file.metadata['mimeType']
    if 'google-apps.folder' in raw_mimeType:
        return 'folder'
    if 'audio' in raw_mimeType:
        return 'audio'
    else:
        return 'other'
    
def pickle_albums():
    """
    Why is this a separate function and the above code is not?
    Because I'm shit at code and need to make sure that load happens at the beginning in global scope
    And dumping happens at the end of main
    """
    with open(drive_album_size_cache, "wb") as fp:
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

def get_artist_size(drive, artist):
    """
    artist: GoogleDriveFile of an artist folder
    """
    albums = list_folder(drive, artist['id'])
    size = 0
    album_list = drive_collection[artist['title']]
    for album in albums:
        file_extension_type = get_file_ext_type(album)
        if album['title'] not in album_list and file_extension_type is 'folder':
            album_list.append(album['title'])
        if file_extension_type is 'audio' and artist['title'] not in audio_in_artist:
            audio_in_artist.append(artist['title'])
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
                global drive_collection
                drive_collection[artist['title']] = []
                print "Getting Filesize: {0}%".format((i/len(artists))*100)
                i += 1
                size += get_artist_size(drive, artist)
    return size

def check_drive_not_in_usb_collection(drive_collection, usb_collection):
    missing_from_usb_collection = {}
    for artist in drive_collection:
        if artist not in usb_collection:
            #TODO: investigate performance of caching lookup (save the list locally instead of looking up artist again)
            missing_from_usb_collection[artist] = []
            for album in drive_collection[artist]:
                missing_from_usb_collection[artist].append(album)
        else:
            for album in drive_collection[artist]:
                if album not in usb_collection[artist]:
                    if artist not in missing_from_usb_collection:
                        missing_from_usb_collection[artist] = []
                    missing_from_usb_collection[artist].append(album)
    return missing_from_usb_collection

def check_usb_not_in_drive_collection(drive_collection, usb_collection):
    missing_from_drive_collection = {}
    for artist in usb_collection:
        if artist not in drive_collection:
            missing_from_drive_collection[artist] = []
            #TODO: investigate performance of caching lookup (save the list locally instead of looking up artist again)
            for album in usb_collection[artist]:
                missing_from_drive_collection[artist].append(album)
        else:
            for album in usb_collection[artist]:
                if album not in drive_collection[artist]:
                    if artist not in missing_from_drive_collection:
                        missing_from_drive_collection[artist] = []
                    missing_from_drive_collection[artist].append(album)
    return missing_from_drive_collection

def clean_unicode(collection):
    clean_dict = {}
    for k in collection:
        k_clean = codecs.utf_8_decode(k.encode('utf-8'))
        clean_dict[k_clean] = []
        for a in collection[k]:
            clean_dict[k_clean].append(codecs.utf_8_decode(a.encode('utf-8')))
    return clean_dict

def print_collection(collection):
    for artist in collection:
        print "Artist: {}".format(artist)
        for album in collection[artist]:
            print "---Album: {}".format(album)

def find_possible_duplicate_albums(missing_from_usb, missing_from_drive):
    """
    Sometimes, usually due to unicode fuckery, albums will be compared as inequal even though they are.
    This function looks for strings that differ due to unicode characters
    Or are substrings of each other.
    """
    for artist in list(missing_from_usb.keys()):
        if artist in missing_from_drive:
            for album in missing_from_usb[artist]:
                for drive_album in missing_from_drive[artist]:
                    if check_duplicate_string(drive_album, album):
                        print "Detected false positive: {0} and {1}".format(drive_album, album)
                        missing_from_usb[artist].remove(album)
                        missing_from_drive[artist].remove(drive_album)
                        if not missing_from_usb[artist]:
                            del missing_from_usb[artist]
                        if not missing_from_drive[artist]:
                            del missing_from_drive[artist]

    return missing_from_usb, missing_from_drive

def check_duplicate_string(s1, s2):
    """
    Check for the approximate equality of strings
    Do this by comparing character freuqency
    """
    chars_s1 = {}
    chars_s2 = {}
    shared = {}
    for c in str(s1):
        if c not in chars_s1:
            chars_s1[c] = 0
        chars_s1[c] += 1
    for c in str(s2):
        if c not in chars_s2:
            chars_s2[c] = 0
        chars_s2[c] += 1
    keys_s1 = set(chars_s1.keys())
    keys_s2 = set(chars_s2.keys())
    shared = keys_s1 & keys_s2
    if len(shared) > 0.7*len(keys_s1) or len(shared) > 0.7*len(keys_s2):
        return True
    else:
        return False

def fix_possible_duplicate_albums(missing_from_usb, missing_from_drive):
    """
    Update files to match
    """
    pass

def main():
    # Drive Stuff
    gauth = login()
    drive = GoogleDrive(gauth)
    folder = 'Music'
    drive_size = get_file_size_recursive(drive, folder)
    print("Your music takes up {0} Kib, {1} Gb of space.".format(drive_size/1024/1024,drive_size/1000/1000/1000)) 
    
    #USB Stuff
    ioreg_device = load_ioreg()
    if not ioreg_device:
        ioreg_device = usb.pick_from_ioreg()
    df_device = usb.pick_from_df()

    print "You picked this device from IOREG: {}".format(ioreg_device)
    print "You picked this device from DF: {}".format(df_device)
    usb_collection = clean_unicode(usb.get_usb_collection(df_device))
    
    global drive_collection
    drive_collection= clean_unicode(drive_collection)
    
    missing_from_usb = check_drive_not_in_usb_collection(drive_collection, usb_collection) 
    missing_from_drive = check_usb_not_in_drive_collection(drive_collection, usb_collection)
    
    missing_from_usb, missing_from_drive = find_possible_duplicate_albums(missing_from_usb, missing_from_drive)

    print "The following are missing from your USB device"
    print_collection(missing_from_usb)
    print "The following are missing from your Drive"
    print_collection(missing_from_drive)

    # Epilogue
    if audio_in_artist:
        print "Heads up, you have audio files directly in the following artists."
        print "You should put them in a folder by album instead."
        print sorted(audio_in_artist)

    # We can pickle the IOREG stuff because its serial no. is invariant, but we can't be sure that its mount point in df will be the same.
    # Need to research if there's a (reliable) link between df and IOREG
    pickle_ioreg(ioreg_device)
    pickle_albums()

if __name__ == '__main__':
    main() 

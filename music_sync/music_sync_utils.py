# Utilities for MusicSync
import gdrive
import codecs
import datetime
import cannery
from PyDrive.drive import GoogleDrive


class MusicCollection:
    """
    Class to store music collections in a way that is useful to this program.
    """
    def __init__(self):
        self.collection = {}
        # Children will implement their own last_mod_by call in their init
        # This is the last_mod_by datetime of the collection, not its cache
        self.last_mod_by = datetime.datetime.now()
        self.file_size = 0

    # TODO: What's the deal with Get/set methods in python?
    def get_file_size(self):
        return self.file_size

    def add_artist(self, artist):
        if artist in self.collection:
            return
        self.collection[artist] = []
        return artist

    def add_album_for_artist(self, album, artist):
        if artist not in self.collection:
            self.collection[artist] = []
        self.collection[artist].append(album)

    def get_albums_for_artist(self, artist):
        if artist not in self.collection:
            raise Exception("Artist not in Collection")
        return self.collection[artist]

    def clean_unicode(self):
        clean_collection = {}
        for k in self.collection:
            k_clean = codecs.utf_8_decode(k.encode('utf-8'))
            clean_collection[k_clean] = []
            for a in self.collection[k]:
                clean_collection[k_clean].append(codecs.utf_8_decode(a.encode('utf-8')))
        self.collection = clean_collection


class GoogleDriveCollection(MusicCollection):
    """
    Google Drive specific collection. Includes metadata from the GoogleDrive object.
    """
    def __init__(self, drive_file):
        """
        :param drive_file: The root folder you are looking for music in.
        """
        super(GoogleDriveCollection, self).__init__()
        self.last_mod_by = drive_file.metadata['modifiedDate']
        self.drive_file = drive_file


class USBCollection(MusicCollection):
    """
    USB Device specific collection. Includes file path of device.
    """
    def __init__(self, path):
        super(USBCollection, self).__init__()
        self.file_path = path
        # Get last mod by from path ? system call??

    
def check_drive_not_in_usb_collection(drive_collection, usb_collection):
    missing_from_usb_collection = {}
    for artist in drive_collection:
        if artist not in usb_collection:
            # TODO: investigate performance of caching lookup (save the list locally instead of looking up artist again)
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
            # TODO: investigate performance of caching lookup (save the list locally instead of looking up artist again)
            for album in usb_collection[artist]:
                missing_from_drive_collection[artist].append(album)
        else:
            for album in usb_collection[artist]:
                if album not in drive_collection[artist]:
                    if artist not in missing_from_drive_collection:
                        missing_from_drive_collection[artist] = []
                    missing_from_drive_collection[artist].append(album)
    return missing_from_drive_collection


def print_collection(collection):
    for artist in collection:
        print "Artist: {}".format(artist)
        for album in collection[artist]:
            print "---Album: {}".format(album)


def find_possible_duplicate_albums(missing_from_usb, missing_from_drive):
    """
    :param missing_from_drive The MusicColleciton of music on USB but not Drive
    :param missing_from_usb The MusicCollection of music on Drive but not USB
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
    :param s1 First string
    :param s2 Second string
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
    :param missing_from_drive The MusicColleciton of music on USB but not Drive
    :param missing_from_usb The MusicCollection of music on Drive but not USB
    Update files to match
    """
    raise NotImplementedError

# Utilities for MusicSync
import codecs
import datetime


# TODO: Mixin vs Class? Semantics???
class NameEqualityMixin(object):

    def __eq__(self, other):
        if isinstance(other, str) or isinstance(other, unicode):
            return self.name == other
        return self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)


class MusicLibrary(object):
    """
    Class to store music collections in a way that is useful to this program.
    """
    def __init__(self):
        self.collection = {}
        # Children will implement their own last_mod_by call in their init
        # This is the last_mod_by datetime of the collection, not its cache
        self.last_mod_by = datetime.datetime.now()

    def get_collection_size(self):
        size = 0
        for artist in self.collection:
            size += self.collection[artist].get_file_size_of_albums()
        return size


def clean_unicode(collection):
    clean_collection = {}
    for artist_name in collection:
        clean_artist_name = codecs.utf_8_decode(artist_name.encode('utf-8'))
        clean_collection[clean_artist_name] = ArtistItem(collection[artist_name].name)
        for album in collection[artist_name].albums:
            clean_album_name = codecs.utf_8_decode(album.name.encode('utf-8'))
            clean_collection[clean_artist_name].albums.append(AlbumItem(clean_album_name, album.file_size))
    return clean_collection


class GoogleDriveLibrary(MusicLibrary):
    """
    Google Drive specific collection. Includes metadata from the GoogleDrive object.
    """
    def __init__(self):
        super(GoogleDriveLibrary, self).__init__()
        self.etag = None


class USBLibrary(MusicLibrary):
    """
    USB Device specific collection. Includes file path of device.
    """
    def __init__(self, path):
        super(USBLibrary, self).__init__()
        self.file_path = path
        # Get last mod by from path ? system call??


class CollectionItem(NameEqualityMixin):

    def __init__(self, name, etag=None):
        self.name = name
        self.etag = etag


class ArtistItem(CollectionItem):

    def __init__(self, name, etag):
        super(ArtistItem, self).__init__(name)
        self.etag = etag
        self.albums = []

    def get_file_size_of_albums(self):
        size = 0
        for album in self.albums:
            size += album.file_size
        return size


class AlbumItem(CollectionItem):

    def __init__(self, name, file_size):
        super(AlbumItem, self).__init__(name, self)
        self.file_size = file_size


# (A - B)
def subtract_collection_elements(collection_a, collection_b):
    """
    Subtract B from A by set subtraction on collection objects
    :param collection_a:
    :param collection_b:
    :return: Dict of elements a of A such that a not in B.
    """
    result_dict = {}
    for artist_name in collection_a:
        # Add artist to result set
        if artist_name not in collection_b:
            result_dict[artist_name] = collection_a[artist_name]
        else:
            for album in dictA[artist].albums:
                if album not in dictB[artist].albums:
                    result_dict[artist] = dictA[artist]
    return result_dict


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


def find_duplicate_albums(missing_from_usb, missing_from_drive):
    """
    :param missing_from_drive The MusicLibrary of music on USB but not Drive
    :param missing_from_usb The MusicLibrary of music on Drive but not USB
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
    :param missing_from_usb The MusicLibrary of music on Drive but not USB
    Update files to match
    """
    raise NotImplementedError

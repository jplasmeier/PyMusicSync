# Utilities for MusicSync
import codecs
import datetime


class NameEqualityMixin(object):

    def __eq__(self, other):
        if isinstance(other, str) or isinstance(other, unicode):
            return self.name == other
        return self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)


class MusicCollection(object):
    """
    Class to store music collections in a way that is useful to this program.
    """
    def __init__(self):
        self.collection = {}
        # Children will implement their own last_mod_by call in their init
        # This is the last_mod_by datetime of the collection, not its cache
        self.last_mod_by = datetime.datetime.now()
        self.file_size = 0

    def get_collection_size(self):
        return sum(self.get_artist_size(a) for a in self.collection)

    def add_artist(self, artist):
        """
        Adds a new artist to the collection in the form of a CollectionItem object.
        This should work when adding from Drive or the Cache.
        :param artist: Artist name in the form of a string
        :return: self per the standard practice here
        """
        collection_artist = self.get_collection_item(artist)
        if collection_artist is None:
            collection_artist = CollectionItem(artist)
            self.collection[collection_artist] = []
        self.collection[collection_artist].append(collection_artist)
        print "Artist {} added".format(collection_artist.name)
        return self

    def get_collection_item(self, item_name):
        collection_item = None
        items = [a for a in self.collection if a.name == item_name]
        if items:
            collection_item = items[0] or None
        else:
            for artist in self.collection:
                print self.collection[artist]
                items = [a for a in self.collection[artist] if a.name == item_name]
                if items:
                    collection_item = items[0]
        return collection_item

    def add_album_for_artist(self, album, artist):
        print "--Album {} added".format(album)
        collection_artist = self.get_collection_item(artist)
        if not collection_artist:
            self.add_artist(artist)
        collection_album = self.get_collection_item(album)
        if not collection_album:
            collection_album = CollectionItem(album)
            self.collection[collection_artist].append(collection_album)
        return self

    def get_albums_for_artist(self, artist):
        collection_artist = CollectionItem(artist)
        if collection_artist.name not in [a.name for a in self.collection]:
            raise Exception("Artist {} not in Collection".format(collection_artist.name))
        return self.collection[collection_artist]

    def set_album_size(self, album, artist, size):
        collection_artist = self.get_collection_item(artist)
        if not collection_artist:
            raise Exception("Artist {} not in Collection".format(artist))
        collection_album, = [a for a in self.collection[collection_artist] if a.name == album]
        if not collection_album:
            raise Exception("Album {} not in artist".format(album))
        collection_album.file_size = size
        return size

    def get_artist_size(self, collection_artist):
        size = 0
        for album in self.collection[collection_artist]:
            size += album.file_size
        return size

    def clean_unicode(self):
        for artist in self.collection:
            for album in self.collection[artist]:
                clean_album_name = codecs.utf_8_decode(artist.name.encode('utf-8'))
                album.name = clean_album_name
            clean_name = codecs.utf_8_decode(artist.name.encode('utf-8'))
            artist.name = clean_name
        return self


class GoogleDriveCollection(MusicCollection):
    """
    Google Drive specific collection. Includes metadata from the GoogleDrive object.
    """
    def __init__(self):
        super(GoogleDriveCollection, self).__init__()
        self.etag = None


class USBCollection(MusicCollection):
    """
    USB Device specific collection. Includes file path of device.
    """
    def __init__(self, path):
        super(USBCollection, self).__init__()
        self.file_path = path
        # Get last mod by from path ? system call??


class CollectionItem(NameEqualityMixin):

    def __init__(self, name, file_size=None, last_mod_by_date=None):
        self.name = name
        if file_size:
            self.file_size = file_size
        if last_mod_by_date:
            self.last_mod_by_date = last_mod_by_date
        else:
            self.last_mod_by_date = datetime.datetime.now()


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

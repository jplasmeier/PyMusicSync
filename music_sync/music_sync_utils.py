# Utilities for MusicSync
import codecs
import copy
import os


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
    def __init__(self, etag):
        self.collection = {}
        self.etag = etag

    def get_collection_size(self):
        size = 0
        for artist in self.collection:
            size += self.collection[artist].get_file_size_of_albums()
        return size

    def __str__(self):
        s = []
        for artist_name in self.collection:
            s.append("Artist: {}\n".format(artist_name))
            for album_item in self.collection[artist_name].albums:
                s.append("---- Album: {}\n".format(album_item.name))
        return str(s)


class USBLibrary(MusicLibrary):
    """
    USB Device specific collection. Includes file path of device.
    """
    def __init__(self, path):
        last_mod_by = os.path.getmtime(path)
        super(USBLibrary, self).__init__(last_mod_by)
        self.file_path = path


class CollectionItem(NameEqualityMixin):

    def __init__(self, name, etag=None):
        if not isinstance(name, str) and not isinstance(name, unicode):
            raise Exception("Given name: {} is not a string".format(name))
        self.name = name
        self.etag = etag

    def __str__(self):
        if not isinstance(self.name, str) and not isinstance(self.name, unicode):
            raise Exception("You set the name to {0}  which is type: {1} not a string".format(self.name, type(self.name)))
        return self.name


class ArtistItem(CollectionItem):

    def __init__(self, name, etag):
        super(ArtistItem, self).__init__(name)
        self.etag = etag
        self.albums = []

    def __str__(self):
        return self.name

    def get_file_size_of_albums(self):
        size = 0
        for album in self.albums:
            size += album.file_size
        return size


class AlbumItem(CollectionItem):

    def __init__(self, name, file_size):
        super(AlbumItem, self).__init__(name, self)
        self.file_size = file_size

    def __str__(self):
        return self.name


# (A - B)
def subtract_collection_elements(library_a, library_b):
    """
    Subtract B from A by set subtraction on collection objects
    :param collection_a:
    :param collection_b:
    :return: Dict of elements a of A such that a not in B.
    """
    result_library = MusicLibrary('result')
    for artist_name in library_a.collection:
        # Add artist to result set
        if artist_name not in library_b.collection:
            result_library.collection[artist_name] = library_a.collection[artist_name]
        else:
            for album in library_a.collection[artist_name].albums:
                if album not in library_b.collection[artist_name].albums:
                    if artist_name not in result_library.collection:
                        result_library.collection[artist_name] = ArtistItem(artist_name, library_a.collection[artist_name].etag)
                    result_library.collection[artist_name].albums.append(album)
    return result_library


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
        print "Artist:", artist
        for album in collection[artist].albums:
            print "-----Album: ", album


def get_difference(album, artist_name, missing_from_usb):
    if album in missing_from_usb.collection[artist_name].albums:
        return
    for usb_album in missing_from_usb.collection[artist_name].albums:
        if check_duplicate_string(usb_album.name, album.name):
            print 'False Positive detected! {0} and {1} are actually the same'.format(usb_album.name, album.name)
            return
    return album


def find_duplicate_albums(missing_from_usb, missing_from_drive):
    """
    If there are artists/albums in both libraries, then we have found a false positive.
    These can occur due to unicode issues.
    :param missing_from_usb: A library of artists with albums that are missing from USB
    :param missing_from_drive: A library of artists with albums that are missing from Drive
    :return: A tuple of two libraries, one for each of the actual libraries, containing the actually missing artists.
    """
    actually_missing_from_usb = MusicLibrary(missing_from_usb.etag)

    # TODO: Write unittests
    for artist_name in missing_from_drive.collection:
        if artist_name in missing_from_usb.collection:
            for album in missing_from_drive.collection[artist_name].albums:
                different_album = get_difference(album, artist_name, missing_from_usb)
                if different_album is not None:
                    if artist_name not in actually_missing_from_usb.collection:
                        actually_missing_from_usb.collection[artist_name] = ArtistItem(artist_name,
                                                                                       missing_from_usb.collection[
                                                                                           artist_name].etag)
                    actually_missing_from_usb.collection[artist_name].albums.append(different_album)
        else:
            if artist_name not in actually_missing_from_usb.collection:
                actually_missing_from_usb.collection[artist_name] = ArtistItem(artist_name,
                                                                               missing_from_drive.collection[
                                                                                   artist_name].etag)
            actually_missing_from_usb.collection[artist_name].albums  = missing_from_drive.collection[artist_name].albums
    return actually_missing_from_usb


def check_duplicate_string(s1, s2):
    """
    :param s1 First string
    :param s2 Second string
    Check for the approximate equality of strings
    Do this by comparing character freuqency
    """
    words_s1 = s1.split(' ')
    words_s2 = s2.split(' ')
    s1 = ' '.join(w for w in words_s1 if w not in words_s2)
    s2 = ' '.join(w for w in words_s2 if w not in words_s1)
    chars_s1 = {}
    chars_s2 = {}
    for c in str(s1):
        if c not in chars_s1:
            chars_s1[c] = 0
        chars_s1[c] += 1
    for c in str(s2):
        if c not in chars_s2:
            chars_s2[c] = 0
        chars_s2[c] += 1
    keys_s1 = set(k for k in chars_s1.keys() if ord(k) < 122)
    keys_s2 = set(k for k in chars_s2.keys() if ord(k) < 122)
    shared = keys_s1 & keys_s2
    if len(shared) > 0.6*len(keys_s1) or len(shared) > 0.6*len(keys_s2):
        return True
    else:
        return False


def clean_unicode(collection):
    clean_collection = {}
    for artist_name in collection:
        clean_artist_name = codecs.utf_8_decode(artist_name.encode('utf-8'))[0]
        clean_collection[clean_artist_name] = copy.deepcopy(collection[artist_name])
        clean_collection[clean_artist_name].albums = []
        for album in collection[artist_name].albums:
            clean_album_name = codecs.utf_8_decode(album.name.encode('utf-8'))[0]
            clean_collection[clean_artist_name].albums.append(AlbumItem(clean_album_name, album.file_size))
    return clean_collection


def fix_possible_duplicate_albums(missing_from_usb, missing_from_drive):
    """
    :param missing_from_drive The MusicColleciton of music on USB but not Drive
    :param missing_from_usb The MusicLibrary of music on Drive but not USB
    Update files to match
    """
    raise NotImplementedError

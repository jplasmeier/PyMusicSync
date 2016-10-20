# Utilities for MusicSync
import codecs
import datetime
import copy
import os


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


# TODO: Possibly deprecate
class GoogleDriveLibrary(MusicLibrary):
    """
    Google Drive specific collection. Includes metadata from the GoogleDrive object.
    """
    def __init__(self, etag):
        super(GoogleDriveLibrary, self).__init__(etag)


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
    print 'result of subtraction: ', result_library.collection
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
    print 'getting diff albums than {0}'.format(album)
    if album in missing_from_usb.collection[artist_name].albums:
        print 'Obvious false positive: {0} is in {1}'.format(album, ', '.join(str(a) for a in missing_from_usb.collection[artist_name].albums))
        return None
    for usb_album in missing_from_usb.collection[artist_name].albums:
        if check_duplicate_string(usb_album.name, (c for c in album.name if c not in usb_album.name)):
            print 'False Positive detected! {0} and {1} are actually the same'.format(usb_album.name, album.name)
            return None
    print 'Album {0} not found in missing_from_usb, so it\'s actually missing'.format(album)
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
    print 'Candidate duplicates on USB: ', missing_from_usb.collection
    print 'Cancdidate duplicates on Drive: ', missing_from_drive.collection

    # TODO: Make this actually work
    # Need to be very careful with determining duplicates and whatnot
    # TODO: Write unittests
    missing_usb_keys =  missing_from_usb.collection.keys()
    print 'missing from drive', missing_from_drive.collection
    for artist_name in missing_from_drive.collection:
        if artist_name in missing_from_usb.collection:
            print 'artist name from weird LC: ', artist_name
            for album in missing_from_drive.collection[artist_name].albums:
                different_album = get_difference(album, artist_name, missing_from_usb)
                if artist_name not in actually_missing_from_usb.collection:
                    actually_missing_from_usb.collection[artist_name] = ArtistItem(artist_name, missing_from_usb.collection[artist_name].etag)
                if different_album is not None:
                    actually_missing_from_usb.collection[artist_name].albums.append(different_album)
    print 'actually missing', actually_missing_from_usb
    return actually_missing_from_usb

# def find_duplicate_albums(missing_from_usb, missing_from_drive):
#     """
#     :param missing_from_drive The MusicLibrary of music on USB but not Drive
#     :param missing_from_usb The MusicLibrary of music on Drive but not USB
#     Sometimes, usually due to unicode fuckery, albums will be compared as inequal even though they are.
#     This function looks for strings that differ due to unicode characters
#     Or are substrings of each other.
#     """
#     # print 'missing from usb', missing_from_usb
#     # print 'missing from drive', missing_from_drive
#     clean_missing_from_usb = {}
#     clean_missing_from_drive = {}
#     # print 'DT in missing from drive: {0}'.format(''.join([str(album) for album in missing_from_drive['Dream Theater'].albums]))
#     print 'Candidate duplicates (usb): ', missing_from_usb
#     print 'Candidate duplicates (drive): ', missing_from_drive
#     for artist_name in list(missing_from_usb.keys()):
#         if artist_name in missing_from_drive:
#             for album in missing_from_usb[artist_name].albums:
#                 # for album in the albums of the artist in missing_from_usb
#                 drive_album = [m for m in missing_from_drive[artist_name].albums if m is album][0]
#                 # if it's in the albums of the missing_from_drive artist too it's a duplicate
#                 if album in missing_from_drive[artist_name].albums:
#                     print 'Obvious duplicate is obvious: {0} and {1} are the same.'.format(drive_album,album)
#                 # if it's quite close to an album in drive
#                 elif check_duplicate_string(album, drive_album):
#                     print 'Less obvious false positive: {0} and {1}'.format(drive_album, album)
#                 # album is in missing_from_usb but not missing_from_drive
#                 else:
#                     print 'Album is not in missing_from_drive, only missing_from_usb.'
#                     if album not in missing_from_drive[artist_name]:
#                         clean_missing_from_usb[artist_name] = ArtistItem(artist_name, missing_from_usb[artist_name].etag)
#                     clean_missing_from_usb[artist_name].albums.append(album)
#                 '''
#                 for drive_album in missing_from_drive[artist].albums:
#                     if check_duplicate_string(drive_album, album):
#                         print "Detected false positive: {0} and {1}".format(drive_album, album)
#                     else:
#                         print "Determined {0} and {1} are not the same album.".format(drive_album, album)
#                         clean_missing_from_drive[artist] = missing_from_drive[artist]
#                         clean_missing_from_usb[artist] = missing_from_usb[artist]
#                 '''
#     return clean_missing_from_usb, clean_missing_from_drive


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
    if len(shared) > 0.8*len(keys_s1) or len(shared) > 0.8*len(keys_s2):
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

# Unit tests for music_sync_utils.py

import unittest
import music_sync_utils
import random


def get_stock_collection(cat_number):
    a1 = create_stock_artist(1)
    a2 = create_stock_artist(2)
    a3 = create_stock_artist(3)
    collection = {}
    if cat_number == 1:
        collection[a1.name] = a1
        collection[a2.name] = a2
        collection[a3.name] = a3
        return collection
    if cat_number == 2:
        collection[a1.name] = a1
        collection[a2.name] = a2
        return collection


def get_stock_library(cat_number):
    if cat_number == 1:
        etag = 'this is stock lib 1'
        lib_a = music_sync_utils.MusicLibrary(etag)


def get_random_string(length):
    s = []
    for i in range(0, length):
        rand_char = chr(int((random.random() * 26)+97))
        i.append(rand_char)
    return ''.join(str(c) for c in s)


def create_stock_artist(cat_number):
    """
    Creates a stock artist based on the number given.
    :param cat_number: The choice of stock artist.
    :return: The stock artist, or default (first) if no artist with the given number exists.
    """
    if cat_number == 1:
        artist = music_sync_utils.ArtistItem('The Testers', 'test-etag-1')
        a1 = music_sync_utils.AlbumItem('Testing Notes', 200)
        a2 = music_sync_utils.AlbumItem('The Return of the Testers', 120)
        a3 = music_sync_utils.AlbumItem('Testing the Great Unknown', 210)
        artist.albums.extend([a1,a2,a3])
        return artist

    if cat_number == 2:
        artist = music_sync_utils.ArtistItem('Technical Debt', 'test-etag-2')
        a1 = music_sync_utils.AlbumItem('VBScript is a Good Idea', 170)
        a2 = music_sync_utils.AlbumItem('Stored Procedures are for Business Logic', 150)
        artist.albums.extend([a1, a2])
        return artist

    if cat_number == 3:
        artist = music_sync_utils.ArtistItem('The Monday Mornings', 'test-etag-3')
        a1 = music_sync_utils.AlbumItem('Traffic Jam', 150)
        a2 = music_sync_utils.AlbumItem('The Last Bagel', 110)
        a3 = music_sync_utils.AlbumItem('Power Walking Blues', 230)
        artist.albums.extend([a1, a2, a3])
        return artist

    # This is number 3 without one of 3's albums.
    if cat_number == 4:
        artist = music_sync_utils.ArtistItem('The Monday Mornings', 'test-etag-3')
        a1 = music_sync_utils.AlbumItem('Traffic Jam', 150)
        a3 = music_sync_utils.AlbumItem('Power Walking Blues', 230)
        artist.albums.extend([a1, a3])
        return artist

    # This is the result of 3 - 4.
    if cat_number == 5:
        artist = music_sync_utils.ArtistItem('The Monday Mornings', 'test-etag-3')
        a2 = music_sync_utils.AlbumItem('The Last Bagel', 110)
        artist.albums.extend([a2])
        return artist

    # The same as 1 with a different name.
    if cat_number == 6:
        artist = music_sync_utils.ArtistItem('The Testers', 'test-etag-1')
        a1 = music_sync_utils.AlbumItem('Testing Notes', 200)
        a2 = music_sync_utils.AlbumItem('The Return of the Testers', 120)
        a3 = music_sync_utils.AlbumItem('Testing the Great Unknown', 210)
        artist.albums.extend([a1,a2,a3])
        return artist


def create_random_artist():
    """
    Creates an artist with randomly generated name, number of albums, and albums.`
    :return:
    """
    random_artist_name = get_random_string(10)
    random_etag = get_random_string(20)
    artist = music_sync_utils.ArtistItem(random_artist_name,random_etag)
    # Populate with 1 thru 10 albums
    num_of_albums = int(random.random() * 10)
    for i in range(0, num_of_albums):
        random_album_name = get_random_string(15)
        random_album_size = random.randint(50,250)
        album = music_sync_utils.AlbumItem(random_album_name, random_album_size)
        artist.albums.append(album)
    return artist


class TestFindDuplicateAlbums(unittest.TestCase):

    def test_missing_artist(self):
        """
        find_duplicate_albums is meant to:
        Sometimes, usually due to unicode fuckery, albums will be compared as inequal even though they are.
        This function looks for strings that differ due to unicode characters
        Or are substrings of each other.
        :return:
        """
        lib_a = music_sync_utils.MusicLibrary('lib a')
        lib_a



class TestSubtractCollectionElements(unittest.TestCase):

    def test_missing_artist(self):
        lib_a = music_sync_utils.MusicLibrary('a')
        lib_b = music_sync_utils.MusicLibrary('b')

        # Has 3 unique artists
        # Has 2 unique artist
        lib_a.collection = get_stock_collection(1)
        lib_b.collection = get_stock_collection(2)

        expected_lib = music_sync_utils.MusicLibrary('expected')
        a3 = create_stock_artist(3)
        expected_lib.collection = {a3.name: a3}
        actual_result = music_sync_utils.subtract_collection_elements(lib_a, lib_b)
        self.assertEqual(expected_lib.collection, actual_result.collection)
        for artist in actual_result.collection:
            self.assertEqual(actual_result.collection[artist], expected_lib.collection[artist])
            self.assertEqual(actual_result.collection[artist].albums, expected_lib.collection[artist].albums)

    def test_missing_album(self):
        """
        subtract_collection_elements test
        Tests for to see if albums subtract properly.
        :return:
        """
        # Album 4 is Album 3 with one fewer album.
        a1 = create_stock_artist(1)
        a2 = create_stock_artist(2)
        a3 = create_stock_artist(3)
        a4 = create_stock_artist(4)

        lib_a = music_sync_utils.MusicLibrary('a')
        lib_b = music_sync_utils.MusicLibrary('b')
        lib_a.collection = {a1.name: a1, a2.name: a2, a3.name: a3}
        lib_b.collection = {a1.name: a1, a2.name: a2, a4.name: a4}

        a5 = create_stock_artist(5)
        expected_lib = music_sync_utils.MusicLibrary('expected')
        expected_lib.collection = {a5.name: a5}
        actual_result = music_sync_utils.subtract_collection_elements(lib_a, lib_b)
        print 'lib a collection', lib_a.collection['The Monday Mornings'].albums
        print 'lib b collection', lib_b.collection['The Monday Mornings'].albums
        print 'expected collection', expected_lib.collection['The Monday Mornings'].albums
        print 'actual collection', actual_result.collection['The Monday Mornings'].albums
        self.assertEqual(expected_lib.collection, actual_result.collection)
        for artist in actual_result.collection:
            self.assertEqual(actual_result.collection[artist], expected_lib.collection[artist])
            self.assertEqual(actual_result.collection[artist].albums, expected_lib.collection[artist].albums)

    def test_name_equality(self):
        a1 = create_stock_artist(1)
        a1_copy = create_stock_artist(1)
        self.assertEqual(a1, a1_copy)

    def test_album_name_equality(self):
        a1 = create_stock_artist(1)
        a1_copy = create_stock_artist(6)
        for idx, a in enumerate(a1.albums):
            self.assertEqual(a, a1_copy.albums[idx])

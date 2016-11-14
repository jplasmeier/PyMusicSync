from pydrive.drive import GoogleDrive
import unittest
import os
import subprocess
import gdrive

MYDIR = os.path.dirname(__file__)

# Music Test Small:
# Vampire Weekend -> [Contra, Vampire Weekend, Modern Vampires of the City]
# Big L -> [Lifestylez Ov Da Poor and Dangerous, The Big Picture]
test_folder_name = 'Music_Test_Small'
test_folder_artists = ['Vampire Weekend', 'Big L']
test_folder_albums = {'Vampire Weekend': ['2013 - Modern Vampires of the City [Deluxe Edition] (2013)', 'Contra', 'Vampire Weekend [Japan Import] V0'],
                      'Big L': ['Lifestylez Ov Da Poor and Dangerous', 'The Big Picture']}
local_folder_name = 'temp_test_music'

# Helper Functions


def mkdir_for_download():
    """
    mkdir here and return it's path.
    :return:
    """


class TestDownloadRecursive(unittest.TestCase):

    def test_download_folder(self):
        """
        Download a test folder from Google Drive to a temporary directory.

        :return:
        """

        # Download to Local
        drive = GoogleDrive(gdrive.login())
        music_folder = gdrive.get_folder_from_root(drive, test_folder_name)
        local_dir = os.path.join(MYDIR, local_folder_name)
        if not os.path.isdir(local_dir):
            os.mkdir(local_dir)
        gdrive.download_recursive(drive, music_folder, local_dir)

        # Check against expected:
        local_artists = os.listdir(local_dir)
        for artist_name in test_folder_artists:
            self.assertIn(artist_name, local_artists)
            local_albums = os.listdir(os.path.join(local_dir, artist_name))
            for album in test_folder_albums[artist_name]:
                self.assertIn(album, local_albums)

        # Clean up
        delete_arguments = ['-rf', local_dir]
        return subprocess.call(["rm"] + delete_arguments)
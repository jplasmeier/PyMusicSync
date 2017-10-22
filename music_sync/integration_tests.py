# integration_tests.py
# Integration Tests for Mass Media Sync

import os
import music_sync

MYDIR = os.path.dirname(__file__)


class TestOneWayDriveToUSB:
    """
    Test that one-way sync from Drive to USB works.
    So, everything in Drive should also be in USB.
    TODO: Fix by pulling out old-style modes from config
    """
    music_sync.main("Media Test", "/Users/jgp/Dropbox/Documents/ProgrammingProjects/Python3/PyMusicSync/Media Test")

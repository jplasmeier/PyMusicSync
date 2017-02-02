# config.py
# Configuration module for Mass Media Sync.


def load_boot_disk_path():
    return "/dev/disk1"


def load_general_cache_path():
    return "general_cache.p"


def load_general_drive_folder_name():
    return "Media"


def load_general_test_drive_folder_name():
    return "Media Test"


def load_general_usb_device_path():
    return "/Users/jgp/Documents/temp"


def load_general_test_usb_device_path():
    return "/Users/jgp/Dropbox/ProgrammingProjects/Python3/PyMusicSync/Media Test"


def load_google_drive_folder_name():
    return "Music"


def load_google_drive_test_folder_name():
    return "Music_Test_Small"


def load_mode():
    """
    trad, genenral
    :return:
    """
    return "general"


def load_option_cache():
    return False


def load_option_clean_unicode():
    return False


def load_option_delete():
    return False


def load_sync_mode():
    """
    one-way, two-way
    :return:
    """
    return "two-way"


def load_trad_cache_path():
    return "trad_cache.p"


def load_usb_device_path():
    return "/Volumes/Untitled"

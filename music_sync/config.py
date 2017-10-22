# config.py
# Configuration module for Mass Media Sync.


def cache_drive_metadata():
    """
    Do not use until the following bug is fixed:
    The massive DriveFolder that is built at the
    beginning of the program does not include
    the new contents from USB that have been
    uploaded, so these files will be uploaded
    multiple times. Google Drive does not
    deduplicate, either.
    :return:
    """
    return False


def ignore_dotfiles():
    return True


def timing_mode():
    return True


def load_boot_disk_path():
    return "/dev/disk1"


def load_general_cache_path():
    return "general_cache.p"


"""
NOTE: This must be at the root of your Google Drive.
"""
def load_general_drive_folder_name():
    return "Music"


def load_general_usb_device_path():
    #return "/Volumes/Untitled/Users/jgp"
    return "/Volumes/Untitled"


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

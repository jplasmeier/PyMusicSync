# 30 Cases of Pickles? That's a lot of pickles!
import pickle
import os.path
import music_sync_utils

# File names
drive_library_cache_path = "drive_library_cache.p"
usb_library_cache_path = "usb_library_cache.p"
drive_collection_cache_path = "drive_collection_cache_path.p"
usb_collection_cache_path = "usb_collection_cache_path.p"


# General pickling functions


def pickle_something(thing, filepath):
    try:
        with open(filepath, "w") as fp:
            pickle.dump(thing, fp)
    except Exception, err:
        print "Error Pickling {0} to {1}: {2}".format(thing, filepath, err)
    return True


def load_something(filepath):
    try:
        thing = None
        if os.path.isfile(filepath):
            with open(filepath, "r") as fp:
                thing = pickle.load(fp)
        return thing
    except Exception, err:
        print "Error loading from {0}: {1}".format(filepath, err)


def pickle_drive_library(library, folder):
    cached_library = get_cached_drive_library(folder)
    if cached_library is not None and cached_library.etag != library.etag:
        print "Saving library changes to cache"
        return pickle_something(library, drive_library_cache_path)
    elif cached_library is None:
        pickle_something(library, drive_library_cache_path)
    else:
        print "Nothing to update in cache."
        return


def load_drive_library():
    return load_something(drive_library_cache_path)


# TODO: Clean up
def get_cached_drive_library(folder):
    """
    Returns a cached version of the Drive collection if there is one
    :param folder: The (incoming) folder that contains the contents of the Collection
    :return: The collection if there's a cached version, otherwise return None
    """
    library_cache = load_drive_library()
    # etags match -> return cache
    if not library_cache:
        return
    if folder.metadata['etag'] == library_cache.etag:
        return library_cache
    else:
        return


def get_cached_drive_collection(gdrive_folder=None):
    """
    For some reason this function takes an optional Google Drive folder
    :param folder:
    :return:
    """
    if gdrive_folder is not None:
        drive_library = get_cached_drive_library(gdrive_folder)
    else:
        drive_library = get_cached_independent_drive_collection()
    if drive_library is not None:
        return drive_library.collection
    else:
        return {}


def get_cached_independent_drive_collection():
    library = load_drive_library()
    if library is not None:
        return library.collection


def pickle_ioreg(ioreg_device, ioreg_file):
    with open(ioreg_file, "wb") as fp:
        pickle.dump(ioreg_device, fp)


def load_ioreg(ioreg_file):
    if os.path.isfile(ioreg_file):
        with open(ioreg_file, "rb") as fp:
            ioreg_device = pickle.load(fp)
        return ioreg_device
    else:
        return None
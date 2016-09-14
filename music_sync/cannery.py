# 30 Cases of Pickles? That's a lot of pickles!
import pickle
import os.path


def load_album_cache(drive_album_size_cache):
    try:
        album_cache = {}
        if os.path.isfile(drive_album_size_cache):
            with open(drive_album_size_cache, "rb") as fp:
                album_cache = pickle.load(fp)
        return album_cache
    except Exception, err:
        print "Cache error: {}".format(err)


def pickle_album_cache(drive_album_size_cache, album_cache):
    """
    drive_album_size_cache: file to pickle album_cache to
    album_cache: the object to be pickled
    """
    try:
        with open(drive_album_size_cache, "wb") as fp:
            pickle.dump(album_cache, fp)
    except Exception, err:
        print "Error Pickling Albums: {}".format(err)
    return True


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


def get_album_size_from_cache(album_id):
    raise NotImplementedError


def add_album_to_cache(album_id, size, current_time):
    pass
    # raise NotImplementedError

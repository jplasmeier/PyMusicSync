# 30 Cases of Pickles? That's a lot of pickles!
import pickle
import os.path

collection_cache_path = "collection_cache.p"


def load_album_cache(drive_album_size_cache):
    try:
        album_cache = {}
        if os.path.isfile(drive_album_size_cache):
            with open(drive_album_size_cache, "rb") as fp:
                album_cache = pickle.load(fp)
        return album_cache
    except Exception, err:
        print "Cache error: {}".format(err)


def pickle_collection_cache(collection):
    """
    drive_album_size_cache: file to pickle album_cache to
    album_cache: the object to be pickled
    """
    try:
        with open(collection_cache_path, "wb") as fp:
            pickle.dump(collection, fp)
    except Exception, err:
        print "Error Pickling Collection: {}".format(err)
    return True


def load_collection_cache():
    try:
        album_cache = None
        if os.path.isfile(collection_cache_path):
            with open(collection_cache_path, "rb") as fp:
                album_cache = pickle.load(fp)
        return album_cache
    except Exception, err:
        print "Cache error: {}".format(err)


# TODO: Test
def get_cached_drive_collection(folder):
    """
    Returns a cached version of the Drive collection
    :param folder: The folder that contains the contents of the Collection
    :return: The collection if there's a cached version, otherwise return None
    """
    print folder.metadata
    incoming_etag = folder.metadata['etag']
    collection_cache = load_collection_cache()
    if not collection_cache or not collection_cache.etag:
        return
    if incoming_etag == collection_cache.etag:
        print collection_cache.etag
        print "collection cache", [k for k in collection_cache.collection]
        return collection_cache
    else:
        return


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

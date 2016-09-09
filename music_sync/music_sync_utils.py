# Utilities for MusicSync
import codecs

def check_drive_not_in_usb_collection(drive_collection, usb_collection):
    missing_from_usb_collection = {}
    for artist in drive_collection:
        if artist not in usb_collection:
            #TODO: investigate performance of caching lookup (save the list locally instead of looking up artist again)
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
            #TODO: investigate performance of caching lookup (save the list locally instead of looking up artist again)
            for album in usb_collection[artist]:
                missing_from_drive_collection[artist].append(album)
        else:
            for album in usb_collection[artist]:
                if album not in drive_collection[artist]:
                    if artist not in missing_from_drive_collection:
                        missing_from_drive_collection[artist] = []
                    missing_from_drive_collection[artist].append(album)
    return missing_from_drive_collection

def clean_unicode(collection):
    clean_dict = {}
    for k in collection:
        k_clean = codecs.utf_8_decode(k.encode('utf-8'))
        clean_dict[k_clean] = []
        for a in collection[k]:
            clean_dict[k_clean].append(codecs.utf_8_decode(a.encode('utf-8')))
    return clean_dict

def print_collection(collection):
    for artist in collection:
        print "Artist: {}".format(artist)
        for album in collection[artist]:
            print "---Album: {}".format(album)

def find_possible_duplicate_albums(missing_from_usb, missing_from_drive):
    """
    Sometimes, usually due to unicode fuckery, albums will be compared as inequal even though they are.
    This function looks for strings that differ due to unicode characters
    Or are substrings of each other.
    """
    for artist in list(missing_from_usb.keys()):
        if artist in missing_from_drive:
            for album in missing_from_usb[artist]:
                for drive_album in missing_from_drive[artist]:
                    if check_duplicate_string(drive_album, album):
                        print "Detected false positive: {0} and {1}".format(drive_album, album)
                        missing_from_usb[artist].remove(album)
                        missing_from_drive[artist].remove(drive_album)
                        if not missing_from_usb[artist]:
                            del missing_from_usb[artist]
                        if not missing_from_drive[artist]:
                            del missing_from_drive[artist]

    return missing_from_usb, missing_from_drive

def check_duplicate_string(s1, s2):
    """
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
    if len(shared) > 0.7*len(keys_s1) or len(shared) > 0.7*len(keys_s2):
        return True
    else:
        return False

def fix_possible_duplicate_albums(missing_from_usb, missing_from_drive):
    """
    Update files to match
    """
    pass

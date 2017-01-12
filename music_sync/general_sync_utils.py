# general_sync_utils
# similar to music_sync_utils but more general


class NameEqualityMixin():

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)


class Folder(NameEqualityMixin):

    def __init__(self, name):
        self.name = name
        self.contents = []

    def __str__(self):
        return "{0}: {1}".format(self.name, [str(c) for c in self.contents])


class File(NameEqualityMixin):

    def __init__(self, name, size):
        self.name = name
        self.size = size

    def __str__(self):
        return self.name


class SyncAssertions:

    def assertFolderEquality(self, actual, expected):

        for a_i in actual.contents:
            if a_i not in expected.contents:
                raise AssertionError("Item {0} not in folder {1}".format(a_i, expected))
            if isinstance(a_i, Folder):
                b_i, = [i for i in expected.contents if i.name == a_i.name]
                print("Checking subfolders: ", a_i, b_i)
                self.assertFolderEquality(a_i, b_i)
        for b_i in expected.contents:
            if b_i not in actual.contents:
                raise AssertionError("Item {0} not in folder {1}".format(b_i, actual))
            if isinstance(b_i, Folder):
                a_i, = [i for i in actual.contents if i.name == b_i.name]
                print("Checking subfolders: ", a_i, b_i)
                self.assertFolderEquality(a_i, b_i)

        return

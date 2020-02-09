# general_sync_utils
# similar to music_sync_utils but more general


class NameEqualityMixin:

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
        self.contents = {}

    def __str__(self):
        return "Folder: {0}: {1}".format(self.name, [str(c) for c in self.contents.keys()])


class File(NameEqualityMixin):

    def __init__(self, name, size):
        self.name = name
        self.size = size

    def __str__(self):
        return "File: {0}".format(self.name)


class SyncAssertions:

    def assertFolderEquality(self, actual, expected):

        for actual_item in actual.contents:
            if actual_item not in expected.contents:
                raise AssertionError("Actual Item {0} not in Expected Folder: {1}".format(actual_item, expected))
            if isinstance(actual_item, Folder):
                expected_item = expected.contents[actual_item.name]
                print("Checking subfolders: ", actual_item, expected_item)
                self.assertFolderEquality(actual_item, expected_item)
        for expected_item in expected.contents:
            if expected_item not in actual.contents:
                raise AssertionError("Expected Item {0} not in Actual Folder {1}".format(expected_item, actual))
            if isinstance(expected_item, Folder):
                actual_item, = actual.contents[expected_item.name]
                print("Checking subfolders: ", actual_item, expected_item)
                self.assertFolderEquality(actual_item, expected_item)

        return

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

import general_sync_utils
import sync
import unittest


def get_file_one():
    return general_sync_utils.File("File One", 400)


def get_file_two():
    return general_sync_utils.File("File Two", 20)


def get_file_three():
    return general_sync_utils.File("File Three", 302)


def get_file_four():
    return general_sync_utils.File("File Four", 23)


def get_empty_difference_result():
    return general_sync_utils.Folder("Difference Root")


def get_subfolder_one_1():
    subfolder_one = general_sync_utils.Folder("Subfolder One")
    file_one = get_file_one()
    subfolder_one.contents.append(file_one)
    return subfolder_one

def get_subfolder_one_3():
    subfolder_one = general_sync_utils.Folder("Subfolder One")
    file_three = get_file_three()
    subfolder_one.contents.append(file_three)
    return subfolder_one

def get_subfolder_one_4():
    subfolder_one = general_sync_utils.Folder("Subfolder One")
    file_four = get_file_four()
    subfolder_one.contents.append(file_four)
    return subfolder_one

def get_subfolder_one_1_3():
    subfolder_one = general_sync_utils.Folder("Subfolder One")
    file_one = get_file_one()
    file_three = get_file_three()
    subfolder_one.contents.extend([file_three, file_one])
    return subfolder_one

def get_subfolder_one_3_4():
    subfolder_one_star = general_sync_utils.Folder("Subfolder One")
    file_three = get_file_three()
    file_four = get_file_four()
    subfolder_one_star.contents.extend([file_three, file_four])
    return subfolder_one_star


def get_union_of_subfolder_one_and_star():
    subfolder_one_union = general_sync_utils.Folder("Subfolder One")
    file_one = get_file_one()
    file_three = get_file_three()
    file_four = get_file_four()
    subfolder_one_union.contents.extend([file_one, file_three, file_four])
    return subfolder_one_union


def get_union_of_folder_one_and_two():
    expected_union = general_sync_utils.Folder("Union Root")
    file_one = get_file_one()
    file_two = get_file_two()
    subfolder_one_expected = get_union_of_subfolder_one_and_star()
    expected_union.contents.extend([file_one, file_two, subfolder_one_expected])
    return expected_union


def get_intersection_of_folder_one_and_two():
    """
    Expected: File One, Subfolder One (File Three)
    :return:
    """
    expected_intersection = general_sync_utils.Folder("Intersection Root")
    file_one = get_file_one()
    subfolder_one = get_subfolder_one_3()
    expected_intersection.contents.extend([file_one, subfolder_one])
    return expected_intersection

def get_test_folder_one():
    folder_one = general_sync_utils.Folder("Folder One")
    file_one = get_file_one()
    subfolder_one = get_subfolder_one_1_3()
    folder_one.contents.extend([file_one, subfolder_one])
    return folder_one


def get_test_folder_two():
    folder_two = general_sync_utils.Folder("Folder Two")
    file_one = get_file_one()
    file_two = get_file_two()
    subfolder_one_star = get_subfolder_one_3_4()

    folder_two.contents.extend([file_one, file_two, subfolder_one_star])
    return folder_two


def get_expected_union_minus_one():
    """
    Union - One: Subfolder One (File Three)
    :return:
    """
    expected_subtraction = general_sync_utils.Folder("Difference Root")
    file_two = get_file_two()
    subfolder_one = get_subfolder_one_4()
    expected_subtraction.contents.extend([file_two, subfolder_one])
    return expected_subtraction


def get_expected_one_minus_intersection():
    """
    One - Intersection: Subfolder One (File One)
    :return:
    """
    expected_subtraction = general_sync_utils.Folder("Difference Root")
    subfolder_one = get_subfolder_one_1()
    expected_subtraction.contents.append(subfolder_one)
    return expected_subtraction


class TestGetClosestIndex(unittest.TestCase):

    def test_closest_index(self):
        boundaries = {0: '3', 257: 'T', 131: 'L', 260: 'V', 263: 'W', 11: 'A', 154: 'M', 31: 'B', 163: 'N', 169: 'O', 47: 'C', 178: 'P', 189: 'R', 62: 'D', 76: 'E', 82: 'F', 213: 'S', 92: 'G', 95: 'H', 99: 'I', 115: 'J', 122: 'K'}
        target_index = 30
        actual = sync.get_closest_index(boundaries, target_index)
        expected = 31
        self.assertEqual(actual, expected)


class TestUnion(unittest.TestCase, general_sync_utils.SyncAssertions):

    def test_union_two_folders(self):
        """
        Folder One: File One, Subfolder One (File One, File Three)
        Folder Two: File One, File Two, Subfolder One (File One, File Four)
        Expected: File One, File Two, Subfolder One (File One, File Three, File Four)
        :return:
        """

        folder_one = get_test_folder_one()
        folder_two = get_test_folder_two()

        expected_folder = get_union_of_folder_one_and_two()

        actual = sync.union([folder_one, folder_two])
        self.assertFolderEquality(actual, expected_folder)


class TestIntersection(unittest.TestCase, general_sync_utils.SyncAssertions):

    def test_intersect_two_folders(self):
        """
        Folder One:     File One, Subfolder One (File One, File Three)
        Folder Two:     File One, File Two, Subfolder One (File One, File Four)
        Expected:       File One, Subfolder One (File Three)
        :return:
        """
        folder_one = get_test_folder_one()
        folder_two = get_test_folder_two()

        expected_folder = get_intersection_of_folder_one_and_two()

        actual = sync.intersection([folder_one, folder_two])
        self.assertFolderEquality(actual, expected_folder)


class TestSubtraction(unittest.TestCase, general_sync_utils.SyncAssertions):

    def test_subtraction_on_union(self):
        """
        Folder One:  File One, Subfolder One (File One, File Three)
        Folder Two:  File One, File Two, Subfolder One (File One, File Four)
        Union:       File One, File Two, Subfolder One (File One, File Three, File Four)
        Union - One: File Two, Subfolder One (File Four)
        :return:
        """
        folder_one = get_test_folder_one()
        folder_two = get_test_folder_two()

        expected_union_minus_one = get_expected_union_minus_one()

        union_folder = sync.union([folder_one, folder_two])
        actual_union_minus_one = sync.subtraction(union_folder, folder_one)
        self.assertFolderEquality(actual_union_minus_one, expected_union_minus_one)

    def test_subtraction_on_intersection(self):
        """
        Folder One:         File One, Subfolder One (File One, File Three)
        Folder Two:         File One, File Two, Subfolder One (File One, File Four)
        Intersection:       File One, Subfolder One (File Three)
        One - Intersection: Subfolder One (File One)
        :return:
        """
        folder_one = get_test_folder_one()
        folder_two = get_test_folder_two()

        expected_one_minus_intersection = get_expected_one_minus_intersection()

        intersection_folder = sync.intersection([folder_one, folder_two])
        actual_one_minus_intersection = sync.subtraction(folder_one, intersection_folder)
        print("Actual Contents: ", [str(c) for c in actual_one_minus_intersection.contents])
        print("Expected Contents: ", [str(c) for c in expected_one_minus_intersection.contents])
        self.assertFolderEquality(actual_one_minus_intersection, expected_one_minus_intersection)

    def test_subtraction_on_intersection_empty_result(self):
        """
        Folder One:         File One, Subfolder One (File One, File Three)
        Folder Two:         File One, File Two, Subfolder One (File One, File Four)
        Intersection:       File One, Subfolder One (File Three)
        Intersection - One: Empty
        :return:
        """
        folder_one = get_test_folder_one()
        folder_two = get_test_folder_two()

        expected_one_minus_intersection = get_empty_difference_result()

        intersection_folder = sync.intersection([folder_one, folder_two])
        actual_one_minus_intersection = sync.subtraction(intersection_folder, folder_one)
        print("Actual Contents: ", [str(c) for c in actual_one_minus_intersection.contents])
        print("Expected Contents: ", [str(c) for c in expected_one_minus_intersection.contents])
        self.assertFolderEquality(actual_one_minus_intersection, expected_one_minus_intersection)
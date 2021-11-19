import os
import tempfile
import shutil

import pytest

from inginious.common.filesystems.local import LocalFSProvider

FILE_CONTENT = b"test string"
PROVIDER=LocalFSProvider

@pytest.fixture
def init_tmp_dir():
    """ Create a temporary folder """
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)

@pytest.fixture
def init_prefix(init_tmp_dir):
    prefix = 'prefix'
    full_prefix = os.path.join(init_tmp_dir, prefix)
    os.mkdir(full_prefix)
    yield full_prefix
    if os.path.exists(full_prefix):
        shutil.rmtree(full_prefix)

@pytest.fixture
def init_prefix_with_file(init_prefix):
    filename = 'test.txt'
    filepath = os.path.join(init_prefix, filename)
    with open(filepath, 'wb') as fd:
        fd.write(FILE_CONTENT)
    yield (init_prefix, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

@pytest.fixture
def init_subfolder(init_prefix):
    """ Create a prefix folder with a subfolder named 'subfolder' within """
    test_dir = 'subfolder'
    subdir = os.path.join(init_prefix, test_dir)
    os.mkdir(subdir)
    yield (init_prefix, test_dir)
    if os.path.exists(subdir):
        os.rmdir(subdir)

@pytest.fixture
def init_subfolder_with_file(init_subfolder):
    filename = 'test.txt'
    prefix, subfolder = init_subfolder
    filepath = subfolder + '/' + filename
    full_filepath = os.path.join(prefix, filepath)
    with open(full_filepath, 'wb') as fd:
        fd.write(FILE_CONTENT)
    yield (prefix, filepath)
    if os.path.exists(full_filepath):
        os.remove(full_filepath)

@pytest.fixture
def init_full(init_prefix_with_file, init_subfolder_with_file):
    prefix, file1 = init_prefix_with_file
    _, file2 = init_subfolder_with_file
    return (prefix, file1, file2)


class TestInit:
    """ LocalFSProvider initialization """

    def test_prefix(self, init_prefix):
        """ Test the prefix of a newly generated LocalFSProvider without trailing slash """
        tmp_dir = init_prefix
        lp = PROVIDER(tmp_dir)
        assert lp.prefix == tmp_dir + '/'

    def test_prefix_trailing(self, init_prefix):
        """ Test the prefix of a newly generated LocalFSProvider with trailing slash """
        tmp_dir = init_prefix + '/'
        lp = PROVIDER(tmp_dir)
        assert lp.prefix == tmp_dir

    def test_prefix_non_existing(self, init_tmp_dir):
        """ Test the prefix of a newly generated LocalFSProvider with non-existing prefix """
        tmp_dir = init_tmp_dir + '/prefix'
        lp = PROVIDER(tmp_dir)
        assert lp.prefix == tmp_dir + '/'


class TestFromSubfolder:
    """ from_subfolder() tests """

    def test_subfolder(self, init_subfolder):
        """ Test the creation of a new LocalFSP whose prefix is a subfolder of an existing one """
        prefix, subfolder = init_subfolder
        lp = PROVIDER(prefix)
        sub_lp = lp.from_subfolder(subfolder)
        assert sub_lp != lp # from_subfolder must return a new LocalFSProvider object
        assert sub_lp.prefix == os.path.join(prefix, subfolder) + '/'


class TestExists:
    """ exists() tests """

    def test_exists_prefix_and_subfolder(self, init_subfolder):
        """ Test if LocalFSP can check that its prefix and subfolder exists """
        lp = PROVIDER(init_subfolder[0])
        assert lp.exists()
        assert lp.exists(os.path.join(init_subfolder[0], init_subfolder[1]))

    def test_exists_non_existing_path(self, init_tmp_dir):
        """ Test if LocalFSP can check that a subfolder does not exist """
        lp = PROVIDER(init_tmp_dir)
        assert not lp.exists(os.path.join(lp.prefix, 'test'))

    def test_exists_non_existing_prefix(self, init_tmp_dir):
        """ Test if LocalFSP can check that its prefix does not exist """
        prefix = os.path.join(init_tmp_dir, 'prefix')
        lp = PROVIDER(prefix)
        assert not lp.exists()


class TestEnsureExists:
    """ ensure_exists() tests """

    def test_ensure_exists(self, init_subfolder_with_file):
        """ Test if LocalFSP can check the existence of its prefix without overriding its content """
        prefix, filepath = init_subfolder_with_file
        lp = PROVIDER(prefix)
        lp.ensure_exists()
        assert os.path.exists(os.path.join(prefix, filepath))

    def test_ensure_exists_prefix(self, init_tmp_dir):
        """ Test if LocalFSP can create its prefix folder if it does not exist """
        prefix = os.path.join(init_tmp_dir, 'prefix')
        lp = PROVIDER(prefix)
        lp.ensure_exists()
        assert os.path.exists(prefix)

    def test_ensure_exists_subfolder(self, init_tmp_dir):
        """ Test if LocalFSP can create its prefix in nested non-existing folders """
        prefix1 = os.path.join(init_tmp_dir, 'prefix1')
        prefix2 = os.path.join(prefix1, 'prefix2')
        lp = PROVIDER(prefix2)
        lp.ensure_exists()
        assert os.path.exists(prefix2)


class TestPut:
    """ put() tests """
    pass # TODO


class TestGetFd:
    """ get_fd() tests """

    def test_get_fd_full_path(self, init_prefix_with_file):
        """ Test getting fd on valid full path """
        prefix, filename = init_prefix_with_file
        lp = PROVIDER(prefix)
        with pytest.raises(FileNotFoundError):
            lp.get_fd(os.path.join(lp.prefix, filename))

    def test_get_fd_non_existing_file(self, init_prefix):
        """ Test get_fd on non-existing filepath """
        lp = PROVIDER(init_prefix)
        with pytest.raises(FileNotFoundError):
            lp.get_fd('test.txt')

    def test_get_fd_directory(self, init_subfolder):
        """ Test get_fd on filepath leading to a folder """
        prefix, subfolder = init_subfolder
        lp = PROVIDER(prefix)
        with pytest.raises(IsADirectoryError):
            lp.get_fd(subfolder)

    def test_get_fd(self, init_prefix_with_file):
        """ Test getting fd on a valid file """
        prefix, filename = init_prefix_with_file
        lp = PROVIDER(prefix)
        fd = lp.get_fd(filename)
        assert fd.read() == FILE_CONTENT


class TestGet:
    """ get() tests """
    pass # TODO


class TestList:
    """ list() tests """

    def test_list_file_populated(self, init_full):
        """ List direct files """
        prefix, filename, _ = init_full
        lp = PROVIDER(prefix)
        assert lp.list(files=True, folders=False) == [filename]

    def test_list_file_populated_recursive(self, init_full):
        """ List all files recursively """
        prefix, file1, file2 = init_full
        lp = PROVIDER(prefix)
        assert set(lp.list(files=True, folders=False, recursive=True)) == set([file1, file2])

    def test_list_folder_populated(self, init_full):
        """ List direct directories """
        prefix, _, file2 = init_full
        lp = PROVIDER(prefix)
        assert set(lp.list(files=False, folders=True)) == set(['%s/' % file2.split('/')[0]])

    def test_list_folder_populated_recursive(self, init_full):
        """ List all directories recursively """
        prefix, _, file2 = init_full
        lp = PROVIDER(prefix)
        assert set(lp.list(files=False, folders=True, recursive=True)) == set(['%s/' % file2.split('/')[0]])

    def test_list_empty(self, init_prefix):
        """ List direct empty prefix """
        lp = PROVIDER(init_prefix)
        assert lp.list(files=True, folders=True) == []

    def test_list_empty_recursively(self, init_prefix):
        """ List empty prefix recursively """
        lp = PROVIDER(init_prefix)
        assert lp.list(files=True, folders=True, recursive=True) == []

    def test_list_populated_disabled(self, init_full):
        """ List nothing """
        prefix, _, _ = init_full
        lp = PROVIDER(prefix)
        assert lp.list(files=False, folders=False) == []

    def test_list_populated_disabled_recursive(self, init_full):
        """ List nothing recursively """
        prefix, _, _ = init_full
        lp = PROVIDER(prefix)
        assert lp.list(files=False, folders=False, recursive=True) == []

    def test_list_populated(self, init_full):
        """ List all direct prefix's content """
        prefix, file1, file2 = init_full
        lp = PROVIDER(prefix)
        assert set(lp.list(files=True, folders=True)) == set([file1, '%s/' % file2.split('/')[0]])

    def test_list_populated_recursively(self, init_full):
        """ List all prefix's content recursively """
        prefix, file1, file2 = init_full
        lp = PROVIDER(prefix)
        assert set(lp.list(files=True, folders=True, recursive=True)) == set([file1, file2, '%s/' % file2.split('/')[0]])

    def test_list_non_existing_prefix(self, init_tmp_dir):
        """ Try to list non-existing prefix """
        prefix = os.path.join(init_tmp_dir, 'prefix')
        lp = PROVIDER(prefix)
        with pytest.raises(FileNotFoundError):
            lp.list()

class TestDelete:
    """ delete() tests """

    def test_delete_non_existing(self, init_tmp_dir):
        """ Delete non-existing prefix """
        prefix = os.path.join(init_tmp_dir, 'prefix')
        lp = PROVIDER(prefix)
        with pytest.raises(FileNotFoundError):
            lp.delete()

    def test_delete_empty_prefix(self, init_prefix):
        """ Delete existing empty prefix """
        lp = PROVIDER(init_prefix)
        lp.delete()
        assert not os.path.exists(init_prefix)

    def test_delete_populated_prefix(self, init_full):
        """ Delete a populated prefix """
        prefix, file1, file2 = init_full
        lp = PROVIDER(prefix)
        lp.delete()
        assert not os.path.exists(prefix)

    def test_delete_subfolder_file(self, init_full):
        """ Delete a subfolder file without removing the subfolder """
        prefix, file1, file2 = init_full
        lp = PROVIDER(prefix)
        lp.delete(file2)
        assert os.path.exists(os.path.join(prefix, file1))
        assert os.path.exists(os.path.join(prefix, file2.split('/')[0]))

    def test_delete_subfolder(self, init_full):
        """ Delete a subfolder """
        prefix, file1, file2 = init_full
        lp = PROVIDER(prefix)
        subfolder = file2.split('/')[0]
        lp.delete(subfolder)
        assert os.path.exists(os.path.join(prefix, file1))
        assert not os.path.exists(os.path.join(prefix, subfolder))

    def test_delete_fullpath(self, init_full):
        """ Try to delete a full path """
        prefix, file1, file2 = init_full
        lp = PROVIDER(prefix)
        subfolder = file2.split('/')[0]
        with pytest.raises(FileNotFoundError):
            lp.delete(os.path.join(prefix, subfolder))


class TestGetLastModificationTime:
    """ get_last_modification_time() test """
    # TODO


class TestMove:
    """ move() tests """

    def test_move_non_existing_file(self, init_prefix):
        lp = PROVIDER(init_prefix)
        with pytest.raises(FileNotFoundError):
            lp.move('non-existing.src', 'non-existing.dst')


# pylint: disable=redefined-outer-name

import os
import re
import time
import tempfile
import shutil
import hashlib

import pytest

from inginious.common.filesystems.local import LocalFSProvider


def myhash(content: str) -> str:
    return hashlib.sha256(content).hexdigest()

FS = {
    'test1.txt': b'test string 1',
    'subfolder/test2.txt': b'test string 2',
    'subfolder2/subfolder3/test3.txt': b'test string 3',
}

FS = {filepath: {'content': content, 'hash': myhash(content)} for filepath, content in FS.items()}

def compare_files(filepath, content):
    return FS[filepath]['hash'] == myhash(content)

def recursive_content(dirname: str) -> list:
    def loop(dirname: str):
        acc = []
        for entry in os.listdir(dirname):
            entry = os.path.join(dirname, entry)
            acc += loop(entry) if os.path.isdir(entry) else [entry]
        return acc                                                    
    return loop(dirname)  

def get_dirs(dirs: list) -> set:
    def loop(dirs: list, acc: list) -> list:
        if dirs == []: return acc
        result = [dir for dir in [os.path.dirname(dir) for dir in dirs] if dir != '']
        return loop(result, acc + result)
    return loop(dirs, [])

def get_formatted_dirs(dirs: list) -> list:
    return ['%s/' % dir for dir in get_dirs(dirs)]

def get_direct_dirs(dirs: list) -> list:
    return ['%s/' % j for (i,j) in [os.path.split(i) for i in get_dirs(dirs)] if i == '']

########################
### Generic fixtures ###
########################

@pytest.fixture
def init_files():
    """ Fixture factory which allows to populate a temporary directory with FS content """
    all_files = []
    all_dirs = []

    def _create(prefix, files):
        for file in files:
            filepath = os.path.join(prefix, file)
            dirs = os.path.dirname(file)
            all_files.append(filepath)
            if dirs != '':
                subdirs = os.path.join(prefix, dirs)
                all_dirs.append(subdirs)
                os.makedirs(subdirs, exist_ok=True)
            with open(filepath, 'wb') as fd:
                fd.write(FS[file]['content'])
        return files

    yield _create

    for filepath in all_files:
        if os.path.exists(filepath):
            os.remove(filepath)
    for dirs in all_dirs:
        if os.path.exists(dirs):
            shutil.rmtree(dirs)

@pytest.fixture
def init_tmp_dir_factory():
    """ Create a temporary folder """
    paths = []

    def _tmp_dir():
        dir_path = tempfile.mkdtemp()
        paths.append(dir_path)
        return dir_path
    yield _tmp_dir

    """ Some FUT could create content in the prefix """
    for path in paths:
        shutil.rmtree(path)

#############################
### Non-provider fixtures ###
#############################

@pytest.fixture
def init_tmp_dir_np(init_tmp_dir_factory):
    return init_tmp_dir_factory()

@pytest.fixture
def init_tmp_single_file_factory(init_tmp_dir_np, init_files):
    """ Fixture factory populating a single file from FS in a temporary directory """
    def _return(idx: int):
        root = init_tmp_dir_np
        files = init_files(root, [list(FS.keys())[idx]])
        return (root, files[0])
    return _return

@pytest.fixture
def init_tmp_file_np(init_tmp_single_file_factory):
    return init_tmp_single_file_factory(0)

@pytest.fixture
def init_tmp_subfolder_file_np(init_tmp_single_file_factory):
    return init_tmp_single_file_factory(1)

@pytest.fixture(params=[idx for idx, key in enumerate(FS.keys())])
def init_tmp_each(request, init_tmp_single_file_factory):
    return init_tmp_single_file_factory(request.param)

@pytest.fixture
def init_tmp_full(init_tmp_dir_np, init_files):
    prefix = init_tmp_dir_np
    files = init_files(prefix, list(FS.keys()))
    return tuple([prefix] + [(files)])


#########################
### Provider fixtures ###
#########################

@pytest.fixture(params=[LocalFSProvider])
def init_tmp_dir(request, init_tmp_dir_factory):
    """ Create a temporary folder and a FSProvider class to test """
    return (request.param, init_tmp_dir_factory())

@pytest.fixture
def init_prefix(init_tmp_dir):
    """ Create a prefix directory for the FSProvider under test """
    provider, tmp_dir = init_tmp_dir
    prefix = 'prefix'
    full_prefix = os.path.join(tmp_dir, prefix)
    os.mkdir(full_prefix)
    provider = provider(full_prefix)

    yield (provider, full_prefix)

    if os.path.exists(full_prefix):
        shutil.rmtree(full_prefix)

@pytest.fixture
def init_single_file_factory(init_prefix, init_files):
    """ Fixture factory populating a single file from FS in a temporary directory """
    def _return(idx: int):
        provider, prefix = init_prefix
        files = init_files(prefix, [list(FS.keys())[idx]])
        return (provider, prefix, files[0])
    return _return

@pytest.fixture(params=[idx for idx, key in enumerate(FS.keys())])
def init_each(request, init_single_file_factory):
    return init_single_file_factory(request.param)

@pytest.fixture
def init_prefix_with_file(init_single_file_factory):
    """ Create a prefix folder with a direct file within
        /tmp/<tmp_dir>/prefix
        |_ test1.txt
    """
    return init_single_file_factory(0)

@pytest.fixture
def init_subfolder_with_file(init_single_file_factory):
    """ Generate
        /tmp/<tmp_dir>/prefix
        |_ subfolder/
            |_ test2.txt
    """
    return init_single_file_factory(1)

@pytest.fixture
def init_full(init_prefix, init_files):
    """ Generates
        /tmp/<tmp_dir>/prefix
        |_ test.txt
        |_ subfolder/
            |_ test.txt
    """
    provider, prefix = init_prefix
    files = init_files(prefix, list(FS.keys()))
    return tuple([provider, prefix] + files)

@pytest.fixture
def init_subfolder(init_prefix):
    """ Create a prefix folder with a subfolder named 'subfolder' within
        /tmp/<tmp_dir>/prefix
        |_ subfolder/
    """

    provider, full_prefix = init_prefix

    test_dir = 'subfolder'
    subdir = os.path.join(full_prefix, test_dir)
    os.mkdir(subdir)

    yield (provider, full_prefix, test_dir)

    if os.path.exists(subdir):
        shutil.rmtree(subdir)


##################
### Test Cases ###
##################


class TestInit:
    """ FileSystemProvider initialization """

    def test_prefix(self, init_prefix):
        """ Test the prefix of a newly generated FileSystemProvider without trailing slash """
        provider, prefix = init_prefix
        assert provider.prefix == prefix + '/'

    def test_prefix_trailing(self, init_tmp_dir):
        """ Test the prefix of a newly generated FileSystemProvider with trailing slash """
        provider, tmp_dir = init_tmp_dir
        prefix = tmp_dir + 'prefix/'
        provider = provider(prefix)
        assert provider.prefix == prefix

    def test_prefix_non_existing(self, init_tmp_dir):
        """ Test the prefix of a newly generated LocalFSProvider with non-existing prefix """
        provider, tmp_dir = init_tmp_dir
        prefix = tmp_dir + 'prefix'
        provider = provider(prefix)
        assert provider.prefix == prefix + '/'


class TestFromSubfolder:
    """ from_subfolder() tests """

    def test_subfolder(self, init_subfolder):
        """ Test the creation of a new FileSystemProvider whose prefix is a subfolder of an existing one """
        provider, prefix, subfolder = init_subfolder
        sub_provider = provider.from_subfolder(subfolder)
        assert sub_provider != provider # from_subfolder must return a new FileSystemProvider object
        assert sub_provider.prefix == os.path.join(prefix, subfolder) + '/'


class TestExists:
    """ exists() tests """

    def test_exists_prefix_and_subfolder(self, init_subfolder):
        """ Test if LocalFSP can check that its prefix and subfolder exists """
        provider, prefix, subfolder = init_subfolder
        assert provider.exists()
        assert provider.exists(os.path.join(prefix, subfolder))

    def test_exists_non_existing_path(self, init_tmp_dir):
        """ Test if LocalFSP can check that a file/subfolder does not exist """
        provider, tmp_dir = init_tmp_dir
        provider = provider(tmp_dir)
        assert not provider.exists(os.path.join(provider.prefix, 'test'))

    def test_exists_non_existing_prefix(self, init_tmp_dir):
        """ Test if LocalFSP can check that its prefix does not exist """
        provider, tmp_dir = init_tmp_dir
        prefix = os.path.join(tmp_dir, 'prefix')
        provider = provider(prefix)
        assert not provider.exists()


class TestEnsureExists:
    """ ensure_exists() tests """

    def test_ensure_exists(self, init_subfolder_with_file):
        """ Test if LocalFSP can check the existence of its prefix without overriding its content """
        provider, prefix, filepath = init_subfolder_with_file
        provider.ensure_exists()
        assert os.path.exists(os.path.join(prefix, filepath))

    def test_ensure_exists_prefix(self, init_tmp_dir):
        """ Test if LocalFSP can create its prefix folder if it does not exist """
        provider, tmp_dir = init_tmp_dir
        prefix = os.path.join(tmp_dir, 'prefix')
        provider = provider(prefix)
        provider.ensure_exists()
        assert os.path.exists(prefix)

    def test_ensure_exists_subfolder(self, init_tmp_dir):
        """ Test if LocalFSP can create its prefix in nested non-existing folders """
        provider, tmp_dir = init_tmp_dir
        prefix1 = os.path.join(tmp_dir, 'prefix1')
        prefix2 = os.path.join(prefix1, 'prefix2')
        provider = provider(prefix2)
        provider.ensure_exists()
        assert os.path.exists(prefix2)


class TestPut:
    """ put() tests """
    
    @pytest.mark.parametrize("file", FS.keys())
    def test_put(self, init_prefix, file):
        """ Write a single file """
        provider, prefix = init_prefix
        full_path = os.path.join(prefix, file)
        provider.put(file, FS[file]['content'])

        # check if the file is correctly written
        assert os.path.exists(full_path)
        with open(full_path, 'rb') as fd:
            content = fd.read()
        assert compare_files(file, content)

        # check side effects
        content = os.listdir(prefix)
        assert len(content) == 1
        if os.path.isdir(content[0]):
            dir = os.path.join(prefix, content[0])
            assert len(os.listdir(dir)) == 1

    def test_subfolder(self, init_subfolder):
        """ Try to rewrite a folder """
        provider, _, subfolder = init_subfolder
        with pytest.raises(IsADirectoryError):
            provider.put(subfolder, 'test')

    def test_write_full_path(self, init_full):
        """ Try to rewrite a file from its full path """
        provider, prefix, *files = init_full
        full_path = os.path.join(prefix, files[0])
        with pytest.raises(FileNotFoundError):
            provider.put(full_path, 'test')

    def test_write_int(self, init_prefix):
        """ Try to write an int rather than a str """
        provider, prefix = init_prefix
        with pytest.raises(TypeError):
            provider.put('test1.txt', 1)


class TestGetFd:
    """ get_fd() tests """

    def test_get_fd_full_path(self, init_prefix_with_file):
        """ Test getting fd on valid full path """
        provider, prefix, filename = init_prefix_with_file
        with pytest.raises(FileNotFoundError):
            provider.get_fd(os.path.join(prefix, filename))

    def test_get_fd_non_existing_file(self, init_prefix):
        """ Test get_fd on non-existing filepath """
        provider, _ = init_prefix
        with pytest.raises(FileNotFoundError):
            provider.get_fd('test.txt')

    def test_get_fd_directory(self, init_subfolder):
        """ Test get_fd on filepath leading to a folder """
        provider, _, subfolder = init_subfolder
        with pytest.raises(IsADirectoryError):
            provider.get_fd(subfolder)

    def test_get_fd(self, init_prefix_with_file):
        """ Test getting fd on a valid file """
        provider, _, filename = init_prefix_with_file
        with provider.get_fd(filename) as fd:
            assert compare_files(filename, fd.read())


class TestGet:
    """ get() tests """
    def test_get(self, init_each):
        """ Get existing files content """
        provider, prefix, file = init_each
        assert compare_files(file, provider.get(file))

    def test_get_non_existing_files(self, init_prefix):
        """ Try to get the content of a non existing file """
        provider, _ = init_prefix
        with pytest.raises(FileNotFoundError):
            provider.get('test.txt')

    def test_get_fd_directory(self, init_subfolder):
        """ Test get_fd on filepath leading to a folder """
        provider, _, subfolder = init_subfolder
        with pytest.raises(IsADirectoryError):
            provider.get(subfolder)


class TestList:
    """ list() tests """

    def test_list_file_populated(self, init_full):
        """ List direct files """
        provider, _, *files = init_full
        assert provider.list(files=True, folders=False) == [files[0]]

    def test_list_file_populated_recursive(self, init_full):
        """ List all files recursively """
        provider, _, *files = init_full
        assert set(provider.list(files=True, folders=False, recursive=True)) == set(files)

    def test_list_folder_populated(self, init_full):
        """ List direct directories """
        provider, _, *files = init_full
        expected = get_direct_dirs(files)
        assert set(provider.list(files=False, folders=True)) == set(expected)

    def test_list_folder_populated_recursive(self, init_full):
        """ List all directories recursively """
        provider, _, *files = init_full
        expected = get_formatted_dirs(files)
        assert set(provider.list(files=False, folders=True, recursive=True)) == set(expected)

    def test_list_empty(self, init_prefix):
        """ List direct empty prefix """
        provider, _ = init_prefix
        assert provider.list(files=True, folders=True) == []

    def test_list_empty_recursively(self, init_prefix):
        """ List empty prefix recursively """
        provider, _ = init_prefix
        assert provider.list(files=True, folders=True, recursive=True) == []

    def test_list_populated_disabled(self, init_full):
        """ List nothing """
        provider, _, _, *_ = init_full
        assert provider.list(files=False, folders=False) == []

    def test_list_populated_disabled_recursive(self, init_full):
        """ List nothing recursively """
        provider, _, _, *_ = init_full
        assert provider.list(files=False, folders=False, recursive=True) == []

    def test_list_populated(self, init_full):
        """ List all direct prefix's content """
        provider, _, *files = init_full
        assert set(provider.list(files=True, folders=True)) == set(get_direct_dirs(files) + [j for (i,j) in [os.path.split(entry) for entry in files] if i == ''])

    def test_list_populated_recursively(self, init_full):
        """ List all prefix's content recursively """
        provider, prefix, *files = init_full
        assert set(provider.list(files=True, folders=True, recursive=True)) == set(files + get_formatted_dirs(files))

    def test_list_non_existing_prefix(self, init_tmp_dir):
        """ Try to list non-existing prefix """
        provider, tmp_dir = init_tmp_dir
        prefix = os.path.join(tmp_dir, 'prefix')
        provider = provider(prefix)
        with pytest.raises(FileNotFoundError):
            provider.list()

class TestDelete:
    """ delete() tests """

    def test_delete_non_existing(self, init_tmp_dir):
        """ Delete non-existing prefix """
        provider, tmp_dir = init_tmp_dir
        prefix = os.path.join(tmp_dir, 'prefix')
        provider = provider(prefix)
        with pytest.raises(FileNotFoundError):
            provider.delete()

    def test_delete_empty_prefix(self, init_prefix):
        """ Delete existing empty prefix """
        provider, prefix = init_prefix
        provider.delete()
        assert not os.path.exists(prefix)

    def test_delete_populated_prefix(self, init_full):
        """ Delete a populated prefix """
        provider, prefix, _, *_ = init_full
        provider.delete()
        assert not os.path.exists(prefix)

    def test_delete_subfolder_file(self, init_full):
        """ Delete a subfolder file without removing the subfolder """
        provider, prefix, *files = init_full
        provider.delete(files[1])
        for path in files + get_dirs(files):
            if path != files[1]:
                assert os.path.exists(os.path.join(prefix, path))

    def test_delete_subfolder(self, init_full):
        """ Delete a subfolder """
        provider, prefix, *files = init_full
        removed = files[1]
        subfolder = os.path.dirname(removed)
        provider.delete(subfolder)
        for path in files + get_dirs(files):
            if path != removed and path != subfolder:
                assert os.path.exists(os.path.join(prefix, path))

    def test_delete_fullpath(self, init_full):
        """ Try to delete a full path """
        provider, prefix, *files = init_full
        subfolder = os.path.dirname(files[1])
        with pytest.raises(FileNotFoundError):
            provider.delete(os.path.join(prefix, subfolder))


class TestMove:
    """ move() tests """

    def test_move(self, init_full):
        """ Try to move a file at the same directory level """
        provider, prefix, *files = init_full
        file1_path = os.path.join(prefix, files[0])
        dest = 'moved_%s' % files[0]
        full_dest = os.path.join(prefix, dest)
        provider.move(files[0], dest)
        assert not os.path.exists(file1_path)
        assert os.path.exists(full_dest)
        with open(full_dest, 'rb') as fd:
            assert compare_files(files[0], fd.read())
        assert os.path.exists(os.path.join(prefix, files[1]))

    def test_move_non_existing_file(self, init_prefix):
        """ Try to move a non existing file """
        provider, _ = init_prefix
        with pytest.raises(FileNotFoundError):
            provider.move('non-existing.src', 'non-existing.dst')

    def test_move_to_non_existing_subfolder(self, init_prefix_with_file):
        provider, prefix, file = init_prefix_with_file
        """ Try to move a file to a non-existing subfolder """
        new_file = 'subfolder/%s' % file
        provider.move(file, new_file)
        full_dest = os.path.join(prefix, new_file)
        assert os.path.exists(full_dest)
        with open(full_dest, 'rb') as fd:
            assert compare_files(file, fd.read())

    def test_move_outside_fullpath(self, init_full, init_prefix):
        """ Try to move a file outside the prefix with a full path """
        _, prefix1 = init_prefix
        provider, _, *files = init_full
        with pytest.raises(FileNotFoundError):
            provider.move(files[0], os.path.join(prefix1, files[0]))

    def test_move_outside_relativepath(self, init_tmp_dir_np, init_full):
        """ Try to move a file outside the prefix with a relative path """
        tmp = init_tmp_dir_np
        provider, prefix, *files = init_full
        path = os.path.join('../../', os.path.basename(tmp))

        curdir = os.getcwd()
        os.chdir(prefix)
        assert os.path.exists(path)
        with pytest.raises(FileNotFoundError):
            provider.move(files[0], os.path.join(path, files[0]))
        os.chdir(curdir)


class TestGetLastModificationTime:
    """ get_last_modification_time() tests """

    def test_non_existing_file(self, init_prefix):
        """ Try to get modification time of a non-existing file """
        provider, prefix = init_prefix
        with pytest.raises(FileNotFoundError):
            provider.get_last_modification_time('test1.txt')

    def test_file(self, init_each):
        """ Try to get the modification time of existing files """
        provider, prefix, file = init_each
        assert provider.get_last_modification_time(file) == os.stat(os.path.join(prefix, file)).st_mtime

    def test_full_path(self, init_each):
        """ Try to get the last modification of a file with its full path """
        provider, prefix, file = init_each
        with pytest.raises(FileNotFoundError):
            provider.get_last_modification_time(os.path.join(prefix, file))

    def test_updated_file(self, init_each):
        """ Get the last modification time after file modification """
        provider, prefix, file = init_each
        full_file = os.path.join(prefix, file)
        before = os.stat(full_file).st_mtime
        time.sleep(1)
        with open(full_file, 'w+') as fd:
            fd.write('test')
        after = os.stat(full_file).st_mtime
        last = provider.get_last_modification_time(file)
        assert last != before
        assert last == after
        
    def test_directory(self, init_subfolder):
        """ Try last modification time of a folder """
        provider, prefix, subfolder = init_subfolder
        assert os.stat(os.path.join(prefix, subfolder)).st_mtime == provider.get_last_modification_time(subfolder)

    def test_updated_directory(self, init_subfolder):
        """ Get last modification time of a folder after modification """
        provider, prefix, subfolder = init_subfolder
        full_path = os.path.join(prefix, subfolder)
        before = os.stat(full_path).st_mtime
        time.sleep(1)
        with open(os.path.join(full_path, 'test'), 'w') as fd:
            fd.write('')
        after = os.stat(full_path).st_mtime
        last = provider.get_last_modification_time(subfolder)
        assert last != before
        assert last == after


class TestCopyTo:
    """ copy_to() tests """
    # TODO: check file rewrite

    @pytest.mark.parametrize("explicit", [True, False])
    def test_copy(self, init_tmp_each, init_prefix, explicit):
        """ Copy a file from the disk to the prefix """
        root, file = init_tmp_each
        provider, prefix = init_prefix
        full_path = os.path.join(root, file)
        new_file = os.path.join(prefix, file if explicit else os.path.basename(file))
        provider.copy_to(full_path, file if explicit else None)
        assert os.path.exists(new_file)
        with open(new_file, 'rb') as fd:
            content = fd.read()
        assert compare_files(file, content)

    @pytest.mark.parametrize("explicit, file", [(explicit, file) for explicit in (True, False) for file in FS.keys()])
    def test_copy_non_existing(self, init_tmp_dir_np, init_prefix, explicit, file):
        """ Copy a non-existing file from the disk to the prefix """
        root = init_tmp_dir_np
        provider, prefix = init_prefix
        full_path = os.path.join(root, file if explicit else os.path.basename(file))
        with pytest.raises(FileNotFoundError):
            provider.copy_to(full_path, file if explicit else None)

    def test_copy_to_subfolder(self, init_tmp_each, init_subfolder):
        """ Copy files to an existing subfolder """
        root, file = init_tmp_each
        provider, prefix, subfolder = init_subfolder
        provider.copy_to(os.path.join(root, file), subfolder)
        dst = os.path.join(prefix, subfolder)
        newfile = os.path.join(dst, os.path.basename(file))
        assert os.path.exists(newfile)
        with open(newfile, 'rb') as fd:
            content = fd.read()
        assert compare_files(file, content)

    def test_copy_to_non_existing_subfolder(self, init_tmp_each, init_prefix):
        """ Copy files to a non-existing subfolder """
        root, file = init_tmp_each
        provider, prefix = init_prefix
        subfolder = 'mysubfolder/'
        provider.copy_to(os.path.join(root, file), subfolder)
        dst = os.path.join(prefix, subfolder)
        newfile = os.path.join(dst, os.path.basename(file))
        assert os.path.exists(newfile)
        with open(newfile, 'rb') as fd:
            content = fd.read()
        assert compare_files(file, content)

    @pytest.mark.parametrize("explicit", [True, False])
    def test_copy_folder(self, init_tmp_full, init_subfolder, explicit):
        """ Copy files to a non-existing subfolder """
        root, files = init_tmp_full
        provider, prefix, subfolder = init_subfolder
        provider.copy_to(root, None if not explicit else subfolder)
        dst = prefix if not explicit else os.path.join(prefix, subfolder)
        for file in files:
            newfile = os.path.join(dst, file)
            assert os.path.exists(newfile)
            with open(newfile, 'rb') as fd:
                content = fd.read()
            assert compare_files(file, content)

    @pytest.mark.parametrize("explicit", [True, False])
    def test_copy_empty_folder(self, init_tmp_dir_np, init_subfolder, explicit):
        """ Copy files to a non-existing subfolder """
        root = init_tmp_dir_np
        provider, prefix, subfolder = init_subfolder
        provider.copy_to(root, None if not explicit else subfolder)
        assert os.listdir(prefix) == [subfolder]
        assert os.listdir(os.path.join(prefix, subfolder)) == []


class TestCopyFrom:
    """ copy_from() tests """

    @pytest.mark.parametrize("explicit", [True, False])
    def test_empty_prefix(self, init_tmp_dir_np, init_prefix, explicit):
        """ copy empty prefix to disk """
        root = init_tmp_dir_np
        provider, prefix = init_prefix
        provider.copy_from('' if explicit else None, root);
        assert os.listdir(root) == []

    @pytest.mark.parametrize("explicit", [True, False])
    def test_full_prefix(self, init_tmp_dir_np, init_full, explicit):
        """ copy populated prefix to disk """
        root = init_tmp_dir_np
        provider, prefix, *files = init_full
        provider.copy_from('' if explicit else None, root);
        for file in files:
            newfile = os.path.join(root, file)
            assert os.path.exists(newfile)
            with open(newfile, 'rb') as fd:
                content = fd.read()
            assert compare_files(file, content)

    @pytest.mark.parametrize("file", FS.keys())
    def test_full_prefix_single(self, init_tmp_dir_np, init_full, file):
        """ copy populated prefix to disk file per file """
        root = init_tmp_dir_np
        provider, prefix, *_ = init_full
        provider.copy_from(file, root);
        filename = os.path.basename(file)
        newfile = os.path.join(root, filename)

        """ Test the file copy """
        assert os.path.exists(newfile)
        with open(newfile, 'rb') as fd:
            content = fd.read()
        assert compare_files(file, content)

        """ Test that only the specified file is copied """
        assert [re.sub(root + '/', '', entry) for entry in recursive_content(root)] == [filename]

    @pytest.mark.parametrize("file", FS.keys())
    def test_copy_non_existing(self, init_tmp_dir_np, init_prefix, file):
        """ Copy a non-existing file from the disk to the prefix """
        root = init_tmp_dir_np
        provider, prefix = init_prefix
        with pytest.raises(FileNotFoundError):
            provider.copy_from(file, root)


class TestDistribute:
    """ Tests for distribute() """

    @pytest.mark.parametrize("file, folders", [(file, folders) for file in FS.keys() for folders in [True, False]])
    def test_non_existing(self, init_prefix, file, folders):
        """ Test distribute non existing files """
        provider, prefix = init_prefix
        (t, m, o) = provider.distribute(file, folders)
        assert t == 'invalid'
        assert m is None
        assert o is None
    
    @pytest.mark.parametrize("folders", [True, False])
    def test_single_files(self, init_full, folders):
        """ Test single files distribution """
        import io
        import mimetypes
        mimetypes.init()

        provider, prefix, *files = init_full
        for file in files:
            (t, m, o) = provider.distribute(file, folders)
            assert t == 'url' or t == 'invalid' or t == 'local'
            assert m is not None if t == 'local' else m is None
            assert o is None if t == 'invalid' else o is not None
            assert isinstance(o, io.BufferedIOBase) if t == 'local' else True
            if t == 'local':
                guessed = mimetypes.guess_type(os.path.join(prefix, file))
                assert guessed[1] is None
                assert m == (guessed[0] if guessed[0] is not None else 'application/octet-stream')
                assert compare_files(file, o.read())

    @pytest.mark.parametrize("folders", [True, False])
    def test_prefix(self, init_tmp_dir_np, init_full, folders):
        """ Test prefix distribution """
        import io
        import zipstream
        import zipfile

        tmp = init_tmp_dir_np
        provider, prefix, *files = init_full
        (t, m, o) = provider.distribute('', folders)
        assert t == ('local' if folders else 'invalid')
        assert m == ('application/zip' if folders else None)
        assert isinstance(o, zipstream.ZipFile) if folders else o is None
        if folders:
            archive = os.path.join(tmp, 'archive.zip')
            with open(archive, 'wb') as fd:
                for data in o:
                    fd.write(data)
            z = zipfile.ZipFile(archive)
            content = z.namelist()
            assert set(content) == set(list(FS.keys()))
            for file in content:
                assert compare_files(file, z.read(file))


class TestClassMethods:
    """ Tests for class methods of FSProvider """

    def test_get_needed_args(self, init_prefix):
        provider, _ = init_prefix
        if isinstance(provider, LocalFSProvider):
            assert provider.get_needed_args() == {"location": (str, True, "On-disk path to the directory containing courses/tasks")}
        else:
            assert False

    def test_init_from_args(self, init_tmp_dir):
        provider_class, tmp = init_tmp_dir
        prefix = os.path.join(tmp, 'prefix')
        if provider_class.__name__ == 'LocalFSProvider':
            provider = provider_class.init_from_args(**{'location': prefix})
            assert provider.prefix == prefix + '/'
        else:
            assert False

# coding=utf-8
from abc import ABCMeta, abstractmethod


class NotFoundException(Exception):
    pass


class FileSystemProvider(object, metaclass=ABCMeta):
    """ Provides tools to access a given filesystem. The filesystem may be distant, and subclasses of FileSystemProvider should take care of 
        doing appropriate caching.
    """
    def __init__(self, prefix):
        """ Init the filesystem provider with a given prefix. """
        self.prefix = prefix
        if not self.prefix.endswith("/"):
            self.prefix += "/"

    @abstractmethod
    def from_subfolder(self, subfolder):
        """
        Returns a new FileSystemProvider, with subfolder as prefix
        """
        pass

    @abstractmethod
    def exists(self, path=None):
        """
        Check that the file at the given path exists. If the path is not given, then checks the existence of the prefix.
        """
        pass

    @abstractmethod
    def ensure_exists(self):
        """ Ensure that the current prefix exists. If it is not the case, creates the directory. """
        pass

    @abstractmethod
    def put(self, filepath, content):
        pass

    @abstractmethod
    def get(self, filepath):
        """ Get the content of a file. Raises NotFoundException if the file does not exists or cannot be retrieved """
        pass

    @abstractmethod
    def list(self, folders=True, files=True, recursive=False):
        """ List all the files/folder in this prefix. Folders are always ending with a '/' """
        pass

    @abstractmethod
    def delete(self, filepath=None, recursive=True):
        """ Delete a path. If filepath is None, then the prefix will be deleted. """
        pass

    @abstractmethod
    def get_last_modification_time(self, filepath):
        """ Get a timestamp representing the time of the last modification of the file at filepath """
        pass

    @abstractmethod
    def move(self, src, dest):
        """ Move path src to path dest, recursively """
        pass

    @abstractmethod
    def copy_to(self, src_disk, dest=None):
        """ Copy the content of *on-disk folder* src_disk into dir dest. If dest is None, copy to the prefix."""
        pass

    @abstractmethod
    def copy_from(self, src, dest_disk):
        """ Copy the content of src into the *on-disk folder* dest_disk. If src is None, copy from the prefix. """
        pass

    @abstractmethod
    def distribute(self, filepath, allow_folders=True):
        """ Give information on how to distribute a file. Provides Zip files of folders. Can return:
            ("file", mimetype, fileobj) where fileobj is an object-like file (with read()) and mimetype its mime-type.
            ("url", None, url) where url is a url to a distant server which possess the file.
            ("invalid", None, None) if the file cannot be distributed
        """
        pass

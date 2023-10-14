import xml.etree.ElementTree as ET
import yaml
import os


class LazyFileLoader:

    def __init__(self, filename):
        self.filename = filename
        self.read_time = None
        self.data = None

        self.reload()

    def reload(self):
        m_time = os.stat(self.filename).st_mtime
        if self.read_time != m_time:
            self.read_time = m_time
            self.load()
            return True

        return False

    def load(self):
        with open(self.filename, "r") as f:
            self.data = f.read()

        return self.data


class StyleLoader(LazyFileLoader):

    def load(self):
        with open(self.filename, "r") as f:
            self.data = yaml.load(f, Loader=yaml.SafeLoader)

        if self.data is None:
            # the file was empty
            self.data = {}


class MarkupLoader(LazyFileLoader):

    def load(self):
        self.data = ET.parse(self.filename)


class FileCache:

    def __init__(self):
        self.files = dict()

    def get(self, file_path, Loader=None):
        if file_path not in self.files:
            if Loader is None:
                raise ValueError(
                    "Unknown file '%s' pass Loader for loading file." %
                    (file_path))
            self.files[file_path] = Loader(file_path)

        return self.files[file_path]

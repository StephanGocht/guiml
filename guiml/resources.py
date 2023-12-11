import xml.etree.ElementTree as ET
import yaml
import os
import logging

from pathlib import Path
from collections import namedtuple

import weakref


class LazyFileLoader:

    def __init__(self, filename):
        self.filename = filename
        self.read_time = None
        self.data = None
        self.changed = True

        self.reload()

    def reload(self):
        m_time = os.stat(self.filename).st_mtime
        if self.read_time != m_time:
            self.read_time = m_time
            self.changed = True
            self.load()
        else:
            self.changed = False

        return self.changed

    def load(self):
        with open(self.filename, "r") as f:
            self.data = f.read()

        return self.data


class StyleLoader(LazyFileLoader):

    def load(self):
        with open(self.filename, "r") as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)

        if data is None:
            # the file was empty
            self.data = {}
        else:
            self.data = dict()
            for key, value in data.items():
                self.data[key] = self.reorganize(value)

    def reorganize(self, data):
        result = dict()
        for key, value in data.items():
            last = key.split(' ')[-1]
            elements = last.split('.')
            if elements[0] == '':
                first = '.' + elements[1]
            else:
                first = elements[0]

            values = result.setdefault(first, list())
            values.append((key, value))

        return result


class XmlLoader(LazyFileLoader):

    def load(self):
        self.data = ET.parse(self.filename).getroot()


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

    def reload(self):
        for loader in self.files.values():
            loader.reload()


ResourceData = namedtuple("ResourceData", "data changed")


class DataHandle:
    """
    An object with a get function to obtain the handled data.
    """

    def get(self):
        raise NotImplementedError()


class RawHandle:
    def __init__(self, data):
        self.data = data
        self.changed = True

    def get(self):
        changed = self.changed
        if changed:
            self.changed = False

        return ResourceData(self.data, changed)


class StyleHandle:
    def __init__(self, loader, index=None):
        self.loader = loader
        self.index = index
        self.read_time = None

    def get(self):
        assert self.index is not None, "Only handeling style files with multiple components."  # noqa: E501

        data = self.loader.data
        if self.index:
            data = data.get(self.index, None)

        changed = False
        if self.read_time != self.loader.read_time:
            self.read_time = self.loader.read_time
            changed = True

        return ResourceData(data, changed)


class TemplateHandle:
    def __init__(self, loader, index=None):
        self.loader = loader
        self.index = index
        self.read_time = None

    def get(self):
        data = self.loader.data
        if self.index:
            data = data.find(self.index)

            if data is None:
                logging.warning(f"Did not find template for '{self.index}'.")

        changed = False
        if self.read_time != self.loader.read_time:
            self.read_time = self.loader.read_time
            changed = True

        return ResourceData(data, changed)


_resource_manger = []


def reload_resources():
    global _resource_manger
    tmp = _resource_manger
    _resource_manger = []

    for ref in tmp:
        manager = ref()
        if manager is not None:
            _resource_manger.append(ref)
            manager.reload()


class ResourceManager:
    def __init__(self, basedir, paths=None):
        self.basedir = Path(basedir)
        self.cache = FileCache()
        self.paths = {}
        if paths is not None:
            for key, path in paths.items():
                path = (self.basedir / path).resolve()
                # todo log warning if path does not exist
                self.paths[key] = path

        global _resource_manger
        _resource_manger.append(weakref.ref(self))

    def style_file(self, file_path, index=None):
        loader = self.cache.get(self.basedir / file_path, StyleLoader)
        return StyleHandle(loader, index)

    def template(self, data):
        return RawHandle(ET.fromstring(data))

    def template_file(self, file_path):
        loader = self.cache.get(self.basedir / file_path, XmlLoader)
        return TemplateHandle(loader)

    def reload(self):
        self.cache.reload()

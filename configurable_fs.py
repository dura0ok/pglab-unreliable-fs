import errno
import importlib
import inspect
import json
import os

from fuse import FuseOSError, Operations

from default_impl import DefaultFS


class ConfigurableFS(DefaultFS):
    def __init__(self, root, config_file_name):
        super().__init__(root)
        self.root = root
        self.config = self.load_config(config_file_name)

    @staticmethod
    def load_config(config_file_name):
        with open(config_file_name, 'r') as f:
            return json.load(f)

    @staticmethod
    def default_implementation(func_name, *args, **kwargs):
        default_func = getattr(DefaultFS, func_name, None)
        print(args, kwargs)
        print(f"RES = {list(default_func(*args, **kwargs))}")
        if default_func:
            return default_func(*args, **kwargs)
        else:
            raise FuseOSError(errno.ENOSYS)

    def apply_replacement(self, path, *args, **kwargs):
        syscall_name = inspect.stack()[1][3]
        replacement = self.config.get(path, {}).get(syscall_name)
        full_path = super().full_path(path)
        if replacement:
            module_name, function_name = replacement['module'], replacement['function']
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)
            return func(full_path, *args[1:], **kwargs)
        else:
            return self.default_implementation(syscall_name, full_path, *args[1:], **kwargs)

    def getattr(self, path, fh=None):
        return self.apply_replacement(path, path, fh)

    def readdir(self, path, fh):
        return self.apply_replacement(path, path, fh)

    def read(self, path, size, offset, fh):
        return self.apply_replacement(path, path, size, offset, fh)

    def write(self, path, data, offset, fh):
        return self.apply_replacement(path, path, data, offset, fh)
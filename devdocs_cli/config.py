from __future__ import print_function

import json
import os
import sys
from collections import namedtuple
from os import path

DEFAULT_CONFIG_FILE = path.expanduser('~/.config/devdocs/config.json')


class Config(namedtuple('DevdocsConfig', (
        'url', 'docs_url', 'cache_dir', 'cache_ttl', 'config_file',
))):
    non_user = ('config_file',)

    def items(self):
        return (
            (key, value)
            for key, value in self._asdict().items()
            if key not in self.non_user
        )

    @property
    def modified(self):
        return {
            field: value
            for field, value in self.items()
            if value != getattr(DEFAULT_CONFIG, field)
        }

    def save(self):
        if not path.exists(path.dirname(self.config_file)):
            os.makedirs(path.dirname(self.config_file))

        with open(self.config_file, 'w') as conf_file:
            json.dump(self.modified, conf_file)


DEFAULT_CONFIG = Config(
    url='https://devdocs.io/',
    docs_url='https://docs.devdocs.io',
    cache_dir=path.expanduser('~/.cache/devdocs'),
    cache_ttl=60 * 60 * 24 * 7,  # 1 week in seconds
    config_file=None,
)


def load_config_file(config_file):
    if not path.exists(config_file):
        return {}

    with open(config_file, 'r') as conf_file:
        config_options = json.load(conf_file)

    invalid_args = {
        config_option: value
        for config_option, value in config_options.items()
        if config_option not in Config._fields
    }
    if invalid_args:
        invalid_options = ', '.join(invalid_args.keys())
        print(
            'Invalid config options of {} in {}'.format(
                invalid_options,
                config_file,
            ),
            file=sys.stderr,
        )
        for key in invalid_args:
            config_options.pop(key)

    return config_options


def from_args(config_file=DEFAULT_CONFIG_FILE, **args):
    """
    Takes a dict of args and returns a config object with defaults and
    returns the remaining arguments. Also if config_file is passed settings will
    loaded from the file
    """
    new_values = load_config_file(config_file)

    remaining_args = {}

    for key in args:
        if key in Config._fields:
            new_values[key] = args[key]
        else:
            remaining_args[key] = args[key]

    return DEFAULT_CONFIG._replace(config_file=config_file, **new_values), remaining_args

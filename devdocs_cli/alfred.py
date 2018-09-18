import json
import plistlib
from argparse import ArgumentParser
from argparse import SUPPRESS
from copy import deepcopy
from os import path
from os import remove
from shutil import copyfile

from . import config
from . import devdocs

DEFAULT_CONFIG = path.expanduser('~/.config/devdocs/alfred.json')

MIDDLE_X_POS = 360
SPACING = 130

BASE_SCIPT = 'PATH=$HOME/repos/kdeal/devdocs-cli/venv/bin:$PATH\n\ndevdocs-alfred search {docset} {{query}}'
BASE_TITLE = 'Search devdocs.io in the {docset} docset'
BASE_SHORTCUT = {
    'config': {
        'alfredfiltersresults': False,
        'argumenttrimmode': 0,
        'argumenttype': 1,
        'escaping': 126,
        'keyword': None,
        'queuedelaycustom': 3,
        'queuedelayimmediatelyinitially': True,
        'queuedelaymode': 0,
        'queuemode': 1,
        'runningsubtext': '',
        'script': None,
        'scriptargtype': 0,
        'scriptfile': '',
        'subtext': '',
        'title': None,
        'type': 0,
        'withspace': True
    },
    'type': 'alfred.workflow.input.scriptfilter',
    'uid': None,
    'version': 2
}


def create_shortcut(docset, shortcut):
    new_shortcut = deepcopy(BASE_SHORTCUT)
    new_shortcut['config']['keyword'] = shortcut
    new_shortcut['config']['script'] = BASE_SCIPT.format(docset=docset)
    new_shortcut['config']['title'] = BASE_TITLE.format(docset=docset)
    new_shortcut['uid'] = '.'.join((shortcut, docset))

    return new_shortcut


def create_shortcut_connection(info):
    for obj in info['objects']:
        if obj['type'] == 'alfred.workflow.action.openurl':
            open_url_uid = obj['uid']
            break

    return [{
        'destinationuid': open_url_uid,
        'modifiers': 0,
        'modifiersubtext': '',
        'vitoclose': False,
    }]


def calc_shortcut_position(info):
    max_y = max(obj['ypos'] for obj in info['uidata'].values())
    return {'xpos': MIDDLE_X_POS, 'ypos': max_y + SPACING}


def get_icon(slug):
    cur_dir = path.dirname(__file__)

    def build_path(slug):
        return path.join(cur_dir, 'icons', slug + '.png')

    icon_path = build_path(slug)
    # If all versions have the same icon than the icon has no version ending
    if not path.isfile(icon_path):
        icon_path = build_path(slug.rsplit('~', 1)[0])

    return icon_path


def search_handler(conf, docset, query):
    items = []
    results = devdocs.search(docset, query, conf)
    for item in results:
        items.append({
            'uid': path.join(docset, item['path']),
            'title': item['name'],
            'subtitle': item['path'],
            'arg': path.join(conf.url, docset, item['path']),
            'autocomplete': item['name'],
        })

    return {'items': items}


def docsets_handler(conf, docsets_filter):
    items = []
    results = devdocs.docsets(docsets_filter, conf)
    for item in results:
        # By default the version is not in the title
        if 'release' in item:
            item['name'] += '(' + item['release'] + ')'

        items.append({
            'uid': item['slug'],
            'title': item['name'],
            'subtitle': item['slug'],
            # Add extra space so that next command has a space
            'arg': item['slug'] + ' ',
            'autocomplete': item['slug'],
            'icon': {'path': get_icon(item['slug'])},
        })

    return {'items': items}


def read_plist():
    with open('./info.plist', 'rb') as info_file:
        return plistlib.readPlist(info_file)  # pylint: disable=deprecated-method


def write_plist(info):
    with open('./info.plist', 'wb') as info_file:
        plistlib.writePlist(info, info_file)  # pylint: disable=deprecated-method


def shortcuts_handler(shortcut, **extra):
    del extra
    info = read_plist()
    script_filters = (
        obj
        for obj in info['objects']
        if obj['type'] == 'alfred.workflow.input.scriptfilter'
    )
    items = []

    for obj in script_filters:
        if 'keyword' not in obj['config']:
            continue
        if not obj['config']['keyword'].startswith('docs'):
            items.append({
                'uid': obj['config']['keyword'],
                'title': obj['config']['keyword'],
                'arg': obj['config']['keyword'],
                'autocomplete': obj['config']['keyword'],
            })

    return {'items': devdocs.search_dicts(items, shortcut, 'arg')}


def delete_shortcut_handler(shortcut, **extra):
    del extra
    info = read_plist()

    for index in range(len(info['objects'])):
        if info['objects'][index]['uid'].startswith(shortcut):
            shortcut_uid = info['objects'][index]['uid']
            del info['objects'][index]

    info['connections'].pop(shortcut_uid, None)
    info['uidata'].pop(shortcut_uid, None)

    if path.exists(shortcut_uid + '.png'):
        remove(shortcut_uid + '.png')

    write_plist(info)

    return shortcut


def shortcut_handler(docset, shortcut, **extra):
    del extra
    info = read_plist()

    shortcut_object = create_shortcut(docset, shortcut)
    info['objects'].append(shortcut_object)
    info['connections'][shortcut_object['uid']] = create_shortcut_connection(info)
    info['uidata'][shortcut_object['uid']] = calc_shortcut_position(info)

    copyfile(get_icon(docset), shortcut_object['uid'] + '.png')

    write_plist(info)

    return '{} to {}'.format(shortcut, docset)


def add_config_handler(conf, option, value):
    if option in conf._fields:
        conf = conf._replace(**{option: value})
    conf.save()
    return '{} set to {}'.format(option, value)


def remove_config_handler(conf, option):
    if option in conf._fields:
        # Revert config value to the default value
        conf = conf._replace(**{option: getattr(config.DEFAULT_CONFIG, option)})
    conf.save()
    return '{} deleted'.format(option)


def list_config_handler(conf, query):
    # The field to set has been selected
    if len(query) > 1:
        value = ' '.join(query[1:])
        return {'items': [
            {
                'uid': query[0],
                'title': 'Set {} to "{}"'.format(query[0], value),
                'arg': '{} {}'.format(query[0], value),
            }
        ]}
    else:
        options = [
            {
                'uid': field,
                'title': field,
                'subtitle': value,
                'autocomplete': field,
                'arg': field,
            }
            for field, value in conf.items()
        ]
        return {'items': devdocs.search_dicts(options, query, 'uid')}


def changed_config_handler(conf):
    return {'items': [
        {
            'uid': field,
            'title': field,
            'subtitle': value,
            'autocomplete': field,
            'arg': field,
        }
        for field, value in conf.modified.items()
    ]}


def create_parser():
    parser = ArgumentParser(description='Query devdocs.io')
    parser.add_argument('-u', '--url', help='base url of devdocs', default=SUPPRESS)
    parser.add_argument('-c', '--config-file', help='read config from', default=DEFAULT_CONFIG)
    subparsers = parser.add_subparsers()

    search_parser = subparsers.add_parser('search', help='search through one doc set')
    search_parser.add_argument('docset', help='Document set to search')
    search_parser.add_argument('query', nargs='*', help='Query to search', default=[])
    search_parser.set_defaults(handler=search_handler)

    docsets_parser = subparsers.add_parser('docsets', help='search through one doc set')
    docsets_parser.add_argument('docsets_filter', metavar='filter', nargs='*', help='filter docsets')
    docsets_parser.set_defaults(handler=docsets_handler)

    shortcut_parser = subparsers.add_parser('shortcut', help='add a shortcut')
    shortcut_parser.add_argument('docset', help='Document set to search')
    shortcut_parser.add_argument('shortcut', help='shortcut query')
    shortcut_parser.set_defaults(handler=shortcut_handler)

    shortcuts_parser = subparsers.add_parser('shortcuts', help='list all shortcuts')
    shortcuts_parser.add_argument('shortcut', help='shortcut query', nargs='*')
    shortcuts_parser.set_defaults(handler=shortcuts_handler)

    delete_parser = subparsers.add_parser('delete-shortcut', help='delete a shortcut')
    delete_parser.add_argument('shortcut', help='shortcut to delete')
    delete_parser.set_defaults(handler=delete_shortcut_handler)

    config_parser = subparsers.add_parser('config', help='add a shortcut')
    config_subparsers = config_parser.add_subparsers()

    config_add_parser = config_subparsers.add_parser('set', help='set a config value')
    config_add_parser.add_argument('option', help='config option to set')
    config_add_parser.add_argument('value', help='value to set config option to')
    config_add_parser.set_defaults(handler=add_config_handler, json=False)

    config_add_parser = config_subparsers.add_parser('remove', help='remove a config option')
    config_add_parser.add_argument('option', help='config option to set')
    config_add_parser.set_defaults(handler=remove_config_handler)

    config_list_parser = config_subparsers.add_parser('list', help='add a shortcut')
    config_list_parser.add_argument('query', nargs='*', help='query that will change value', default=[])
    config_list_parser.set_defaults(handler=list_config_handler)

    config_options_parser = config_subparsers.add_parser('changed', help='add a shortcut')
    config_options_parser.set_defaults(handler=changed_config_handler)

    return parser


def main():
    args = create_parser().parse_args()
    conf, handler_args = config.from_args(**vars(args))
    handler = handler_args.pop('handler')
    use_json = handler_args.pop('json', True)
    result_dict = handler(conf=conf, **handler_args)
    if use_json:
        print(json.dumps(result_dict))
    else:
        print(result_dict)


if __name__ == '__main__':
    main()

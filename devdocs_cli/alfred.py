import json
from argparse import ArgumentParser
from os import path

import devdocs_cli.__main__ as devdocs


def get_icon(slug):
    cur_dir = path.dirname(__file__)

    def build_path(slug):
        return path.join(cur_dir, 'icons', slug + '.png')

    icon_path = build_path(slug)
    # If all versions have the same icon than the icon has no version ending
    if not path.isfile(icon_path):
        icon_path = build_path(slug.rsplit('~', maxsplit=1)[0])

    return {'path': icon_path}


def search_handler(docset, query, url):
    items = []
    results = devdocs.search(docset, query, url)
    for item in results:
        items.append({
            'uid': path.join(docset, item['path']),
            'title': item['name'],
            'subtitle': item['path'],
            'arg': path.join(url, docset, item['path']),
            'autocomplete': item['name'],
        })

    return {'items': items}


def docsets_handler(docsets_filter, url):
    items = []
    results = devdocs.docsets(docsets_filter, url)
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
            'icon': get_icon(item['slug']),
        })

    return {'items': items}


def create_parser():
    parser = ArgumentParser(description='Query devdocs.io')
    parser.add_argument('-u', '--url', help='base url of devdocs', default=devdocs.DEFAULT_URL)
    subparsers = parser.add_subparsers()

    search_parser = subparsers.add_parser('search', help='search through one doc set')
    search_parser.add_argument('docset', help='Document set to search')
    search_parser.add_argument('query', nargs='*', help='Query to search', default=[])
    search_parser.set_defaults(handler=search_handler)

    docsets_parser = subparsers.add_parser('docsets', help='search through one doc set')
    docsets_parser.add_argument('docsets_filter', metavar='filter', nargs='*', help='filter docsets')
    docsets_parser.set_defaults(handler=docsets_handler)

    return parser


def main():
    args = create_parser().parse_args()
    handler_args = vars(args)
    handler = handler_args.pop('handler')
    result_dict = handler(**handler_args)
    print(json.dumps(result_dict))


if __name__ == '__main__':
    main()

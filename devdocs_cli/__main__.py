import os
from argparse import ArgumentParser
from subprocess import run
from tempfile import NamedTemporaryFile

from . import devdocs


def view_handler(browser, **view_args):
    html, tag = devdocs.view(**view_args)
    if tag:
        tag = '#' + tag
    with NamedTemporaryFile(suffix='.html') as tempfile:
        tempfile.write(html.encode('utf-8'))
        run((browser, tempfile.name + tag))


def print_handler(key, func, **kwargs):
    results = func(**kwargs)
    for item in results:
        print(item[key])


def create_parser():
    parser = ArgumentParser(description='Query devdocs.io')
    parser.add_argument('-u', '--url', help='base url of devdocs', default=devdocs.DEFAULT_URL)
    subparsers = parser.add_subparsers()

    search_parser = subparsers.add_parser('search', help='search through one doc set')
    search_parser.add_argument('docset', help='Document set to search')
    search_parser.add_argument('query', nargs='*', help='Query to search')
    search_parser.set_defaults(handler=print_handler, func=devdocs.search, key='name')

    view_parser = subparsers.add_parser('view', help='view through one doc set')
    view_parser.add_argument(
        '-b', '--browser', help='Browser to view docs in',
        default=os.environ.get('BROWSER', 'elinks'),
    )
    view_parser.add_argument('docset', help='Document set to view')
    view_parser.add_argument('query', nargs='*', help='Query to view')
    view_parser.set_defaults(handler=view_handler)

    docsets_parser = subparsers.add_parser('docsets', help='search through one doc set')
    docsets_parser.add_argument('docsets_filter', metavar='filter', nargs='*', help='filter docsets')
    docsets_parser.set_defaults(handler=print_handler, func=devdocs.docsets, key='slug')

    return parser


def main():
    args = create_parser().parse_args()
    handler_args = vars(args)
    handler = handler_args.pop('handler')
    handler(**handler_args)


if __name__ == '__main__':
    main()

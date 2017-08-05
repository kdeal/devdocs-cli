import json
import os
from argparse import ArgumentParser
from os import path
from subprocess import run
from tempfile import NamedTemporaryFile
from time import time

import requests


DEFAULT_URL = 'http://localhost:9292/'
DOCS_URL = 'https://docs.devdocs.io'
CACHE_DIR = path.expanduser('~/.cache/devdocs')
CACHE_TTL = 60 * 60 * 24 * 7  # 1 week in seconds


def cache_request(func):
    def strip_url(url):
        for pattern in ('http://', 'https://'):
            url = url.replace(pattern, '')
        return url

    def decorator(endpoint, url, *args, **kwargs):
        filename = path.join(CACHE_DIR, strip_url(url), endpoint.replace('docs/', ''))
        if path.exists(filename):
            with open(filename) as cache_file:
                cache = json.load(cache_file)

            if time() - cache['timestamp'] < CACHE_TTL:
                return cache['resp']

        resp = func(endpoint, url, *args, **kwargs)

        os.makedirs(path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as cache_file:
            cache_file.write(json.dumps({'resp': resp, 'timestamp': time()}))
        return resp

    return decorator


@cache_request
def make_request(endpoint, url, transform=False):
    # Should handle this in a better way
    # local devdocs allows docs/<slug>/db.json, but devdocs.io
    # requires docs.devdocs.io/<slug>/db.json
    if transform and url == DEFAULT_URL and endpoint.startswith('docs/'):
        url = DOCS_URL
        endpoint = endpoint[5:]
    try:
        return requests.get(path.join(url, endpoint), json=None).json()
    except Exception as error:
        print(path.join(url, endpoint))
        raise error


def get_index(docset, url):
    return make_request(path.join('docs', docset, 'index.json'), url)


def priority(query, string):
    if string.startswith(' '.join(query)):
        return 2
    elif all(part in string for part in query):
        return 1
    else:
        return 0


def search_dicts(docs, query, key):
    matched_docs = []
    for doc in docs:
        doc['priority'] = priority(query, doc[key])
        if doc['priority'] > 0:
            matched_docs.append(doc)

    matched_docs.sort(key=lambda doc: (doc['priority'] * -1, doc[key]))
    return matched_docs


def docsets(docsets_filter, url):
    all_docsets = make_request('docs/docs.json', url)
    return search_dicts(all_docsets, docsets_filter, 'slug')


def search(docset, query, url):
    docset_index = get_index(docset, url)
    matched_docs = search_dicts(docset_index['entries'], query, 'name')
    return matched_docs


def view(docset, query, url):
    docset_index = get_index(docset, url)
    matched_docs = search_dicts(docset_index['entries'], query, 'name')
    if matched_docs:
        doc_path = matched_docs[0]['path']
        html_db = make_request(path.join('docs', docset, 'db.json'), url, transform=True)
        tag = ''
        if '#' in doc_path:
            doc_path, tag = doc_path.split('#', maxsplit=1)
        return html_db[doc_path], tag


def view_handler(browser, **view_args):
    html, tag = view(**view_args)
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
    parser.add_argument('-u', '--url', help='base url of devdocs', default=DEFAULT_URL)
    subparsers = parser.add_subparsers()

    search_parser = subparsers.add_parser('search', help='search through one doc set')
    search_parser.add_argument('docset', help='Document set to search')
    search_parser.add_argument('query', nargs='*', help='Query to search')
    search_parser.set_defaults(handler=print_handler, func=search, key='name')

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
    docsets_parser.set_defaults(handler=print_handler, func=docsets, key='slug')

    return parser


def main():
    args = create_parser().parse_args()
    handler_args = vars(args)
    handler = handler_args.pop('handler')
    handler(**handler_args)


if __name__ == '__main__':
    main()

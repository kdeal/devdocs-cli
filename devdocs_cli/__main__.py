import json
import os
from argparse import ArgumentParser
from os import path
from subprocess import run
from tempfile import NamedTemporaryFile
from time import time

import requests


DEFAULT_URL = 'https://devdocs.io'
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


def get_docs(url):
    return make_request('docs/docs.json', url)


def get_index(doc_set, url):
    return make_request(path.join('docs', doc_set, 'index.json'), url)


def get_db(doc_set, url):
    return make_request(path.join('docs', doc_set, 'db.json'), url, transform=True)


def view_in_elinks(string, tag='', browser='elinks'):
    if tag:
        tag = '#' + tag
    with NamedTemporaryFile(suffix='.html') as tempfile:
        tempfile.write(string.encode('utf-8'))
        run((browser, tempfile.name + tag))


def priority(query, string):
    if string.startswith(query):
        return 2
    elif query in string:
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


def docsets_handler(args):
    docsets = get_docs(args.url)
    for doc in search_dicts(docsets, ' '.join(args.filter), 'slug'):
        print(doc['slug'])


def search_handler(args):
    docset_index = get_index(args.doc_set, args.url)
    matched_docs = search_dicts(
        docset_index['entries'], ' '.join(args.query), 'name')
    for doc in matched_docs:
        print(doc['name'])


def view_handler(args):
    docset_index = get_index(args.doc_set, args.url)
    matched_docs = search_dicts(
        docset_index['entries'], ' '.join(args.query), 'name')
    if matched_docs:
        doc_path = matched_docs[0]['path']
        html_db = get_db(args.doc_set, args.url)
        tag = ''
        if '#' in doc_path:
            doc_path, tag = doc_path.split('#', maxsplit=1)
        view_in_elinks(html_db[doc_path], tag, args.browser)


def create_parser():
    parser = ArgumentParser(description='Query devdocs.io')
    parser.add_argument(
        '-u', '--url', help='base url of devdocs', default=DEFAULT_URL)
    subparsers = parser.add_subparsers()

    search = subparsers.add_parser('search', help='search through one doc set')
    search.add_argument('doc_set', help='Document set to search')
    search.add_argument('query', nargs='*', help='Query to search')
    search.set_defaults(func=search_handler)

    view = subparsers.add_parser('view', help='view through one doc set')
    view.add_argument(
        '-b', '--browser', help='Browser to view docs in',
        default=os.environ.get('BROWSER', 'elinks'),
    )
    view.add_argument('doc_set', help='Document set to view')
    view.add_argument('query', nargs='*', help='Query to view')
    view.set_defaults(func=view_handler)

    docsets = subparsers.add_parser(
        'docsets', help='search through one doc set')
    docsets.add_argument('filter', nargs='*', help='filter docsets')
    docsets.set_defaults(func=docsets_handler)

    return parser


def main():
    args = create_parser().parse_args()
    args.func(args)


if __name__ == '__main__':
    main()

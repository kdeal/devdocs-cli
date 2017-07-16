import json
from argparse import ArgumentParser
from os import path

import requests


def make_request(endpoint, url, data=None):
    try:
        return requests.get(path.join(url, endpoint), json=None).json()
    except Exception as e:
        print(path.join(url, endpoint))
        raise e


def get_docs(url):
    return make_request('docs/docs.json', url)


def get_index(doc_set, url):
    return make_request(path.join('docs', doc_set, 'index.json'), url)

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
    matched_docs = search_dicts(docset_index['entries'], ' '.join(args.query), 'name')
    for doc in matched_docs:
        print(doc['name'])


def create_parser():
    parser = ArgumentParser(description='Query devdocs.io')
    parser.add_argument('-u', '--url', help='base url of devdocs', default='https://devdocs.io')
    subparsers = parser.add_subparsers()

    search = subparsers.add_parser('search', help='search through one doc set')
    search.add_argument('doc_set', help='Document set to search')
    search.add_argument('query', nargs='*', help='Query to search')
    search.set_defaults(func=search_handler)

    docsets = subparsers.add_parser('docsets', help='search through one doc set')
    docsets.add_argument('filter', nargs='*', help='filter docsets')
    docsets.set_defaults(func=docsets_handler)

    return parser


def main():
    args = create_parser().parse_args()
    args.func(args)


if __name__ == '__main__':
    main()

from __future__ import print_function

import json
import os
import sys
from os import path
from time import time

import requests

from .config import DEFAULT_CONFIG


def cache_request(func):
    def strip_url(url):
        for pattern in ('http://', 'https://'):
            url = url.replace(pattern, '')
        return url

    def decorator(endpoint, conf, *args, **kwargs):
        filename = path.join(conf.cache_dir, strip_url(conf.url), endpoint.replace('docs/', ''))
        if path.exists(filename):
            with open(filename) as cache_file:
                cache = json.load(cache_file)

            if time() - cache['timestamp'] < conf.cache_ttl:
                return cache['resp']

        resp = func(endpoint, conf, *args, **kwargs)

        if not path.exists(path.dirname(filename)):
            os.makedirs(path.dirname(filename))

        with open(filename, 'w') as cache_file:
            cache_file.write(json.dumps({'resp': resp, 'timestamp': time()}))
        return resp

    return decorator


@cache_request
def make_request(endpoint, conf, transform=False):
    # Should handle this in a better way
    # local devdocs allows docs/<slug>/db.json, but devdocs.io
    # requires docs.devdocs.io/<slug>/db.json
    if transform and conf.url == DEFAULT_CONFIG.url and endpoint.startswith('docs/'):
        base_url = conf.docs_url
        endpoint = endpoint[5:]
    else:
        base_url = conf.url

    try:
        return requests.get(path.join(base_url, endpoint), json=None).json()
    except Exception as error:
        print(path.join(conf.url, endpoint), file=sys.stderr)
        raise error


def get_index(docset, conf):
    return make_request(path.join('docs', docset, 'index.json'), conf)


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


def docsets(docsets_filter, conf):
    all_docsets = make_request('docs/docs.json', conf)
    return search_dicts(all_docsets, docsets_filter, 'slug')


def search(docset, query, conf):
    docset_index = get_index(docset, conf)
    matched_docs = search_dicts(docset_index['entries'], query, 'name')
    return matched_docs


def view(docset, query, conf):
    docset_index = get_index(docset, conf)
    matched_docs = search_dicts(docset_index['entries'], query, 'name')
    if matched_docs:
        doc_path = matched_docs[0]['path']
        html_db = make_request(path.join('docs', docset, 'db.json'), conf, transform=True)
        tag = ''
        if '#' in doc_path:
            doc_path, tag = doc_path.split('#', 1)
        return html_db[doc_path], tag
    else:
        return None, None

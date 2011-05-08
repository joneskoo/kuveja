#!/usr/bin/env python3
#encoding: UTF-8
# Joonas Kuorilehto 2009-2011

import os
import sys
import time
import glob

DB_URI = 'kuveja.sqlite'
title = 'joneskoon kuvafeedi'
description = 'Kuveja joneskoon elämän varrelta. Live as it happens.'
rooturl = 'http://joneskoo.kapsi.fi/kuveja'
url = 'http://joneskoo.kapsi.fi/'
rssfile = 'feed.rss'
globfilter = '*.[Jj][pP][gG]'

try:
    if os.stat('.').st_mtime - os.stat(rssfile).st_mtime < 0:
        # Ei tarvi päivittää
        sys.exit(0)
except OSError:
    # Tiedostoa ei kait ollut
    pass

from datetime import datetime
import sqlite3

#from meta import readmeta

def readmeta(name):
    '''PLACEHOLDER, no python3 exif library'''
    return "", None

import rss

con = sqlite3.connect(DB_URI)
cur = con.cursor()

existing_files = []
try:
    cur.execute("select file from kuveja")
    existing_files = list(map(lambda x: x[0], list(cur)))
except sqlite3.OperationalError:
    cur.execute("create table kuveja(file, timestamp, meta)")

items = []
files = glob.glob(globfilter)
files.sort(key=lambda x: (-os.stat(x).st_mtime, x))

def is_new_file(name):
    if name not in existing_files:
        return True
    return False

def is_file_deleted(name):
    if name not in files:
        return True
    return False

new_files = filter(is_new_file, files)
deleted_files = filter(is_file_deleted, existing_files)

for name in deleted_files:
    cur.execute("delete from kuveja where file = ?", (name,))

for name in new_files:
    mtime = os.stat(name).st_mtime
    meta, timestamp = readmeta(name)
    if not timestamp:
        timestamp = datetime.utcfromtimestamp(mtime)
    cur.execute("insert into kuveja(file, timestamp, meta) values (?, ?, ?)",
            (name, timestamp, meta))
con.commit()

cur.execute("select file, timestamp, meta from kuveja order by timestamp desc")
metadatas = []
for file, timestamp, meta in cur:
    d = {}
    d['file'] = file
    d['timestamp'] = timestamp
    d['meta'] = meta
    metadatas.append(d)

import json
json.dump(metadatas, open('kuveja.json', 'w'))

html = '''<html>
<head>
 <title>%s</title>
 <link rel="alternate" title="kuveja RSS" href="http://joneskoo.kapsi.fi/kuveja.rss" type="application/rss+xml">
 <link rel="stylesheet" href="style.css" type="text/css" media="screen"/> 
</head>
<body>
 <h1>%s</h1>
 <p>%s</p>''' % (title, title, description)

channel = rss.Channel('joneskoon kuvafeedi',
                      'http://joneskoo.kapsi.fi/feed.rss',
                      'Kuveja joneskoon elämän varrelta. Live as it happens.',
                      generator = 'rss.py',
                      pubdate = datetime.now(),
                      language = 'fi-FI')

for d in metadatas[:35]:
    d['link'] = "%s/%s" % (rooturl, d['file'])
    itemhtml = '<p><img alt="%(file)s" src="%(file)s" /></p>%(meta)s' % d
    html += "<h3>%s</h3>%s" % (d['file'], itemhtml)
    it = rss.Item(channel,
        title=d['file'],
        link=d['link'],
        description=itemhtml)
    channel.additem(it)

html += "</body></html>"
open('index.html', 'w').write(html)

con.close()

with open(rssfile, "w") as f:
    f.write(channel.toxml())

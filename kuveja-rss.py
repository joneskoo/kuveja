#!/usr/bin/env python
#encoding: UTF-8
# Joonas Kuorilehto 2009-2011

import os
import sys
import time
import glob
from datetime import datetime
from meta import readmeta

title = 'joneskoon kuvafeedi'
description = u'Kuveja joneskoon elämän varrelta. Live as it happens.'
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

import sqlite3

con = sqlite3.connect("kuveja.sqlite")
cur = con.cursor()
try:
    cur.execute("select file from kuveja")
    existing_files = map(lambda x: x[0], list(cur))
except sqlite3.OperationalError:
    cur.execute("create table kuveja(file, timestamp, meta)")
    existing_files = []

import PyRSS2Gen

items = []
files = glob.glob(globfilter)
files.sort(key=lambda x: (-os.stat(x).st_mtime, x))

def is_new_file(file):
    if file not in existing_files:
        return True
    return False

def is_file_deleted(file):
    if file not in files:
        return True
    return False

new_files = filter(is_new_file, files)
deleted_files = filter(is_file_deleted, existing_files)

for file in deleted_files:
    cur.execute("delete from kuveja where file = ?", (file,))

for file in new_files:
    mtime = os.stat(file).st_mtime
    meta, timestamp = readmeta(file)
    if not timestamp:
        timestamp = datetime.utcfromtimestamp(mtime)
    cur.execute("insert into kuveja(file, timestamp, meta) values (?, ?, ?)",
            (file, timestamp, meta))
con.commit()

cur.execute("select file, timestamp, meta from kuveja order by timestamp desc")
metadatas = []
for file, timestamp, meta in cur:
    d = {}
    d['file'] = file
    d['timestamp'] = timestamp
    d['meta'] = meta
    metadatas.append(d)

import simplejson
simplejson.dump(metadatas, open('kuveja.json', 'w'))

html = u'''<html>
<head>
 <title>%s</title>
 <link rel="alternate" title="kuveja RSS" href="http://joneskoo.kapsi.fi/kuveja.rss" type="application/rss+xml">
 <link rel="stylesheet" href="style.css" type="text/css" media="screen"/> 
</head>
<body>
 <h1>%s</h1>
 <p>%s</p>''' % (title, title, description)

for d in metadatas[:35]:
    d['link'] = "%s/%s" % (rooturl, d['file'])
    itemhtml = '<p><img alt="%(link)s" src="%(link)s" /></p>%(meta)s' % d
    html += "<h3>%s</h3>%s" % (d['file'], itemhtml)
    r = PyRSS2Gen.RSSItem(
        title = d['file'],
        description = itemhtml,
        link = d['link'],
        pubDate = d['timestamp'])
    items.append(r)

html += "</body></html>"
open('index.html', 'w').write(html.encode("UTF-8"))

rss = PyRSS2Gen.RSS2(
    title = title,
    link = url,
    description = description,
    lastBuildDate = datetime.now(),
    items = items)
rss.write_xml(open(rssfile, "w"))

con.close()
sys.exit(0)


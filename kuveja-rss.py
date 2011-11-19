#!/usr/bin/env python
#encoding: UTF-8
# Joonas Kuorilehto 2009-2011

import os
import sys
import json
import time
import glob
from datetime import datetime
from meta import readmeta

# RSS config
TITLE = 'joneskoon kuvafeedi'
DESCRIPTION = u'Kuveja joneskoon elämän varrelta. Live as it happens.'
ROOTURL = 'http://joneskoo.kapsi.fi/kuveja'
LINKURL = 'http://joneskoo.kapsi.fi/'
RSSFILE = 'feed.rss'
HTML_TEMPLATE = '/home/users/joneskoo/kuveja/template.html'
GLOBFILTER = '*.[Jj][pP][gG]'
PICCOUNT = 20

try:
    if os.stat('.').st_mtime - os.stat(RSSFILE).st_mtime < 0:
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
    cur.execute("create table kuveja(file, timestamp, meta, mtime)")
    existing_files = []

import PyRSS2Gen

items = []
files = glob.glob(GLOBFILTER)

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
    mtime = datetime.utcfromtimestamp(os.stat(file).st_mtime)
    meta, timestamp = readmeta(file)
    # If EXIF capture time is not available, use mtime
    if not timestamp:
        timestamp = mtime
    cur.execute("insert into kuveja(file, timestamp, meta, mtime) "+ \
                "values (?, ?, ?, ?)", (file, timestamp, meta, mtime))
con.commit()

# Order by mtime, but use capture time
cur.execute("select file, timestamp, meta from kuveja order by mtime desc")
metadatas = []
for file, timestamp, meta in cur:
    d = {}
    d['file'] = file
    d['timestamp'] = unicode(timestamp)
    d['meta'] = meta
    metadatas.append(d)

json.dump(metadatas, open('kuveja.json', 'w'))

pichtml = ""
for d in metadatas[:PICCOUNT]:
    d['link'] = "%s/%s" % (ROOTURL, d['file'])
    itemhtml = '<p><img alt="%(link)s" src="%(link)s" /></p>%(meta)s' % d
    pichtml += "<h3>%s</h3>%s" % (d['file'], itemhtml)
    r = PyRSS2Gen.RSSItem(
        title = d['file'],
        description = itemhtml,
        link = d['link'],
        pubDate = d['timestamp'])
    items.append(r)

template = open(HTML_TEMPLATE).read().decode("UTF-8")
html = template.replace("__KUVEJA_INITIAL_PICS__", pichtml).replace(
                        "__KUVEJA_PIC_COUNT__", str(PICCOUNT))
open('index.html', 'w').write(html.encode("UTF-8"))

rss = PyRSS2Gen.RSS2(
    title = TITLE,
    link = LINKURL,
    description = DESCRIPTION,
    lastBuildDate = datetime.now(),
    items = items)
rss.write_xml(open(RSSFILE, "w"))

con.close()
sys.exit(0)


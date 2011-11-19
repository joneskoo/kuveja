#!/usr/bin/env python
#encoding: UTF-8
# Joonas Kuorilehto 2009-2011

import os
import sys
import glob
import sqlite3
import time
import PyRSS2Gen
from datetime import datetime
import ConfigParser
try:
    import json
except:
    import simplejson as json

from meta import readmeta

mypath = os.path.dirname(__file__)

# Read configs
config = ConfigParser.ConfigParser()
config.read(os.path.join(mypath, 'kuveja.cfg'))
config.read(['kuveja.cfg', os.path.expanduser('~/.kuveja.cfg')])

INPUTDIR = config.get('source', 'inputdir')
GLOBFILTER = config.get('source', 'globfilter')
OUTPUTDIR = config.get('target', 'outputdir')
TITLE = config.get('rss', 'title')
DESCRIPTION = config.get('rss', 'description')
ROOTURL = config.get('rss', 'mediaurl')
LINKURL = config.get('rss', 'linkurl')
RSSFILE = config.get('target', 'rssname')
JSONFILE = config.get('target', 'jsonname')
RSSCOUNT = config.getint('rss', 'count')
DBFILE = config.get('cache', 'db')

class Cache:
    existing_files = []

    def __init__(self, dbfile):
        self.con = sqlite3.connect(dbfile)
        self.read_existing_files()

    def read_existing_files(self):
        cur = self.con.cursor()
        try:
            cur.execute("select file from kuveja")
            existing_files = [x[0] for x in cur]
        except sqlite3.OperationalError:
            # Assume the table was missing
            cur.execute("create table kuveja(file, timestamp, meta, mtime)")
            existing_files = []
        self.existing_files = existing_files

    def update(self, files):
        def not_in(fname, files):
            if fname not in files:
                return True
            return False

        new_files = [x for x in files if not_in(x, files)]
        existing = self.existing_files
        deleted_files = [x for x in existing if not_in(x, existing)]

        # Remove files that no longer exist
        for fname in deleted_files:
            cur.execute("delete from kuveja where file = ?", (fname,))

        # Read metadata of existing files into cache
        for fname in new_files:
            mtime = datetime.utcfromtimestamp(os.stat(fname).st_mtime)
            meta, timestamp = readmeta(fname)
            # If EXIF capture time is not available, use mtime
            if not timestamp:
                timestamp = mtime
            cur.execute("insert into kuveja(file, timestamp, meta, mtime) "+ \
                        "values (?, ?, ?, ?)", (fname, timestamp, meta, mtime))
        self.con.commit()

    def get_metadatas(self):
        '''Order by mtime, but use capture time'''
        cur = self.con.cursor()
        cur.execute("select file, timestamp, meta from kuveja order by mtime desc")
        metadatas = []
        for file, timestamp, meta in cur:
            d = {}
            d['file'] = file
            d['timestamp'] = unicode(timestamp)
            d['meta'] = meta
            metadatas.append(d)
        return metadatas

    def __destructor__(self):
        self.con.close()

def update_needed():
    '''Update is needed if RSS file is newer than input directory'''
    rssfile = os.path.join(OUTPUTDIR, RSSFILE)
    try:
        if os.stat(INPUTDIR).st_mtime < os.stat(rssfile).st_mtime:
            # Already up to date
            return True
    except OSError:
        # File did not exist or something
        return False

def write_rss(metadatas):
    rssfile = os.path.join(OUTPUTDIR, RSSFILE)
    items = []
    pichtml = ""
    for d in metadatas[:RSSCOUNT]:
        d['link'] = "%s/%s" % (ROOTURL, d['file'])
        itemhtml = '<p><img alt="%(link)s" src="%(link)s" /></p>%(meta)s' % d
        pichtml += "<h3>%s</h3>%s" % (d['file'], itemhtml)
        r = PyRSS2Gen.RSSItem(
            title = d['file'],
            description = itemhtml,
            link = d['link'],
            pubDate = d['timestamp'])
        items.append(r)

    rss = PyRSS2Gen.RSS2(
        title = TITLE,
        link = LINKURL,
        description = DESCRIPTION,
        lastBuildDate = datetime.now(),
        items = items)
    with open(rssfile, "w") as f:
        rss.write_xml(f)
        f.write("\n")

def main():
    if update_needed():
        # Already up to date
        sys.exit(0)
    cache = Cache(DBFILE)
    files = glob.glob(os.path.join(INPUTDIR, GLOBFILTER))
    cache.update(files)
    metadatas = cache.get_metadatas()

    # Simply dump metadatas as a JSON file
    jsonfile = os.path.join(OUTPUTDIR, JSONFILE)
    json.dump(metadatas, open(jsonfile, 'w'))

    # Generate the RSS feed
    write_rss(metadatas)

    # Done
    sys.exit(0)

if __name__ == '__main__':
    main()
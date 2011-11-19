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

SCRIPTPATH = os.path.dirname(__file__)

# Read configs
config = ConfigParser.ConfigParser()
config.read(os.path.join(SCRIPTPATH, 'kuveja.cfg'))
config.read(['kuveja.cfg', os.path.expanduser('~/.kuveja.cfg')])

# Cache
DBFILE = config.get('cache', 'db')

# General settings
INPUTDIR = os.path.expanduser(config.get('source', 'inputdir'))
GLOBFILTER = config.get('source', 'globfilter')
OUTPUTDIR = os.path.expanduser(config.get('target', 'outputdir'))

# RSS output
TITLE = config.get('rss', 'title')
DESCRIPTION = config.get('rss', 'description')
ROOTURL = config.get('rss', 'mediaurl')
LINKURL = config.get('rss', 'linkurl')
RSSFILE = config.get('target', 'rssname')
RSSURL = config.get('rss', 'feedurl')
RSSCOUNT = config.getint('rss', 'count')

# JSON output
JSONFILE = config.get('target', 'jsonname')

# HTML output
HTMLFILE = config.get('target', 'htmlname')
HTMLTEMPLATE = config.get('html', 'template')
HTMLCOUNT = config.getint('html', 'initialcount')
HTMLIMG = """  <div class="kuva">
    <h3>%(title)s</h3>
    <img src="%(url)s" alt="%(title)s" />
  </div>"""

class Cache:
    # TODO: configurable database fields
    # TODO: metadata function should be passed as a callback or something
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
        cur = self.con.cursor()
        def not_in(fname, files):
            if fname not in files:
                return True
            return False

        existing = self.existing_files
        new_files = [x for x in files if not_in(x, existing)]
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
        for fname, timestamp, meta in cur:
            d = {}
            d['file'] = os.path.basename(fname)
            d['timestamp'] = unicode(timestamp)
            d['meta'] = meta
            metadatas.append(d)
        return metadatas

    def __del__(self):
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

def templatefill(template, data):
    for key, value in data.items():
        replacekey = '__%s__' % key.upper()
        template = template.replace(replacekey, value)
    return template

def write_html(metadatas):
    htmlfile = os.path.join(OUTPUTDIR, HTMLFILE)
    templatefile = os.path.join(SCRIPTPATH, HTMLTEMPLATE)
    with open(templatefile, 'r') as f:
        template = f.read().decode("UTF-8")
    HTMLIMG = """  <div class="kuva">
        <h3>%(title)s</h3>
        <img src="%(url)s" alt="%(title)s" />
      </div>"""
    images = ""
    for meta in metadatas[:HTMLCOUNT]:
        images += HTMLIMG % dict(title=meta['file'],
                                 url="%s/%s" % (ROOTURL, meta['file']))

    data = dict(title=TITLE,
                rss_url=RSSURL,
                kuveja=images,
                initial_count=str(HTMLCOUNT))
    output = templatefill(template, data)
    with open(htmlfile, 'w') as f:
        f.write(output.encode("UTF-8"))

def main():
    if update_needed() and False:
        # Already up to date
        sys.exit(0)
    cache = Cache(DBFILE)
    files = glob.glob(os.path.join(INPUTDIR, GLOBFILTER))
    cache.update(files)
    metadatas = cache.get_metadatas()

    # Simply dump metadatas as a JSON file
    jsonfile = os.path.join(OUTPUTDIR, JSONFILE)
    json.dump(metadatas, open(jsonfile, 'w'))

    # Generate the RSS feed and HTML
    write_rss(metadatas)
    write_html(metadatas)

    # Done
    sys.exit(0)

if __name__ == '__main__':
    main()

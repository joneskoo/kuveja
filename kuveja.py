#!/usr/bin/env python
#encoding: UTF-8
# Joonas Kuorilehto 2009-2011

import os
import sys
import glob
import time
import PyRSS2Gen
from datetime import datetime
import ConfigParser
try:
    import json
except:
    import simplejson as json

from meta import readmeta
from cache import Cache

# Read configs
config = ConfigParser.ConfigParser()
# Default config from the same directory as this script
SCRIPTPATH = os.path.dirname(__file__)
config.read(os.path.join(SCRIPTPATH, 'kuveja.cfg'))
# User config overrides from the working directory or dot file in home
config.read(['kuveja.cfg', os.path.expanduser('~/.kuveja.cfg')])

# Cache
DBFILE = config.get('cache', 'db')

# General settings
INPUTDIR = os.path.expanduser(config.get('source', 'inputdir'))
GLOBFILTER = config.get('source', 'globfilter')
OUTPUTDIR = os.path.expanduser(config.get('target', 'outputdir'))
UPTODATECHECK = config.getboolean('source', 'uptodatecheck')

# RSS output
TITLE = config.get('rss', 'title')
DESCRIPTION = config.get('rss', 'description')
RSSMEDIA = config.get('rss', 'mediaurl')
LINKURL = config.get('rss', 'linkurl')
RSSFILE = config.get('target', 'rssname')
RSSURL = config.get('rss', 'feedurl')
RSSCOUNT = config.getint('rss', 'count')

# JSON output
JSONFILE = config.get('target', 'jsonname')

# HTML output
HTMLFILE = config.get('target', 'htmlname')
HTMLTEMPLATE = config.get('html', 'template')
HTMLMEDIA = config.get('html', 'mediaurl')
HTMLCOUNT = config.getint('html', 'initialcount')
HTMLIMG = """  <div class="kuva">
    <h3>%(title)s</h3>
    <img src="%(url)s" alt="%(title)s" />
  </div>"""
RSSIMG = '  <h3>%(title)s</h3><p><img alt="%(title)s" src="%(url)s" /></p>' \
         + '%(meta)s'

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
        d['url'] = "%s/%s" % (RSSMEDIA, d['file'])
        d['title'] = d['file']
        itemhtml = RSSIMG % d
        r = PyRSS2Gen.RSSItem(
            title = d['file'],
            description = itemhtml,
            link = d['url'],
            pubDate = d['timestamp'])
        items.append(r)

    rss = PyRSS2Gen.RSS2(
        title = TITLE,
        link = LINKURL,
        description = DESCRIPTION,
        lastBuildDate = datetime.now(),
        items = items)
    with open(rssfile, "w") as f:
        rss.write_xml(f, encoding="UTF-8")
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
                                 url="%s/%s" % (HTMLMEDIA, meta['file']))

    data = dict(title=TITLE,
                rss_url=RSSURL,
                kuveja=images,
                initial_count=str(HTMLCOUNT))
    output = templatefill(template, data)
    with open(htmlfile, 'w') as f:
        f.write(output.encode("UTF-8"))


def metadata_read(fname):
    mtime = datetime.utcfromtimestamp(os.stat(fname).st_mtime)
    meta, timestamp = readmeta(fname)
    # If EXIF capture time is not available, use mtime
    if not timestamp:
        timestamp = mtime
    return timestamp, meta, mtime

class MetadataReader(object):
    """Get metadata from images"""
    def __init__(self, globstring, cache=None):
        super(MetadataReader, self).__init__()
        self.globstring = globstring
        if cache:
            self.cache = Cache(cache)
        else:
            self.cache = None

    def read(self):
        files = glob.glob(self.globstring)
        if self.cache:
            self.cache.update(files, metadata_read)
            metadatas = self.cache.get_metadatas()
        else:
            metadatas = []
            for fname in files:
                timestamp, meta, mtime = metadata_read(fname)
                d = dict(file=os.path.basename(fname),
                            meta=meta,
                            timestamp=unicode(timestamp))
                metadatas.append(d)
        return metadatas

def main():
    if update_needed() and UPTODATECHECK:
        # Already up to date
        sys.exit(0)
    globstring = os.path.join(INPUTDIR, GLOBFILTER)
    reader = MetadataReader(globstring, cache=DBFILE)
    metadatas = reader.read()

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

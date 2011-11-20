# encoding: UTF-8

import os
import sqlite3

class Cache:
    # TODO: configurable database fields
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

    def update(self, files, callback):
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
            timestamp, meta, mtime = callback(fname)
            cur.execute("insert into kuveja(file, timestamp, meta, mtime) "+ \
                        "values (?, ?, ?, ?)", (fname, timestamp, meta, mtime))
        self.con.commit()

    def get_metadatas(self):
        '''Order by mtime, but use capture time'''
        cur = self.con.cursor()
        cur.execute("select file, timestamp, meta from kuveja order by mtime desc")
        metadatas = []
        for fname, timestamp, meta in cur:
            d = dict(file=os.path.basename(fname),
                        meta=meta,
                        timestamp=unicode(timestamp))
            metadatas.append(d)
        return metadatas

    def __del__(self):
        self.con.close()

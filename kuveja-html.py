#!/usr/bin/env python3
import json
from sys import argv

if len(argv) > 1:
    FILE = argv[1]
else:
    FILE = 'kuveja.json'
PREFIX = 'http://joneskoo.kapsi.fi/kuveja/'
HEADER = """---
layout: main
title: joneskoon kuvafeedi
---"""
HTML = """<div class="kuva">
    <h3>%(title)s</h3>
    <img src="%(url)s" alt="%(title)s" />
</div>"""
FOOTER = "<div class='clear' id='endkuveja'></div>"

def main():
    with open(FILE) as f:
        data = json.load(f)

    print(HEADER)
    for d in data[0:10]:
        title = d['file']
        url = PREFIX + d['file']
        print(HTML % vars())
    print(FOOTER)

if __name__ == '__main__':
    main()

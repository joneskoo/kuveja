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
rss: http://joneskoo.kapsi.fi/kuveja.rss
---
<p>Kuveja joneskoon elämän varrelta.
Saatavana myös <a href="http://joneskoo.kapsi.fi/kuveja.rss">RSS:nä</a>.</p>
"""
HTML = """<div class="kuva">
    <h3>%(title)s</h3>
    <img src="%(url)s" alt="%(title)s" />
</div>"""
FOOTER = """
<div class='clear' id='endkuveja'></div>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.6.4/jquery.min.js"
        type="text/javascript"></script>
<script language="Javascript" type="text/javascript">
//<![CDATA[

var kuveja;
var index = 10;
var prefix = "/kuveja/";
var template;

function load_bottom () {
    var k = kuveja[index++];
    var html = template.clone();
    $("h3", html)[0].textContent = k['file'];
    var img = $("img", html)[0]
    img.src = prefix + k['file'];
    img.alt = k['file'];
    $("#content").append(html);
}

$(document).ready(function() {
    $.getJSON('/kuveja/kuveja.json', function(data) { kuveja = data; });
    template = $("div.kuva:first");

    $(window).scroll(function(){
        var pixels_to_bottom = ($(document).height() - $(window).height()) - $(window).scrollTop();
        if (pixels_to_bottom < 100){
            load_bottom();
        }
    });
});
//]]>
</script>
"""

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

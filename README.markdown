# Kuveja #

Kuveja is a simple photo feed generator that takes a directory of JPEG images
and writes out:

 1) a JSON listing with EXIF metadata
 2) HTML
 3) RSS

Internally everything is cached to a sqlite-database to speed up so each
image metadata is only read once.

Kuveja is licensed under the MIT License.

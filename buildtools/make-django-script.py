"""
Prepend boilerplate required for scripts which make use of Django's ORM.

$Id$

Copyright (C) 2011  Internet Systems Consortium ("ISC")

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND ISC DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS.  IN NO EVENT SHALL ISC BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
"""

import os, sys

sys.stdout.write('''\
#!%(AC_PYTHON_INTERPRETER)s
# Automatically constructed script header

import sys, os
# sys.path[0] is the cwd of the script being executed, so we add the
# path to the settings.py file after it
sys.path.insert(1, '%(AC_PYTHONPATH)s')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# Original script starts here

''' % os.environ)

sys.stdout.write(sys.stdin.read())
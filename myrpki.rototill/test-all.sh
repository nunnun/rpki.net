#!/bin/sh -
# $Id$

# Copyright (C) 2009  Internet Systems Consortium ("ISC")
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND ISC DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS.  IN NO EVENT SHALL ISC BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
# OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
 
set -x

export TZ=UTC

screen -X split
screen -X focus

for i in ../rpkid/testbed.*.yaml
do
  rm -rf *.xml bpki.myrpki bpki.myirbe test
  python sql-cleaner.py 
  screen python yamltest.py $i
  date
  sleep 180
  for j in . . . . . . . . . .
  do
    sleep 30
    date
    ../rcynic/rcynic
    xsltproc --param refresh 0 ../rcynic/rcynic.xsl rcynic.xml | w3m -T text/html -dump
    date
  done
  pstree -ws python | awk '/yamltest/ {system("kill -INT " $2)}'
  sleep 30
  make backup
done
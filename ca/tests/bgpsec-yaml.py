#!/usr/bin/env python
#
# $Id$
#
# Copyright (C) 2014  Dragon Research Labs ("DRL")
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND DRL DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS.  IN NO EVENT SHALL DRL BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
# OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

"""
Script to generate YAML to feed to test scripts.  A bit circular, but less work this way.

This is a quick hack to generate some test data using BGPSEC router certificates.
It does not (yet?) correspond to any router configurations here or anywhere.  At some
point it may evolve into a proper test program.
"""

import yaml

root = "Root"

def kid(n):			# pylint: disable=W0621
  name = "ISP-%03d" % n
  ipv4 = "10.%d.0.0/16" % n
  asn  = n
  router_id = n * 10000

  return dict(name = name,
              ipv4 = ipv4,
              asn  = asn,
              hosted_by   = root,
              roa_request = [dict(asn = asn, ipv4 = ipv4)],
              router_cert = [dict(asn = asn, router_id = router_id)])

print '''\
# This configuration was generated by a script.  Edit at your own risk.
'''

print yaml.dump(dict(name         = root,
                     crl_interval = "1h",
                     regen_margin = "20m",
                     valid_for    = "1y",
                     kids         = [kid(n + 1) for n in xrange(200)]))

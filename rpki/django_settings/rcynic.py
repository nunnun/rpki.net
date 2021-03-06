# $Id$

# Copyright (C) 2015-2016  Parsons Government Services ("PARSONS")
# Portions copyright (C) 2014  Dragon Research Labs ("DRL")
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notices and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND PARSONS AND DRL DISCLAIM ALL
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS.  IN NO EVENT SHALL
# PARSONS OR DRL BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
# OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
# WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
This module contains configuration settings for Django libraries.
At present, rcynicng only uses the Django ORM, not the rest of Django.
Unlike the CA tools rcynicng defaults to using SQLite3 as its database
engine, so we tweak the defaults a little before instantiating the
database configuration here.
"""

from .common import *                   # pylint: disable=W0401,W0614

__version__ = "$Id$"


# Database configuration.

class DBConfigurator(DatabaseConfigurator):

    default_sql_engine = "sqlite3"

    @property
    def sqlite3(self):
        return dict(
            ENGINE   = "django.db.backends.sqlite3",
            NAME     = cfg.get("sql-database", section = self.section, default = "rcynic.db"))


DATABASES = DBConfigurator().configure(cfg, "rcynic")

del DBConfigurator
del DatabaseConfigurator


# Apps.

INSTALLED_APPS = ["rpki.rcynicdb"]


# Debugging
#
# DO NOT ENABLE DJANGO DEBUGGING IN PRODUCTION!
#
#DEBUG = True


# Allow local site to override any setting above -- but if there's
# anything that local sites routinely need to modify, please consider
# putting that configuration into rpki.conf and just adding code here
# to read that configuration.
try:
    from local_settings import *        # pylint: disable=W0401,F0401
except ImportError:
    pass

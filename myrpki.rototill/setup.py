"""
$Id$

Copyright (C) 2010  Internet Systems Consortium ("ISC")

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

import subprocess, csv, re, os, getopt, sys, base64, time, glob
import myrpki, rpki.config, rpki.cli

from xml.etree.ElementTree import Element, SubElement, ElementTree

def read_xml_handle_tree(filename):
  handle = os.path.splitext(os.path.split(filename)[-1])[0]
  etree  = myrpki.etree_read(filename)
  return handle, etree

class main(rpki.cli.Cmd):

  prompt = "setup> "

  completedefault = rpki.cli.Cmd.filename_complete

  me = None
  parents = {}
  children = {}
  repositories = {}


  def __init__(self):
    os.environ["TZ"] = "UTC"
    time.tzset()

    self.cfg_file = os.getenv("MYRPKI_CONF", "myrpki.conf")

    opts, argv = getopt.getopt(sys.argv[1:], "c:h?", ["config=", "help"])
    for o, a in opts:
      if o in ("-c", "--config"):
        self.cfg_file = a
      elif o in ("-h", "--help", "-?"):
        argv = ["help"]

    if not argv or argv[0] != "help":
      self.read_config()

    rpki.cli.Cmd.__init__(self, argv)


  def read_config(self):

    self.cfg = rpki.config.parser(self.cfg_file, "myrpki")
    myrpki.openssl = self.cfg.get("openssl", "openssl")
    self.histfile  = self.cfg.get("history_file", ".setup_history")

    self.handle    = self.cfg.get("handle")
    self.run_rpkid = self.cfg.getboolean("run_rpkid")
    self.run_pubd  = self.cfg.getboolean("run_pubd")
    self.run_rootd = self.cfg.getboolean("run_rootd")

    self.entitydb_dir = self.cfg.get("entitydb_dir", "entitydb")

    if self.run_rootd and (not self.run_pubd or not self.run_rpkid):
      raise RuntimeError, "Can't run rootd unless also running rpkid and pubd"

    self.bpki_resources = myrpki.CA(self.cfg_file, self.cfg.get("bpki_resources_directory"))
    if self.run_rpkid or self.run_pubd or self.run_rootd:
      self.bpki_servers = myrpki.CA(self.cfg_file, self.cfg.get("bpki_servers_directory"))

    self.pubd_contact_info = self.cfg.get("pubd_contact_info", "")

    self.rsync_module = self.cfg.get("publication_rsync_module")
    self.rsync_server = self.cfg.get("publication_rsync_server")

  def entitydb(self, *args):
    return os.path.join(self.entitydb_dir, *args)


  def load_xml(self):
    self.me = myrpki.etree_read(self.entitydb("identity.xml"))
    self.parents      = dict(read_xml_handle_tree(i) for i in glob.glob(self.entitydb("parents", "*.xml")))
    self.children     = dict(read_xml_handle_tree(i) for i in glob.glob(self.entitydb("children", "*.xml")))
    self.repositories = dict(read_xml_handle_tree(i) for i in glob.glob(self.entitydb("repositories", "*.xml")))

    if False:
      print "++ Loaded ++"
      print handle, self.me
      print "Parents:     ", self.parents
      print "Children:    ", self.children
      print "Repositories:", self.repositories
      print "-- Loaded --"


  # Disable all this parent-based offer and hint cruft for now, it's confusing more basic issues

  disable_parent_offers_and_hints = True
  

  def do_initialize(self, arg):
    if arg:
      raise RuntimeError, "This command takes no arguments"

    print "This may take a little while, have to generate RSA keys..."

    self.bpki_resources.setup(self.cfg.get("bpki_resources_ta_dn",
                                           "/CN=%s BPKI Resource Trust Anchor" % self.handle))
    if self.run_rpkid or self.run_pubd or self.run_rootd:
      self.bpki_servers.setup(self.cfg.get("bpki_servers_ta_dn",
                                           "/CN=%s BPKI Server Trust Anchor" % self.handle))

    # Create entitydb directories.

    for i in ("parents", "children", "repositories", "pubclients"):
      d = self.entitydb(i)
      if not os.path.exists(d):
        os.makedirs(d)

    if self.run_rpkid or self.run_pubd or self.run_rootd:

      if self.run_rpkid:
        self.bpki_servers.ee(self.cfg.get("bpki_rpkid_ee_dn",
                                          "/CN=%s rpkid server certificate" % self.handle), "rpkid")
        self.bpki_servers.ee(self.cfg.get("bpki_irdbd_ee_dn",
                                          "/CN=%s irdbd server certificate" % self.handle), "irdbd")

      if self.run_pubd:
        self.bpki_servers.ee(self.cfg.get("bpki_pubd_ee_dn",
                                          "/CN=%s pubd server certificate" % self.handle), "pubd")

      if self.run_rpkid or self.run_pubd:
        self.bpki_servers.ee(self.cfg.get("bpki_irbe_ee_dn",
                                          "/CN=%s irbe client certificate" % self.handle), "irbe")

      if self.run_rootd:
        self.bpki_servers.ee(self.cfg.get("bpki_rootd_ee_dn",
                                          "/CN=%s rootd server certificate" % self.handle), "rootd")

    # Build the identity.xml file.  Need to check for existing file so we don't
    # overwrite?  Worry about that later.

    e = Element("identity", handle = self.handle)
    myrpki.PEMElement(e, "bpki_ca_certificate", self.bpki_resources.cer)
    myrpki.etree_write(e, self.entitydb("identity.xml"))

    # If we're running pubd, construct repository entry for it.

    if not self.disable_parent_offers_and_hints and self.run_pubd:
      r = Element("repository", type = "confirmed",
                  service_url = "https://%s:%s/" % (self.cfg.get("pubd_server_host"),
                                                    self.cfg.get("pubd_server_port")))
      SubElement(r, "contact_info").text = self.pubd_contact_info

    # If we're running rootd, construct a fake parent to go with it,
    # and cross-certify in both directions so we can talk to rootd.

    if self.run_rootd:

      e = Element("parent", parent_handle = "rootd", child_handle = self.handle,
                  service_url = "https://localhost:%s/" % self.cfg.get("rootd_server_port"))

      myrpki.PEMElement(e, "bpki_resource_ca", self.bpki_servers.cer)
      myrpki.PEMElement(e, "bpki_server_ca",   self.bpki_servers.cer)

      if not self.disable_parent_offers_and_hints:
        e.append(r)

      myrpki.etree_write(e, self.entitydb("parents", "rootd.xml"))

      self.bpki_resources.xcert(self.bpki_servers.cer)

      rootd_child_fn = self.cfg.get("child-bpki-cert", None, "rootd")
      if not os.path.exists(rootd_child_fn):
        os.link(self.bpki_servers.xcert(self.bpki_resources.cer), rootd_child_fn)

    if not self.disable_parent_offers_and_hints and self.run_pubd:
      myrpki.PEMElement(r, "bpki_server_ca", self.bpki_servers.cer)
      myrpki.etree_write(r, self.entitydb("repositories", "%s.xml" % self.handle))


  def do_compose_request_to_parent(self, arg):
    print "For the moment, the request to parent is identical to identity.xml, just send that file"


  def do_answer_child(self, arg):

    self.load_xml()

    child_handle = None

    opts, argv = getopt.getopt(arg.split(), "", ["child_handle="])
    for o, a in opts:
      if o == "--child_handle":
        child_handle = a
    
    if len(argv) != 1 or not os.path.exists(argv[0]):
      raise RuntimeError, "Need to specify filename for child.xml"

    if not self.run_rpkid:
      raise RuntimeError, "Don't (yet) know how to set up child unless we run rpkid"

    c = myrpki.etree_read(argv[0])

    if child_handle is None:
      child_handle = c.get("handle")

    print "Child calls itself %r, we call it %r" % (c.get("handle"), child_handle)

    self.bpki_servers.fxcert(c.findtext("bpki_ca_certificate"))

    e = Element("parent", parent_handle = self.handle, child_handle = child_handle,
                service_url = "https://%s:%s/up-down/%s/%s" % (self.cfg.get("rpkid_server_host"),
                                                               self.cfg.get("rpkid_server_port"),
                                                               self.handle, child_handle))

    myrpki.PEMElement(e, "bpki_resource_ca", self.bpki_resources.cer)
    myrpki.PEMElement(e, "bpki_server_ca",   self.bpki_servers.cer)

    if not self.disable_parent_offers_and_hints:

      # Testing run_pubd here is probably wrong.  We need better logic
      # for deciding whether to offer our own pubd or give a referal.
      # For the moment, while just trying to get the new code off the
      # ground, this will suffice.

      if False and self.run_pubd:
        SubElement(e, "repository", type = "offer",
                   service_url = "https://%s:%s/" % (self.cfg.get("pubd_server_host"),
                                                     self.cfg.get("pubd_server_port")))

      # This business with the service_url is almost certainly wrong.
      # For hints, only the repository can tell us what's right; for
      # offers, well, this is one of the parts we never managed to
      # automate properly before, so this may require examining what we
      # ended up doing by hand when testing.

      if len(self.repositories) == 1:
        repo = self.repositories.values()[0]
        b = repo.find("bpki_server_ca")
        r = SubElement(e, "repository",
                       service_url = "%s%s/" % (repo.get("service_url"), child_handle),
                       type = "offer" if self.run_pubd else"hint")

        if not self.run_pubd:

          # CMS-signed blob authorizing use of part of our space by our
          # child goes here, once I've written that code.

          # Insert BPKI data child will need to talk to repository
          r.append(b)

      else:
        print "Warning: Not obvious which repository to hint or offer to child"



    myrpki.etree_write(e, self.entitydb("children", "%s.xml" % child_handle))


  def do_process_parent_answer(self, arg):

    self.load_xml()

    parent_handle = None
    repository_handle = None

    opts, argv = getopt.getopt(arg.split(), "", ["parent_handle=", "repository_handle="])
    for o, a in opts:
      if o == "--parent_handle":
        parent_handle = a
      elif o == "--repository_handle":
        repository_handle = a

    if len(argv) != 1 or not os.path.exists(argv[0]):
      raise RuntimeError, "Need to specify filename for parent.xml on command line"

    p = myrpki.etree_read(argv[0])

    if parent_handle is None:
      parent_handle = p.get("parent_handle")

    if repository_handle is None:
      repository_handle = parent_handle

    print "Parent calls itself %r, we call it %r" % (p.get("parent_handle"), parent_handle)
    print "Parent calls us %r" % p.get("child_handle")
    print "We call repository %r" % repository_handle

    self.bpki_resources.fxcert(p.findtext("bpki_resource_ca"))
    self.bpki_resources.fxcert(p.findtext("bpki_server_ca"))

    myrpki.etree_write(p, self.entitydb("parents", "%s.xml" % parent_handle))

    if not self.disable_parent_offers_and_hints:

      r = p.find("repository")

      if r is not None and r.get("type") == "offer":
        e = Element("repository", service_url = r.get("service_url"))
        e.append(p.find("bpki_server_ca"))
        myrpki.etree_write(e, self.entitydb("repositories", "%s.xml" % repository_handle))

      elif r is not None and r.get("type") == "hint":
        myrpki.etree_write(r, self.entitydb("repositories", "%s.xml" % repository_handle))

      else:
        print "Couldn't find repository offer or hint"


  def do_compose_request_to_repository(self, arg):
    if self.disable_parent_offers_and_hints:
      print "For the moment, the request to repository is identical to identity.xml, just send that file"
    else:
      raise RuntimeError, "Support for hints not available yet"


  def do_answer_repository_client(self, arg):

    if not self.disable_parent_offers_and_hints:
      raise RuntimeError, "Support for hints not available yet"

    self.load_xml()

    sia_base = None

    opts, argv = getopt.getopt(arg.split(), "", ["sia_base="])
    for o, a in opts:
      if o == "--sia_base":
        sia_base = a
    
    if len(argv) != 1 or not os.path.exists(argv[0]):
      raise RuntimeError, "Need to specify filename for client.xml"

    c = myrpki.etree_read(argv[0])

    # Critical thing at this point is to figure out what client's
    # sia_base value should be.  Three cases:
    #
    # - client has no particular relationship to any other client:
    #   sia_base is top-level, or as close as we can make it taking
    #   rsyncd module into account (maybe homed under us, hmm, how do
    #   we detect case where we are talking to ourself?)
    #
    # - client is a direct child of ours to whom we (in our parent
    #   role) made an offer of publication service.  client homes
    #   under us, presumably.
    #
    # - client is a child of a client of ours who referred the new
    #   client to us, along with a signed referral.  signed referral
    #   includes sia_base of referring client, new client homes under
    #   that per referring client's wishes.

    # client_handle is sia_base with "rsync://hostname:port/" stripped
    # off the front, "/" stripped off the end, and (perhaps, to
    # simplify XML file naming) all remaining "/" characters
    # translated to ".".  This will require minor tweaks to
    # publication protocol schema, or perhaps we just do it in XML
    # land and leave publication protocol alone (for now?).

    # Checking of signed referrals goes somewhere around here.  Must
    # be after reading client's XML, but before deciding what the
    # client's sia_base and handle will be.

    if sia_base is None:
      sia_base = "rsync://%s/%s/%s/" % (self.rsync_server, self.rsync_module, c.get("handle"))

    client_handle = "/".join(sia_base.rstrip("/").split("/")[3:])

    print "Client calls itself %r, we call it %r" % (c.get("handle"), client_handle)

    self.bpki_servers.fxcert(c.findtext("bpki_ca_certificate"))

    e = Element("repository", repository_handle = self.handle,
                client_handle = client_handle, sia_base = sia_base,
                service_url = "https://%s:%s/client/%s" % (self.cfg.get("pubd_server_host"),
                                                           self.cfg.get("pubd_server_port"),
                                                           client_handle))

    myrpki.PEMElement(e, "bpki_server_ca",   self.bpki_servers.cer)

    myrpki.etree_write(e, self.entitydb("pubclients", "%s.xml" % client_handle.replace("/", ".")))


  def do_process_repository_answer(self, arg):

    self.load_xml()

    repository_handle = None

    opts, argv = getopt.getopt(arg.split(), "", ["repository_handle="])
    for o, a in opts:
      if o == "--repository_handle":
        repository_handle = a

    if len(argv) != 1 or not os.path.exists(argv[0]):
      raise RuntimeError, "Need to specify filename for repository.xml on command line"

    r = myrpki.etree_read(argv[0])

    if repository_handle is None:
       repository_handle = r.get("repository_handle")

    print "Repository calls itself %r, we call it %r" % (r.get("repository_handle"), repository_handle)
    print "Repository calls us %r" % r.get("client_handle")

    myrpki.etree_write(r, self.entitydb("repositories", "%s.xml" % repository_handle))


  def do_compose_request_to_host(self, arg):
    pass

  def do_answer_hosted_entity(self, arg):
    pass

  def do_process_host_answer(self, arg):
    pass


if __name__ == "__main__":
  main()

# ----------------------------------------------------------------------------
#
# osgsa: OpenStack user management on LDAP + Kerberos
#
# Version 1.0.0
# July 9th, 2013
# Copyright (C) 2013  Matteo Panella (morpheus@level28.org)
#
# ----------------------------------------------------------------------------
# GNU General Public License v3
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# ----------------------------------------------------------------------------

import argparse
import getpass
import ldap
import os
import sys
import uuid

# PyYAML loader black magick
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


# Default rcfile contents
DEFAULTCFG = """# osgsa configuration file

# LDAP URL
ldap_url: "ldap://localhost"

# DN for binding
bind_dn: "cn=admin,dc=example,dc=com"

# Base directory DN
base_dn: "dc=example,dc=com"

# Organizational unit containing users
users_ou: "ou=Users"

# groupOfNames for enabled bit emulation
enabled_cn: "cn=enabled_users"

# Kerberos realm
realm: "EXAMPLE.COM"

# Remove the following line :-)
please: "remove this line"
"""

RCFILE_PATH = os.path.expanduser("~/.osgsarc")

def create_or_parse_rcfile():
    if not os.path.exists(RCFILE_PATH):
        # Create default rcfile and exit
        with file(RCFILE_PATH, "w") as rc:
            rc.write(DEFAULTCFG)
        print >>sys.stderr, "A default configuration file has been created at %s" % RCFILE_PATH
        print >>sys.stderr, "Please edit it accordingly and relaunch the script"
        sys.exit(0)
    else:
        # The rcfile exists, parse it as yaml and check for the magic line
        cfg = {}
        try:
            with file(RCFILE_PATH, "r") as rc:
                cfg = load(rc, Loader=Loader)
        except:
            print >>sys.stderr, "Configuration file failed to load, please check its syntax"
            sys.exit(1)
        # Check if the user even bothered to read and understand the configuration file *AT ALL*
        if cfg.has_key("please"):
            print >>sys.stderr, "You didn't even read the default configuration file, did you?"
            sys.exit(1)
        # Check for required params
        for param in ["ldap_url", "bind_dn", "base_dn", "users_ou", "enabled_cn", "realm"]:
            if not cfg.has_key(param):
                print >>sys.stderr, "Required parameter %s is missing from configuration file" % param
                sys.exit(1)
        return cfg

# Entry point for osadduser
def adduser():
    config = create_or_parse_rcfile()
    users_dn = "%s,%s" % (config["users_ou"], config["base_dn"])
    enabled_dn = "%s,%s" % (config["enabled_cn"], config["base_dn"])

    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="name of the user that should be added")
    parser.add_argument("email", help="email address of the user")
    args = parser.parse_args()
    args.username = args.username.strip()

    if args.username == "":
        print >>sys.stderr, "Invalid username"
        sys.exit(1)
    # FIXME: validate username
    try:
        pw = getpass.getpass("LDAP Password: ")
    except KeyboardInterrupt:
        sys.exit(255)

    try:
        con = ldap.initialize(config["ldap_url"])
        status, msg = con.simple_bind_s(config["bind_dn"], pw)
        if status != 97:
            print >>sys.stderr, "Ouch! (%s)" % ", ".join(msg)
            sys.exit(1)
        # Check if user exists
        res = con.search_s(users_dn, ldap.SCOPE_SUBTREE, "(sn=%s)" % args.username, ["cn"])
        if len(res) > 0:
            print >>sys.stderr, "User %s already exists" % args.username
        else:
            # Create user
            cn = str(uuid.uuid4()).replace('-', '')
            dn = "cn=%s,%s" % (cn, users_dn)
            add_record = [
                    ("objectclass", ["inetorgperson"]),
                    ("cn", [cn]),
                    ("sn", [args.username]),
                    ("mail", [args.email]),
                    ("userpassword", ["{SASL}%s@%s" % (args.username, config["realm"])]),
            ]
            con.add_s(dn, add_record)
            # Enable user
            mod_attrs = [ (ldap.MOD_ADD, "member", dn) ]
            con.modify_s(enabled_dn, mod_attrs)
            print "User %s has been created and enabled" % args.username
        con.unbind()
    except ldap.LDAPError, e:
        if type(e.message) == dict and e.message.has_key("desc"):
            print >>sys.stderr, "LDAP Error: %s" % e.message["desc"]
        else:
            print >>sys.stderr, "LDAP Error: %s" % e

# Entry point for osmoduser
def moduser():
    config = create_or_parse_rcfile()
    users_dn = "%s,%s" % (config["users_ou"], config["base_dn"])
    enabled_dn = "%s,%s" % (config["enabled_cn"], config["base_dn"])

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-e", "--enable", action="store_true", help="enable user")
    group.add_argument("-d", "--disable", action="store_true", help="enable user")
    parser.add_argument("username", help="name of the user that should be modified")
    args = parser.parse_args()
    args.username = args.username.strip()

    if args.username == "":
        print >>sys.stderr, "Invalid username"
        sys.exit(1)
    # FIXME: validate username
    try:
        pw = getpass.getpass("LDAP Password: ")
    except KeyboardInterrupt:
        sys.exit(255)

    try:
        con = ldap.initialize(config["ldap_url"])
        status, msg = con.simple_bind_s(config["bind_dn"], pw)
        if status != 97:
            print >>sys.stderr, "Ouch! (%s)" % ", ".join(msg)
            sys.exit(1)
        # Check if user exists
        res = con.search_s(users_dn, ldap.SCOPE_SUBTREE, "(sn=%s)" % args.username, ["cn"])
        if len(res) == 0:
            print >>sys.stderr, "User %s does not exist" % args.username
        else:
            dn = res[0][0]
            if args.enable:
                # Check if the user is already enabled
                res = con.search_s(enabled_dn, ldap.SCOPE_SUBTREE, "(member=%s)" % dn, ["member"])
                if len(res) > 0:
                    print >>sys.stderr, "User %s is already enabled" % args.username
                else:
                    # Perform the enable operation
                    mod_attrs = [ (ldap.MOD_ADD, "member", dn) ]
                    con.modify_s(enabled_dn, mod_attrs)
                    print "User %s has been enabled" % args.username
            else:
                # Disable the user if it's not already disabled
                try:
                    mod_attrs = [ (ldap.MOD_DELETE, "member", dn) ]
                    con.modify_s(enabled_dn, mod_attrs)
                    print "User %s has been disabled" % args.username
                except ldap.NO_SUCH_ATTRIBUTE:
                    print >>sys.stderr, "User %s is already disabled" % args.username

        con.unbind()
    except ldap.LDAPError, e:
        if type(e.message) == dict and e.message.has_key("desc"):
            print >>sys.stderr, "LDAP Error: %s" % e.message["desc"]
        else:
            print >>sys.stderr, "LDAP Error: %s" % e

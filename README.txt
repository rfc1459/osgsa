=====
OSGSA
=====

OSGSA is a suite of tools which enables OpenStack admins to easily manage
users in an LDAP+SASL+Kerberos setup.

It currently provides a tool for user creation and one to enable/disable
users.

It has been developed for use on INFN - LNGS OpenStack cluster as part of a
P.O.R. F.S.E. project, but it's general enough to be used on other setups as
well.


Authors
=======

Matteo Panella <`morpheus@level28.org <mailto:morpheus@level28.org>`>


License
=======

GPLv3


Usage
=====

On the first run, either ``osadduser`` or ``osmoduser`` will create a file
named ``~/.osgsarc`` containing the configuration of the LDAP environment.
This file **must** be modified to suit your specific environment, otherwise
both tools will refuse to start.

osadduser
---------

Synopsis::

    osadduser <username> <email address>

The command will add a new user to the directory, bind it to the Kerberos
principal with the same name and enable it.

osmoduser
---------

Synopsis::

    osmoduser -e|-d <username>

The command will enable or disable the given user. Users in disabled state
cannot access OpenStack through Nova or Horizon.

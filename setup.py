from setuptools import setup

setup(name = "osgsa",
      version = "1.0.0",
      description = "Management tools for OpenStack users on LDAP",
      long_description = open('README.txt').read(),
      author = "Matteo Panella",
      author_email = "morpheus@level28.org",
      url = "https://github.com/rfc1459/osgsa/",
      py_modules = [ "osgsa" ],
      entry_points = {
          'console_scripts': [
              'osadduser = osgsa:adduser',
              'osmoduser = osgsa:moduser'
          ]
      },
      install_requires = [ 'python-ldap', 'PyYAML' ],
      license = "LICENSE")

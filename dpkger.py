#!/usr/bin/python

import os
import sys
import shutil
import textwrap
import subprocess

class deb_packager:
   def __init__(self):
       self.base_dir = '/var/deb_packager'
       self.puppet_repo = '/opt/puppetmaster'
       self.puppet_site = '/home/russ/site.pp'
       self.puppet_modules = ['standard',
                              'stdlib',
                              'engineering_users',
                              'gogrid_mirror']
       self.control_file = '/home/russ/site.pp'
       self.postinit_sh = '/home/russ/postinit'
       self.pkg_name = 'ggmirror'
       self.pkg_vers = '0.1-1'
       self.pkg_path = self.base_dir + '/' + self.pkg_name
       # This is where control, preinstall, postinstall files go
       self.pkg_path_root = self.pkg_path + '/DEBIAN'

   def init_pkg_path(self):
       """ Create the Directory to build the Package """
       print '+ Initializing package path (%s).' % self.pkg_path_root
       if not os.path.exists(self.pkg_path_root):
           os.makedirs(self.pkg_path_root)

   def remove_pkg_path(self):
       """ If there is an old package dir, get rid of it """
       if os.path.exists(self.pkg_path):
           rm_path = self.base_dir + '/' + self.pkg_name
           print '+ Cleaning up package remnants at %s' % rm_path
           shutil.rmtree(rm_path)

   def add_puppet(self):
       """ Add Puppet Modules and site.pp to a package """
       print '+ Adding Puppet Modules. (%s)' % self.puppet_modules
       # This is where packages get copied inside the skel environment
       pkg_puppet_path = self.pkg_path + '/opt/puppet'
       if not os.path.exists(self.puppet_repo):
           print '\nDid not find Puppet repository at %s.\n' % self.puppet_repo
           sys.exit('Exiting.')
       if not os.path.exists(pkg_puppet_path):
           os.makedirs(pkg_puppet_path)
       for mod in self.puppet_modules:
           end_path = '/modules/' + mod
           orig_modpath = self.puppet_repo + end_path
           pkg_modpath = pkg_puppet_path + end_path
           shutil.copytree(orig_modpath, pkg_modpath)
       # Create manifest path
       pkg_manifest_path = pkg_puppet_path + '/manifests'
       if not os.path.exists(pkg_manifest_path):
           os.makedirs(pkg_manifest_path)
       # Create site.pp
       sitepp = 'node default {\n'
       for mod in self.puppet_modules: 
           sitepp = sitepp + '  include %s\n' % mod
       sitepp = sitepp + '}\n'
       with open(pkg_manifest_path + '/site.pp', 'w') as f:
           f.write(sitepp)

   def add_control_file(self):
       """ Every Debian package needs a control file """
       control_file = self.pkg_path_root + '/control'
       content = textwrap.dedent("""
               Package: %s
               Version: %s
               Section: base
               Priority: optional
               Architecture: all
               Depends: 
               Maintainer: Russ!
               Description: %s
               """ % (self.pkg_name, self.pkg_vers, self.pkg_name))

       with open(control_file, 'w') as f:
           f.write(content)

   def add_prun_script(self):
       """ Add a small script to do a local Puppet Apply """
       prun_script = self.pkg_path + '/usr/local/bin/prun'
       content = '#!/bin/bash\n/usr/bin/puppet apply --modulepath /opt/puppet/modules ' +\
                 '/opt/puppet/manifests/site.pp\n'
       ulb_path = self.pkg_path + '/usr/local/bin'
       if not os.path.exists(ulb_path):
           os.makedirs(ulb_path)
       with open(prun_script, 'w') as f:
           f.write(content)

   def build_package(self):
       """ Contruct the actual Deb file """
       try:
           output = subprocess.Popen(['dpkg-deb', '--build', self.pkg_path],
                                     stdout=subprocess.PIPE).communicate()[0]
           init_pkg_fname = self.pkg_path + '.deb'
           post_pkg_fname = self.base_dir + '/%s_%s.deb' % (self.pkg_name, self.pkg_vers)
           shutil.move(init_pkg_fname, post_pkg_fname)
           print '+ Built package (%s)' % post_pkg_fname
       except:
           raise

   def main(self):
       self.remove_pkg_path()
       self.init_pkg_path()
       self.add_puppet()
       self.add_control_file()
       self.add_prun_script()
       self.build_package()
                       

if __name__ == '__main__':
   dpkgr = deb_packager()
   dpkgr.main()

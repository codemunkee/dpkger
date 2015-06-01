#!/usr/bin/python

import os
import sys
import shutil
import textwrap
import subprocess

class deb_packager:
   """ This class will create debian packages that can be installed. You need
       to tell it about a few things though:

       base_dir : where your files sit that you want to turn into a pkg
       puppet_repo : directory containing your puppet modules and manifests
       control_file : the control file for building the pkg
       postinit : a link to the postinit script you want to run
       pkg_name : what should the pkg be called?
       pkg_vers : whats the version number?
       puppet_modules : a list of the modules you want include in the pkg """

   def __init__(self, base_dir, puppet_repo, control_file, postinit, pkg_name
                pkg_vers, puppet_modules):
       self.base_dir = base_dir
       self.puppet_repo = puppet_repo
       self.puppet_site = None
       self.puppet_modules = []
       self.control_file = control_file
       self.postinit_sh = postinit
       self.pkg_name = pkg_name
       self.pkg_vers = pkg_vers
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
               Depends: puppet (>= 2.7.23-1~deb7u3)
               Maintainer: Russ!
               Description: %s
               """ % (self.pkg_name, self.pkg_vers, self.pkg_name))

       with open(control_file, 'w') as f:
           f.write(content)

   def add_prun_script(self):
       """ Add a small script to do a local Puppet Apply """
       prun_script = self.pkg_path + '/usr/local/sbin/prun'
       content = '#!/bin/bash\n/usr/bin/puppet apply --modulepath /opt/puppet/modules ' +\
                 '/opt/puppet/manifests/site.pp\n'
       ulb_path = self.pkg_path + '/usr/local/sbin'
       if not os.path.exists(ulb_path):
           os.makedirs(ulb_path)
       with open(prun_script, 'w') as f:
           f.write(content)
       os.chmod(prun_script, 700)

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

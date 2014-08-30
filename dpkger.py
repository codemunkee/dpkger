#!/usr/bin/python

class deb_packager:
   def __init__(self):
       self.base_dir = '/var/deb_packager'

   def main(self):
       print self.base_dir

if __name__ == '__main__':
   dpkgr = deb_packager()
   dpkgr.main()

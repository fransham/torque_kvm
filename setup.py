#!/usr/bin/env python
########################################################################
#  
#  setup.py: A python distutils script for installing torque_kvm.
#
#  Usage: python setup.py install
#
#  Kyle Fransham, December 2011
#
########################################################################

setup(name='torque_kvm',
      version='1.0',
      description='Virtualization extensions for torque',
      author='Kyle Fransham',
      author_email='kyle@fransham.ca',
      package_dir = {'': 'lib'},
     )

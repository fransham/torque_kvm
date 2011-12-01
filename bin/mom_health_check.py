#!/usr/bin/python
########################################################################
#
# mom_health_check.py
# This script will check the database on each hypervisor for 
# consistency.  We need to make sure that there is a one to one mapping
# between running virtual machines and entries in the database.
#
########################################################################

import libvirt

def main():
	# get list of running VMs from libvirt
	
	# get entries in database
	
	# compare
	
	pass

def get_running_vms(self):
	try:
		lconn = libvirt.open(None)
		ids = lconn.listDomainsID();
		domains = []
		for id in ids:
			domains.append(libvirt.getName(libvirt.lookupByID(lconn, id))
	except:
		pass 

def get_database_entries(self):
	

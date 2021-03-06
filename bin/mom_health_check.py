#!/usr/bin/python
########################################################################
#
# mom_health_check.py
# This script will check the database on each hypervisor for 
# consistency.  We need to make sure that there are no entries in the
# database that are not associated with running jobs.
#
########################################################################

import libvirt
import commands

try:
    import sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3

config = ConfigParser.ConfigParser()
config.read('/etc/torque-kvm.conf')
torque_home=config.get("torque","torque_home")
vmrundir = config.get("virt", "vmrundir")
dbfile=torque_home + "/net/network.db"
conn=sqlite3.connect(dbfile)

def main():
		
	# get entries in database
	dbentries = get_database_entries()
	
	# get currently running jobs
	running_jobs = get_running_jobs()
	
	# compare and fix if necessary
	compare_running_to_db(running_jobs, dbentries)
	

def get_running_vms():
	try:
		lconn = libvirt.open(None)
		ids = lconn.listDomainsID();
		domains = []
		for id in ids:
			domains.append(libvirt.getName(libvirt.lookupByID(lconn, id))
	except:
		pass 

def get_database_entries():
	global conn
	c=conn.cursor()
	c.execute('select * from reservations where inuse <> 0')
	c.close()
	
	uuids = []
	try:
		while:
			(host,ip,mac,inuse) = c.next()
			uuids.add(inuse)
	except StopIteration:
		pass;
	
	return uuids
	
def get_running_jobs():
	(ret, running_jobs) = commands.getstatusoutput('momctl -q jobs')
	if (ret != 0):
		print "cannot query torque for jobs")
		sys.exit(1)
	
	#strip off the leading text: "   localhost:         jobs = 'jobs="
	joblist = running_jobs[35:]
	
	#check if there are any jobs in the list:
	if not re.match('.*slac\.stanford\.edu', joblist):
		return None
	
	uuids = []
	
	# get the number of the running job:	
	foreach(job in job_list.split(' ')):
		parts = job.split('.')
		uuids.append(parts[0])
		
	return uuids
	
# Make sure that every entry in the DB is associated
# with a running job.  Note, we don't check for the reverse 
# situation, since a baremetal job can have a running job without
# an associated VM.  However, there should never be a situation where
# there is an entry in the database that is not associated with a 
# running job.  If we find one of these, clear it.
def compare_running_to_db(running, indb):
	for dbentry in indb:
		if dbentry in running:
			continue
			
		#if we're executing the following code, it's to fix a problem...
		global conn
		c=conn.cursor()
		c.execute("update reservations set inuse=0 where inuse=?",[jobnumber])
		conn.commit()
		c.close()

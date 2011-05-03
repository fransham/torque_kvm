#!/usr/bin/env python

###########################################
#
#  This script is called by torque when the
# user's job is done.  It will destroy the 
# VM.
#
###########################################


#parameters... hardcoded for now.
dirname = os.path.dirname( os.path.abspath(__file__) )
dbfile=dirname + "/../var/network.db"
lockfile=dirname + "/../var/db.lock


import libvirt
import smtplib
try:
    import sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3

# epilogue gets 3 arguments:
# 1 -- jobid
# 2 -- userid
# 3 -- grpid

jobid=sys.argv[0]
userid=sys.argv[1]
uuid=jobid+'.'+userid

#destroy the vm
conn = libvirt.open(None)
if conn == None:
    print 'Failed to open connection to the hypervisor'    
    sys.exit(1)

try:
    dom = conn.lookupByName(uuid)
except:
    print 'Failed to find the domain'
    sys.exit(1)

dom.destroy()

del dom
del conn

print "domain " + uuid + " destroyed"
sys.exit(1)

#get the entry from the host file
host = open(dirname + '/../var/tmp/torque-'+uuid,'w').read()

#add the entry back into the db
conn=sqlite3.connect(dbfile)
c=conn.cursor()
c.execute("update reservations set inuse = 0 where hostname=?",[host])
conn.commit()
c.close()


#!/usr/bin/env python

###########################################
#
#  This script is called by torque when the
# user's job is done.  It will destroy the 
# VM.
#
###########################################

import libvirt
import smtplib

# epilogue gets 3 arguments:
# 1 -- jobid
# 2 -- userid
# 3 -- grpid

jobid=sys.argv[0]
userid=sys.argv[1]
uuid=jobid+'.'+userid


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


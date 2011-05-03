#!/usr/bin/env python

##############################################
# 
# This is a prologue script for torque.  It 
# will boot a virtual machine for a job.
#
##############################################
import sys
import commands
import os
import time
import libvirt
try:
    import sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3


# some parameters, hardcoded for now:
imagefile = "/opt/nimbus/var/workspace-control/images/bbr-ltda.qcow2"
vmrundir = "/scratch/secureimages"
dirname = os.path.dirname( os.path.abspath(__file__) )
dbfile=dirname + "/../var/network.db"
lockfile=dirname + "/../var/db.lock"



# prologue gets 3 arguments:
# 1 -- jobid
# 2 -- userid
# 3 -- grpid

jobid=sys.argv[0]
userid=sys.argv[1]
uuid=jobid+'.'+userid


#clone the image:
target=vmrundir+'/'+userid+'.'+jobid
(ret, out) = commands.getstatusoutput('qemu-img create -b '+imagefile+' -f qcow2 '+target)
if (ret != 0):
	print "Error creating image.  Error message follows:" 
	print out
	sys.exit(1)

#get a lock on the database
count=0
while(count < 60):
	try:
		os.mkdir(lockfile)
		break
	except OSError:
		time.sleep(1)
		count+=1

if (count >= 60):
	print "could not acquire lock on db... exiting."
	sys.exit(1)

#now we have an exclusive lock on the database, get an unused mac address:
conn=sqlite3.connect(dbfile)
c=conn.cursor()
c.execute('select * from reservations where inuse = 0')

try:
        (host,ip,mac,inuse) = c.next()
except StopIteration:
        print "no free network slots!"
        sys.exit(1)

# update the db
c.execute("update reservations set inuse = 1 where hostname=?",[host])
conn.commit()

#release the lock
os.rmdir(lockfile)
c.close()

# create the libvirt xml for our domain
xmldesc="""<domain type='kvm'>
  <name>"""+uuid+"""</name>
  <memory>2097152</memory>
  <currentMemory>2097152</currentMemory>
  <vcpu>1</vcpu>
  <os>
    <type arch='x86_64' machine='rhel5.4.0'>hvm</type>
    <boot dev='hd'/>
  </os>
  <clock offset='utc'>
    <timer name='pit' tickpolicy='delay'/>
  </clock>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>destroy</on_crash>
  <devices>
    <emulator>/usr/libexec/qemu-kvm</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='"""+target+"""'/>
      <target dev='hda' bus='ide'/>
      <address type='drive' controller='0' bus='0' unit='0'/>
    </disk>
    <controller type='ide' index='0'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>
    </controller>
    <interface type='bridge'>
      <mac address='"""+mac+"""'/>
      <source bridge='br0'/>
      <target dev='"""+uuid+"""-0'/>
      <model type='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
    </interface>
  </devices>
</domain>
"""

# Boot the vm
lconn = libvirt.open(None)
if lconn == None:
    print 'Failed to open connection to the hypervisor'
    sys.exit(1)
dom = lconn.createLinux(xmldesc, 0)
if dom == None:
    print 'Virtual machine creation failed'
    sys.exit(1)

print "Domain: id %d starting %s" % (dom.ID(), dom.OSType())

# write the ip address of the booted vm to a file so that the
# user's job can read it:
jobfile = open(dirname + '/../var/tmp/torque-'+uuid,'w')
jobfile.write(host)
jobfile.close()

#vm created! 
sys.exit(0)

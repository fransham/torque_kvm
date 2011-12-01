#!/usr/bin/env python

import sys
import commands
import os
import time
import libvirt
import subprocess
import re
import ConfigParser

try:
    import sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3
    

class prologue_exception(Exception):
	pass


class prologue:
	
	def __init__(self, jobid, userid, groupid, jobname, requested_resources, queue):
		
		self.jobid               = jobid
		self.userid              = userid
		self.groupid             = groupid
		self.jobname             = jobname
		self.requested_resources = requested_resources
		self.queue               = queue
		self.jobnum              = jobid.split('.')[0]
		self.uuid                = 'vm-'+jobnum
		self.hostname			 = ""
		self.imagefile           = ""
		
		readconfigs()
		
		
	def readconfigs(self):
		
		self.config = ConfigParser.ConfigParser()
		config.read('/etc/torque-kvm.conf')

		self.torque_home     = config.get("torque","torque_home")
		self.vmrundir        = config.get("virt", "vmrundir")
		self.dbfile          = torque_home + "/net/network.db"
		self.conn            = sqlite3.connect(self.dbfile)
		self.lockfile        = torque_home + "/net/db.lock"
		self.target_hostfile = torque_home+"/virt/"+self.jobid
		self.mempercore      = config.get("virt", "mempercore")
		self.disable_libvirt = config.get("virt", "disable_libvirt")



	def run_prologue(self):
		
		try:

			# get imagepath from keyword and resource info:
			imagepath = get_image_path(get_keyword())
	
			# check if the imagepath is for a baremetal session:
			check_image(imagepath)
	
			# clone the backing image:
			target = clone_image(imagepath,vmrundir+'/'+uuid)
	
			# get free hostname/mac:
			(host,mac) = get_host_mac()
	
			# get the number of cpus requested:
			ncpus = get_ncpus()
	
			# create the xml and boot the vm:
			#boot_vm(create_xml(target,mac,ncpus,get_memory(int(ncpus)), get_scratch_disk()))
			boot_vm(uuid,get_memory(int(ncpus)),ncpus,mac,target,
				    get_scratch_disk())
			
			# write the job file:
			write_jobfile(hostname)
	
			#cleanup and exit:
			finalize()
			
		except prologue_exception as detail:
			
			print get_output_message()
			print "An error occured in the prologue: ", detail
			print "\n"
			print "Shutting down virtual machines. You may see some errors below."
			print "They can safely be ignored."
			
			if not self.disable_libvirt:
				try:
					print 				
					lconn = libvirt.open(None)
					dom = lconn.lookupByName(uuid)
					dom.destroy()
				except:
					pass
					
			if self.hostname:
				c=self.conn.cursor()
				c.execute("update reservations set inuse = 0 where hostname=?",[hostname])
				conn.commit()
				c.close()
				
			release_db_lock()
			sys.exit(1)
			
	

	# get keyword:
	def get_keyword(self):
		return parse_resources('other')

	def get_ncpus():
		ncpus = parse_resources('ncpus')
		if ncpus:
			return ncpus
		return '1'
	
	def get_memory(self, num_cpus):
		mempercore = config.getint("virt","mempercore")
		return str( num_cpus * mempercore * 1048)	
		
	def get_scratch_in_gb(self):
		reqfile = parse_resources('file').lower()
		if not reqfile:
			return None
		if re.match('.*tb', reqfile):
			return int(reqfile[:-2])*1024
		elif re.match('.*gb', reqfile):
			return int(reqfile[:-2])
		elif re.match('.*mb', reqfile):
			return int(reqfile[:-2])/1024
		elif re.match('.*kb', reqfile):
			return int(reqfile[:-2])/1048576
		elif re.match('.*b', reqfile):
			return int(reqfile[:-2])/1073741824
		return None
			
		
	
	def parse_resources(self, tofind):
		if re.match('.*'+tofind+'=.*', requested_resources):
			request = re.split(',',requested_resources.rstrip())
			for resource in request:
				if resource.startswith(tofind+'='):
					match = re.split('=',resource)[1]
					return match
		return ""
	
	# get image path:
	def get_image_path(self, keyword):
		request = config.get('resources','map')
		rules = request.split(';')
		for rule in rules:
			sections = rule.strip().split(' ')
			if ( ( sections[0] == queue or sections[0] == '%' ) and
				 ( sections [1] == keyword or sections[1] == '%') and
				 ( sections [2] == userid or sections[2] == '%') and
				 ( sections [3] == groupid or sections[3] == '%') ):
				return sections[4].strip()
				
	
	#check the image path.  Exit if it's for a baremetal session:
	def check_image(self, imagefile):
		if imagefile == None or imagefile == "None":
			self.sessiontype = "baremetal"	
			open(target_hostfile, 'w').close() 
			os.chmod(target_hostfile, 644)
			do_exit()
		
		self.sessiontype = "virtualization"
		
		if not os.path.exists(imagefile):
			raise prologue_exception( ' Cannot file image file: '+
									 imagefile )
		
		self.imagefile = imagefile
	
	#clone the image:
	def clone_image(self, imagefile, target):
		(ret, out) = commands.getstatusoutput('qemu-img create -b '+
											  imagefile+' -f qcow2 '+
											  target)
		if (ret != 0):
			 raise prologue_error("Error creating image.  Error message follows: \n" + out) 
		return target
	
	#get a lock on the database
	def lock_db(self):
		count=0
		while(count < 60):
			try:
				os.mkdir(lockfile)
				break
			except OSError:
				time.sleep(1)
				count+=1
	
		if (count >= 60):
			do_exit_error( "could not acquire lock on db... exiting." )
	
	#get a hostname and mac from the database
	def get_host_mac(self):
		lock_db()
		c=self.conn.cursor()
		c.execute('select * from reservations where inuse = 0')
	
		try:
			(host,ip,mac,inuse) = c.next()
		except StopIteration:
			do_exit_error( "no free network slots!" )
	
		# update the db
		c.execute("update reservations set inuse = ? where hostname=?",
				  [jobnum, host])
		conn.commit()
		c.close()
	
		#release the lock
		release_db_lock()
	
		self.hostname 
	
		return (host,mac)
	
	# if we want scratch space for the VM, get it from this function
	def get_scratch_disk(self):
		scratch = None
		requested_scratch = get_scratch_in_gb()
		if not requested_scratch:
			try: 
				requested_scratch = int(config.get('resources', 
						'default_scratch').strip())
			except ConfigParser.NoOptionError:
				return None
		try:
			scratch = config.get('resources', 'scratch')
		except ConfigParser.NoOptionError:
			return None
			
		#iterate over the entries in the conf file
		scratch_disks = scratch.split(';')
		for disk in scratch_disks:
			#skip over this if it's a blank line:
			if not disk:
				continue
			sections = disk.strip().split(' ')
			target = sections[1].strip()
			# break if the current entry has more scratch space than 
			# is needed
			if ( int(sections[0]) >= requested_scratch ):
				break
		
		cloned_scratch = clone_image(target, 
									 vmrundir+'/'+uuid+'.scratch')
		return cloned_scratch
		

	# Boot the vm
	def boot_vm_qemu(self, uuid,mem,ncpus,mac,target,scratch):
	
		#todo: use getstatusoutput instead to check return values.
		os.system('/usr/sbin/tunctl -t '+uuid+'>/dev/null')
		os.system('/usr/sbin/brctl addif br0 '+uuid)
		os.system('/sbin/ifconfig '+uuid+' up')
  	 	optionstring='-name '+uuid+' -m '+mem+' -smp '+ncpus+
					 ' -cpu qemu64 -net nic,macaddr='+mac+
					 ',vlan=0,model=virtio -net tap,ifname='+uuid+
					 ',vlan=0,script=no,downscript=no  -boot c -drive file='+
					 target+',if=ide,bus=0,unit=0,boot=on,format=qcow2 -drive file='+
					 scratch+',if=ide,bus=0,unit=1,format=qcow2 -balloon virtio -nographic -no-acpi -clock unix'
		(ret, out) = commands.getstatusoutput(''/usr/libexec/qemu-kvm '+optionstring+'&')
		if (ret != 0):
			 raise prologue_error("Error creating image.  Error message follows: \n" + out) 
		return target
   

	# write the hostname of the booted vm to a file so that the
	# user's job can read it:
	def write_jobfile(host):
		jobfile = open(target_hostfile,'w')
		jobfile.write(host)
		jobfile.close()
		os.chmod(target_hostfile,644)
	
	def finalize():
		print get_output_message()
		do_exit()
	
	def release_db_lock():
		try:		
			os.rmdir(lockfile)	
		except:
			pass
	
	def do_exit():
		sys.exit(0)


		

	# create the libvirt xml for our domain
	def create_xml(target,mac,ncpus,mem,scratch):
		xmldesc="""<domain type='kvm'>
  <name>"""+uuid+"""</name>
  <memory>"""+mem+"""</memory>
  <vcpu>"""+ncpus+"""</vcpu>
  <os>
    <type arch='i686'>hvm</type>
    <boot dev='hd'/>
  </os>
  <devices>
    <emulator>/usr/libexec/qemu-kvm</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='"""+target+"""'/>
      <target dev='hda'/>
    </disk>
    """
		if scratch:
			xmldesc += """
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='"""+scratch+"""'/>
      <target dev='hdb'/>
    </disk>
    """
		xmldesc += """<interface type='bridge'>
      <mac address='"""+mac+"""'/>
      <source bridge='br0'/>
      <target dev='"""+uuid+"""-0'/>
      <model type='virtio'/>
    </interface>
  </devices>
  <cpu match='minimum'>
	<model>qemu32</model>
  </cpu>

</domain>

"""
		return xmldesc


	def get_output_message(self):
		output ='''
------------------------------------------------------------------------
TORQUE PROLOGUE:
  jobid:               '''+self.jobid+'''
  userid:              '''+self.userid+'''
  requested resources: '''+self.requested_resources+'''
  queue:               '''+self.queue+'''
  host:			       '''+self.hostname+'''
  sessiontype:         '''+self.sessiontype+'''
  imagefile: 		   '''+self.imagefile+'''
------------------------------------------------------------------------
  
''' 

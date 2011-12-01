#!/usr/bin/env python

##
## IMPORTS
import sys
import commands
import os
import time
import libvirt
import logging
import subprocess
import re
import ConfigParser
try:
    import sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3
import torque_kvm.pyratemp    

##
## PROLOGUE EXCEPTION CLASS
class PrologueError(Exception):
	pass

##
## PROLOGUE CLASS
## This class is called before a job starts.
class Prologue:
	
## Initialize with torque job parameters	
	def __init__(self, jobid, userid, groupid, jobname, 
				 requested_resources, queue):
		
		self.jobid = jobid
		self.userid = userid
		self.groupid = groupid
		self.jobname = jobname
		self.requested_resources = requested_resources
		self.queue = queue
		self.jobnum = jobid.split('.')[0]
		self.uuid = 'vm-'+jobnum
		self.hostname = ""
		self.imagefile = ""
		logging.basicConfig(filename=config.get("logging", "prolog"), 
							level=config.get("logging", "loglevel"), 
							format='%(asctime)s %(message)s')
		readconfigs()
		
## Read parameters from the configuration file		
	def readconfigs(self):
		
		self.config = ConfigParser.ConfigParser()
		config.read('/etc/torque-kvm.conf')

		self.torque_home = config.get("torque","torque_home")
		self.vmrundir = config.get("virt", "vmrundir")
		self.dbfile = torque_home + "/net/network.db"
		self.conn = sqlite3.connect(self.dbfile)
		self.lockfile = torque_home + "/net/db.lock"
		self.target_hostfile = torque_home+"/virt/"+self.jobid
		self.mempercore = config.get("virt", "mempercore")
		self.disable_libvirt = config.get("virt", "disable_libvirt")
        self.bridge = 'br0' 
        if config.has_option("virt", "bridge"):
            bridge = config.get("virt", "bridge")

## Call this method to configure the job environment and boot a 
## virtual machine, if necessary.
	def run_prologue(self):
		
		try:

			# get imagepath from keyword and resource info:
			imagepath = get_image_path(get_keyword())
	
			# check if the imagepath is for a baremetal session:
			self.check_image(imagepath)
	
			# clone the backing image:
			target = self.clone_image(imagepath,vmrundir+'/'+uuid)
	
			# get free hostname/mac:
			(host,mac) = self.get_host_mac()
	
			# get the number of cpus requested:
			ncpus = self.get_ncpus()
	
			# boot the vm:
			self.boot_vm(uuid,get_memory(int(ncpus)),ncpus,mac,target,
				    get_scratch_disk())
			
			# write the job file:
			self.write_jobfile(self.hostname)
	
			#cleanup and exit:
			finalize()

## Check for any failures, and cleanup if something failed.			
		except PrologueError as detail:
			
			print self.get_output_message()
			print "An error occured in the prologue: ", detail
			print "\n"
			print "Shutting down virtual machines."
			print "You may see some errors below."
			print "They can safely be ignored. \n"
			
			logging.warn(self.get_output_message)
			
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
				c.execute("update reservations set inuse = 0 where hostname=?",
				          [hostname])
				self.conn.commit()
				c.close()
				
			self.release_db_lock()
			sys.exit(1)
			
	
##
## Prologue Class Utility methods

	def get_keyword(self):
		return self.parse_resources('other')

	def get_ncpus():
		ncpus = self.parse_resources('ncpus')
		if ncpus:
			return ncpus
		return '1'
	
	def get_memory(self, num_cpus):
		mempercore = config.getint("virt","mempercore")
		return str( num_cpus * mempercore * 1048)	
		
	def get_scratch_in_gb(self):
		reqfile = self.parse_resources('file').lower()
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
				
	def check_image(self, imagefile):
		if imagefile == None or imagefile == "None":
			#Exit if this is a baremetal session
			self.sessiontype = "baremetal"	
			open(target_hostfile, 'w').close() 
			os.chmod(target_hostfile, 644)
			do_exit()
		
		self.sessiontype = "virtualization"
		
		if not os.path.exists(imagefile):
			raise PrologueError(' Cannot file image file: ' + imagefile)
		
		self.imagefile = imagefile

	def clone_image(self, imagefile, target):
		(ret, out) = commands.getstatusoutput('qemu-img create -b '+
											  imagefile+' -f qcow2 '+
											  target)
		if (ret != 0):
			 raise PrologueError("""Error creating image.  
								 Error message follows: \n""" + out) 
		return target
	

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
	

	def get_host_mac(self):
		self.lock_db()
		c=self.conn.cursor()
		c.execute('select * from reservations where inuse = 0')
	
		try:
			(host,ip,mac,inuse) = c.next()
		except StopIteration:
			raise PrologueError( "no free network slots!" )
	
		# update the db
		c.execute("update reservations set inuse = ? where hostname=?",
				  [jobnum, host])
		conn.commit()
		c.close()	
		self.release_db_lock()	
		self.hostname = host	
		return (host,mac)
	
	def get_scratch_disk(self):
		scratch = None
		requested_scratch = self.get_scratch_in_gb()
		if not requested_scratch:
			if config.has_option("resources", "default_scratch"):
				requested_scratch = int(config.get('resources', 
										'default_scratch').strip())
			else:
				return None
		if config.has_option('resources', 'scratch'):
			scratch = config.get('resources', 'scratch')
			
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
		
		cloned_scratch = self.clone_image(target, 
									 vmrundir+'/'+uuid+'.scratch')
		return cloned_scratch
		

	def boot_vm(self, uuid, mem, ncpus, mac, target, scratch):
		if self.disable_libvirt:
			self.boot_vm_qemu(uuid, mem, ncpus, mac, target, scratch)
		else:
			self.boot_vm_libvirt(create_xml
									(boot_vm_libvirt
										(target, mac,ncpus,mem,scratch)))
	
	def boot_vm_libvirt(xmldesc):
		try:
			lconn = libvirt.open(None)
			dom = lconn.createLinux(xmldesc, 0)
			if dom == None:
				logging.error('Failed to boot VM:\n%s' % (xmldesc))
				raise PrologueError("Failed to boot VM")
			logging.debug('%s' % (dom))
		except Exception, e:
			logging.error('Failed to boot VM\n%s' % (e))
			raise PrologueError("failed to boot VM")
			
	def boot_vm_qemu(self, uuid,mem,ncpus,mac,target,scratch):
		
  	 	optionstring='-name '+uuid+' -m '+mem+' -smp '+ncpus+
					 ' -cpu qemu64 -net nic,macaddr='+mac+
					 ',vlan=0,model=virtio -net tap,ifname='+uuid+
					 ',vlan=0,script=no,downscript=no  -boot c -drive file='+
					 target+',if=ide,bus=0,unit=0,boot=on,format=qcow2 '+
					 '-drive file='+scratch+',if=ide,bus=0,unit=1,'+
					 'format=qcow2 -balloon '+'virtio -nographic -no-acpi '+
					 '-clock unix'	
		(ret, out) = commands.getstatusoutput('/usr/sbin/tunctl -t '+
											  uuid+'>/dev/null')
		if (ret != 0):
			 raise PrologueError("Error creating image: \n" + out) 
		(ret, out) = commands.getstatusoutput('/usr/sbin/brctl addif br0 '+
											  uuid)
		if (ret != 0):
			 raise PrologueError("Error creating image: \n" + out) 
		(ret, out) = commands.getstatusoutput('/sbin/ifconfig '+
		                                      uuid+' up')
		if (ret != 0):
			 raise PrologueError("Error creating image: \n" + out) 
		(ret, out) = commands.getstatusoutput('/usr/libexec/qemu-kvm '+
											  optionstring+'&')
		if (ret != 0):
			 raise PrologueError("Error creating image: \n" + out) 
		return target
   
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
		
	def create_xml(target,mac,ncpus,mem,scratch):
		try:
			t = pyratemp.Template(filename=config.get('templates', 
			                                          'libvirt_xml'),
								  escape=pyratemp.NONE)
			result = t(target=target, mac=mac, ncpus=ncpus, mem=mem, 
				       scratch=scratch, bridge=self.bridge)
		    xmldesc = result.encode("utf-8")
		except TemplateSyntaxError as detail:
			logging.error(detail)
			raise PrologueError("There was a syntax error in your xml",
								detail)
		return xmldesc


	def get_output_message(self):
		try:
			t = pyratemp.Template(filename=config.get('templates', 
			                                          'job_header'),
								  escape=pyratemp.NONE)
			result = t(jobid=self.jobid, userid=self.userid, 
			           requested_resources=self.requested_resources,
			           queue=self.queue, hostname=self.hostname, 
			           sessiontype = self.sessiontype, imagefile=self.imagefile)
		    message = result.encode("utf-8")
		except TemplateSyntaxError as detail:
			logging.error(detail)
			raise PrologueError("There was a syntax error in your job header",
								detail)
		return message

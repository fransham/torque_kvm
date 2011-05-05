#!/usr/bin/env python
################################################################3
#
#  submit filter.  This script takes the user's submit file, and
#  customizes it to pipe it via ssh into the vm.
#  The script reads the user's job file from STDIN, and sends
#  the customzed file to STDOUT.  The output file, when executed
#  as a job, will write the original job to a file, copy that job
#  to the vm, and execute it via ssh
#
#################################################################

import sys

#customize any system defaults you want in here.
system_defaults='''
#PBS -l mem=2048MB
#PBS -l walltime=48:00:00 
#PBS -l nodes=1 
#PBS -l ncpus=1
'''

#get the user's job script from STDIN
data = sys.stdin.readlines()

#print shebang if it's there:
first= data[0]
shell_is_csh = False
if first.startswith('#!'):
	print first
	if (first.startswith('#!/bin/tcsh') or first.startswith('#!/bin/csh')):
		shell_is_csh = True

#next add system defaults
print system_defaults

#the actual job will be contained in userjob.
userjob = []
for line in data:
	#any PBS directives we want to go to STDOUT
	if line.startswith('#PBS'):
		print line,
	#otherwise save it for later
	else:
		userjob.append(line)

#torque environment variables to send to the job
envvars_to_job=("PBS_O_HOST","PBS_O_LOGNAME",
	"PBS_O_HOME","PBS_O_WORKDIR","PBS_ENVIRONMENT",
	"PBS_O_QUEUE","PBS_JOBID", "PBS_JOBNAME",
	"PBS_NODEFILE")

#set the job's target host, script file, and envvars:
if shell_is_csh:
	print 'setenv TARGET_HOST `cat /usr/local/ltda/var/tmp/${PBD_JOBID}`'
	print 'setenv TARGET_SCRIPT /usr/local/ltda/var/tmp/${PBD_JOBID}.job'	
	for var in envvars_to_job:
		print 'echo setenv '+var+' $'+var+' >> $TARGET_SCRIPT'
else:
	print 'export TARGET_HOST=`cat /usr/local/ltda/var/tmp/${PBD_JOBID}`'
	print 'export TARGET_SCRIPT=/usr/local/ltda/var/tmp/${PBD_JOBID}.job'	
	for var in envvars_to_job:
		print 'echo export '+var+'\=$'+var+' >> $TARGET_SCRIPT'
	
#switch to the correct initial directory
print 'echo cd $PBS_O_WORKDIR >> $TARGET_SCRIPT'

#write the user's script to the job file
for line in userjob:
	print 'echo \''+line.replace('\'','\'\\\'\'').rstrip()+'\' >> $TARGET_SCRIPT'

#stall to make sure the VM has come online.  If it's not online after
#5 mins, it's probably not coming up, and the other commands will fail too
#The user will see connection timed out, or no route to host in the
#job log
print 'ssh -o ConnectionAttempts=300 ${TARGET_HOST} "/bin/true"'

#the vm is online now.  Copy the job file.
print 'scp ${TARGET_SCRIPT} ${TARGET_HOST}:/tmp/${PBS_JOBID}'

#make the job file execuable
print 'ssh ${TARGET_HOST} "chmod 755 /tmp/${PBS_JOBID}"'

#run the job!
print 'ssh ${TARGET_HOST} "/tmp/${PBS_JOBID}"'




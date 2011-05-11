#!/bin/tcsh
############################################################
#
#  place this script in /etc/profile.d so that it gets executed
#  on user login.  We're checking if we're in an interactive session
#  if so, then execute the user's job (i.e. boot and 
#  ssh to a virtual machine) and logout when the user exits
#  the VM.
#############################################################


#test if we're in a PBS session:
if ($?PBS_ENVIRONMENT) then

	#if we're not in an interactive session, then exit
	if (${PBS_ENVIRONMENT} == "PBS_INTERACTIVE") then

  	setenv JOBFILE /var/spool/torque/virt/${PBS_JOBID}
  	if ( ! -e ${JOBFILE} ) then
    	echo "No job file present... exiting"
    	exit 1
  	endif
  	setenv TARGET_HOST `cat ${JOBFILE}`
  	if ( ! ($?TARGET_HOST) ) then
    	echo "Cannot find vm host name... exiting"
    	exit 1
  	endif

  	echo "Starting virtual machine... please wait"
   
  	# stall to make sure the VM is online:
  	ssh -o ConnectionAttempts=300 ${TARGET_HOST} "/bin/true"
  	
  	if ( $status ) then
  		echo "VM creation failed... exiting."
  		logout
  	endif

  	echo "VM is ready. Connecting..."
  	echo " "

  	# connect to the VM:
  	ssh -t ${TARGET_HOST} "/bin/bash -i"

  	# exit when we're done.
  	logout
  endif
endif


 

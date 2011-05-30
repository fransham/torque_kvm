#!/bin/bash
############################################################
#
#  place this script in /etc/profile.d so that it gets executed
#  on user login.  We're checking if we're in an interactive session
#  if so, then execute the user's job (i.e. boot and 
#  ssh to a virtual machine) and logout when the user exits
#  the VM.
#############################################################

#if we're not in an interactive session, then exit
if [ "$PBS_ENVIRONMENT" = "PBS_INTERACTIVE" ]; then

  trap '{ echo destroying VM and exiting... ; exit 1; }' INT

  JOBFILE=/var/spool/torque/virt/${PBS_JOBID}
  if [ -f ${JOBFILE} ]; then

  	TARGET_HOST=`cat ${JOBFILE}`
  	if [ -n "$TARGET_HOST" ]; then

  		echo "Starting virtual machine... please wait"

		# get all environment variables:
		for userenv in `env | grep -v -E '^HOSTNAME=|^ENVIRONMENT=|^HOST=|^WORKDIR=|^PWD=|^_=|^TMPDIR=|^TMP=|^SSH_|^DISPLAY='`
			do 
				export ALLENVS=${ALLENVS}' -V '$userenv 
			done
  
  		# stall to make sure the VM is online:
  		ssh -o ConnectionAttempts=300 ${TARGET_HOST} "/bin/true"

  		echo "VM is ready. Connecting..."
  		echo " "

  		# connect to the VM:
  		sshenv ${ALLENVS} -q -t ${TARGET_HOST} "/bin/bash -i"

  		# exit when we're done.
  		exit 0
  # we're running on the baremetal
  	else
		echo "baremetal session started"
  	fi
  fi
fi

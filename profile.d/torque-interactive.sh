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

  TARGET_HOST=`cat /var/spool/torque/virt/${PBS_JOBID}`
  if [ ! -f $TARGET_HOST ]; then
    echo "Cannot find job...  exiting"
    exit 1
  fi

  echo "Connecting to virtual machine... please wait"
  
  # stall to make sure the VM is online:
  ssh -o ConnectionAttempts=300 ${TARGET_HOST} "/bin/true"

  # connect to the VM:
  ssh -t ${TARGET_HOST} "source /tmp/${PBS_JOBID};/bin/bash -i"

  # exit when we're done.
  exit 0
fi

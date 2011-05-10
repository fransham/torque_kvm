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
if [ ! "$PBS_ENVIRONMENT" = "PBS_INTERACTIVE" ]; then
  exit 0	
fi


# trap keyboard interrupt (control-c)
trap control_c SIGINT

# run the user's job:
TORQUE_DIR=/var/spool/torque/mom_priv/jobs
USERJOB=${TORQUE_DIR}/${PBS_JOBID}.SC

if [ ! -f $USERJOB ]; then
  echo "Cannot find job...  exiting"
  exit 1
fi

echo "Connecting to virtual machine... please wait"

sh $USERJOB



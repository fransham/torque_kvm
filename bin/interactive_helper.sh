#!/bin/bash
#######################################################3
#
#  interactive helper:
#  When torque starts an interactive session, the user's
#  job script doesn't get executed by default.  We want
#  to execute the job script, since that's the one that
#  connects to the VM.
#
########################################################

#finish the interactive session.
do_logout(){
  kill -HUP `pgrep -s 0 -o`
}

control_c()
# run if user hits control-c
{
  echo -en "\n*** Exiting Interactive Session ***\n"
  do_logout
}
 
# trap keyboard interrupt (control-c)
trap control_c SIGINT

# run the user's job:
TORQUE_DIR=/var/spool/torque/mom_priv/jobs
USERJOB=${TORQUE_DIR}/${PBS_JOBID}.SC

if [ ! -f $USERJOB ]; then
  echo "Cannot find job...  exiting"
fi

echo "connecting to virtual machine... please wait"

sh $USERJOB

#all done.  kill the interactive session:
do_logout



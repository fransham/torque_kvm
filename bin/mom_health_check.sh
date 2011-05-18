#!/bin/bash
#############################################################
#
#  mom_health_check.sh
#  this script is run by the pbs_mom to make sure it's healthy
#  For our system, we see crashes in libvirtd, so this script
#  checks to make sure libvirtd is running.
#  if it finds that libvirtd is not running, it attempts to 
#  restart it.  If it can't be restarted, it returns an ERROR
#  and we can configure Maui to take the node offline.
#
##############################################################


LIBVIRT_CHECK=`ps  aux | grep libvirtd | grep -v grep | wc -l`

if [ $LIBVIRT_CHECK -lt 2 ]; then
	# libvirt isn't running.  Let's try to restart it:
	/etc/init.d/libvirtd restart
	# sleep 5 seconds to let it come online:
	sleep 5
	# and check if it's running again:
	LIBVIRT_CHECK=`ps  aux | grep libvirtd | grep -v grep | wc -l`
	# send me an e-mail so I can track the frequency:
	echo "bad news..." > /tmp/message
	mail -s "libvirtd crashed" "fransham@slac.stanford.edu" < /tmp/message 
	if [ $LIBVIRT_CHECK -lt 2 ]; then
		#libvirt is really dead.  Report an error
		echo "ERROR libvirt cannot be restarted"		
		mail -s "libvirt cannot be restarted" "fransham@slac.stanford.edu" < /tmp/message 
	fi
fi


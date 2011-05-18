#!/bin/bash

#########################################################
#
#  Installation script for the virtualization extensions
#
#########################################################

# set this parameter for your torque install on the worker node:
export TORQUE_HOME=/var/spool/torque

# nothing below should need to be changed.

SCRIPTDIR=$(cd `dirname $0` && echo `pwd`)

rm -f /etc/torque-kvm.conf
sed  "s#TO_BE_SET_BY_INSTALL_SCRIPT#$TORQUE_HOME#g" $SCRIPTDIR/torque-kvm.conf > /etc/torque-kvm.conf

mkdir -p $TORQUE_HOME/virt
mkdir -p $TORQUE_HOME/net

chmod 1777 $TORQUE_HOME/virt

cp -v $SCRIPTDIR/bin/prologue $TORQUE_HOME/mom_priv/prologue
cp -v $SCRIPTDIR/bin/epilogue $TORQUE_HOME/mom_priv/epilogue
cp -v $SCRIPTDIR/bin/mom_health_check.sh $TORQUE_HOME/mom_priv/mom_health_check.sh
cp -v $SCRIPTDIR/net/initialize $TORQUE_HOME/net/
cp -i -v $SCRIPTDIR/net/network.conf $TORQUE_HOME/net/
cp -v $SCRIPTDIR/profile.d/torque-interactive.* /etc/profile.d/
cp -v $SCRIPTDIR/bin/sshenv /usr/bin/

echo "remember to run TORQUE_HOME/net/initialize to configure your database"


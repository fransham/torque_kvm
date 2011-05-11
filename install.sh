#!/bin/bash

#########################################################
#
#  Installation script for the virtualization extensions
#
#########################################################

SCRIPTDIR=$(cd `dirname $0` && echo `pwd`)

#set this parameter for your torque install on the worker node:
TORQUE_HOME=/var/spool/torque

mkdir -p $TORQUE_HOME/virt
mkdir -p $TORQUE_HOME/net

chmod 1777 $TORQUE_HOME/virt

cp -v $SCRIPTDIR/bin/prologue $TORQUE_HOME/mom_priv/prologue
cp -v $SCRIPTDIR/bin/epilogue $TORQUE_HOME/mom_priv/epilogue
cp -v $SCRIPTDIR/net/initialize $TORQUE_HOME/net/
cp -i -v $SCRIPTDIR/net/network.conf $TORQUE_HOME/net/
cp -v $SCRIPTDIR/profile.d/torque-interactive.* /etc/profile.d/


echo "remember to run TORQUE_HOME/net/initialize to configure your database"


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



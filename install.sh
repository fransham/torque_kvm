#!/bin/bash

#########################################################
#
#  Installation script for the virtualization extensions
#
#########################################################

#set this parameter for your torque install on the worker node:
TORQUE_HOME=/var/spool/torque

mkdir -p $TORQUE_HOME/virt
mkdir -p $TORQUE_HOME/net

chmod 1777 $TORQUE_HOME/virt

cp -v bin/prologue $TORQUE_HOME/virt/prologue
cp -v bin/epilogue $TORQUE_HOME/virt/epilogue
cp -v net/* $TORQUE_HOME/net/

$TORQUE_HOME/net/initialize



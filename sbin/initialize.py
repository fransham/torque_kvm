#!/usr/bin/env python

#####################################################
#
# initialize.py: initializes the database and
# dhcp config based on the network config 
# file in ../etc/network.conf.  If this file
# is not present, please create it with the  
# following format:
#
# #hostname ipaddress macaddress
# vm001 192.168.0.1 AA:AA:AA:BB:CC:DD
#
# make sure there are no jobs running when you run
# this script,  as it could cause them to fail.
################################################# 

#some parameters for your network:
subnetmask="255.255.252.0"
gateway="172.23.128.1"
broadcast="172.23.255.255"
dnsserver="172.23.136.8"

import os
import sqlite3

dirname = os.path.dirname( os.path.abspath(__file__) )
netfile=dirname + "/../etc/network.conf"
dbfile=dirname + "/../var/network.db"
dhcpfile=dirname + "/../etc/dhcpd.entries"

#delete old files
try:
	os.remove(dbfile)
	os.remove(dhcpfile)
except OSError:
	pass

#create the database
conn = sqlite3.connect(dbfile)
c = conn.cursor()
c.execute('''create table reservations
(hostname text, ipaddr text, macaddr text, inuse integer)''')

outfile = open(dhcpfile,'w')

lines = open(netfile, 'r').readlines()
for line in lines:
	if line.startswith(('#',' ')):
		continue
	(hostname, ipaddr, macaddr) = line.rstrip().split(' ')

	#database insertion
	c.execute('insert into reservations values (?,?,?,?)', (hostname, ipaddr, macaddr, 0) )

	#dhcpd.conf include file 
	outfile.write('host '+hostname+" {\n")
	outfile.write(' hardware ethernet '+macaddr+";\n")
	outfile.write(' fixed-address '+ipaddr+";\n")
	outfile.write(' option host-name "'+hostname+"\";\n")
	outfile.write(' option subnet-mask '+subnetmask+";\n")
	outfile.write(' option routers '+gateway+";\n");
	outfile.write(' option broadcast-address '+broadcast+";\n")
	outfile.write(' option domain-name-servers '+dnsserver+";\n")
	outfile.write("}\n")	

conn.commit()
c.close()
outfile.close()
	





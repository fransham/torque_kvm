#!/usr/bin/env python

host = '172.23.136.8'
port = 12345

import socket
import sys

def combine_args(arglist):
	output = ''
	for arg in arglist:
		output += arg + ' '
	return output

def main(argv):
	message = combine_args(argv[1:])
	sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	sock.connect((host, port))
	sock.send(message)
	data = sock.recv(1024)	
	sock.close()
	print repr(data)
	
if __name__ == '__main__':
	main(sys.argv)

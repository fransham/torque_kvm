#!/usr/bin/env python

## tracejob_xinetd.py
## this is a small wrapper to enable remote users to query tracejob
## to get torque job results.

import sys
import commands

def main():
	tjinput = sys.stdin.readline().strip()
	(ret, out) = commands.getstatusoutput('/usr/bin/tracejob '+tjinput)
	if (ret != 0):
		print out

if __name__ == "__main__":
	main()

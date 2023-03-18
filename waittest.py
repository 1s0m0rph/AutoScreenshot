#!/bin/python3
"""
testing cpu usage during wait() calls

CONCLUSION: cpu usage is essentially zero. running this with top -d 0.5 -p <this's PID> results in a total uptime of 30.01 seconds. cpu usage shows consistently as zero while running. we should be safe to use this method over long periods of time
"""

from random import choice
from time import sleep, time

for _ in range(6):
	
	# do a bunch of stuff for 5 seconds
	active_cycle_start = time()
	while time() < active_cycle_start + 5:
		choice([1,2,3,4,5,6,7,8,9,0])
	
	# wait for 5 seconds
	sleep(5)

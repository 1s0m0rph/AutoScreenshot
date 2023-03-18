#!/bin/python3

from mss import mss
from time import gmtime, sleep
from datetime import datetime, timedelta
from os.path import isdir
from os import listdir, makedirs
import random
import logging
import logging.config
import re

SCREENSHOTS_DIR = "/home/isomorph/AutoSS/"	# where are the screenshots saved?
LOGFILE_NAME = "AutoSSLog.log"
MIN_INTERVAL = timedelta(days=1)				# min time between screenshots
MAX_INTERVAL = timedelta(days=7)				# max time between screenshots (approx)
MIN_UPTIME_BEFORE_SHOT = timedelta(minutes=5)	# minimum running time before taking a screenshot. overrides max interval

# make our dir if it doesn't already exist
ss_dir_had_to_be_made = False
if not isdir(SCREENSHOTS_DIR):
	# make it
	makedirs(SCREENSHOTS_DIR)
	ss_dir_had_to_be_made = True

# set up logging
logging.basicConfig(filename=SCREENSHOTS_DIR + LOGFILE_NAME,
                    encoding='utf-8',
                    level=logging.DEBUG,
                    format='%(asctime)s, %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S %Z')

                    
if ss_dir_had_to_be_made:
	logging.warning("Screenshot dir did not exist prior to startup. Created directory " + SCREENSHOTS_DIR)
	
logging.info("Auto-screenshot script started.")
# record start time
script_start_time = datetime.now()

def gen_filename():
	"""
	generate the filename for a screenshot created right now. adding precise times ensures unique file names
	"""
	# format (e.g.): AUTO_SS_2023-03-18_111004_123456.png
	d8 = datetime.now()
	year = d8.year
	month = f'{d8.month:02}'
	day = f'{d8.day:02}'
	hour = f'{d8.hour:02}'
	minute = f'{d8.minute:02}'
	second = f'{d8.second:02}'
	microsecond = f'{d8.microsecond:06}'
	return SCREENSHOTS_DIR + "AUTO_SS_{}-{}-{}_{}{}{}_{}.png".format(year, month, day, hour, minute, second, microsecond)

def take_ss():
	"""
	take a screenshot using mss
	
	NOTE: if this gives you problems you may need to switch from wayland to xorg
	"""
	filename = gen_filename()
	logging.info("Taking screenshot " + filename)
	with mss() as sct:
		sct.shot(mon=-1,output=gen_filename())

def most_recent_ss_time():
	"""
	get the time of the most recent screenshot
	"""
	most_recent = datetime(1,1,1,0,0,0,0)
	# screenshots dir must exist by now
	# special case: it's empty
	dir_contents = listdir(SCREENSHOTS_DIR)
	if len(dir_contents) == 0:
		return most_recent
	# special case 2: only have a logfile
	if (len(dir_contents) == 1) and (dir_contents[0] == LOGFILE_NAME):
		return most_recent
	
	# otherwise there should be at least one screenshot here
	for f in dir_contents:
		rem = re.match(r"AUTO_SS_([0-9]+)-([0-9]{2})-([0-9]{2})_([0-9]{2})([0-9]{2})([0-9]{2})_([0-9]{6}).png",f)
		if rem:
			yr = int(rem.group(1))
			mo = int(rem.group(2))
			dy = int(rem.group(3))
			hr = int(rem.group(4))
			mi = int(rem.group(5))
			sc = int(rem.group(6))
			us = int(rem.group(7))
			dt_this = datetime(yr,mo,dy,hr,mi,sc,us)
			if dt_this > most_recent:
				most_recent = dt_this
	
	return most_recent

def gen_ss_delay(min_delay,max_delay):
	return random.uniform(min_delay,max_delay)

# perform initialization actions
# first figure out what the most recent screenshot is -- initial special case
most_recent_ss = most_recent_ss_time()

# figure out how long it's been since then
time_since_most_recent_ss = datetime.now() - most_recent_ss

# figure out when the first screenshot will be
time_until_next_ss = 0.0 # seconds -- input to sleep()
# a few cases here:
# case 1: we've passed the max interval
if time_since_most_recent_ss > MAX_INTERVAL:
	# delay the minimum time
	logging.debug("Initial screenshot: case 1 (max interval passed at script init)")
	time_until_next_ss = MIN_UPTIME_BEFORE_SHOT.total_seconds()

# case 2: we haven't massed the max, but if we wait for uptime we will (i.e. now + min uptime > most recent + max interval)
elif (script_start_time + MIN_UPTIME_BEFORE_SHOT) > (most_recent_ss + MAX_INTERVAL):
	# delay the minimum time
	logging.debug("Initial screenshot: case 2 (not past max yet, but waiting for uptime will pass it)")
	time_until_next_ss = MIN_UPTIME_BEFORE_SHOT.total_seconds()

# case 3: we haven't passed the max, and if we wait for the min uptime we still won't pass the max, but will pass the min
elif (most_recent_ss + MIN_INTERVAL) < (script_start_time + MIN_UPTIME_BEFORE_SHOT):
	# treat min uptime as the new min interval
	logging.debug("Initial screenshot: case 3 (not past max, but waiting for uptime will pass min)")
	time_until_next_ss = gen_ss_delay(MIN_UPTIME_BEFORE_SHOT.total_seconds(),MAX_INTERVAL.total_seconds())

# case 4: if we wait the min uptime we won't pass the min time between shots OR the max time
else:
	logging.debug("Initial screenshot: case 4 (not past max, and waiting for uptime will not pass min)")
	time_until_next_ss = gen_ss_delay(MIN_INTERVAL.total_seconds(), MAX_INTERVAL.total_seconds())

# begin initial delay
logging.info("Beginning initial delay. Next screenshot will occur at {} (delay = {} sec)".format((script_start_time + timedelta(seconds=time_until_next_ss)), time_until_next_ss))

# start loop
while True:
	# delay
	sleep(time_until_next_ss)
	# take screenshot
	take_ss()
	# calculate new delay
	time_until_next_ss = gen_ss_delay(MIN_INTERVAL.total_seconds(), MAX_INTERVAL.total_seconds())
	# log next ss time
	logging.info("Next screenshot at {} (delay = {} sec)".format(datetime.now() + timedelta(seconds=time_until_next_ss), time_until_next_ss))

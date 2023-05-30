#!python

from mss import mss
from time import gmtime, sleep
from datetime import datetime, timedelta
from os.path import isdir, isfile
from os import listdir, makedirs
from configparser import ConfigParser
import random
import logging
import logging.config
import re

# ------------------------ do not edit above this line ---------------------------
# change this dir if you move the config file location
PATH_TO_CONFIG = r'./auto_ss.ini'
# ------------------------ do not edit below this line ---------------------------

# set default logging settings in case there are any problems with setting up configs
logger = logging.getLogger(__name__)
log_formatter = logging.Formatter(fmt = '%(asctime)s, %(levelname)s: %(message)s', datefmt = '%Y-%m-%d %H:%M:%S %Z')
log_init_err_handler = logging.FileHandler('./AUTO_SS_ERRORS.log')
log_init_err_handler.setFormatter(log_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(log_init_err_handler)


# parse the config file
REQUIRED_CFG_STUCTURE = {
	'DEBUG':{},
	'LOGGING':{},
	'TIMING':{},
	'DIRECTORIES':{
		'PathToLogFile',
		'PathToScreenshotsDir'
	}
}
# verify config file exists first
if not isfile(PATH_TO_CONFIG):
	logger.critical("Cannot find config file {}.".format(PATH_TO_CONFIG))
	exit(1)
# set up parser
cfgparse = ConfigParser()
cfgparse.read(PATH_TO_CONFIG)
# verify correct structure
config_file_fields_all_present = True
for sect in REQUIRED_CFG_STUCTURE:
	if sect not in cfgparse:
		logger.critical("Required section {} not found in config file {}.".format(sect,PATH_TO_CONFIG))
		config_file_fields_all_present = False
	else:
		for key in REQUIRED_CFG_STUCTURE[sect]:
			if key not in cfgparse[sect]:
				logger.critical("Required key {} not found in config file ({}) section {}.".format(key,PATH_TO_CONFIG,sect))
				config_file_fields_all_present = False

if not config_file_fields_all_present:
	logger.critical("Config file incomplete. Cannot start execution")
	exit(1)

# read the parsed data
# DEBUG
DEBUG_TIMES = cfgparse['DEBUG'].getboolean('UseDebugTiming',fallback=False)
# LOGGING
parsed_loglevel = cfgparse['LOGGING'].get('LogLevel',fallback='info')
LOGGING_LEVEL = logging.INFO
if 'info' == parsed_loglevel:
	LOGGING_LEVEL = logging.INFO
elif 'debug' == parsed_loglevel:
	LOGGING_LEVEL = logging.DEBUG
elif 'warning' == parsed_loglevel:
	LOGGING_LEVEL = logging.WARNING
elif 'error' == parsed_loglevel:
	LOGGING_LEVEL = logging.ERROR
elif 'critical' == parsed_loglevel:
	LOGGING_LEVEL = logging.CRITICAL
else:
	logger.error("Unknown log level specification: {}. Defaulting to INFO".format(parsed_loglevel))
# DIRECTORIES
PATH_TO_LOGFILE = cfgparse['DIRECTORIES']['PathToLogFile']
SCREENSHOTS_DIR = cfgparse['DIRECTORIES']['PathToScreenshotsDir']
if '/' != SCREENSHOTS_DIR[-1]:
	SCREENSHOTS_DIR += '/'
# TIMING
MIN_INTERVAL = timedelta(seconds=cfgparse['TIMING'].getfloat('MinTimeBetweenScreenshotsSec',fallback=86400))
MAX_INTERVAL = timedelta(seconds=cfgparse['TIMING'].getfloat('MaxTimeBetweenScreenshotsSec',fallback=604800))
MIN_UPTIME_BEFORE_SHOT = timedelta(seconds=cfgparse['TIMING'].getfloat('MinUptimeBeforeShotSec',fallback=300))
CHECK_SCHEDULE_INTERVAL = timedelta(seconds=cfgparse['TIMING'].getfloat('TimeBetweenScheduleChecksSec',fallback=3600))
	
if DEBUG_TIMES:
	MIN_INTERVAL = timedelta(seconds=10)
	MAX_INTERVAL = timedelta(seconds=60)
	MIN_UPTIME_BEFORE_SHOT = timedelta(seconds=30)
	CHECK_SCHEDULE_INTERVAL = timedelta(seconds=5)

# set up logging
logger.removeHandler(log_init_err_handler)
log_handler = logging.FileHandler(PATH_TO_LOGFILE)
log_handler.setFormatter(log_formatter)
logger.setLevel(LOGGING_LEVEL)
logger.addHandler(log_handler)

# make screenshots dir if it didn't exist already
if not isdir(SCREENSHOTS_DIR):
	# make it
	makedirs(SCREENSHOTS_DIR)
	logger.warning("Screenshot dir did not exist prior to startup. Created directory " + SCREENSHOTS_DIR)

logger.info("Auto-screenshot script initialized.")
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
	logger.info("Taking screenshot " + filename)
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

def gen_ss_delay(min_delay:timedelta,max_delay:timedelta):
	return timedelta(seconds=random.uniform(min_delay.total_seconds(), max_delay.total_seconds()))
	
def get_startup_shot_time():
	"""
	handles the 'startup shot' timing which is done when the script starts running
	"""
	# first figure out what the most recent screenshot is -- initial special case
	most_recent_ss = most_recent_ss_time()

	# figure out how long it's been since then
	time_since_most_recent_ss = datetime.now() - most_recent_ss
	
	# figure out how long we're actually allowed to delay (if we want the max gap between shots to be MAX_INTERVAL, then we can't necessarily delay MAX_INTERVAL from right now)
	max_allowable_delay = max(MIN_UPTIME_BEFORE_SHOT, MAX_INTERVAL - time_since_most_recent_ss)
	
	# figure out the smallest amount of time we're allowed to delay
	min_allowable_delay = max(MIN_UPTIME_BEFORE_SHOT, MIN_INTERVAL - time_since_most_recent_ss)
	
	# (b)log it
	logger.debug("Initial screenshot. Minimum delay is {}. Maximum delay is {}.".format(min_allowable_delay,max_allowable_delay))
	
	# generate the delay
	return gen_ss_delay(min_allowable_delay, max_allowable_delay)

def exe_check_delay(time_until_next):
	"""
	release CPU until the next time we need to check the schedfile
	"""
	if time_until_next <= CHECK_SCHEDULE_INTERVAL:
		logger.debug("Next screenshot occurs before the check interval is up, delaying exact amount.")
		sleep(time_until_next.total_seconds())
	else:
		logger.debug("Next screenshot occurs after the check interval is up, delaying for the check interval")
		sleep(CHECK_SCHEDULE_INTERVAL.total_seconds())

def check_perform_ss(scheduled_time):
	"""
	check if it's time to take a shot (do so if it is) and return the time for the next shot and whether we took a shot
	"""
	
	# for efficiency and consistency, record a universal "now"
	time_now = datetime.now()
	remain_time = scheduled_time - time_now
	# case 1: the timer is expired
	if remain_time <= timedelta(0):
		# case 1a: we expired very recently (we likely WEREN'T interrupted by computer sleep)
		if abs(remain_time) < CHECK_SCHEDULE_INTERVAL:
			# take the shot now
			take_ss()
			# generate a new time
			return time_now + gen_ss_delay(MIN_INTERVAL, MAX_INTERVAL), True
		# case 1b: we expired but it was a while ago (we likely WERE interrupted by computer sleep)
		else:
			logger.debug("Detected timer overrun (presumably due to a computer sleep), delaying minimum amount.")
			# take no shot, and delay the minimum amount
			return time_now + MIN_UPTIME_BEFORE_SHOT, False
	else:
		# nothing to do, keep with the current time
		return scheduled_time, False
			
		

# ready initial screenshot delay (get time until and start the first delay)
time_until_next = get_startup_shot_time()
time_to_perform_next = datetime.now() + time_until_next # important distinction here -- since this is a real time it can tell us if we've overrun the timer
logger.info("Beginning initial delay. Next screenshot scheduled for {} (delay = {}).".format(time_to_perform_next,time_until_next))

try:
	# start loop
	while True:
		# delay
		exe_check_delay(time_until_next)
		# for evaluation purposes, record cycle time
		cycle_start_time = datetime.now()
		# check if we need to take a shot, and record when we take the next one
		time_to_perform_next,shot_taken_this_cycle = check_perform_ss(time_to_perform_next)
		time_until_next = time_to_perform_next - datetime.now()
		# log next ss time
		if shot_taken_this_cycle:
			logger.info("Next screeshot scheduled for {} (delay = {})".format(time_to_perform_next, time_until_next))
		cycle_end_time = datetime.now()
except BaseException as e:
	if (SystemExit == type(e)) and ("0" == str(e)):
		# not an error, exit normally
		exit(0)

	logger.critical(f"Caught unhandled exception during runtime: {type(e).__name__}: {e}.")

	# reraise exception after catching -- we just wanted a record of it
	raise e

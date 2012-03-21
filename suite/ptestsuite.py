#!/usr/bin/python3


import sys
import os
import time
import csv
import numpy
import math
import threading
import configparser
import subprocess

monitors = {}
monitor_data = {}
recording = False

tests = {}

# pseudo classes to create a struct like behavior, see 'parse_testsuite' for members of this classes
class testsuite:
	blub = ''
class testprofile:
	name = ''

verbose = True
def vprint(arg):
	if verbose:
		print(arg)

# load all available python files from the monitors directory
def monitors_load():
	global monitors
	global monitor_data
	monitor_dir = os.path.join(os.getcwd(), 'monitors')
	sys.path.insert(0, monitor_dir)
	vprint("MONITOR: Loading modules")
	for i in os.listdir(monitor_dir):
		path = os.path.join(monitor_dir, i)
		if not os.path.isfile(path) or i[-3:] != '.py':
			continue
		modname = i[:-3]
		vprint("MONITOR: Detected " + modname)
		monitors[modname] = __import__(modname)
		monitor_data[modname] = []

def monitors_write_headers(tgtdir):
	tgtdir = os.path.join(tgtdir, 'monitors')
	for k,v in monitors.items():
		monitor_file = os.path.join(tgtdir, k)
		f = open(monitor_file, 'a')
		c = csv.writer(f, delimiter=',')
		c.writerow(['time_s'] + v.get_hdr())
		f.close()


# function for the monitoring thread. The thread iterates through all detected
# monitors and gets the values for each of them as an array of values.
# At the beginning all monitors get one 'pre' call to prepare the first reading.
# We delay the write of the data to get as clean readings as possible (no IO).
# A float timestamp is prepended to every value array received from a monitor.
def monitors_proc():
	global recording
	global monitor_data
	start_time = time.time()
	for k,v in monitors.items():
		v.pre()
	end_time = time.time()
	remain_wait = 1.0 - (end_time - start_time)
	if remain_wait > 0:
		time.sleep(remain_wait)

	while recording:
		start_time = time.time()
		for k,v in monitors.items():
			current = []
			if not k in monitor_data:
				monitor_data[k] = []
			current = v.get()
			monitor_data[k].append([time.time()] + current)

		# calculate the time we needed to process all monitors and try to sleep the remaining time
		end_time = time.time()
		remain = 1.0 - (end_time - start_time)
		if remain > 0.0:
			time.sleep(remain)
	for k,v in monitors.items():
		v.post()

# stop the monitor thread and write the collected data to disk.
def monitors_stop(tgtdir):
	global monitor_data
	global recording
	recording = False
	time.sleep(2)
	for k,v in monitor_data.items():
		tgtfile = os.path.join(tgtdir, k)
		f = open(tgtfile, "a")
		c = csv.writer(f, delimiter=',')
		for i in v:
			c.writerow(i)
		f.close()
	monitor_data = {}

# wrapper class to start a thread that calls the monitors_proc function
class monitor_process():
	def __call__(bla):
		monitors_proc()

# fork a thread for the monitor
def monitors_start():
	global recording
	recording = True
	threading.Thread(target=monitor_process()).start()

# Run a test and prepend the timestamp to the results. This also starts the monitors.
def test_run(test, result_path):
	monitor_dir = os.path.join(result_path, 'monitors')
	if os.path.exists(test.pre_cmd[0]):
		subprocess.call(test.pre_cmd[:])
	monitors_start()
	# wait two second to be sure that all monitors recorded their first values before the
	# test starts running
	time.sleep(2)
	starttime = time.time()
	p = subprocess.Popen(test.cmd[:], stdout=subprocess.PIPE)
	p.wait()
	monitors_stop(monitor_dir)
	values = p.stdout.read().decode().strip().split(',')
	if os.path.exists(test.post_cmd[0]):
		subprocess.call(test.post_cmd[:])
	return (starttime, [float(i) for i in values])

# calculate the standard error, not standard deviation
def calc_stderr(values):
	return math.sqrt(numpy.var(values)) / math.sqrt(float(len(values)))

# Run and repeat a test until the desired standard error is reached for all values,
# or the number of runs exceed max_runs. The test runs at least min_runs times.
def test(test, path):
	vprint('')
	vprint('Test ' + test.name + ' min_runs ' + str(test.min_runs) + ' max_runs ' + str(test.max_runs) + ' max_err ' + str(test.stderr))
	vprint('Cmd: ' + ' '.join(test.cmd))
#perhaps read the old values before to continue calculation
	values = []
	value_lines = None
	result_path = os.path.join(path, test.name)
	if not os.path.exists(result_path):
		os.mkdir(result_path)
	max_stderr = 0
	runs = 0
	
	f = open(os.path.join(result_path, 'results'), 'w')
	c = csv.writer(f, delimiter=',')
	vprint('cd ' + test.directory)
	os.chdir(test.directory)
	hdr = None
	if os.path.exists(test.hdr_cmd[0]):
		p = subprocess.Popen(test.hdr_cmd[:], stdout=subprocess.PIPE)
		p.wait()
		hdr = p.stdout.read().decode().strip().split(',')
		c.writerow(['time_s'] + hdr)
	
	monitor_dir = os.path.join(result_path, 'monitors')
	if not os.path.exists(monitor_dir):
		os.mkdir(monitor_dir)
	monitors_write_headers(result_path)
	while True:
		starttime, run = test_run(test, result_path)
		values.append(run)
		if value_lines == None:
			value_lines = []
			for n in range(0, len(run)):
				value_lines.append([])
		for n in range(0, len(run)):
			value_lines[n].append(run[n])
		runs += 1
		vprint("Values: " + ' '.join([str(run_item) for run_item in run]))
		c.writerow([starttime] + run)
		if runs < test.min_runs:
			continue
		if runs > test.max_runs:
			break
		errors_ok = True
		for i in value_lines:
			mean = sum(i) / float(len(i))
			stderr = calc_stderr(i)
			if mean * test.stderr < stderr:
				vprint("Needed stderror: " + str(mean * test.stderr) + " is: " + str(stderr))
				errors_ok = False
				break
		if errors_ok:
			break
	f.close()
	result = [sum(i) / len(i) for i in value_lines]
	result_errors = [calc_stderr(i) for i in value_lines]
	vprint('Test ' + test.name)
	vprint('Results ' + ', '.join([str(i) for i in result]))
	vprint('Errors  ' + ', '.join([str(i) for i in result_errors]))
	return (hdr, result[:], result_errors[:])

# run all tests defined in a testsuite.
def testsuite_run(testsuite, runname, path):
	runpath = os.path.join(os.path.join(path, 'results'), runname)
	if not os.path.exists(runpath):
		os.mkdir(runpath)
	summarypath = os.path.join(runpath, 'summary')
	c = csv.writer(open(summarypath, 'a'), delimiter=',')
	for i in testsuite.tests:
		hdr, result, resulte = test(i, runpath)
		hdr = ['name'] + hdr
		c.writerow(hdr)
		row = [i.name]
		for n in range(0, len(result)):
			row.append(result[n])
			row.append(resulte[n])
		c.writerow(row)

# parse a testsuite configuration file.
def parse_testsuite(tests_path, path):
	conf = configparser.RawConfigParser()
	conf.read(path)
	min_runs = 3
	max_runs = 10
	stderr = 5.0
	suite = testsuite()
	suite.tests = []

	if conf.has_section('general'):
		if conf.has_option('general', 'min_runs'):
			min_runs = int(conf.get('general', 'min_runs'))
		if conf.has_option('general', 'max_runs'):
			max_runs = int(conf.get('general', 'max_runs'))
		if conf.has_option('general', 'stderr'):
			stderr = float(conf.get('general', 'stderr'))
	for section in conf.sections():
		if section == 'general':
			continue
		test = testprofile()
		test.min_runs = min_runs
		test.max_runs = max_runs
		test.stderr = stderr
		test.name = section[:]
		test.cmd = ['./run']
		test.pre_cmd = ['./pre']
		test.post_cmd = ['./post']
		test.hdr_cmd = ['./hdr']
		test.directory = test.name
		for k,v in conf.items(section):
			if k == 'min_runs':
				test.min_runs = max(test.min_runs, int(v))
			elif k == 'max_runs':
				test.max_runs = min(test.max_runs, int(v))
			elif k == 'test':
				test.directory = v
			elif k == 'args':
				test.cmd += v.strip().split(',')
			elif k == 'pre_args':
				test.pre_cmd += v.strip().split(',')
			elif k == 'post_args':
				test.post_cmd += v.strip().split(',')
		test.directory = os.path.join(tests_path, test.directory)
		settingsdir = os.path.join(test.directory, 'config')
		# yes, we might read the config file of a test multiple times
		# but this is no performance critical part
		if os.path.exists(settingsdir):
			settings = configparser.RawConfigParser()
			settings.read(settingsdir)
			for k,v in conf.items('general'):
				if k == 'min_runs':
					test.min_runs = max(test.min_runs, int(v))
				elif k == 'pre_args':
					if len(test.pre_cmd) == 1:
						test.pre_cmd += v.strip().split(',')
				elif k == 'post_args':
					if len(test.post_cmd) == 1:
						test.post_cmd += v.strip().split(',')
				elif k == 'args':
					if len(test.cmd) == 1:
						test.cmd += v.strip().split(',')
				elif k == 'max_runs':
					test.max_runs = min(test.max_runs, int(v))
		test.hdr_cmd += test.cmd[1:]
		if test.min_runs > test.max_runs:
			test.min_runs = test.max_runs
		suite.tests.append(test)

	return suite
if len(sys.argv) < 3:
	print("USAGE: <TESTSUITE> <RUNNAME>")
	sys.exit(1)
monitors_load()
base = os.getcwd()
suites = os.path.join(base, 'testsuites')
testsuitepath = os.path.join(suites, sys.argv[1])
suite = parse_testsuite(os.path.join(base, 'tests'), testsuitepath)
testsuite_run(suite, sys.argv[2], base)

#!/usr/bin/python3

import sys
import os
import time
import configparser
import subprocess

ssh_cmd = ['ssh']

verbose = True

def vprint(output):
	if (verbose):
		print(output)

# try to read a config item or set a default value
def conf_default(config, section, option, default=None):
	if config.has_option(section, option):
		return config.get(section, option)
	return default

# try to read a config item as command, so the value is transformed into a list
def conf_default_cmd(config, section, option, default=None):
	result = conf_default(config, section, option, default)
	if result != None:
		result = result.split(',')
	return result

# execute a command. Depending of the configuration, the command is executed on
# the local machine or on a remote host if ssh is set.
def execute_cmd(cmd, sleep=0, ssh=None, ssh_option=None):
	if cmd == None:
		return 0
	vprint('cmd ' + ' '.join(cmd))
	if ssh == None:
		status = subprocess.call(cmd)
	else:
		if ssh_option == None:
			ssh_option = []
		# we pass the command to ssh in one argument
		cmd = ssh_cmd[:] + [ssh] + ssh_option + [' '.join(cmd)]
		status = subprocess.call(cmd)
	time.sleep(sleep)
	return status

# execute a testsuite with given settings. version is used to identify the
# testsuite execution. This also parses the config file
def run_settings(base, setting, version):
	vprint('run settings ' + base + ' ' + setting + ' ' + version)
	conf = configparser.RawConfigParser()
	configpath = os.path.join(os.path.join(base, 'testsettings'), setting)
	vprint(configpath)
	conf.read(configpath)
	writeback = conf_default(conf, 'general', 'writeback_results', 0) == 1

	for sec in conf.sections():
		vprint(sec)
		if (sec == 'general'):
			continue
		ssh = conf_default(conf, sec, 'ssh_host', None)
		ssh_option = conf_default_cmd(conf, sec, 'ssh_options', None)
		setup_cmd = conf_default_cmd(conf, sec, 'setup_cmd', None)
		pre_cmd = conf_default_cmd(conf, sec, 'pre_cmd', None)
		post_cmd = conf_default_cmd(conf, sec, 'post_cmd', None)
		testsuite_path = conf_default(conf, sec, 'testsuite_path', None)
		if testsuite_path == None:
			vprint('ERROR: section ' + sec + ' has no testsuite_path, aborting')
			return
		working_dir = conf_default(conf, sec, 'working_dir', '/tmp')
		sleep = int(conf_default(conf, sec, 'sleep_between', 0))
		testsuites = conf_default_cmd(conf, sec, 'testsuites', None)
		execute_cmd(setup_cmd, sleep, ssh, ssh_option)
		execute_cmd(pre_cmd, sleep, ssh, ssh_option)
		for suite in testsuites:
			vprint('executing testsuite ' + suite)
			now_str = time.strftime('%Y-%m-%d-%H-%M-%S')
			test_identifier = setting + '_' + version + '_' + now_str
			cmd = []
			if ssh == None:
				os.chdir(working_dir)
				cmd = [testsuite_path, suite, test_identifier]
			else:
				cmd = ['cd', working_dir, '&&', testsuite_path, suite, test_identifier]
			execute_cmd(cmd, 0, ssh, ssh_option)
		execute_cmd(post_cmd, sleep, ssh, ssh_option)


if len(sys.argv) < 2:
	print('USAGE: <TESTSETTING>:<VERSION> [...]')
	sys.exit(0)
base = os.getcwd()
for i in sys.argv[1:]:
	vprint(i)
	runid = i.split(':')
	if len(runid) != 2:
		print('ERROR in "' + i + '", version part of runid is missing')
		print('Continuing with the next one')
		continue
	run_settings(base, runid[0], runid[1])


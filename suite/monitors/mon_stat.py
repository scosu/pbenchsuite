#!/usr/bin/python3

import os

init = None
hdrs = ['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq',
		'steal', 'guest', 'guest_nice',
		'contextswitches', 'processes', 'processes_running',
		'processes_blocked']

def check_requirements():
	if not os.path.isfile('/proc/stat'):
		return ['/proc/stat']
	return []
def install():
	return True

def collect_data(cumulative_only=False):
	f = open('/proc/stat', 'r')
	lines = f.read().splitlines()
	f.close()
	results = [int(i) for i in lines[0].split()[1:]]
	for i in lines:
		if i.startswith('ctxt'):
			results.append(int(i.split()[1]))
		elif i.startswith('processes'):
			results.append(int(i.split()[1]))
		elif not cumulative_only:
			if i.startswith('procs_running'):
				results.append(int(i.split()[1]))
			elif i.startswith('procs_blocked'):
				results.append(int(i.split()[1]))
	return results

def to_dict():
	return {'name': 'System Stat Monitor',
		'description': 'Monitors the /proc/stat file, currently especially for scheduling values'}

def pre():
	global init
	init = collect_data(cumulative_only = True)
	return 0

def get():
	results = collect_data()
	for i in range(0, len(init)):
		results[i] -= init[i]
	jsonr = {}
	for i in range(0, len(init)):
		jsonr[hdrs[i]] = results[i]
	return jsonr

def post():
	return 0


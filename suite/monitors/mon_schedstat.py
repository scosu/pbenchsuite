#!/usr/bin/python3

init = None

def check_requirements():
	if not os.path.isfile('/proc/schedstat'):
		print("ERROR: can't find /proc/schedstat, please use a kernel with scheduer statistics support")
		return ['/proc/schedstat']
	return []
def install():
	return True

def collect_data():
	results = None
	f = open('/proc/schedstat', 'r')
	dat = f.read().splitlines()
	f.close()
	for i in dat:
		if i.startswith('cpu'):
			cpu = i.split()[1:]
			if results == None:
				results = [int(n) for n in cpu]
			else:
				results = [results[n] + int(cpu[n]) for n in range(0, len(cpu))]
	return results

def pre():
	global init
	init = collect_data()
	return

def post():
	return
def get():
	results = collect_data()
	return [results[i] - init[i] for i in range(0, len(init))]

def get_hdr():
	return ['yields', 'expired_depr', 'sched_requests', 'sched_idle', 'ttwus', 'ttwu_cpu', 'time_running', 'time_waiting', 'timeslices']

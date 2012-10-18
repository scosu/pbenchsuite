#!/usr/bin/python3

import time

def check_requirements():
	return []
def install():
	return 0
def pre():
	return 0

def post():
	return 0
def to_dict():
	return {'name': 'Scheduler Latency Monitor',
		'description': 'Measures the latency of sleeping. It sleeps 0.25s and measures the deviation from the desired sleep time.'}

def get():
	start_time = time.time()
	time.sleep(0.25)
	end_time = time.time()
	return {'value': end_time - start_time - 0.25,
		'unit': 's'}


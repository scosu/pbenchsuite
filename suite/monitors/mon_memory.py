#!/usr/bin/python3
import re
import os

def check_requirements():
	if not os.path.isfile('/proc/meminfo'):
		return ['/proc/meminfo']
	return []

def install():
	return 0

def pre():
	return 0
def post():
	return 0
def to_dict():
	return {
		'name': 'Memory monitor',
		'description': 'Reads /proc/meminfo'}

def get():
	f = open('/proc/meminfo', 'r')
	cont = f.read().splitlines()
	f.close()
	result = {}
	for i in cont:
		match = re.match("^(\S*):\s*([0-9]+)\s*(\S*)\s*", i)
		if (match != None):
			result[match.group(1)] = {
				'value': int(match.group(2)),
				'unit': match.group(3)}
	return result

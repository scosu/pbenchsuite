#!/usr/bin/python3
import re
import os

def check_requirements():
	if not os.path.isfile('/proc/meminfo'):
		return ['/proc/meminfo']
	return []

def install():
	return True

def pre():
	return
def post():
	return
def get_hdr():
	f = open('/proc/meminfo', 'r')
	cont = f.read().splitlines()
	f.close()
	result = []
	for i in cont:
		m = re.match("^(\S*):\s*[0-9]+\s*(\S*)", i)
		hdr = m.group(1)
		if m.group(2) != '':
			hdr += '_' + m.group(2)
		result.append(hdr)
	return result

def get():
	f = open('/proc/meminfo', 'r')
	cont = f.read().splitlines()
	f.close()
	result = []
	for i in cont:
		match = re.match("^\S*\s*([0-9]+)\s*\S*", i)
		if (match == None):
			result.append(0)
		else:
			result.append(int(match.group(1)));
	return result

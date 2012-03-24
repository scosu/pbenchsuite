#!/usr/bin/python3

import time

def pre():
	return

def post():
	return
def get_hdr():
	return ['Latency_s']
def get():
	start_time = time.time()
	time.sleep(0.25)
	end_time = time.time()
	return [end_time - start_time - 0.25]


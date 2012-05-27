#!/usr/bin/python2

import argparse
import sys
import os

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--plotter', help='Plotter to plot the given data. For multiple plotters, add multiple -p arguments', dest='plotters', metavar='PLOTTER', action='append')
parser.add_argument('tgt', help='Where to put the generated charts', nargs=1)
parser.add_argument('path', help='Pathes to files you want to plot', nargs='+')
parsed = parser.parse_args()

sys.path.insert(0, 'plotters')
plotters = []
if parsed.plotters == None:
	try:
		plotters.append(('generic_plotter', __import__('generic_plotter')))
	except:
		print("Error: Couldn't find plotter " + i)
		sys.exit(-1)
else:
	for i in parsed.plotters:
		try:
			plotters.append((i, __import__(i)))
		except:
			print("Error: Couldn't find plotter " + i)
			sys.exit(-1)
tgt = os.path.expanduser(parsed.tgt[0])
if not os.path.exists(tgt):
	os.mkdir(tgt)

for i in plotters:
	t = os.path.join(tgt, i[0])
	if not os.path.exists(t):
		os.mkdir(t)
	try:
		i[1].plot_pathes(parsed.path, t)
	except:
		print("Plotter " + i[0] + " failed: " + str(sys.exc_info()[1]))


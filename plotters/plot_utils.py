#!/usr/bin/python2

# pbenchsuite system benchmark suite for linux.
# Copyright (C) 2012  Markus Pargmann < scosu _AT_ allfex ORG >
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import matplotlib.pyplot as plt
import scipy
import scipy.stats
import numpy
import operator


def mean_confidence_interval(data, confidence=0.95):

	a = 1.0*numpy.array(data)
	n = len(a)
	m, se = numpy.mean(a), scipy.stats.sem(a)
	# calls the inverse CDF of the Student's t distribution
	h = se * scipy.stats.t._ppf((1+confidence)/2., n-1)
	return m, h


##
# @brief Draw a bar chart in grouped form.
#    _         _
#  _| |       | |
# | | |_   _ _| |
# | | | | | | | |
#  a b c   a b c
#    1       2
#
#
# @param data Dict of dicts in following format:
# You can replace the floats on the deepest level by lists of floats for stacked
# bars.
# @param available_sub_keys
#
# @return

def _arg_string_sort(a, b):
	al = a.split(' ')
	bl = b.split(' ')
	l = min(len(al), len(bl))
	for i in range(0, l):
		try:
			if float(al[i]) < float(bl[i]):
				return -1
			if float(al[i]) > float(bl[i]):
				return 1
			continue
		except:
			pass
		if al[i] < bl[i]:
			return -1
		if al[i] > bl[i]:
			return 1
	if len(al) < len(bl):
		return -1
	if len(al) > len(bl):
		return 1
	return 0

def _sort_keys(keys):
	return sorted(keys, cmp=_arg_string_sort)

def _plot_stuff(title = None, x_label = None, y_label = None, no_legend = False, max_x = None):
	if title != None:
		plt.title(title)
	if x_label != None:
		plt.xlabel(x_label)
	if y_label != None:
		plt.ylabel(y_label)
	if not no_legend and max_x != None:
		handles, labels = plt.gca().get_legend_handles_labels()
		hl = sorted(zip(handles, labels), cmp=_arg_string_sort, key=operator.itemgetter(1))
		handles, labels = zip(*hl)
		max_label = 0
		for k in labels:
			max_label = max(len(k), max_label)
		plt.xlim(xmax = max(max_x + 1, max_x * (1 + (max(0, max_label - 3)) * 0.06)))
		plt.legend(handles, labels, loc='center right', bbox_to_anchor=(1.13, 0.5), fancybox=True, shadow=True)


# Takes something like this:
#data_line = {
#		'x': [(0,1), (1,3), (2,2), (3,5)],
#		'y': [(0,1), (2,1), (3,2), (4,5)],
#		'z': [(0,[1,2,3,2,2,2,2]), (1,[2,3,2,2,3,3,3,3]), (2,2), (3,5)]
#}
def plot_line_chart(data, x_keys=None, title=None, y_label=None, x_label=None, no_legend=False, confidence_arg=0.95, fmts_arg=None):
	global fmts
	global fmtsid
	if fmts_arg == None:
		fmts = [
				{'color': 'b', 'linestyle': '-', 'marker': ' '},
				{'color': 'g', 'linestyle': '-', 'marker': ' '},
				{'color': 'r', 'linestyle': '-', 'marker': ' '},
				{'color': 'c', 'linestyle': '-', 'marker': ' '},
				{'color': 'm', 'linestyle': '-', 'marker': ' '},
				{'color': 'y', 'linestyle': '-', 'marker': ' '},
				{'color': 'b', 'linestyle': '--', 'marker': ' '},
				{'color': 'g', 'linestyle': '--', 'marker': ' '},
				{'color': 'r', 'linestyle': '--', 'marker': ' '},
				{'color': 'c', 'linestyle': '--', 'marker': ' '},
				{'color': 'm', 'linestyle': '--', 'marker': ' '},
				{'color': 'y', 'linestyle': '--', 'marker': ' '},
				{'color': '0.4', 'linestyle': '-', 'marker': ' '},
				{'color': '0.4', 'linestyle': '--', 'marker': ' '},
			]
	else:
		fmts = fmts_arg
	fmtsid = 0
	def _next_fmt():
		global fmtsid
		fmt = fmts[fmtsid%len(fmts)]
		fmtsid += 1
		return fmt

	if x_keys == None:
		x_keys = _sort_keys(data.keys())

	max_overall_x = None
	min_overall_x = None
	for k in x_keys:
		if k not in data:
			continue
		v = data[k]
		xs = []
		ys = []
		yerrs = []
		yerr_not_zero = False
		for pt in v:
			xs.append(pt[0])
			if max_overall_x == None:
				max_overall_x = pt[0]
				min_overall_x = pt[0]
			else:
				max_overall_x = max(max_overall_x, pt[0])
				min_overall_x = min(min_overall_x, pt[0])
			if isinstance(pt[1], list):
				m, h = mean_confidence_interval(pt[1])
				yerrs.append(h)
				ys.append(m)
				yerr_not_zero = True
			else:
				ys.append(pt[1])
				yerrs.append(0.0)
		fmt = _next_fmt()
		if yerr_not_zero:
			plt.errorbar(xs, ys, yerrs, label=k, linestyle=fmt['linestyle'], marker=fmt['marker'], color=fmt['color'])
		else:
			plt.plot(xs, ys, label=k, linestyle=fmt['linestyle'], marker=fmt['marker'], color=fmt['color'])
	rang = max_overall_x - min_overall_x
	plt.xlim(xmin = (min_overall_x - rang*0.05))
	_plot_stuff(title=title, x_label=x_label, y_label=y_label, no_legend=no_legend, max_x=(max_overall_x + rang*0.05))


# Works with all those structures:
#data = {'a':1, 'b':4, 'c':2}
#data = {
#		'a': {'1': 2, '2': 1, 'dummy': 4},
#		'b': {'1': 3, '2': 1, 'dummy': 3},
#		'c': {'1': 4, '2': 2, 'dummy': 1}
#}
#data = {
#		'x': {'1': {'a': 4, 'e': [1, 2, 3], 'c': 3}, '2': {'d':5, 'e': 2}, 'dummy': {'e':3}},
#		'y': {'1': {'a': 6, 'e': [1, 2, 2, 3], 'c': 1}, '2ab': {'d':5}, 'dummy': {'e':3}},
#		'z': {'1': {'a': 2, 'eaasd': [1, 2, 2, 2, 3], 'c': 4}, '2': {'d':5}, 'dummy': {'e':3}}
#}
##
# @brief Plot a bar chart with data of up to 3 dimensions
#
# @param data maximal 3 level depth of dictionary with lists of floats or floats
# as lowest children. Lists will produce errorbars. The keys of the dictionary
# are used to sort the stuff.
# @param l1_keys Level 1 keys, this specifies the order
# @param l2_keys Level 2 keys, this specifies the order
# @param l3_keys Level 3 keys, this specifies the order
# @param colors_arg
# @param confidence_arg
#
# @return
def plot_bar_chart(data, l1_keys=None, l2_keys=None, l3_keys=None, colors_arg=None, confidence_arg=0.95, no_legend=False, title=None, y_label=None, x_label=None):
#Many global hacks because python 2.7 doesn't support nonlocal
	if l1_keys == None:
		l1_keys = _sort_keys(data.keys())
	if l2_keys == None:
		l2_keys = set()
		for k1, v1 in data.items():
			if not isinstance(v1, dict):
				continue
			for k2, v2 in v1.items():
				l2_keys.add(k2)
		l2_keys = _sort_keys(list(l2_keys))
	if l3_keys == None:
		l3_keys = set()
		for k1, v1 in data.items():
			if not isinstance(v1, dict):
				continue
			for k2, v2 in v1.items():
				if not isinstance(v2, dict):
					continue
				for k3, v3 in v2.items():
					l3_keys.add(k3)
		l3_keys = _sort_keys(list(l3_keys))
	xxticks = []
	xticks = []
	global confidence
	confidence = confidence_arg
	global label_colors
	label_colors = {}
	global colors
	if colors_arg == None:
		colors = ['0.3', '0.5', '0.7', '0.4', '0.6', '0.8']
	else:
		colors = colors_arg
	global colorid
	colorid = 0
	global x
	x = 1
	global max_overall
	max_overall = 0
	def _xtick(label, x_val = None):
		global x
		if x_val == None:
			x_val = x
		xxticks.append(x_val)
		xticks.append(label)
	def _color_get(label):
		global colorid
		if label in label_colors:
			return False, label_colors[label]
		else:
			label_colors[label] = colors[colorid % len(colors)]
			colorid += 1
			return True, label_colors[label]
	def _plt_bar(x, y, label):
		global confidence
		set_label, color = _color_get(label)
		if isinstance(y, list):
			global max_overall
			m,h = mean_confidence_interval(y, confidence)
			max_overall = max(m, max_overall)
			if label == None or not set_label:
				plt.bar(x, m, align="center", color = color, ecolor='r', yerr = h)
			else:
				plt.bar(x, m, align="center", color = color, ecolor='r', label = label, yerr = h)
		else:
			max_overall = max(max_overall, y)
			if label == None or not set_label:
				plt.bar(x, y, align="center", color = color)
			else:
				plt.bar(x, y, align="center", color = color, label = label)

	levels = 0
	for l1_key in l1_keys:
		l1_val = data[l1_key]
		levels = 1
		if not isinstance(l1_val, dict):
			_xtick(l1_key)
			_plt_bar(x, l1_val, l1_key)
			x += 1
		else:
			_xtick(l1_key, x + int(len(l1_val.keys()) / 2))
			levels = 2
			for l2_key in l2_keys:
				if l2_key not in l1_val:
					continue
				l2_val = l1_val[l2_key]
				levels = 3
				if not isinstance(l2_val, dict):
					_plt_bar(x, l2_val, l2_key)
					max_val = 0
					x += 1

				else:
					max_val = 0
					for l3_key in l3_keys:
						if l3_key not in l2_val:
							continue
						l3_val = l2_val[l3_key]
						if isinstance(l3_val, list):
							max_val = max(sum(l3_val)/len(l3_val), max_val)
						else:
							max_val = max(l3_val, max_val)
						_plt_bar(x, l3_val, l3_key)

					rot = min((len(l2_key) - 1)*30, 90)
					plt.text(x, max_val + max_overall * 0.02, l2_key, horizontalalignment='center', verticalalignment='bottom', rotation=rot)
					x += 1
			x += 1
	if levels == 3:
		plt.ylim(ymin = 0, ymax=1.2*max_overall)
	else:
		plt.ylim(ymin = 0)
	plt.xticks(xxticks, xticks)
	_plot_stuff(x_label = x_label, y_label = y_label, title = title, no_legend = no_legend, max_x = x-1)





#!/usr/bin/python2.7

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

import data_loader
import os
import plot_utils
import matplotlib.pyplot as plt
import json
import copy
import cProfile
import pstats

args = []
store_dir = ''
pathes = []

def generic_data_colapser(data):
	result = {}
	if isinstance(data, dict):
		for k,v in data.items():
			ret = generic_data_colapser(v)
			if ret == None:
				continue
			if isinstance(ret, dict):
				if len(ret) > 1:
					for k2, v2 in ret.items():
						result[k+k2] = v2
				else:
					result[k] = list(ret.values())[0]
			else:
				result[k] = ret
	elif isinstance(data, list):
		rlist = []
		for i in data:
			ret = generic_data_colapser(i)
			if ret == None:
				continue
			if isinstance(ret, dict):
				for k,v in ret.items():
					if k in result:
						if not isinstance(result[k], list):
							result[k] = [result[k]]
						result[k].append(v)
					else:
						result[k] = v
			else:
				rlist.append(ret)
		for k,v in result.items():
			if isinstance(v, list):
				result[k] = sum(v)/len(v)
		if len(rlist) > 0:
			avg = sum(rlist) / len(rlist)
			if len(result) > 0:
				k = 'raw'
				while k in result:
					k += '_'
				result[k] = avg
			else:
				result = avg
	elif isinstance(data, int) or isinstance(data, float):
		result = data
	else:
		result = None
	return result

def _savefig(path):
	path += '.png'
	path = path.replace(' ', '_')
	print(path)
	plt.savefig(path, dpi=200)
	plt.clf()


def arg_to_filter(args):
	filters = []
	if len(args) == 0:
		return None
	for i in args:
		if isinstance(i, list):
			filters.append(i)
		else:
			filters.append([i])
	return filters

def plot_bench(bench):
	tgt = os.path.join(store_dir, bench)
	if not os.path.exists(tgt):
		os.mkdir(tgt)
	loader = data_loader.loader()
	loader.load_pathes(pathes, only_benchs=[bench])
	# get the argvariations between all arguments. Use this to filter the
	# data for the plots
	args = loader.get_arg_variation(bench)
	if len(args) > 0:
		max_args_differ = 0
		for i in args:
			max_args_differ = max(max_args_differ, max([len(k) for k in i]))
	else:
		max_args_differ = 0
	max_depth = 2
	max_args_differ = min(max_depth, max_args_differ)
	data = {}
	monitor = {}
	# iterate through all detected arg combinations and gather the data and reformat it
	for argsetting in args:
		pre_args = argsetting[0]
		args = argsetting[1]
		post_args = argsetting[2]
		pre_filters = arg_to_filter(pre_args)
		filters = arg_to_filter(args)
		post_filters = arg_to_filter(post_args)
		dat = loader.get_filtered_data(bench=bench, pre_filters=pre_filters, filters=filters, post_filters=post_filters, no_regex=True)
		if dat == None:
			print("Error: Didn't find data for the given args")
			continue
		depth = 0
		path = []
		# create a hierarchy path for this argument combination, we have 3
		# hierarchy level, the last one is used for the system, so 2 remaining
		for i in argsetting[0] + argsetting[1] + argsetting[2]:
			if depth >= max_depth:
				if isinstance(i, list):
					path[max_depth] += ' '.join(i)
				else:
					path[max_depth] += i
				break
			depth += 1
			if isinstance(i, list):
				path.append(' '.join(i))
			else:
				path.append(i)
		while len(path) < max_args_differ:
			path.append('N/A')
		if len(dat) != 1:
			print("Error: we filtered " + str(len(dat.values())) + " instances instead of 1")
			print("Filters:")
			print(pre_args)
			print(args)
			print(post_args)
			continue
		# The first level in the dat dictionary holds the instancename,
		# the previous check shows that this has only one element...
		dat = list(dat.values())[0]
		for k,v in dat.items():
			r = {}
			mondat = {}
			for run in v['instance']['runs']:
				t = generic_data_colapser(run['results'])
				for tk, tv in t.items():
					if tk not in r:
						r[tk] = tv
					else:
						if isinstance(r[tk], list):
							r[tk].append(tv)
						else:
							r[tk] = [r[tk], tv]
				for monname, mon in run['monitors'].items():
					row = {}
					for m in mon['data']:
						t = generic_data_colapser(m['values'])
						for tk, tv in t.items():
							if tk not in row:
								row[tk] = [[m['time'], tv]]
							else:
								row[tk].append([m['time'], tv])
					if monname not in mondat:
						mondat[monname] = {}
					for rk, rv in row.items():
						if rk not in mondat[monname]:
							mondat[monname][rk] = []
						mondat[monname][rk].append(rv)
			for rk, rv in r.items():
				dptr = data
				cmpl_path = [rk] + path + [k]
				for i in cmpl_path[:-1]:
					if i not in dptr:
						dptr[i] = {}
					dptr = dptr[i]
				dptr[cmpl_path[-1]] = rv
			for mk, mv in mondat.items():
				for mk2, mv2 in mv.items():
					dptr = monitor
					cmpl_path = [mk, mk2] + path + [k]
					for i in cmpl_path[:-1]:
						if i not in dptr:
							dptr[i] = {}
						dptr = dptr[i]
					dptr[cmpl_path[-1]] = mv2
		dat = None
	result_tgt = os.path.join(tgt, 'results')
	if not os.path.exists(result_tgt):
		os.mkdir(result_tgt)
	monitor_tgt = os.path.join(tgt, 'monitors')
	if not os.path.exists(monitor_tgt):
		os.mkdir(monitor_tgt)
	for k,v in data.items():
		plot_utils.plot_bar_chart(v)
		plt.title(bench + ' ' + k)
		plt.grid(axis='y')
		_savefig(os.path.join(result_tgt, k))
	def plot_mon(path, data, try_level_colapse=False):
		plot_it = False
		level_colapse = False
		if try_level_colapse and isinstance(data, dict) and isinstance(list(data.values())[0], dict) and isinstance(list(list(data.values())[0].values())[0], list):
			max_l1 = len(data)
			max_l2 = 0
			max_combos_to_plot = 15
			for k,v in data.items():
				max_l2 = max(max_l2, len(v))
			if max_l1 * max_l2 < max_combos_to_plot:
				plot_it = True
				level_colapse = True
		if not plot_it:
			for k,v in data.items():
				if isinstance(v, list):
					plot_it = True
					break
				plot_mon(path + '_' + k, v, try_level_colapse)
		if not plot_it:
			return
		if level_colapse:
			tmp = {}
			for k,v in data.items():
				for k2,v2 in v.items():
					tmp[k+' '+k2] = v2
			data = tmp
		else:
			if try_level_colapse:
				return
		max_times = []
		for k,v in data.items():
			for ri in range(0, len(v)):
				row = v[ri]
				starttime = row[0][0]
				for i in range(0, len(row)):
					row[i][0] -= starttime
				if ri >= len(max_times):
					max_times.append(0)
				max_times[ri] = max(max_times[ri], row[-1][0] + 1)
		ct = 0
		for i in range(0, len(max_times)):
			tmp = ct
			ct += max_times[i]
			max_times[i] = tmp
		for k in data.keys():
			tmp = []
			for ri in range(0, len(data[k])):
				row = data[k][ri]
				if len(tmp) > 0:
					tmp.append([tmp[-1][0]+1, row[0][1]])
				for i in row:
					tmp.append((i[0]+max_times[ri], i[1]))
			data[k] = tmp
			last_tmp = tmp
		plot_utils.plot_line_chart(data)
		plt.grid(axis='y')
		_savefig(path)

	for k,v in monitor.items():
		t = os.path.join(monitor_tgt, k)
		if not os.path.exists(t):
			os.mkdir(t)
		t = os.path.join(t, 'mon')
		plot_mon(t, copy.deepcopy(v), try_level_colapse=True)
		plot_mon(t, v, try_level_colapse=False)

def plot_pathes(paths, storedir):
	global store_dir
	global pathes
	pathes = paths
	store_dir = storedir
	if not os.path.exists(storedir):
		os.mkdir(storedir)
	loader = data_loader.loader()
	benches = loader.get_benchnames_pathes(pathes)
	for bench in benches:
		plot_bench(bench)

def profiling():
	pathes = []
	for i in [1,2,3,4,5,6,7,8,16,32,64,128]:
		pathes.append('/mnt/local_storage/pbench/cfs3.4/kernel' + str(i) + ".json")
	plot_pathes(pathes, '/tmp/test')


if __name__ == '__main__':
	cProfile.run('profiling()', 'stored_profiling')
	p = pstats.Stats('stored_profiling')
	p.sort_stats('time')
	p.print_stats()

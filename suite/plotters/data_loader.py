
import json
import os
import re
import sys


# filtered_arg is a list of lists. The sublists express the argument we match
# as a regular expression
def filter_matcher(filtered_arg, args, no_regex = False):
	matched_filters = 0
	for f in filtered_arg:
		matching = 0
		for arg in args:
			if (no_regex and f[matching] == str(arg)) or (not no_regex and re.match(f[matching], str(arg))):
				matching += 1
				if matching == len(f):
					matched_filters += 1
					break
	return matched_filters == len(filtered_arg)

# Match options against the given filters and monitors. Returns True if those are
# matching
def filter_options(options, pre_filters=None, filters=None, post_filters=None, monitors=None, no_regex=False):
	matches = 0
	if pre_filters == None:
		matches += 1
	else:
		if filter_matcher(pre_filters, options['pre_args'], no_regex):
			matches += 1
	if filters == None:
		matches += 1
	else:
		if filter_matcher(filters, options['args'], no_regex):
			matches += 1
	if post_filters == None:
		matches += 1
	else:
		if filter_matcher(post_filters, options['post_args'], no_regex):
			matches += 1
	if monitors == None:
		matches += 1
	else:
		if 'monitors' in options:
			match_fail = False
			for mon in monitors:
				if mon not in options['monitors']:
					match_fail = True
					break
			if not match_fail:
				matches += 1

	if matches == 4:
		return True
	return False

# Deep equality check of a and b, detects dict, list, str, float and int
def deep_equal(a, b):
	types = [dict, list, str, float, int]
	for t in types:
		if isinstance(a, t) and not isinstance(b, t):
			return False
	if isinstance(a, dict):
		if not deep_equal(a.keys(), b.keys()):
			return False
		for k in a.keys():
			if not deep_equal(a[k], b[k]):
				return False
	elif isinstance(a, list):
		if len(a) != len(b):
			return False
		for i in range(0, len(a)):
			if not deep_equal(a[i], b[i]):
				return False
	elif isinstance(a, float) or isinstance(a, int) or isinstance(a, str):
		if a != b:
			return False
	return True

# add variation to the set of variations
def _add_var_set(bigset, diff):
	equal = False
	for i in bigset:
		if deep_equal(i, diff):
			equal = True
			break
	if not equal:
		bigset.append(diff)

# Compare all arguments in args with all argumentlines in the argset.
# Returns the argument parts that are not in the argset
def get_args_not_in_set(args, argset):
	diff = []
	last_i = None
	ct = 0
	while ct < len(args):
		if args[ct].startswith('-') and ct < len(args)-1 and not args[ct+1].startswith('-'):
			for arg in argset:
				rang = max(0, len(arg) - 1)
				not_found = True
				for ct2 in range(0, rang):
					if args[ct] == arg[ct2] and args[ct+1] == arg[ct2+1]:
						not_found = False
						break
				if not_found:
					d = [args[ct], args[ct+1]]
					if d not in diff:
						diff.append(d)
					ct += 1
					break
		elif args[ct] not in diff:
			for arg in argset:
				if args[ct] not in arg:
					if args[ct] not in diff:
						diff.append(args[ct])
					break
		ct += 1
	return diff

# Compute the argument variation in a list of argumentlists
def arg_variation(argset):
	pre_args = []
	args = []
	post_args = []
	for i in argset:
		pre_args.append(i[0])
		args.append(i[1])
		post_args.append(i[2])
	diffs = []
	for i in argset:
		diff = []
		diff.append(get_args_not_in_set(i[0], pre_args))
		diff.append(get_args_not_in_set(i[1], args))
		diff.append(get_args_not_in_set(i[2], post_args))
		diffs.append(diff)
	return diffs

	variations = []
	for args in argset:
		diff_pre = []
		diff_post = []
		diff = []
		state = 0
		last_state1_appended = False
		last_i = None
		for i in args:
			if state == 0 and i.startswith('-'):
				state = 1
			elif state == 1 and not i.startswith('-'):
				state = 2
			elif state == 2 or state == 3:
				if i.startswith('-'):
					state = 1
				else:
					state = 3
			for arg in argset:
				if i not in arg:
					if state == 0:
						if i not in diff_pre:
							diff_pre.append(i)
					elif state == 2:
						if last_i not in diff:
							diff.append(last_i)
							diff.append(i)
					elif state == 3:
						if i not in diff_post:
							diff_post.append(i)
			last_i = i
		diff_opt = []
		state = 0
		last = None
		for i in range(0, len(diff)):
			if state == 1:
				if diff[i].startswith('-'):
					if last != None:
						diff_opt.append([last])
						last = None
					state = 0
				else:
					diff_opt.append([last, diff[i]])
					last = None
			if state == 0:
				if diff[i].startswith('-'):
					state = 1
					last = diff[i]
				else:
					diff_opt.append([diff[i]])
		_add_var_set(variations, diff_pre + diff_opt + diff_post)


	return variations


# loader simplifies the data loading from multiple files
class loader:
	def __init__(self):
		self.data = {}
		self.systems = {}

	# get the benchmark name of a result file
	def get_benchname(self, filepath):
		f = open(filepath, 'r')
		data = json.load(f)
		f.close()
		return data['bench']['name']

	# get benchmark names of resultfiles in a directory
	def get_benchnames_dir(self, directory):
		result = set()
		for dir_item in os.listdir(directory):
			abs_path = os.path.join(directory, dir_item)
			if not os.path.isfile(abs_path):
				continue
			try:
				result.add(self.get_benchname(abs_path))
			except:
				continue
		return list(result)

	# get benchmark names of resultfiles at the given pathes
	def get_benchnames_pathes(self, pathes):
		result = set()
		for i in pathes:
			print(i)
			if os.path.isfile(i):
				try:
					result.add(self.get_benchname(i))
				except:
					print("load file exception: " + sys.exc_info()[0])
					continue
			elif os.path.isdir(i):
				result = result.union(self.get_benchnames_dir(i))
		return list(result)

	# Create a loader local system info table with runnames as identifiers
	def _get_system(self, runname, sysinfo):
		if runname in self.systems:
			if deep_equal(sysinfo, self.systems[runname]):
				return runname
			while runname in self.systems:
				runname = runname + "_"
		self.systems[runname] = sysinfo
		return runname

	# Load a file with the given filters
	def load_file(self, f, only_benchs=None, only_instances=None, pre_filters=None, filters=None, post_filters=None, monitors=None):
		try:
			f = open(f, 'r')
			data = json.load(f)
			f.close()
			bench_name = data['bench']['name']
			instance_name = data['instance']['name']
			if only_benchs != None and bench_name not in only_benchs:
				return False
			if only_instances != None and instance_name not in only_instances:
				return False
			if not filter_options(data['instance']['options'], pre_filters, filters, post_filters, monitors):
				return False
			if bench_name not in self.data:
				self.data[bench_name] = {}
			system = self._get_system(data['suite']['runname'], data['system'])
			if instance_name not in self.data[bench_name]:
				self.data[bench_name][instance_name] = {}
			self.data[bench_name][instance_name][system] = data
			return True
		except:
			print("load exception: " + sys.exc_info()[0])
			return False
	def load_dir(self, directory, only_benchs=None, only_instances=None):
		try:
			for dir_item in os.listdir(directory):
				abs_path = os.path.join(directory, dir_item)
				if not os.path.isfile(abs_path):
					continue
				self.load_file(abs_path, only_benchs, only_instances)
		except:
			return False
	def load_path(self, path, only_benchs=None, only_instances=None):
		if os.path.isfile(path):
			return self.load_file(path, only_benchs, only_instances)
		elif os.path.isdir(path):
			return self.load_dir(path, only_benchs, only_instances)
		else:
			print("Error: " + path + " is not a directory and not a file")
			return False
	# Load pathes
	def load_pathes(self, pathes, only_benchs=None, only_instances=None):
		success = True
		for i in pathes:
			s = self.load_path(i, only_benchs, only_instances)
			success = s and success
		return success
	# get loaded data
	def get_data(self):
		return self.data

	# pre_filters, filters and post_filters have to be a list of lists of
	# regular expressions. The result is accepted as match if all filters
	# match
	def get_filtered_data(self, bench=None, pre_filters=None, filters=None, post_filters=None, monitors=None, no_regex=False):
		matched = {}
		if bench != None:
			for instancename,instance in self.data[bench].items():
				for runname, run in instance.items():
					if filter_options(run['instance']['options'], pre_filters, filters, post_filters, monitors, no_regex=no_regex):
						if instancename not in matched:
							matched[instancename] = {}
						matched[instancename][runname] = run
		else:
			for benchname, benchobj in self.data.items():
				for instancename, instance in benchobj.items():
					for runname, run in instance.items():
						if filter_options(run['instance']['options'], pre_filters, filters, post_filters, monitors, no_regex=no_regex):
							if benchname not in matched:
								matched[benchname] = {}
							if instancename not in matched[benchname]:
								matched[instancename] = {}
							matched[benchname][instancename][runname] = instance

		return matched
	def get_arg_variation(self, bench):
		argset_pre = []
		argset = []
		argset_post = []
		for instname, inst in self.data[bench].items():
			for sysname, system in inst.items():
				arg_sum = []
				args = system['instance']['options']['args']
				args_pre = system['instance']['options']['post_args']
				args_post = system['instance']['options']['pre_args']
				if args_pre != None:
					arg_sum.append(args_pre)
				else:
					arg_sum.append([])
				if args != None:
					arg_sum.append(args)
				else:
					arg_sum.append([])
				if args_post != None:
					arg_sum.append(args_post)
				else:
					arg_sum.append([])
				argset.append(arg_sum)
		return arg_variation(argset)

if __name__ == '__main__':
	l = loader()
	l.load_path('/mnt/local_storage/pbench/cfs_test')
	print(l.get_argvariation('hackbench'))
	print(l.get_argvariation('kernel_compile'))
	print(l.get_argvariation('unixbench'))
	print(l.get_argvariation('postfix_msg_passing'))
	print(l.get_argvariation('yield_benchmark'))

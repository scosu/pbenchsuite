#!/usr/bin/python3


import sys
import os
import time
import math
import threading
import configparser
import subprocess
import signal
import logging
import argparse
import json


class monitor:
	def __init__(self, name):
		self.name = name
		self.module = __import__(name)

	def check_requirements(self):
		return self.module.check_requirements()

	def install(self, psuite):
		installed_file = os.path.join(psuite.state_mon_installed_path, self.name)
		if os.path.isfile(installed_file):
			return 0
		if self.module.install() != 0:
			return -1
		f = open(installed_file, 'w')
		f.write("\n")
		f.close()
		return 0

	def pre(self):
		self.data = {'name' : self.name, 'data' : []}
		self.data['info'] = self.module.to_dict()
		self.module.pre()

	def tick(self, cur_time):
		values = self.module.get()
		self.data['data'].append({'time':cur_time, 'values':values})

	def to_dict(self):
		return self.data

class monitor_proc:
	def __init__(self, monitors):
		self.monitors = monitors
		self.stop_rec = False
	def sleep_remaining(self, start, sleep):
		remain = sleep - (time.time() - start)
		if remain > 0:
			time.sleep(remain)

	def __call__(self):
		start = time.time()
		for i in self.monitors:
			i.pre()
		self.sleep_remaining(start, 1)
		while not self.stop_rec:
			start = time.time()
			for i in self.monitors:
				i.tick(start)
			self.sleep_remaining(start, 1)
		self.stop_rec = False
	def stop(self):
		self.stop_rec = True
		while self.stop_rec == True:
			time.sleep(0.1)

def dir_create(path):
	try:
		os.mkdir(path)
	except:
		return

class pbenchsuite:
	data = {}
	base_path = ""
	monitors_path = ""
	benchs_path = ""
	results_path = ""
	state_path = ""
	state_mon_installed_path = ""
	benchsuites_path = ""

	def init_dir(self, path):
		dir_create(path)
		return path

	def __init__(self, base_path = None):
		if base_path == None:
			base_path = os.getcwd()
		self.base_path = base_path
		self.monitors_path = os.path.join(base_path, 'monitors')
		dir_create(self.monitors_path)
		sys.path.insert(0, self.monitors_path)
		self.benchs_path = os.path.join(base_path, 'benchmarks')
		dir_create(self.benchs_path)
		self.results_path = os.path.join(base_path, 'results')
		dir_create(self.results_path)
		self.state_path = os.path.join(base_path, 'state')
		dir_create(self.state_path)
		self.state_mon_installed_path = os.path.join(self.state_path, 'monitors_installed')
		dir_create(self.state_mon_installed_path)
		self.state_bench_installed_path = os.path.join(self.state_path, 'benchs_installed')
		dir_create(self.state_bench_installed_path)
		self.benchsuites_path = os.path.join(base_path, 'benchsuites')
		dir_create(self.benchsuites_path)

		self.benchsuites = []
		self.monitors = {}
		self.loaded_benchs = {}
		self.store_system_information()

	def store_system_information(self):
		sysinfo_files = {
			'cpuinfo': '/proc/cpuinfo',
			'distribution': '/etc/issue',
			'mtab': '/etc/mtab',
			'fstab': '/etc/fstab'}
		for i in sysinfo_files:
			if os.path.exists(i):
				f = open(i, 'r')
				self.data[i] = f.read()
				f.close()

		i = 0
		cpus = {}
		while True:
			if not os.path.isdir('/sys/devices/system/cpu/cpu' + str(i)):
				break

			cpu_freqs = {}
			cpu_freqs['max'] = open('/sys/devices/system/cpu/cpu' + str(i) + '/cpufreq/scaling_max_freq', 'r').read().strip()
			cpu_freqs['min'] = open('/sys/devices/system/cpu/cpu' + str(i) + '/cpufreq/scaling_min_freq', 'r').read().strip()
			cpu_freqs['cur'] = open('/sys/devices/system/cpu/cpu' + str(i) + '/cpufreq/scaling_cur_freq', 'r').read().strip()
			cpu_freqs['governor'] = open('/sys/devices/system/cpu/cpu' + str(i) + '/cpufreq/scaling_governor', 'r').read().strip()
			cpus[str(i)] = cpu_freqs

			i += 1

		self.data['cpus'] = cpus

		self.data['modules'] = execute_cmd(['lsmod'])
		self.data['kernal'] = execute_cmd(['uname', '-a'])
	def to_dict(self):
		return self.data

	def get_monitor(self, mon):
		if mon not in self.monitors:
			self.monitors[mon] = monitor(mon)
		return self.monitors[mon]

	def add_benchsuite(self, path, runname):
		if not os.path.isabs(path):
			if not os.path.isfile(path):
				path = os.path.join(self.benchsuites_path, path)
		if not os.path.isfile(path):
			logging.critical("Can't find benchsuite " + path)
			return -1

		self.benchsuites.append(benchsuite(path, self, runname))
		return 0

	def check_requirements(self):
		all_reqs = []
		for k,bench in self.loaded_benchs.items():
			reqs = bench.check_requirements()
			if len(reqs) != 0:
				logging.critical("Benchmark '" + bench.name + "' requires following missing packages")
			all_reqs += reqs
			for i in reqs:
				logging.critical("\t" + i)
		for k,v in self.monitors.items():
			reqs = v.check_requirements()
			all_reqs += reqs
			if len(reqs) != 0:
				logging.critical("Monitor '" + k + "' requires following missing packages")
			for i in reqs:
				logging.critical("\t" + i)

		if len(all_reqs) != 0:
			logging.critical("Requirement summary")
			for i in set(all_reqs):
				logging.critical("\t" + i)
			return -1
		return 0


	def install(self):
		success = 1
		for k,bench in self.loaded_benchs.items():
			a = bench.install()
			if a != 0:
				success = 0
				logging.critical("Benchmark " + bench.name + " failed installing")
		for k,v in self.monitors.items():
			a = v.install(self)
			if a != 0:
				success = 0
				logging.critical("Monitor " + k + " failed installing")
		if success == 0:
			return -1
		else:
			return 0

	def run(self):
		failed = 0
		for suite in self.benchsuites:
			suite.run()
		for suite in self.benchsuites:
			if len(suite.failed_benchs) != 0:
				logging.error("Benchsuite " + suite.name + " failed to run some benchs:")
				failed = 1
				for i in suite.failed_benchs:
					logging.error("\t" + i)
		return failed

def run_limit_options(config, section):
	options = {}
	if not config.has_section(section):
		return options
	intoptions = ['min_runs', 'max_runs', 'min_runtime', 'max_runtime', 'warmup_runs']
	floatoptions = ['relative_min_runs', 'relative_max_runs', 'relative_warmup_runs', 'relative_stderr']
	for i in intoptions:
		if config.has_option(section, i):
			options[i] = config.getint(section, i)
	for i in floatoptions:
		if config.has_option(section, i):
			options[i] = config.getfloat(section, i)
	return options

def execute_cmd(cmd):
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdo, stde = p.communicate()
	result = {
		'returncode': p.returncode,
		'stdout': stdo.decode(),
		'stderr': stde.decode()}
	return result


class bench:
	options = {}
	psuite = None
	name = ""
	bench_path = ""
	def __init__(self, psuite, benchname):
		logging.debug('Creating bench ' + benchname)
		conf = configparser.RawConfigParser()
		bench_path = os.path.join(psuite.benchs_path, benchname)
		conf.read(os.path.join(bench_path, 'config'))
		self.options = run_limit_options(conf, 'general')
		list_opts = ['pre_args', 'args', 'post_args']
		for i in list_opts:
			if conf.has_option('general', i):
				self.options[i] = [n.strip() for n in conf.get('general', i).split(',')]
			else:
				self.options[i] = []
		self.psuite = psuite
		self.name = benchname
		self.bench_path = bench_path

	def check_requirements(self):
		req_path = os.path.join(self.bench_path, 'requirements')
		if not os.path.isfile(req_path):
			return []
		data = execute_cmd([req_path])
		result = []
		for i in data['stdout'].splitlines():
			if i.strip() != "":
				result.append(i.strip())
		return result

	def install(self):
		inst_path = os.path.join(self.bench_path, 'install')
		if not os.path.exists(inst_path):
			return 0
		inst_state = os.path.join(self.psuite.state_bench_installed_path, self.name)
		if os.path.isfile(inst_state):
			return 0
		os.chdir(self.bench_path)
		installation = execute_cmd([inst_path])
		if installation['returncode'] != 0:
			logging.critical("Benchmark " + self.name + " failed installing. Stderr:")
			logging.critical(installation['stderr'])
			return 1
		f = open(inst_state, 'w')
		f.write("\n")
		f.close()
		return 0

	def pre(self, args):
		pre_path = os.path.join(self.bench_path, 'pre')
		os.chdir(self.bench_path)
		if not os.path.isfile(pre_path):
			return 0

		cmd = [pre_path]
		if args == None:
			cmd += self.options['pre_args']
		else:
			cmd += args
		result = execute_cmd(cmd)
		return result['returncode']
	def post(self, args):
		post_path = os.path.join(self.bench_path, 'post')
		if not os.path.isfile(post_path):
			return 0

		cmd = [post_path]
		if args == None:
			cmd += self.options['post_args']
		else:
			cmd += args
		result = execute_cmd(cmd)
		return result['returncode']
	def run(self, args):
		run_path = os.path.join(self.bench_path, 'run')
		cmd = [run_path]
		if args == None:
			cmd += self.options['args']
		else:
			cmd += args
		run = execute_cmd(cmd)
		return run

	def to_dict(self):
		data = {}
		data['options'] = self.options
		data['name'] = self.name
		data['bench_path'] = self.bench_path
		return data



# This function traverses recursively any dict or list to gather all int/float
# values in a single list. The stderror check uses this to make calculations on
# the raw result data
def result_list(d):
	results = []
	if isinstance(d, int):
		return [d]
	elif isinstance(d, float):
		return [d]
	elif isinstance(d, dict):
		for k,v in d.items():
			results += result_list(v)
	elif isinstance(d, list):
		for i in d:
			results += result_list(i)
	return results

def calc_variance(values):
	avg = sum(values)/len(values)
	sumsqr = 0.0
	for i in values:
		sumsqr += (avg - i)**2
	return sumsqr / len(values)

# calculate the standard error, not standard deviation
def calc_stderr(values):
	return math.sqrt(calc_variance(values)) / math.sqrt(float(len(values)))

class benchinstance:
	def __init__(self, bench, config, sect, suite):
		self.bench = bench
		self.suite = suite
		self.monitors = suite.monitors
		self.info = {}
		self.result_file = os.path.join(suite.results_path, sect + '.json')
		bench_opts = self.bench.options
		suite_opts = suite.options
		inst_opts = run_limit_options(config, sect)
		opts = bench_opts.copy()
		for k,v in suite_opts.items():
			opts[k] = v
		for k,v in inst_opts.items():
			opts[k] = v
		if 'relative_min_runs' in opts:
			opts['relative_min_runs'] = opts['relative_min_runs'] * bench_opts['min_runs']
		if 'relative_max_runs' in opts:
			opts['relative_max_runs'] = opts['relative_max_runs'] * bench_opts['max_runs']
		if 'relative_warmup_runs' in opts:
			opts['warmup_runs'] = max(opts['warmup_runs'],
				round(opts['relative_warmup_runs'] * bench_opts['warmup_runs']))
		if 'warmup_runs' not in opts:
			opts['warmup_runs'] = 1
		if 'relative_min_runs' not in opts:
			opts['relative_min_runs'] = 0
		if 'min_runs' not in opts:
			opts['min_runs'] = 3
		opts_arrays = ['pre_args', 'args', 'post_args']
		for i in opts_arrays:
			if config.has_option(sect, i):
				opts[i] = [n.strip() for n in config.get(sect, i).split(',')]
			else:
				opts[i] = None
		opts['monitors'] = []
		for i in self.monitors:
			opts['monitors'].append(i)
		self.options = opts
		self.name = sect


	def run_once(self):
		self.bench.pre(args = self.options['pre_args'])
		mon_proc = monitor_proc(self.monitors.values())
		threading.Thread(target = mon_proc).start()
		time.sleep(1)
		self.last_run = self.bench.run(args = self.options['args'])
		mon_proc.stop()
		self.bench.post(args = self.options['post_args'])

	def store_run_data(self):
		last = self.last_run
		try:
			last['results'] = json.loads(last['stdout'])
		except:
			last['results'] = {"failure": 1}
		del last['stdout']
		last['monitors'] = {}
		for k,v in self.monitors.items():
			last['monitors'][k] = v.to_dict()
		self.data['runs'].append(last)

	def stderr_okay(self):
		try:
			if 'relative_stderr' not in self.options:
				return False
			sums = None
			for i in self.data['runs']:
				value_list = result_list(i['results'])
				if sums == None:
					sums = []
					for i in range(0, len(value_list)):
						sums.append([])
				for v in range(0, len(value_list)):
					sums[v].append(value_list[v])
			for i in sums:
				avg = sum(i)/len(i)
				stderr_goal = self.options['relative_stderr'] * avg
				stderr = calc_stderr(i)
				logging.debug("Stderr: " + str(stderr) + "/" + str(stderr_goal))
				if stderr_goal < stderr:
					return False
			return True
		except:
			# This is a situation, where the number of results varies
			# which is not handled at the moment
			# TODO
			return False


	def run(self):
		self.data = {'runs':[], 'name':self.name}
		self.data['info'] = self.info
		start_time = time.time()
		for i in range(0, self.options['warmup_runs']):
			logging.info("Warmup Run " + str(i+1) + " of bench instance " + self.name + " (bench " + self.bench.name + ")")
			self.run_once()
			if self.last_run['returncode'] != 0:
				self.store_run_data()
				self.data['failure'] = 1
				return self.last_run['returncode']
		self.data['warmup_time'] = time.time() - start_time
		runs = 0
		start_time = time.time()
		while True:
			runs += 1
			logging.info("Run " + str(runs) + " of bench instance " + self.name + " (bench " + self.bench.name + ")")
			self.run_once()
			self.store_run_data()
			if self.last_run['returncode'] != 0:
				self.data['failure'] = 1
				return self.last_run['returncode']

			now = time.time()
			if self.options['min_runs'] > runs:
				logging.debug("min_runs not reached")
				continue
			if self.options['min_runtime'] > now - start_time:
				logging.debug("min_runtime not reached")
				continue
			if self.options['relative_min_runs'] > runs:
				logging.debug("relative_min_runs not reached")
				continue
			if 'max_runtime' in self.options and self.options['max_runtime'] < now - start_time:
				logging.debug("max_runtime reached, abort")
				break
			if 'relative_max_runs' in self.options and self.options['relative_max_runs'] < runs:
				logging.debug("relative_max_runs reached, abort")
				break
			if 'max_runs' in self.options and self.options['max_runs'] <= runs:
				logging.debug("max_runs reached, abort")
				break
			if self.stderr_okay():
				logging.debug("stderr reached, abort")
				break
		self.data['runtime'] = time.time() - start_time
		return 0

	def store_runs_to_file(self):
		logging.debug("Storing to file " + self.result_file)
		f = open(self.result_file, 'w')
		all_data = {}
		all_data['suite'] = self.suite.to_dict()
		all_data['bench'] = self.bench.to_dict()
		all_data['system'] = self.suite.psuite.to_dict()
		self.data['options'] = self.options
		all_data['instance'] = self.data
		logging.debug("Storing data of instance " + self.name + " to file " + self.result_file + " (size: " + str(sys.getsizeof(all_data)) + ")")
		json.dump(all_data, f)
		f.close()
		self.data = {}


class benchsuite:


	def __init__(self, path, psuite, runname):
		self.name = os.path.basename(path)
		self.psuite = psuite
		self.benchinstances = []
		self.failed_benchs = []
		self.monitors = {}
		self.data = {}
		self.results_path = os.path.join(psuite.results_path, runname)
		dir_create(self.results_path)
		logging.debug("Constructing benchsuite " + self.name + " with config file " + path)

		conf = configparser.RawConfigParser()
		logging.debug("reading config at " + path)
		conf.read(path)

		# set defaults for the benchsuite
		self.options = {}
		self.options['min_runs'] = 3
		limit_opts = run_limit_options(conf, 'general')
		for k,v in limit_opts.items():
			self.options[k] = v
		if conf.has_option('general', 'monitors'):
			mons = conf.get('general', 'monitors').split(',')
			for mon in mons:
				mon = mon.strip()
				self.monitors[mon] = psuite.get_monitor(mon)
		for sect in conf.sections():
			if sect == 'general':
				continue
			benchid = sect
			if conf.has_option(sect, 'benchmark'):
				benchid = conf.get(sect, 'benchmark')
			if benchid not in psuite.loaded_benchs:
				tmp = bench(psuite, benchid)
				psuite.loaded_benchs[benchid] = tmp
			benchid = psuite.loaded_benchs[benchid]
			self.benchinstances.append(benchinstance(benchid, conf, sect, self))

	def run(self):
		self.data['run_start'] = time.time()
		num = 1
		for instance in self.benchinstances:
			logging.info("Benchsuite " + self.name + " starting benchinstance " + instance.name + ' ' + str(num) + "/" + str(len(self.benchinstances)))
			num += 1
			failed = instance.run()
			instance.store_runs_to_file()
			if failed != 0:
				logging.error("Bench instance failed to run: " + instance.name)
				self.failed_benchs.append(instance.name)
		self.data['run_end'] = time.time()

	def to_dict(self):
		data = self.data.copy()
		data['options'] = {}
		for k,v in self.options.items():
			data['options'][k] = v
		data['name'] = self.name
		data['results_path'] = self.results_path
		return data




# Some of the benchs are using SIGUSR1 and SIGUSR2 for communication. To prevent
# this script from exiting, handle them with a dummy function
def sig_dummy(x, y):
	return
signal.signal(signal.SIGUSR1, sig_dummy)
signal.signal(signal.SIGUSR2, sig_dummy)

if __name__ == '__main__':

	logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

	parser = argparse.ArgumentParser(description='PBenchSuite')
	parser.add_argument('suites', metavar='<SUITE>:<RUNNAME>', type=str, nargs='+', help='Suite name or path followed by the runname (The directory inside results where all results should be stored)')
	parser.add_argument('-i', '--install', dest='install_only', action='store_true', default=False, help='Only install the necessary tests')
	args = parser.parse_args()

	psuite = pbenchsuite()

	for argstr in args.suites:
		arg = argstr.split(':')
		if len(arg) != 2:
			print("ERROR: Failed to parse '" + argstr + "' correctly. Please read the help for information about the format")
			sys.exit(1)
		status = psuite.add_benchsuite(arg[0], arg[1])
		if status != 0:
			print("ERROR: Failed to add a benchsuite. Aborting")
			sys.exit(1)

	s = psuite.check_requirements()
	if s != 0:
		print("ERROR: Missing requirements. Aborting")
		sys.exit(1)
	s = psuite.install()
	if s != 0:
		print("ERROR: Installation failed. Aborting")
		sys.exit(1)
	if args.install_only:
		sys.exit(0)
	psuite.run()

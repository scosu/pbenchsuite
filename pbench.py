#/usr/bin/python3

import hashlib
import subprocess
import os
import time
import shutil
import threading

glbl_shutdown = False

#
# Some helper functions
################################################################################


def get_executable_path(name):
	for path in os.environ['PATH'].split(os.pathsep):
		exec_path = os.path.join(path, name)
		if os.path.isfile(exec_path) and os.access(exec_path, os.X_OK):
			return exec_path
	return None


#
# Helper functions for internal use only
################################################################################

def _init_list(parameter):
	if isinstance(parameter, list):
		return parameter
	if parameter != None:
		raise Exception("Expected list, got something else: " + str(parameter))
	return []

def _init_dict(parameter):
	if isinstance(parameter, dict):
		return parameter
	if parameter != None:
		raise Exception("Expected dict, got something else: " + str(parameter))
	return {}

def _get_indentation(indent, indent_str):
	ind = ''
	for i in range(indent):
		ind += indent_str
	return ind

def _print_block_text(text, width=80, indent=0, indent_str='  '):
	ind = _get_indentation(indent, indent_str)
	output = ''
	for line in text.splitlines():
		words = line.split(' ')
		line_size = len(ind)
		output += ind
		for word in words:
			if line_size + len(word) > width:
				output = output[:-1] + "\n"
				output += ind
				line_size = len(ind)
			output += word + ' '
			line_size += len(word) + 1
		output += "\n"
	output = output[:-1]
	print(output)

def version_compare(v1, v2, match_mode=False):
	vs1 = v1.split('.')
	vs2 = v2.split('.')
	end = min(len(vs1), len(vs2))
	for i in range(end):
		try:
			i1 = int(vs1[i])
		except:
			return 1
		try:
			i2 = int(vs2[i])
		except:
			return -1
		if i1 < i2:
			return -1
		if i2 < i1:
			return 1
	if len(vs1) < len(vs2):
		if match_mode:
			return 0
		return -1
	if len(vs2) < len(vs1):
		return 1
	return 0

def version_match(vmatch, version):
	if len(vmatch) > 2 and vmatch[:2] in ['<=', '!=', '>=']:
		matches = version_compare(vmatch[2:], version, match_mode = True)
		if vmatch[:2] == '<=' and (matches == 1 or matches == 0):
			return 1
		if vmatch[:2] == '>=' and (matches == -1 or matches == 0):
			return 1
		if vmatch[:2] == '!=' and (matches == -1 or matches == 1):
			return 1
	elif vmatch[0] in ['<', '=', '>']:
		matches = version_compare(vmatch[1:], version, match_mode = True)
		if vmatch[0] == '<' and matches == 1:
			return 1
		if vmatch[0] == '>' and matches == -1:
			return 1
		if vmatch[0] == '=' and matches == 0:
			return 1
	else:
		print('Error: invalid version matching string \'' + vmatch + '\'')
		raise Exception('Error: invalid version matching string \'' + vmatch + '\'')
	return 0


class ValueType:
	"""
	Class describing a value type. Necessary to translate results into
	a database scheme.
	"""
	def __init__(self, unit, datatype = 'int', description = None):
		"""
			unit, correct unit string
			datatype, one of 'str', 'int' or 'float'
			description, description string
		"""
		self.unit = unit
		self.description = description
		self.datatype = datatype

class Requirement:
	"""
	Requirement of any kind. Please also create Requirement objects for
	fullfilled requirements.
	"""
	def __init__(self, name, description = None, version=None, found=True):
		self.name = name
		self.description = description
		self.version = version
		self.found = found
	def missing(self):
		return not self.found
	def to_string(self):
		ret = self.name
		if self.version != None:
			ret += ' ' + self.version
		if self.description != None:
			ret += ' ' + self.description
		return ret

class Option:
	"""
	Available option. All available options are passed to the runner
	with a value. If you do not set a default, your runner should be
	able to handle None values.
	"""
	def __init__(self, name, description = None, default = None):
		self.name = name
		self.description = description
		self.default = default

class OptionValue:
	def __init__(self, option, args = None):
		self.option = option
		self.value = option.default
		if args == None:
			return
		if isinstance(args, dict):
			if option.name in args:
				self.value = args[option.name]
		elif isinstance(args, list):
			for i in args:
				argk, _, argv = i.partition('=')
				if argk == option.name:
					if argv == '':
						self.value = True
					else:
						self.value = argv
	def get_value():
		return self.value

class Plugin:
	def __init__(self, name, intern_version, description = None,
			available_options = None, requirements = None):
		self._plug_mod = None
		self.name = name
		self.description = description
		self.intern_version = intern_version
		self.available_options = _init_list(available_options)
		self.requirements = _init_list(requirements)
	def _print_data_only(self, indent=0, indent_str='  '):
		ind = _get_indentation(indent, indent_str)
		ind_deep = _get_indentation(indent + 1, indent_str)
		ind_deep2 = _get_indentation(indent + 2, indent_str)
		if self.description != None:
			print(ind + 'Description')
			_print_block_text(self.description, indent=indent+1,
					indent_str = indent_str)
		if self.intern_version != None:
			print(ind + 'Internal version: ' + self.intern_version)
		if self.requirements != None:
			missing = []
			fullfilled = []
			for req in self.requirements:
				if not req.missing():
					fullfilled.append(req.to_string())
					continue
				missing.append(req.to_string())
			if len(self.requirements) != 0:
				print(ind + 'Requirements')
			if len(missing) != 0:
				print(ind_deep + 'Missing')
				for req in missing:
					print(ind_deep2 + req)
			if len(fullfilled) != 0:
				print(ind_deep + 'Found')
				for req in fullfilled:
					print(ind_deep2 + req)


	def print(self, indent=0, indent_str='  '):
		ind = _get_indentation(indent, indent_str)
		print(ind + 'Plugin ' + self.name)
		self._print_data_only(indent+1, indent_str)
	def _generate_option_values(self, opts):
		vals = []
		print("nr opts " + str(len(self.available_options)))
		for opt in self.available_options:
			vals.append(OptionValue(opt, opts))
		return vals
	def get_missing_requirements(self):
		ret = []
		for i in self.requirements:
			if i.missing():
				ret.append(i)
		return ret
	def get_huid(self):
		huid = ''
		if self._mod != None:
			huid = self._mod.__name__ + '_'
		huid += self.name + '_'
		huid += self.intern_version
		return huid
	def cmp(self, plug):
		return version_compare(self.intern_version, plug.intern_version)



class Merger(Plugin):
	def print(self, indent=0, indent_str='  '):
		ind = _get_indentation(indent, indent_str)
		print(ind + 'Merger ' + self.name)
		self._print_data_only(indent+1, indent_str)
	pass

class Visualizer(Plugin):
	def print(self, indent=0, indent_str='  '):
		ind = _get_indentation(indent, indent_str)
		print(ind + 'Visualizer ' + self.name)
		self._print_data_only(indent+1, indent_str)
	pass

class BGLoad(Plugin):
	def print(self, indent=0, indent_str='  '):
		ind = _get_indentation(indent, indent_str)
		print(ind + 'BGLoad ' + self.name)
		self._print_data_only(indent+1, indent_str)
	pass

class BGLoadWrapped(Plugin):
	def __init__(self, benchmark):
		self.benchmark_plugin = benchmark
	def print(self, indent=0, indent_str='  '):
		ind = _get_indentation(indent, indent_str)
		print(ind + 'BGLoad Wrapped Benchmark')
		self.benchmark_plugin.print(indent+1, indent_str)


class DataCollector(Plugin):
	""" Benchmark class """
	def __init__(self, name, data_version, intern_version, description = None,
			valuetypes = None, requirements = None, available_options = None):
		super(DataCollector, self).__init__(name = name,
				description = description,
				intern_version = intern_version,
				requirements = requirements,
				available_options = available_options)
		if '.' in name or ',' in name:
			raise Exception("Error: '.' not allowed in name '"
					+ name + "'")
		self.data_version = data_version
		self.valuetypes = valuetypes

	def get_id(self):
		return hashlib.sha1(str(
				self.name
				+ self.data_version
				+ self.intern_version).encode('utf-8')).hexdigest()
	def get_huid(self):
		huid = super(DataCollector, self).get_huid() + '_'
		return huid + self.data_version

class Benchmark(DataCollector):
	def __init__(self, name, data_version, intern_version, description = None,
			valuetypes = None, requirements = None, available_options = None,
			nr_independent_values = 1):
		super(Benchmark, self).__init__(name = name,
				data_version = data_version,
				intern_version = intern_version,
				description = description,
				valuetypes = valuetypes,
				requirements = requirements,
				available_options = available_options)

		if nr_independent_values == None:
			self.nr_independent_values = len(valuetypes)
		else:
			self.nr_independent_values = nr_independent_values
	def print(self, indent=0, indent_str='  '):
		ind = _get_indentation(indent, indent_str)
		print(ind + 'Benchmark ' + self.name)
		self._print_data_only(indent+1, indent_str)

class Monitor(DataCollector):
	def print(self, indent=0, indent_str='  '):
		ind = _get_indentation(indent, indent_str)
		print(ind + 'Monitor ' + self.name)
		self._print_data_only(indent+1, indent_str)
	pass

class RunSetting:
	"""
	Settings for the execution of one or multiple benchmarks
	"""
	def __init__(self, min_runs = 2, min_runtime = 0, percent_stderr = 0,
			max_runtime = None, max_runs = None):
		""" min_runtime and max_runtime are runtimes per independent value """
		self.min_runs = min_runs
		self.min_runtime = min_runtime
		self.percent_stderr = percent_stderr
		self.max_runtime = max_runtime
		self.max_runs = max_runs

class PluginRunDef:
	"""
	Defines the run setup for one plugin. plugin_name is a plugin identifier.
	The instance is used to define benchsuite plugins or to translate
	command line arguments into objects. Every Plugin Run Definition is embedded
	into a RunCombination, even if it contains just one instance.
	"""
	def __init__(self, plugin_name, options_dict = None):
		self.plugin_name = plugin_name
		self.options_dict = _init_dict(options_dict)
		self._plugin = None
		self.is_bgload = False
	def _map_to_plugin(self, plugin_manager):
		p = plugin_manager.get_plugin_by_identifier(self.plugin_name)
		if isinstance(p, BGLoadWrapped):
			self.is_bgload = True
			self._plugin = p.benchmark_plugin
		else:
			self._plugin = p
	def _instantiate(self):
		runner = None
		try:
			opts = self._plugin._generate_option_values(self.options_dict)
			if isinstance(self._plugin, Benchmark):
				runner = self._plugin._plugin_mod.mod.create_benchmark(self._plugin.name, opts)
				if self.is_bgload:
					runner = BGLoadBenchRunner(runner)
			elif isinstance(self._plugin, Monitor):
				runner = self._plugin._plugin_mod.mod.create_monitor(self._plugin.name, opts)
			elif isinstance(self._plugin, BGLoad):
				runner = self._plugin._plugin_mod.mod.create_bgload(self._plugin.name, opts)
		except Exception as e:
			raise Exception("Problem creating an instance of a plugin for " + self.plugin_name + " " + str(e))
		if runner == None:
			raise Exception("Unknown type of plugin " + self.plugin_name)
		return runner
	def get_missing_requirements(self):
		return self._plugin.get_missing_requirements()

class RunCombination:
	def __init__(self, plugins, setting = None):
		self.plugins = plugins
		self.setting = setting
	def _gather_plugins(self, plugin_manager):
		for i in self.plugins:
			i._map_to_plugin(plugin_manager)
	def _instantiate(self):
		plugin_instances = []
		for i in self.plugins:
			plugin_instances.append(DefRunnerTuple(i, i._instantiate()))
		ctxt = RunContext(plugin_instances, self.setting)
		return ctxt
	def get_missing_requirements(self):
		ret = []
		for i in self.plugins:
			ret += i.get_missing_requirements()
		return ret


class Benchsuite(Plugin):
	def __init__(self, name, run_combos, version='1.0', description=None,
			setting = None):
		super(Benchsuite, self).__init__(name = name,
				description = description,
				intern_version = version)
		self.run_combos = run_combos
		self.setting = setting
		self.found_components = False
	def _gather_plugins(self, plugin_manager):
		for i in self.run_combos:
			i._gather_plugins(plugin_manager)
		self.found_components = True
	def _instantiate(self):
		ctxts = []
		for i in self.run_combos:
			ctxts.append((i, i._instantiate()))
		return SuiteContext(ctxts, self.setting)
	def get_missing_requirements(self):
		if not self.found_components:
			raise Exception('Benchsuite ' + self.name + ' not able to'
					' get missing requirements because some '
					'plugin identifiers failed to map to real plugins')
		ret = super(Benchsuite, self).get_missing_requirements()
		for i in self.run_combos:
			ret += i.get_missing_requirements()
		return ret

class DefRunnerTuple:
	def __init__(self, plug_def, runner):
		self.plug_def = plug_def
		self.runner = runner
		self.work_dir = None
	def run(self):
		self.runner.run(self.work_dir)
class DefResultTuple:
	def __init__(self, plug_def, result, time):
		self.plug_def = plug_def
		self.result = result
		self.time = time

class SuiteContext:
	def __init__(self, runctxts, settings = None):
		self.runctxts = runctxts
		self.settings = settings
	def execute(self, work_dir, remaining_runtime_others = 0):
		for i in self.runctxts:
			if glbl_shutdown:
				break
			i.execute(work_dir, remaining_runtime_others)

class InstallThread(threading.Thread):
	def __init__(self, runnertup):
		super(InstallThread, self).__init__()
		self.success = False
		self.runnertup = runnertup
	def run(self):
		try:
			print(self.runnertup.work_dir)
			os.makedirs(self.runnertup.work_dir, exist_ok=True)
		except Exception as e:
			print("Error creating work dir for plugin " + self.runnertup.plugin._plugin.name)
			self.success = False
			return
		self.success = self.runnertup.runner.install(self.runnertup.plug_def._plugin._plugin_mod.prepare_path, self.runnertup.work_dir)
		if not self.success:
			print("Error: Failed installing plugin " + self.runnertup.plugin.name)
class UninstallThread(threading.Thread):
	def __init__(self, runnertup):
		super(UninstallThread, self).__init__()
		self.success = False
		self.runnertup = runnertup
	def run(self):
		self.success = self.runnertup.runner.uninstall(self.runnertup.work_dir)
		try:
			shutil.rmtree(self.runnertup.work_dir)
		except Exception as e:
			print("Error removing work dir for plugin " + self.runnertup.plugin._plugin.name)
			self.success = False

		if not self.success:
			print("Error: Failed uninstalling plugin " + self.runnertup.plugin._plugin.name)
class RunnerThread(threading.Thread):
	def __init__(self, runnertup):
		super(RunnerThread, self).__init__()
		self.success = False
		self.runnertup = runnertup
	def run(self):
		self.success = self.runnertup.run()
	def send_stop(self):
		self.runnertup.stop()
class MonitorThread(threading.Thread):
	def __init__(self, runnertups):
		super(MonitorThread, self).__init__()
		self.data = []
		self.runnertups = runnertups
		self.shutdown = False
	def run(self):
		sleep_tgt = time.time()
		while not self.shutdown:
			run_data = []
			for i in self.runnertups:
				now = time.time()
				dat = i.runner.run(i.work_dir)
				result = DefResultTuple(i.plugin, dat, now)
				run_data.append(result)
			self.data.append(run_data)
			now = time.time()
			sleep_time = max(0, sleep_tgt + 1 - now)
			sleep_tgt = now + sleep_time
			time.sleep(sleep_time)
	def send_stop(self):
		self.shutdown = True


class RunContext:
	types = ['benchmarks', 'bgloads', 'monitors']


	def __init__(self, runnertuple, settings=None):
		self.benchmarks = []
		self.bgloads = []
		self.monitors = []
		for i in runnertuple:
			if isinstance(i.runner, BenchmarkRunner):
				self.benchmarks.append(i)
			elif isinstance(i.runner, MonitorRunner):
				self.monitors.append(i)
			elif isinstance(i.runner, BGLoadRunner)\
					or isinstance(i.runner, BGLoadBenchRunner):
				self.bgloads.append(i)
			else:
				print(i.runner)
				raise Exception("Error: Unknown instance type for plugin " + i.plugin._plugin.name)
		self.run_ct = 0
		self.time_started = -1
	def execute(self, work_dir, remaining_runtime_others = 0):
		ct = 0
		for typ in self.types:
			vallist = getattr(self, typ)
			for i in vallist:
				i.work_dir = os.path.join(work_dir, str(ct))
				ct += 1
		threads = []
		for typ in self.types:
			vallist = getattr(self, typ)
			print(len(vallist))
			for i in vallist:
				t = InstallThread(i)
				t.start()
				threads.append(t)
		success = True
		for t in threads:
			t.join()
			if not t.success:
				success = False
		self.time_started = time.time()
		while success and not glbl_shutdown:
			for i in self.bgloads:
				i.runner.pre(i.work_dir)
			for i in self.benchmarks:
				i.runner.pre(i.work_dir)

			bgload_threads = []
			bench_threads = []
			monitor_thread = MonitorThread(self.monitors)
			for i in self.bgloads:
				t = RunnerThread(i)
				bgload_threads.append(t)
			for i in self.benchmarks:
				t = RunnerThread(i)
				bench_threads.append(t)


			for i in self.monitors:
				i.runner.pre(i.work_dir)
			for t in bgload_threads:
				t.start()
			monitor_thread.start()
			for t in bench_threads:
				t.start()

			# Everything is running now, wait for benchmarks

			for i in bench_threads:
				t.join()
			monitor_thread.send_stop()
			for t in bgload_threads:
				t.send_stop()
			monitor_thread.join()
			for t in bgload_threads:
				t.join()

			for i in self.bgloads:
				i.runner.post(i.work_dir)
			for i in self.benchmarks:
				dat = i.runner.post(i.work_dir)
				print(dat)
			for i in self.monitors:
				i.runner.post(i.work_dir)


			# one run
			self.run_ct += 1


		threads = []
		for typ in self.types:
			vallist = getattr(self, typ)
			for i in vallist:
				t = UninstallThread(i)
				t.start()
				threads.append(t)
		for t in threads:
			t.join()
			if not t.success:
				success = False
		return success
	def remaining_runtime(self):
		return 10

class Runner:
	def run(self, work_dir):
		raise NotImplementedError('Runner run not implemented')
	def install(self, preperation_path, work_dir):
		return True
	def uninstall(self, work_dir):
		return True
	def pre(self, work_dir):
		return True
	def post(self, work_dir):
		return True

class BenchmarkRunner(Runner):
	def post(self):
		raise NotImplementedError('post not implemented, you have to return'
				+ ' the results here')
	def check_stderr(self, last_results, percent_stderr):
		raise NotImplementedError()

class MonitorRunner(Runner):
	pass

class BGLoadRunner(Runner):
	def stop(self):
		raise NotImplementedError('not stopable bgload runner')

class BGLoadBenchRunner(BGLoadRunner):
	def __init__(self, bench_runner):
		self.bench_runner = bench_runner
		self.shutdown = False
	def install(self, preperation_path, work_dir):
		return self.bench_runner.install(preperation_path, work_dir)
	def uninstall(self, work_dir):
		return self.bench_runner.uninstall(work_dir)
	def pre(self, work_dir):
		return self.bench_runner.pre(work_dir)
	def post(self, work_dir):
		return self.bench_runner.post(work_dir)
	def run(self, work_dir):
		self.bench_runner.run(work_dir)
		while not self.shutdown:
			self.bench_runner.post()
			self.bench_runner.pre()
			self.bench_runner.run()
	def stop(self):
		self.shutdown = True




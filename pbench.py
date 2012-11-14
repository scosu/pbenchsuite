#/usr/bin/python3

import hashlib
import subprocess
import os

def get_executable_path(name):
	for path in os.environ['PATH'].split(os.pathsep):
		exec_path = os.path.join(path, name)
		if os.path.isfile(exec_path) and os.access(exec_path, os.X_OK):
			return exec_path
	return None

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

class ValueType:
	""" Class describing a value type """
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
	""" Requirement of any kind """
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
		self._plugin_mod = None
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
		for opt in self.available_options:
			vals.append(OptionValue(opt, opts))
		return vals
	def get_missing_requirements(self):
		ret = []
		for i in self.requirements:
			if i.missing():
				ret.append(i)
		return ret



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
	def __init__(self, min_runs = 2, min_runtime = 0, percent_stderr = 0,
			max_runtime = None, max_runs = None):
		""" min_runtime and max_runtime are runtimes per independent value """
		self.min_runs = min_runs
		self.min_runtime = min_runtime
		self.percent_stderr = percent_stderr
		self.max_runtime = max_runtime
		self.max_runs = max_runs

class PluginRunDef:
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
				runner = self._plugin._plugin_mod.create_benchmark(self._plugin.name, opts)
				if self.is_bgload:
					runner = BGLoadBenchRunner(runner)
			elif isinstance(self._plugin, Monitor):
				runner = self._plugin._plugin_mod.create_monitor(self._plugin.name, opts)
			elif isinstance(self._plugin, BGLoad):
				runner = self._plugin._plugin_mod.create_bgload(self._plugin.name, opts)
		except Exception as e:
			raise Exception("Problem creating an instance of a plugin for " + self.plugin_name + " " + str(e))
		if runner == None:
			raise Exception("Unknown type of plugin " + self.plugin_name)
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
	def __init__(self, plugin, runner):
		self.plugin = plugin
		self.runner = runner
class DefResultTuple:
	def __init__(self, plugin, result):
		self.plugin = plugin
		self.result = result

class SuiteContext:
	def __init__(self, runctxts, settings = None):
		self.runctxts = runctxts
		self.settings = settings

class RunContext:
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
	def execute(self):
		while True:
			# one run
			pass
	def remaining_runtime(self):
		return 10

class Runner:
	def run(self):
		raise NotImplementedError('Runner run not implemented')
	def install(self, preperation_path):
		return True
	def uninstall(self):
		return True
	def pre(self):
		return True
	def post(self):
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
	def install(self, preperation_path):
		return self.bench_runner.install(preperation_path)
	def uninstall(self):
		return self.bench_runner.uninstall()
	def pre(self):
		return self.bench_runner.pre()
	def post(self):
		return self.bench_runner.post()
	def run(self):
		self.bench_runner.run()
		while not self.shutdown:
			self.bench_runner.post()
			self.bench_runner.pre()
			self.bench_runner.run()
	def stop(self):
		self.shutdown = True




#/usr/bin/python3

import hashlib

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

class Option:
	def __init__(self, name, description = None, default = None):
		self.name = name
		self.description = description
		self.default = default

class OptionValue:
	def __init__(self, option, args = []):
		self.value = option.default
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
			available_options = []):
		self.__plugin_obj = None
		self.name = name
		self.description = description
		self.intern_version = intern_version
		self.available_options = available_options

class Merger(Plugin):
	pass

class Visualizer(Plugin):
	pass

class BGLoad(Plugin):
	pass


class DataCollector(Plugin):
	""" Benchmark class """
	def __init__(self, name, data_version, intern_version, description = None,
			valuetypes = {}, requirements = [], available_options = []):
		"""
			name, is a unique name for this benchmark
			data_version, string about datastructure version, every
				change to the datastructure returned has to increase
				the datastructure version
			intern_version, string of concatenated versions of internally
				used software
			description, optional description of this benchmark
			valuetypes, dict of name => value_type-object
			requirements, List of requirement objects
			available_options, list of option objects
		"""
		super(Plugin, self).__init__(name = name,
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
			valuetypes = {}, requirements = [], available_options = [],
			nr_independent_values = 1):
		""" nr_independent_values should be the number of independent values
			measured by this benchmark in one round"""
		super(DataCollector, self).__init__(name = name,
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

class Monitor(DataCollector):
	pass

class BenchmarkRunner:
	def run(self):
		raise NotImplementedError('run not implemented')
	def install(self, preperation_path, install_path):
		return True
	def uninstall(self, install_path):
		return True
	def pre(self):
		return True
	def post(self):
		raise NotImplementedError('post not implemented, you have to return'
				+ ' the results here')
	def check_stderr(self, last_results, percent_stderr):
		raise NotImplementedError()

class MonitorRunner:
	def install(self, preperation_path, install_path):
		return True
	def uninstall(self, install_path):
		return True
	def init(self):
		return True
	def acquire_data(self):
		raise NotImplementedError('acquire_data not implemented, you have'
				+ ' to implement this function for a monitor')
	def shutdown(self):
		return True

class RunSetting:
	def __init__(self, min_runs = 2, min_runtime = 0, percent_stderr = 0,
			max_runtime = None, max_runs = None):
		""" min_runtime and max_runtime are runtimes per independent value """
		self.min_runs = min_runs
		self.min_runtime = min_runtime
		self.percent_stderr = percent_stderr
		self.max_runtime = max_runtime
		self.max_runs = max_runs

class RunCombination:
	def __init__(self, benchmarks, bgload=[], monitors=[], setting = None):
		self.benchmarks = benchmarks
		self.bgload = bgload
		self.monitors = monitors
		self.setting = setting

class Benchsuite:
	def __init__(self, run_combos, mergers = ['generic'],
			visualizers = ['generic'], setting = None):
		self.run_combos = run_combos
		self.mergers = mergers
		self.visualizers = visualizers
		self.setting = setting

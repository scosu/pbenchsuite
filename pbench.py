#/usr/bin/python3

import hashlib

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
			available_options = None, requirements = None):
		self.__plugin_mod = None
		self.name = name
		self.description = description
		self.intern_version = intern_version
		self.available_options = available_options
		self.requirements = requirements
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
		print(ind + 'BGLoader ' + self.name)
		self._print_data_only(indent+1, indent_str)
	pass


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
	def __init__(self, benchmarks, bgload = None, monitors = None, setting = None):
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

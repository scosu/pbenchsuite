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

class DataMerger:
	def __init__(self):
		self.bla = None
class DataVisualizer:
	def __init__(self):
		self.bla = None

class DataCollector:
	""" Benchmark class """
	def __init__(self, name, data_version, intern_version, description = None, valuetypes = {}, requirements = [], available_options = []):
		"""
			name, is a unique name for this benchmark
			data_version, string about datastructure version, every change to the datastructure returned has to increase the datastructure version
			intern_version, string of concatenated versions of internally used software
			description, optional description of this benchmark
			valuetypes, dict of name => value_type-object
			requirements, List of requirement objects
			available_options, list of option objects
		"""
		if '.' in name:
			raise Exception("Error: '.' not allowed in benchmark name '" + name + "'")
		self.name = name
		self.data_version = data_version
		self.intern_version = intern_version
		self.description = description
		self.valuetypes = valuetypes
		self.requirements = requirements
		self.available_options = available_options

	def get_id(self):
		return hashlib.sha1(str(
					self.name
					+ self.data_version
					+ self.intern_version).encode('utf-8')).hexdigest()

class Benchmark(DataCollector):
	benchmark = True
	monitor = False

class Monitor(DataCollector):
	benchmark = False
	monitor = True

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
		raise NotImplementedError('post not implemented, you have to return the results here')
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
		raise NotImplementedError('acquire_data not implemented, you have to implement this function for a monitor')
	def shutdown(self):
		return True


import pbench

def register():
	rq1 = pbench.Requirement('randomlib', version='>2.0', found=False)
	rq2 = pbench.Requirement('randomlib2', version='<1.5-rc1', found=True)
	valuetypedict = {}
	valuetypedict['date'] = pbench.ValueType('s', description='unix timestamp',
					datatype = 'float')
	opt1 = pbench.Option('option1', description='option1, if present, enables bla')
	opt2 = pbench.Option('option2', description='option2 int threads')
	b1 = pbench.Benchmark(
			"dummy1",
			data_version = "1.0",
			intern_version = "bzip2_gzip1",
			description = 'dummy1 is the first out of two dummy ' +
					'benchmarks that should help you to ' +
					'understand pbenchsuite.',
			requirements = [rq1],
			valuetypes = valuetypedict)
	b2 = pbench.Benchmark(
			"dummy2",
			data_version = "1.0",
			intern_version = "1.0",
			description = 'dummy2 is the second dummy',
			requirements = [rq1, rq2],
			valuetypes = valuetypedict,
			available_options = [opt1, opt2])
	monitor1 = pbench.Monitor(
			"dummy_monitor",
			data_version = ".0",
			intern_version = "1.0",
			description = 'this is the registration of a dummy monitor',
			valuetypes = valuetypedict)
	runcombo1 = pbench.RunCombination([pbench.PluginRunDef('benchmark.dummy1'),
					pbench.PluginRunDef('bgload.dummy1'),
					pbench.PluginRunDef('dummy_monitor')])
	runcombo2 = pbench.RunCombination([pbench.PluginRunDef('benchmark.dummy1'),
					pbench.PluginRunDef('benchmark.dummy2')])
	suite1 = pbench.Benchsuite('testbenchsuite', [runcombo1, runcombo2])
	return [b1, b2, monitor1, suite1]

def prepare_installation(preperation_path):
	# Prepare all datafiles and everything for the installation.
	# The installation is executed just before running the benchmark in a
	# working directory.
	# preperation_path is a created, empty directory where you can store
	# downloads or similar things.

	# return True for successfull preparation
	return True

class dummy_run(pbench.BenchmarkRunner):
	def run():
		self.time = time.time()
		return True
	def post():
		result = {}
		result['date'] = self.time
		self.time = 0
		return result

def create_benchmark(benchmark_name, options):
	return dummy_run()

def create_monitor(monitor_name, options):
	return

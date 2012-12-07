import pbench
import multiprocessing
import subprocess
import re

exec_7z = None

def register():
	global exec_7z

	exec_7z = pbench.get_executable_path('7z')
	req = pbench.Requirement('7z', found=(exec_7z != None))

	valuetypedict = {}
	valuetypedict['decompression'] = pbench.ValueType('MIPS',
			description='Decompression performance in MIPS, more is better.',
			datatype = 'int')
	valuetypedict['compression'] = pbench.ValueType('MIPS',
			description='Compression performance in MIPS, more is better.',
			datatype = 'int')
	opt_nrthreads = pbench.Option('nrthreads',
			description='Number threads used for benchmarking',
			default=str(multiprocessing.cpu_count()))
	opt_dictsize = pbench.Option('dictsize',
			description='Dictionary size',
			default='22')

	version = 'unknown'
	if exec_7z:
		version_str = subprocess.check_output([exec_7z, '-h'])
		for line in version_str.decode().splitlines():
			m = re.match('^p7zip Version (\d+\.\d+) .*$', line)
			if m == None:
				continue
			version = m.group(1)
			break

	b1 = pbench.Benchmark(
			"7zip-bench",
			data_version = "1.0",
			intern_version = version,
			description = '7zip compression/decompression benchmark. CPU-intensive 7zip benchmark. Not using files.',
			requirements = [req],
			valuetypes = valuetypedict,
			nr_independent_values = 2,
			available_options = [opt_nrthreads, opt_dictsize])
	return [b1]

class zip7_run(pbench.BenchmarkRunner):
	class zip7_result:
		def __init__(self, compression, decompression):
			self.compression = compression
			self.decompression = decompression
	def __init__(self, options):
		cmd = [exec_7z, 'b']
		for opt in options:
			if opt.option.name == 'nrthreads':
				cmd.append('-mmt' + opt.value)
			elif opt.option.name == 'dictsize':
				self.dictsize = opt.value
				cmd.append('-md' + opt.value)
		self.cmd = cmd
		print(' '.join(cmd))
		self.stdout = None
		self.stderr = None
	def run(self, work_dir):
		p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.stdout, self.stderr = p.communicate()
		if p.returncode == 0:
			return True
		else:
			return False
	def post(self, work_dir):
		err = self.stderr.decode().strip()
		if err != '':
			print('7zip benchmark stderr:')
			print(err)
			return None
		result = None
		for line in self.stdout.decode().splitlines():
			m = re.match('^' + self.dictsize + ':\s+\d+\s+\d+\s+\d+\s+(\d+)\s*|\s+\d+\s+\d+\s+\d+\s+(\d+)\s*$', line)
			if m != None:
				result = self.zip7_result(m.group(1), m.group(2))
				break
		return result

def create_benchmark(benchmark_name, options):
	return zip7_run(options)

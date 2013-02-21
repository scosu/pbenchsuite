#!/usr/bin/python

import argparse
import pkgutil
import logging
import traceback
import threading
import os
import sys
import signal

import pbench
import plugin

logging.basicConfig()
log = logging.getLogger()

glbl_shutdown = False

def sig_handler(signum, frame):
	global glbl_shutdown
	if glbl_shutdown:
		print("Forced shutdown, there may be child processes left running")
		sys.exit(1)
	print("Triggered shutdown, waiting for tasks to finish, this may take a while")
	glbl_shutdown = True
	pbench.glbl_shutdown = True

signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)

plugin_types = ['bgload', 'benchmark', 'cooldown', 'monitor', 'visualizer', 'merger', 'benchsuite', 'sysinfo']

def category_to_type(cat):
	cat = cat.lower()
	if cat == 'bench' or cat == 'benchmark':
		return 'benchmark'
	if cat == 'load' or cat == 'bgload':
		return 'bgload'
	if cat == 'suite' or cat == 'benchsuite':
		return 'benchsuite'
	if cat == 'monitor' or cat == 'mon':
		return 'monitor'
	if cat == 'vis' or cat == 'plot' or cat == 'plotter' or cat == 'visualizer':
		return 'visualizer'
	if cat == 'merger':
		return 'merger'
	log.info('Unknown category ' + cat)
	return ''

class PluginModule:
	def __init__(self, mod, prepare_path):
		self.mod = mod
		self.benchmark = {}
		self.monitor = {}
		self.bgload = {}
		self.visualizer = {}
		self.merger = {}
		self.benchsuite = {}
		self.sysinfo = {}
		self.prepare_path = os.path.join(prepare_path, mod.__name__)

	def print(self, indent = 0, indent_str = '  '):
		ind = pbench._get_indentation(indent, indent_str)
		print(ind + 'Module ' + self.mod.__name__)


class PluginManager:
	def __gather_benchsuite_plugins(self):
		exceptions = []
		for k in self.benchsuite.keys():
			v = self.benchsuite[k]
			try:
				v._gather_plugins(self)
			except Exception as e:
				log.error('Benchsuite ' + k + ' did not find all'
						+ ' necessary plugins: ' + str(e))
				exceptions.append(k)
		for i in exceptions:
			del self.benchsuite[i]
	def __init__(self, prepare_dir):
		self.module = {}
		self.benchmark = {}
		self.bgload = {}
		self.monitor = {}
		self.visualizer = {}
		self.merger = {}
		self.sysinfo = {}
		self.benchsuite = {}
		try:
			if not os.path.isdir(prepare_dir):
				os.makedirs(prepare_dir, exist_ok=True)
		except Exception as e:
			print("Error, failed to create prepare directory " + prepare_dir + " " + str(e))
			raise e

		for _, name, ispkg in pkgutil.walk_packages(plugin.__path__):
			if ispkg:
				continue
			log.debug('Found plugin file ' + name + ', importing...')
			m = __import__('plugin.' + name)
			mod = getattr(m, name)
			plug = PluginModule(mod, prepare_dir)

			log.debug('Loading available plugins from module ' + name)
			try:
				plugins = mod.register()
			except Exception as e:
				log.error('Plugin module ' + name + ' does not' +
						' implement a register() method? ' + str(e))
				log.error(traceback.format_exc())
				continue

			for i in plugins:
				plug_type = None
				if isinstance(i, pbench.BGLoad):
					plug_type = 'bgload'
				elif isinstance(i, pbench.Benchmark):
					plug_type = 'benchmark'
				elif isinstance(i, pbench.Monitor):
					plug_type = 'monitor'
				elif isinstance(i, pbench.Visualizer):
					plug_type = 'visualizer'
				elif isinstance(i, pbench.Merger):
					plug_type = 'merger'
				elif isinstance(i, pbench.Benchsuite):
					plug_type = 'benchsuite'
				elif isinstance(i, pbench.SysInfo):
					plug_type = 'sysinfo'

				if plug_type == None:
					log.error(name + ": Unknown plugin type, object " + str(i))
					continue

				if i.name in getattr(self, plug_type):
					log.error(name + ': ' + plug_type + ' ' + i.name + ' already exists')
					continue
				if i.name in plug.bgload:
					log.error(name + ': Double definition ' + plug_type + ' ' + i.name)
					continue
				ins_dict = getattr(plug, plug_type)
				if i.name not in ins_dict:
					ins_dict[i.name] = PluginSet()
				ins_dict[i.name].add(i)

				i._plugin_mod = plug



			log.debug('Module ' + name + ' defines valid plugins')
			# Everything was successfull, store the module
			self.module[name] = plug
			for typ in plugin_types:
				for k,v in getattr(plug, typ).items():
					getattr(self, typ)[k] = v
		self.__gather_benchsuite_plugins()

	def print_modules(self, indent=0, indent_str='  ', by_modules = False,
			by_plugins=True):
		ind = pbench._get_indentation(indent, indent_str)
		if by_modules:
			for k in sorted(self.module.keys()):
				v = self.module[k]
				v.print(indent + 1, indent_str)
		if by_plugins:
			for typ in sorted(plugin_types):
				typdict = getattr(self, typ)
				if len(typdict) == 0:
					continue
				print(ind + typ)
				for k in sorted(typdict.keys()):
					v = typdict[k]
					v.print(indent = indent + 1, indent_str = indent_str)
					print("")

	# see identifier specifications for the full grammar
	def parse_full_identifiers(self, data):
		ctxts = data.split(';')
		for ctxt in ctxts:
			ctxt, s, option_part = ctxt.partition(':')
			ctxt, s, ver_part = ctxt.partition('@')
			ver_part = ver_part

			ver_conditions = ver_part.split('@')

			option_dict = {}
			for i in option_part.split(':'):
				optk, s, optv = i.partition('=')
				if s == '':
					option_dict[optk] = True
				else:
					option_dict[optk] = optv

			plugin_type, s, plugin_name = ctxt.partition('.')
			if s == '':
				plugin_name = plugin_type
				plugin_type = ''

	def get_plugins_by_identifier(self, id, category=None):
		type_filter = None
		if category != None:
			typ = category_to_type(category)
			name = id
			type_filter = typ
		else:
			cat, sep, name = id.partition('.')
			if sep == '.':
				typ = category_to_type(cat)
				if typ != '':
					type_filter = typ
			else:
				name = cat

		ret = []
		for typ in plugin_types:
			if type_filter != None and type_filter != typ:
				continue
			typ_dict = getattr(self, typ)
			if name == '':
				ret += typ_dict.values()
				continue
			if name in typ_dict:
				ret.append(typ_dict[name])
		if type_filter == 'bgload' and (name == '' or len(ret) == 0):
			if name == '':
				new = []
				for i in self.benchmark.values():
					new.append(pbench.BGLoadWrapped(i))
				ret = new + ret
			elif name in self.benchmark:
				ret = [pbench.BGLoadWrapped(self.benchmark[name])] + ret
		if len(ret) == 0:
			log.error('Could not find plugin matching identifier ' + id)
		return ret
	def get_plugin_by_identifier(self, id, category=None):
		ret = self.get_plugins_by_identifier(id, category)
		if len(ret) != 1:
			raise Exception("Could not find necessary plugin " + id)
		return ret[0]
	def get_all_plugins(self):
		plugs = []
		for typ in plugin_types:
			plugs += getattr(self, typ).values()
		return plugs
	def get_all_modules(self):
		return list(self.module.values())

class PluginSet:
	"""PluginSet gathers all different versions of one plugin name"""
	def __init__(self):
		self.sorted_plugins = []
	def add(self, plug):
		self.sorted_plugins.append(plug)
		self.sorted_plugins.sort()
	def print(self, indent=0, indent_str='  '):
		ind = pbench._get_indentation(indent+1, indent_str)
		self.sorted_plugins[0].print(indent, indent_str)
		if len(self.sorted_plugins) > 1:
			print(ind + "Other available versions:")
			for i in self.sorted_plugins[1:]:
				i.print_version(indent+2, indent_str)
	def _gather_plugins(self, pm):
		for p in self.sorted_plugins:
			p._gather_plugins(pm)

def plugins_to_modules(plugins):
	modules = []
	for i in plugins:
		if i._plugin_mod in modules:
			continue
		modules.append(i._plugin_mod)
	return modules

def check_plugins_requirements(plugins):
	missing = []
	for i in plugins:
		missing += i.get_missing_requirements()
	if len(missing) == 0:
		return True
	print('Missing requirements:')
	for i in set(missing):
		print('    ' + i.to_string())
	return False


def prepare_plugins(plugins):
	if not check_plugins_requirements(plugins):
		return False
	modules = plugins_to_modules(plugins)
	success = True
	prepare_threads = []
	class PrepareThread(threading.Thread):
		def __init__(self, mod, mod_path):
			super(PrepareThread, self).__init__()
			self.mod = mod
			self.mod_path = mod_path
		def run(self):
			ret = False
			try:
				ret = mod.prepare_installation(self.mod_path)
			except Exception as e:
				log.error(str(e))
				pass
			if not ret:
				log.error("Error in preparing " + self.mod.__name__)
				success = False
	for mod in modules:
		if 'prepare_installation' not in dir(mod):
			continue
		mod_path = os.path.expanduser(os.path.join(parsed.package_dir, mod.__name__))
		try:
			os.makedirs(mod_path, exist_ok = True)
		except Exception as e:
			log.debug('Failed to create dir ' + mod_path + ' ' + str(e))
			pass
		if not os.path.isdir(mod_path):
			log.error('Error preparing ' + mod.__name__ + ', could not create dir ' + mod_path)
			continue
		t = PrepareThread(mod, mod_path)
		prepare_threads.append(t)
		log.info('Preparing ' + mod.__name__)
		t.start()
	for t in prepare_threads:
		t.join()
	log.info('Finished prepare installation, success: ' + str(success))
	return success

def cmd_info(parsed):
	p = PluginManager(os.path.expanduser(parsed.package_dir))
	if len(parsed.identifier) == 0:
		p.print_modules(indent_str='    ')
	else:
		items = []
		for id in parsed.identifier:
			items += p.get_plugins_by_identifier(id)
		for i in items:
			i.print(indent_str='    ')
			print("")

def cmd_prepare(parsed):
	p = PluginManager(os.path.expanduser(parsed.package_dir))
	plugs = []
	if len(parsed.identifier) == 0:
		plugs = p.get_all_plugins()
	else:
		plugs = []
		for id in parsed.identifier:
			plugs += p.get_plugins_by_identifier(id)
	return prepare_plugins(plugs)


def cmd_run(parsed):
	plugins = []
	p = PluginManager(os.path.expanduser(parsed.package_dir))
	for combo in parsed.bench:
		# parse <ID>;<ID>:<OPTION>,<OPTION>;<ID>
		for id in combo.split(';'):
			name = id.split(':')[0]
			plugins.append(p.get_plugin_by_identifier(id))
	status = prepare_plugins(plugins)
	if not status:
		log.error("Failed to prepare all modules, not able to start run")
		return False

	# List of RunCombination and Benchsuite objects
	run_definitions = []
	for combo in parsed.bench:
		benchs = combo.split(';')
		if len(benchs) == 1:
			name, s, optionstr = benchs[0].partition(':')
			plug = p.get_plugin_by_identifier(name)
			if s == '' and isinstance(plug, pbench.Benchsuite):
				run_definitions.append(plug)
				continue

		has_suite = False
		plug_run_defs = []
		for bench in benchs:
			name, s, optionstr = bench.partition(':')
			options = {}
			for opt in optionstr.split(','):
				opt_k, opt_s, opt_v = opt.partition('=')
				if opt_k in options:
					print('Error: Option ' + opt_k + ' defined twice for name ' + name)
					return False
				if opt_s == '':
					options[opt_k] = True
				else:
					options[opt_k] = opt_v
			plugin = p.get_plugin_by_identifier(name)
			if isinstance(plugin, pbench.Benchsuite):
				if has_suite:
					print('Error: ' + combo + ' contains at least two benchsuites.')
					return False
				has_suite = True
				plug_run_defs += plugin.run_combos
			elif isinstance(plugin, pbench.Benchmark)\
					or isinstance(plugin, pbench.BGLoad)\
					or isinstance(plugin, pbench.BGLoadWrapped)\
					or isinstance(plugin, pbench.Monitor):
				plug_run_defs.append(pbench.PluginRunDef(name, options))
			elif isinstance(plugin, pbench.Merger) or\
					isinstance(plugin, pbench.Visualizer):
				print('Error: ' + combo + ' contains merger or visualizer. Please use \'plot\' command.')
				return False
			else:
				print('Error: ' + bench + ' defines unknown plugin')
				return False
		run_definitions.append(pbench.RunCombination(plug_run_defs))

	for i in run_definitions:
		i._gather_plugins(p)

	run_instances = []

	for i in run_definitions:
		run_instances.append(i._instantiate())


	if parsed.work_dir == None:
		work_dir = os.path.expanduser('~/.pbenchsuite/work_dirs/' + str(os.getpid()))
	else:
		work_dir = parsed.work_dir

	print(len(run_instances))

	for i in run_instances:
		i.execute(work_dir)

	return True


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-l', '--loglevel', default='WARN')
	parser.add_argument('--package_dir', default='~/.pbenchsuite/install_data/')

	parse_cmds = parser.add_subparsers()


	parser_info = parse_cmds.add_parser('info',
			help='Information about plugins and pbenchsuite')
	parser_info.add_argument('identifier', nargs='*', help='[[(bench|suite|monitor|merger|plotter)].][name]')
	parser_info.set_defaults(func=cmd_info)


	parser_prepare = parse_cmds.add_parser('prepare',
			help='Information about plugins and pbenchsuite')
	parser_prepare.add_argument('identifier', nargs='*', help='[[(bench|suite|monitor|merger|plotter)].][name]')
	parser_prepare.set_defaults(func=cmd_prepare)


	parser_merge = parse_cmds.add_parser('merge',
			help='Merge multiple databases into one')


	parser_print = parse_cmds.add_parser('print',
			help='Print database')


	parser_run = parse_cmds.add_parser('run',
			help='Run benchmarks and/or benchsuites',
			formatter_class=argparse.RawTextHelpFormatter)
	parser_run.set_defaults(func=cmd_run)
	parser_run.add_argument('-w', '--work_dir', default=None)
	parser_run.add_argument('-s', '--sysinfo', default='',
			help="Additional system information about the current system state.")
	parser_run.add_argument('-d', '--database', default='~/.pbenchsuite/results.sqlite',
			help="Database where to store the results.\nDefault:"
				+ ' ~/.pbenchsuite/results.sqlite')
	parser_run.add_argument('bench', nargs='+',
			help='''
bench arguments consist of a comma-seperated list
of '<category>.<name>' tuples. Category is one
of bench (benchmark), suite (benchsuite), bgload
(backgroundload) or monitor. Name is a name of a
plugin, which may refer to any plugin type. Name is
not necessarily the same as the filename. Use the
command 'pbenchsuite.py info' for information about
the available plugins. You can add options to every
category by adding ':OPTION=VALUE;OPTION2=VALUE'
and so on. Here are some examples:

Run benchmarks dummy1 and dummy2 at the same time
and use Monitor dummy

	bench.dummy1,bench.dummy2,monitor.dummy

Run a benchmark or loadgenerator in background while
benchmarking dummy1

	bench.dummy1,bgload.dummyload

Run a benchsuite with additional monitor
dummymon.  Other benchmarks or benchsuites
are not allowed in such a statement including
a benchsuite.

	suite.scheduler,monitor.dummymon
	suite.scheduler,monitor.dummymon,bgload.dummyload
			''')
	parser_run.add_argument('--min_runs', type=int, help='Repeat each benchmark at least min_runs times.')
	parser_run.add_argument('--max_runs', type=int, help='Repeat each benchmark at most max_runs times.')
	parser_run.add_argument('--min_runtime', type=int, help='Minimum runtime per independent value in seconds.')
	parser_run.add_argument('--max_runtime', type=int, help='Maximum runtime per independent value in seconds.')
	parser_run.add_argument('--percent_stderr', type=float, help=
'''Limit standard error to percent_stderr *
mean. pbenchsuite tries to repeat the benchmark as
long as this is smaller than the real standard error.''')


	parser_plot = parse_cmds.add_parser('plot',
			help='Plot/Visualize results')
	parser_plot.add_argument('-d', '--database', action='append',
			default='~/.pbenchsuite/results.sqlite',
			help='Database from where to load the data, -d can be '
				+ 'added multiple times. Default:'
				+ ' ~/.pbenchsuite/results.sqlite')






	parsed = parser.parse_args()
	log.setLevel(parsed.loglevel.upper())
	ret = parsed.func(parsed)
	if ret:
		sys.exit(0)
	else:
		sys.exit(-1)

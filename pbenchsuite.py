#!/usr/bin/python

import argparse
import pkgutil
import logging
import traceback

import pbench
import plugin

log = logging.getLogger()

class PluginModule:
	def __init__(self, mod):
		self.mod = mod
		self.benchmark = {}
		self.monitor = {}
		self.bgload = {}
		self.visualizer = {}
		self.merger = {}


class PluginManager:
	def __init__(self):
		self.module = {}
		self.benchmark = {}
		self.bgload = {}
		self.monitor = {}
		self.visualizer = {}
		self.merger = {}

		for _, name, ispkg in pkgutil.walk_packages(plugin.__path__):
			if ispkg:
				continue
			log.info('Found plugin file ' + name + ', importing...')
			m = __import__('plugin.' + name)
			mod = getattr(m, name)
			plug = PluginModule(mod)

			log.info('Loading available plugins from module ' + name)
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

				if plug_type == None:
					log.error(name + ": Unknown plugin type, object " + str(i))
					continue

				if i.name in getattr(self, plug_type):
					log.error(name + ': ' + plug_type + ' ' + i.name + ' already exists')
					continue
				if i.name in plug.bgload:
					log.error(name + ': Double definition ' + plug_type + ' ' + i.name)
					continue
				getattr(plug, plug_type)[i.name] = i




			# Everything was successfull, store the module
			self.modules[name] = mod






def cmd_info(parsed):
	p = PluginManager()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()

	parse_cmds = parser.add_subparsers()


	parser_info = parse_cmds.add_parser('info',
			help='Information about plugins and pbenchsuite')
	parser_info.set_defaults(func=cmd_info)


	parser_merge = parse_cmds.add_parser('merge',
			help='Merge multiple databases into one')


	parser_print = parse_cmds.add_parser('print',
			help='Print database')


	parser_run = parse_cmds.add_parser('run',
			help='Run benchmarks and/or benchsuites',
			formatter_class=argparse.RawTextHelpFormatter)
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
	parsed.func(parsed)

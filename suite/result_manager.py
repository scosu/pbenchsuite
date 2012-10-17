#!/usr/bin/python3

# pbenchsuite system benchmark suite for linux.
# Copyright (C) 2012  Markus Pargmann < scosu _AT_ allfex ORG >
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import argparse
import logging
import re
import os

def create_char_dict(d):
	if isinstance(d, int):
		return 'int'
	if isinstance(d, float):
		return 'float'
	if isinstance(d, str):
		return 'string'
	if isinstance(d, list):
		if len(d) == 0:
			return []
		types = []
		types.append(create_char_dict(d[0]))
		return types
	if isinstance(d, dict):
		types = {}
		for k,v in d.items():
			types[k] = create_char_dict(v)
		return types
	return "Unknown type"

class instance_runs:
	def __init__(self, runs):
		self.runs = runs
		self.cur = 0
	def get_current(self):
		return self.runs[self.cur]
	def get(self, index):
		return self.runs[index]
	def next(self):
		if self.cur >= len(self.runs) - 1:
			return False
		self.cur += 1
		return True

	def prev(self):
		if self.cur <= 0:
			return False
		self.cur -= 1
		return True
	def set(self, index):
		if index >= len(self.runs):
			self.cur = len(self.runs) - 1
		elif index < 0:
			self.cur = 0
		else:
			self.cur = index

	def delete(self, index = None):
		if index == None:
			index = self.cur
		if index >= len(self.runs) or index < 0:
			return
		del self.runs[index]
		if self.cur >= len(self.runs):
			if len(self.runs) == 0:
				self.cur = 0
			self.cur -= 1

	def size(self):
		return len(self.runs)


	def print_characteristics(self, index = None):
		char = {}
		if index == None:
			index = self.cur
		if index == -1:
			char = create_char_dict(self.runs)
		else:
			char = create_char_dict(self.runs[index])
		print(json.dumps(char, indent=4))

	def print(self, verbose = False, index = None):
		if index == None:
			index = self.cur
		data = {}
		if index == -1:
			runs = list(self.runs)
			if not verbose:
				for i in runs:
					del i['monitors']
			data = runs
		else:
			if index >= 0 and index < len(self.runs):
				data = self.runs[index].copy()
				if not verbose:
					del data['monitors']
		if verbose:
			print(json.dumps(data, indent = 4, sort_keys = True))
		else:
			js = json.dumps(data, indent = 4, sort_keys = True)
			if len(js.splitlines()) > 50:
				js = "\n".join(js.splitlines()[:50])
			print(js)


class instance_file:
	def __init__(self, path):
		self.file_path = path
		self.data = None

	def load(self):
		try:
			f = open(self.file_path, 'r')
			self.data = json.load(f)
			f.close()
			return True
		except:
			return False

	def store(self):
		try:
			f = open(self.file_path, 'w')
			json.dump(self.data, f)
			f.close()
			return True
		except:
			return False

	def set_path(self, path):
		self.file_path = path
	def print_characteristics(self):
		char = create_char_dict(self.data)
		print(json.dumps(char, indent=4))
	def print(self, verbose = False):
		print("Instance file: " + self.file_path)
		data = self.data.copy()
		if not verbose:
			data['instance'] = data['instance'].copy()
			del data['instance']['runs']
		print(json.dumps(data, indent=4, sort_keys = True))

	def add(self, new_data):
		if self.data == None:
			self.data = new_data.copy()
			return True
		binfo = self.data['bench']
		binfo2 = new_data['bench']
		if binfo['name'] != binfo2['name']:
			logging.critical('Can\'t add instance "' + binfo2['name'] + '" to "' + binfo['name'] + '"')
			return False
		iinfo1 = self.data['instance']['options']
		iinfo2 = new_data['instance']['options']
		checks = ['args', 'pre_args', 'post_args']
		for c in checks:
			in_both = 0
			if iinfo1[c] != None:
				in_both += 1
			if iinfo2[c] != None:
				in_both += 1
			if in_both == 0:
				continue
			if in_both == 1 or len(iinfo1[c]) != len(iinfo2[c]):
				logging.critical("Can't add instance \"" + binfo2['name'] + '" to "' + binfo['name'] + '" because of different ' + c)
				return False

			for i in range(0, len(iinfo1[c])):
				if iinfo1[c][i] != iinfo2[c][i]:
					logging.critical("Can't add instance \"" + binfo2['name'] + '" to "' + binfo['name'] + '" because of different ' + c)
					return False
		# TODO: check for monitor equality
		self.data['instance']['runs'] += new_data['instance']['runs']

		return True

	def get_runs(self):
		return instance_runs(self.data['instance']['runs'])

def cmd_print(args):
	for i in args.file:
		instance = instance_file(args.file[0])
		instance.load()
		if args.types:
			instance.print_characteristics()
		else:
			instance.print(verbose = args.verbose)
		print("")

def cmd_copy(args):
	dst = instance_file(args.dst[0])
	dst.load()
	for i in args.src:
		f = open(i, 'r')
		data = json.load(f)
		f.close()
		dst.add(data)
	dst.store()

def rec_rename(pathes, old_name, new_name):
	for path in pathes:
		if os.path.isfile(path):
			try:
				data = json.load(open(path, 'r'))
				if data['suite']['runname'] == old_name:
					data['suite']['runname'] = new_name
					json.dump(data, open(path, 'w'))
					print('Renamed file ' + path)
				else:
					print('Not renaming file ' + path + '. Name does not match ' + data['suite']['runname'])
			except:
				print('Failed loading file ' + path + '. Perhaps this file is not a valid pbenchsuite result file.')
				pass
		elif os.path.isdir(path):
			rec_rename([os.path.join(path, i) for i in os.listdir(path)], old_name, new_name)

def cmd_rename(args):
	new_name = args.new_name
	old_name = args.old_name
	pathes = args.pathes
	rec_rename(pathes, old_name, new_name)

def cmd_browse(args):
	print('Result Browser. For available commands, type help()')
	instance = instance_file(args.file[0])
	if not instance.load():
		return False
	i = instance.get_runs()
	last_cmd = None
	while True:
		cmd = input('>>> ')
		if cmd.strip() == '.':
			if last_cmd == None:
				print("Error: There is no last command")
				continue
			cmd = last_cmd
		else:
			last_cmd = cmd
		cmd_arg0 = re.match('\s*(\S+)\s*\(\s*\)\s*', cmd)
		cmd_arg1 = re.match('\s*(\S+)\s*\(\s*(\S+)\s*\)\s*', cmd)
		cmd_arg2 = re.match('\s*(\S+)\s*\(\s*(\S+)\s*,\s*(\S+)\s*\)\s*', cmd)

		if cmd_arg0 != None:
			name = cmd_arg0.group(1)
			if name == 'help':
				print('x can be replaced by a range "lower:upper". This will affect all elements from lower to upper including upper')
				print('Available Commands:')
				print(	'	.			Repeat the last command')
				print(	'	print(x)		Print data of run x in short')
				print(	'	print_all()		The same as print but all runs')
				print(	'	print_verbose(x)	Print data of run x in full length and indented')
				print(	'	print_verbose_all()	The same as print_verbose but all runs')
				print(	'	print_types(x)		Print types')
				print(	'	print_types_all()	Print types of all runs')
				print(	'	delete(x)		Delete data of run x')
				print(	'	save()			Save the modified runs')
				print(	'	items()			Print the number of items available')
				print(	'	exit()			Exit the browser')
				print(	'Iterator commands:')
				print(	'	next()			Go to the next item and print it in short')
				print(	'	print()			Print the current item')
				print(	'	print_verbose()		Print current item verbose')
				print(	'	print_types()		Print types of the current item')
				print(	'	set(x)			Go to item x and print it in short')
				print(	'	prev()			Go to the previous item and print it in short')
				print(	'	delete()		Delete current item')
			elif name == 'print':
				i.print()
			elif name == 'print_verbose':
				i.print(verbose = True)
			elif name == 'print_all':
				for k in range(0, i.size()):
					i.print(index = k)
			elif name == 'print_verbose_all':
				i.print(verbose = True, index = -1)
			elif name == 'print_types_all':
				i.print_characteristics(index = -1)
			elif name == 'print_types':
				i.print_characteristics()
			elif name == 'save':
				instance.store()
			elif name == 'exit':
				break
			elif name == 'delete':
				i.delete()
			elif name == 'next':
				status = i.next()
				if status:
					i.print()
				else:
					print("Error: Already on the last item")
			elif name == 'previous':
				status = i.prev()
				if status:
					i.print()
				else:
					print("Error: Already on the first item")
			elif name == 'items':
				print("Items: " + str(i.size()))
			else:
				print("Error: Unknown command " + name)
		elif cmd_arg1 != None:
			name = cmd_arg1.group(1)
			x_range = cmd_arg1.group(2).split(':')
			if len(x_range) == 1:
				x = int(cmd_arg1.group(2))
				if name == 'print':
					i.print(index = x)
				elif name == 'print_verbose':
					i.print(index = x, verbose = True)
				elif name == 'delete':
					i.delete(index = x)
				elif name == 'set':
					i.set(x)
				elif name == 'print_types':
					i.print_characteristics(x)
				else:
					print("Error: Unknown command " + name)
			elif len(x_range) == 2:
				x = int(x_range[0])
				y = int(x_range[1])
				if x >= y:
					print("Error: This is not a valid range")
					continue
				if name == 'print':
					for k in range(x, y+1):
						i.print(index = k)
				elif name == 'print_verbose':
					for k in range(x, y+1):
						i.print(index = k, verbose = True)
				elif name == 'delete':
					for k in reversed(range(x, y+1)):
						i.delete(index = k)
				elif name == 'print_types':
					for k in range(x, y+1):
						i.print_characteristics(index = k)
				else:
					print("Error: Unknown command " + name)
			else:
				print("Error: Not a range")
		else:
			print("Error: Not a command")

	return True


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parse_cmds = parser.add_subparsers()

	parse_print = parse_cmds.add_parser('print', help='Print content of a result file')
	print_type = parse_print.add_mutually_exclusive_group()
	print_type.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False)
	print_type.add_argument('-t', '--types', dest='types', action='store_true', default=False)
	parse_print.add_argument('file', nargs='+', metavar='RESULT.json')
	parse_print.set_defaults(func=cmd_print)

	parse_copy = parse_cmds.add_parser('cp', help='Copy benchmark instance runs to another result file. This will only work if all involved result files are for the same benchmark instance (same benchmark and arguments)')
	parse_copy.add_argument('src', nargs='+', metavar='SRC.json', help='One or more source json files')
	parse_copy.add_argument('dst', nargs=1, metavar='DST.json', help='One destination file')
	parse_copy.set_defaults(func=cmd_copy)

	parse_browse = parse_cmds.add_parser('browse', help='Browse the benchmark instance runs. You also can delete here')
	parse_browse.add_argument('file', nargs=1, metavar='RESULT.json')
	parse_browse.set_defaults(func=cmd_browse)

	parse_rename = parse_cmds.add_parser('rename', help='Rename the testrun. (This does not move the file)')
	parse_rename.add_argument('old_name')
	parse_rename.add_argument('new_name')
	parse_rename.add_argument('pathes', nargs='+')
	parse_rename.set_defaults(func=cmd_rename)

	parser.parse_args()
	parsed = parser.parse_args()
	parsed.func(parsed)







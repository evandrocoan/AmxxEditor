# Sublime AMXX-Editor by Destro

import os
import re
import string
import sys
import sublime, sublime_plugin
import webbrowser
import time
import urllib.request
from collections import defaultdict
from queue import *
from threading import Timer, Thread

sys.path.append(os.path.dirname(__file__))
import watchdog.events
import watchdog.observers
import watchdog.utils
from watchdog.utils.bricks import OrderedSetQueue

def plugin_loaded() :
#{
	settings = sublime.load_settings("amxx.sublime-settings")

	on_settings_modified( True );
	settings.add_on_change('amxx', on_settings_modified)
	sublime.set_timeout_async(check_update, 2500)
#}

def unload_handler() :
#{
	file_observer.stop()
	process_thread.stop()
	to_process.put(("", ""))
	sublime.load_settings("amxx.sublime-settings").clear_on_change("amxx")
#}

class ColorAmxxEditorCommand(sublime_plugin.ApplicationCommand):
#{
	def run(self, index) :
	#{
		if index >= g_color_schemes['count'] :
			return

		g_color_schemes['active'] = index

		file_path = sublime.packages_path()+"/User/amxx.sublime-settings"
		f = open(file_path, "r")
		if not f :
			return

		content = f.read()

		rx = re.compile(r'("color_scheme"\s*:\s*")(.*)(".*)')
		content = rx.sub(r'\g<1>'+ g_color_schemes['list'][index] +'\g<3>', content)

		f.close()

		f = open(file_path, "w")
		f.write(content)
		f.close()
	#}

	def is_visible(self, index) :
		return (index < g_color_schemes['count'])

	def is_checked(self, index) :
		return (index < g_color_schemes['count'] and g_color_schemes['list'][index] == g_color_schemes['active'])

	def description(self, index) :
		if index < g_color_schemes['count'] :
			return g_color_schemes['list'][index]
		return ""
#}

class NewAmxxIncludeCommand(sublime_plugin.WindowCommand):
	def run(self):
		new_file("inc")
class NewAmxxPluginCommand(sublime_plugin.WindowCommand):
	def run(self):
		new_file("sma")

def new_file(type):
#{
	view = sublime.active_window().new_file()
	view.set_name("untitled."+type)

	plugin_template = sublime.load_resource("Packages/amxmodx/default."+type)
	plugin_template = plugin_template.replace("\r", "")

	view.run_command("insert_snippet", {"contents": plugin_template})
#}

class AboutAmxxEditorCommand(sublime_plugin.WindowCommand):
#{
	def run(self):
	#{
		about = "Sublime AMXX-Editor v"+ EDITOR_VERSION +" by Destro\n\n\n"

		about += "CREDITs:\n"
		about += "- Great:\n"
		about += "   ppalex7     (SourcePawn Completions)\n\n"

		about += "- Contributors:\n"
		about += "   sasske        (white color scheme)\n"
		about += "   addons_zz (npp color scheme)\n"
		about += "   KliPPy        (build version)\n"
		about += "   Mistrick     (mistrick color scheme)\n"

		sublime.message_dialog(about)
	#}
#}

class UpdateAmxxEditorCommand(sublime_plugin.WindowCommand):
#{
	def run(self) :
	#{
		sublime.set_timeout_async(self.check_update_async, 100)
	#}
	def check_update_async(self) :
	#{
		check_update(True)
	#}
#}

def check_update(bycommand=0) :
#{
	data = urllib.request.urlopen("https://amxmodx-es.com/st.php").read().decode("utf-8")

	if data :
	#{
		data = data.split("\n", 1)

		fCheckVersion = float(data[0])
		fCurrentVersion = float(EDITOR_VERSION)

		if fCheckVersion == fCurrentVersion and bycommand :
			msg = "AMXX: You are using the latest version v"+ EDITOR_VERSION
			sublime.ok_cancel_dialog(msg, "OK")

		if fCheckVersion > fCurrentVersion :
		#{
			msg  = "AMXX: A new version available v"+ data[0]
			msg += "\n\nNews:\n" + data[1]
			ok = sublime.ok_cancel_dialog(msg, "Update")

			if ok :
				webbrowser.open_new_tab("https://amxmodx-es.com/showthread.php?tid=12316")
		#}
	#}
#}

class AmxxBuildVerCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		region = self.view.find("^#define\s+(?:PLUGIN_)?VERSION\s+\".+\"", 0, sublime.IGNORECASE)
		if region == None :
			region = self.view.find("new\s+const\s+(?:PLUGIN_)?VERSION\s*\[\s*\]\s*=\s*\".+\"", 0, sublime.IGNORECASE)
			if region == None :
				return

		line = self.view.substr(region)
		result = re.match("(.*\"(?:v)?\d{1,2}\.\d{1,2}\.(?:\d{1,2}-)?)(\d+)(b(?:eta)?)?\"", line)
		if not result :
			return

		build = int(result.group(2))
		build += 1

		beta = result.group(3)
		if not beta :
			beta = ""

		self.view.replace(edit, region, result.group(1) + str(build) + beta + '\"')

class AMXXEditor(sublime_plugin.EventListener):
	def __init__(self) :
		process_thread.start()
		self.delay_queue = None
		file_observer.start()

	def on_window_command(self, window, cmd, args) :
		if cmd != "build" :
			return

		view = window.active_view()
		if not self.is_amxmodx_file(view) or not g_enable_buildversion :
			return

		view.run_command("amxx_build_ver")

	def on_selection_modified_async(self, view) :
		if not self.is_amxmodx_file(view) or not g_enable_inteltip :
			return

		region = view.sel()[0]
		scope = view.scope_name(region.begin())
		print_debug(1, "(inteltip) scope_name: [%s]" % scope)

		if not "support.function" in scope and not "include_path.pawn" in scope or region.size() > 1 :
			view.hide_popup()
			view.add_regions("inteltip", [ ])
			return

		if "include_path.pawn" in scope :
			self.inteltip_include(view, region)
		else :
			self.inteltip_function(view, region)

	def inteltip_include(self, view, region) :
		location 	= view.word(region).end() + 1
		line = view.substr(view.line(region))
		include = includes_re.match(line).group(1)

		(file_name, exists) = get_file_name(view.file_name(), include)
		if not exists :
			return

		link_local = file_name + '#'
		if not '.' in include :
			link_web = include + '#'
			include += ".inc"
		else :
			link_web = None

		html  = '<style>'+ g_inteltip_style +'</style>'
		html += '<div class="top">'
		html += '<a class="file" href="'+link_local+'">'+include+'</a>'
		if link_web :
			html += ' | <a class="file" href="'+link_web+'">WebAPI</a>'

		html += '</div><div class="bottom">'

		html += '<span class="func_type">Location:</span><br>'
		html += '<span class="func_name">'+file_name+'</span>'
		html += '</div>'

		view.show_popup(html, 0, location, max_width=700, on_navigate=self.on_navigate)

	def inteltip_function(self, view, region) :

		word_region = view.word(region)
		location 	= word_region.end() + 1
		search_func = view.substr(word_region)
		doctset 	= set()
		visited 	= set()
		found 		= None
		node 		= nodes[view.file_name()]

		self.generate_doctset_recur(node, doctset, visited)

		for func in doctset :
			if search_func == func[0] :
				found = func
				if found[3] != 1 :
					break

		if found:
			print_debug(0, "param2: [%s]" % simple_escape(found[1]))
			filename = os.path.basename(found[2])


			if found[3] :
				if found[4] :
					link_local = found[2] + '#' + FUNC_TYPES[found[3]] + ' ' + found[4] + ':' + found[0]
				else :
					link_local = found[2] + '#' + FUNC_TYPES[found[3]] + ' ' + found[0]

				link_web = filename.rsplit('.', 1)[0] + '#' + found[0]
			else :

				link_local = found[2] + '#' + '^' + found[0]
				link_web = ''

			html  = '<style>'+ g_inteltip_style +'</style>'
			html += '<div class="top">'							############################## TOP

			html += '<a class="file" href="'+link_local+'">'+os.path.basename(found[2])+'</a>'
			if link_web:
				html += ' | <a class="file" href="'+link_web+'">WebAPI</a>'

			html += '</div><div class="bottom">'		############################## BOTTOM

			html += '<span class="func_type">'+FUNC_TYPES[found[3]]+':</span> <span class="func_name">'+found[0]+'</span>'
			html += '<br>'
			html += '<span class="params">Params:</span> <span class="params_definition">('+ simple_escape(found[1]) +')</span>'
			html += '<br>'

			if found[4] :
				html += '<span class="return">Return:</span> <span class="return_type">'+found[4]+'</span>'

			html += '</div>'									############################## END

			view.show_popup(html, 0, location, max_width=700, on_navigate=self.on_navigate)
			view.add_regions("inteltip", [ word_region ], "inteltip.pawn")

		else:
			view.hide_popup()
			view.add_regions("inteltip", [ ])

	def on_navigate(self, link) :
		(file, search) = link.split('#')

		if "." in file :
			view = sublime.active_window().open_file(file);
			def do_position() :
				if view.is_loading():
					sublime.set_timeout(do_position, 100)
				else :
					r=view.find(search, 0, sublime.IGNORECASE)

					view.sel().clear()
					view.sel().add(r)

					view.show(r)
			do_position()
		else :
			webbrowser.open_new_tab("http://www.amxmodx.org/api/"+file+"/"+search)

	def on_activated_async(self, view) :
		if not self.is_amxmodx_file(view):
			return
		if not view.file_name() :
			return
		if not view.file_name() in nodes :
			add_to_queue(view)

	def on_modified_async(self, view) :
		self.add_to_queue_delayed(view)

	def on_post_save_async(self, view) :
		self.add_to_queue_now(view)

	def on_load_async(self, view) :
		self.add_to_queue_now(view)

	def add_to_queue_now(self, view) :
		if not self.is_amxmodx_file(view):
			return
		add_to_queue(view)

	def add_to_queue_delayed(self, view) :
		if not self.is_amxmodx_file(view):
			return

		if self.delay_queue is not None :
			self.delay_queue.cancel()

		self.delay_queue = Timer(float(g_delay_time), add_to_queue_forward, [ view ])
		self.delay_queue.start()

	def is_amxmodx_file(self, view) :
		return view.file_name() is not None and view.match_selector(0, 'source.sma')

	def on_query_completions(self, view, prefix, locations):
		if not self.is_amxmodx_file(view):
			return None

		if view.match_selector(locations[0], 'source.sma string') :
			return ([], sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

		return (self.generate_funcset(view.file_name()), sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

	def generate_funcset(self, file_name) :
		funcset = set()
		visited = set()

		node = nodes[file_name]

		self.generate_funcset_recur(node, funcset, visited)
		return sorted_nicely(funcset)

	def generate_funcset_recur(self, node, funcset, visited) :
		if node in visited :
			return

		visited.add(node)
		for child in node.children :
			self.generate_funcset_recur(child, funcset, visited)

		funcset.update(node.funcs)

	def generate_doctset_recur(self, node, doctset, visited) :
		if node in visited :
			return

		visited.add(node)
		for child in node.children :
			self.generate_doctset_recur(child, doctset, visited)

		doctset.update(node.doct)


def on_settings_modified(is_loading=False):
#{
	print_debug( 1, "on_settings_modified" )
	global g_enable_inteltip

	settings = sublime.load_settings("amxx.sublime-settings")
	invalid  = is_invalid_settings(settings)

	if invalid:
	#{
		if not is_loading:
			sublime.message_dialog("AMXX-Editor:\n\n" + invalid)

		g_enable_inteltip = 0
		return
	#}

	# check package path
	packages_path = sublime.packages_path() + "/amxmodx"
	if not os.path.isdir(packages_path) :
		os.mkdir(packages_path)

	# fix-path
	fix_path(settings, 'include_directory')

	# Get the set color scheme
	color_scheme = settings.get('color_scheme')

	# popUp.CSS
	global g_inteltip_style
	g_inteltip_style = sublime.load_resource("Packages/amxmodx/"+ color_scheme +"-popup.css")
	g_inteltip_style = g_inteltip_style.replace("\r", "") # fix win/linux newlines

	# cache setting
	global g_enable_buildversion, g_debug_level, g_delay_time, g_include_dir
	g_enable_inteltip 		= settings.get('enable_inteltip', True)
	g_enable_buildversion 	= settings.get('enable_buildversion', False)
	g_debug_level 			= settings.get('debug_level', 0)
	g_delay_time			= settings.get('live_refresh_delay', 1.0)
	g_include_dir 			= settings.get('include_directory')

	print_debug( 1, "( on_settings_modified ) g_debug_level: %d" % g_debug_level )
	print_debug( 1, "( on_settings_modified ) g_include_dir: " + g_include_dir )

	# generate list of color schemes
	global g_color_schemes, g_default_schemes
	g_color_schemes['list'] = g_default_schemes[:]
	g_color_schemes['active'] = color_scheme

	for file in os.listdir(sublime.packages_path()+"/") :
	#{
		if file.endswith("-pawn.tmTheme") :
			g_color_schemes['list'] += [ file.replace("-pawn.tmTheme", "") ]
	#}

	g_color_schemes['count'] = len(g_color_schemes['list'])

	file_observer.unschedule_all()
	file_observer.schedule(file_event_handler, g_include_dir, True)
#}

def is_invalid_settings(settings) :
#{
	if settings.get('include_directory') is None or settings.get('color_scheme') is None :
		return "You are not set correctly settings for AMXX-Editor.\n\nNo has configurado correctamente el AMXX-Editor."

	temp = settings.get('include_directory')
	if not os.path.isdir(temp) :
		return "The `include_directory` directory not exist!\n\n\"%s\"\n\nPlease, go to the menu:\n`Amx Mod X -> Configure AMXX-Autocompletion Settings`" % temp

	return None
#}

def fix_path(settings, key) :
#{
	org_path = settings.get(key)

	if org_path is "${file_path}" :
		return

	path = os.path.normpath(org_path)
	if os.path.isdir(path):
		path += '/'

	settings.set(key, path)
#}

def sorted_nicely( l ):
	""" Sort the given iterable in the way that humans expect."""
	convert = lambda text: int(text) if text.isdigit() else text
	alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key[0]) ]
	return sorted(l, key = alphanum_key)

def add_to_queue_forward(view) :
	sublime.set_timeout(lambda: add_to_queue(view), 0)

def add_to_queue(view) :
	# The view can only be accessed from the main thread, so run the regex
	# now and process the results later
	to_process.put((view.file_name(), view.substr(sublime.Region(0, view.size()))))

def add_include_to_queue(file_name) :
	to_process.put((file_name, None))

class IncludeFileEventHandler(watchdog.events.FileSystemEventHandler) :
	def __init__(self) :
		watchdog.events.FileSystemEventHandler.__init__(self)

	def on_created(self, event) :
		sublime.set_timeout(lambda: on_modified_main_thread(event.src_path), 0)

	def on_modified(self, event) :
		sublime.set_timeout(lambda: on_modified_main_thread(event.src_path), 0)

	def on_deleted(self, event) :
		sublime.set_timeout(lambda: on_deleted_main_thread(event.src_path), 0)

def on_modified_main_thread(file_path) :
	if not is_active(file_path) :
		add_include_to_queue(file_path)

def on_deleted_main_thread(file_path) :
	if is_active(file_path) :
			return

	node = nodes.get(file_path)
	if node is None :
		return

	node.remove_all_children_and_funcs()

def is_active(file_name) :
	return sublime.active_window().active_view().file_name() == file_name

class ProcessQueueThread(watchdog.utils.DaemonThread) :
	def run(self) :
		while self.should_keep_running() :
			(file_name, view_buffer) = to_process.get()
			if view_buffer is None :
				self.process_existing_include(file_name)
			else :
				self.process(file_name, view_buffer)

	def process(self, view_file_name, view_buffer) :
		(current_node, node_added) = get_or_add_node(view_file_name)

		base_includes = set()

		includes = includes_re.findall(view_buffer)

		for include in includes:
			self.load_from_file(view_file_name, include, current_node, current_node, base_includes)

		for removed_node in current_node.children.difference(base_includes) :
			current_node.remove_child(removed_node)

		process_buffer(view_buffer, current_node)

	def process_existing_include(self, file_name) :
		current_node = nodes.get(file_name)
		if current_node is None :
			return

		base_includes = set()

		with open(file_name, 'r') as f :
			print_debug(0, "(analyzer) Processing Include File %s" % file_name)
			includes = include_re.findall(f.read())

		for include in includes:
			self.load_from_file(view_file_name, include, current_node, current_node, base_includes)

		for removed_node in current_node.children.difference(base_includes) :
			current_node.remove_child(removed_node)

		process_include_file(current_node)


	def load_from_file(self, view_file_name, base_file_name, parent_node, base_node, base_includes) :
		(file_name, exists) = get_file_name(view_file_name, base_file_name)
		if not exists :
			print_debug(0, "(analyzer) Include File Not Found: %s" % base_file_name)

		(node, node_added) = get_or_add_node(file_name)
		parent_node.add_child(node)

		if parent_node == base_node :
			base_includes.add(node)

		if not node_added or not exists:
			return

		with open(file_name, 'r') as f :
			print_debug(0, "(analyzer) Processing Include File %s" % file_name)
			includes = includes_re.findall(f.read())

		for include in includes :
			self.load_from_file(view_file_name, include, node, base_node, base_includes)

		process_include_file(node)


def get_file_name(view_file_name, base_file_name) :

	print_debug( 1, "get_file_name: " + g_include_dir )

	if local_re.search(base_file_name) == None:
		file_name = os.path.join(g_include_dir, base_file_name + '.inc')
	else:
		file_name = os.path.join(os.path.dirname(view_file_name), base_file_name)

	return (file_name, os.path.exists(file_name))

def get_or_add_node( file_name) :
	node = nodes.get(file_name)
	if node is None :
		node = Node(file_name)
		nodes[file_name] = node
		return (node, True)

	return (node, False)

# ============= NEW CODE ------------------------------------------------------------------------------------------------------------
class Node :
#{
	def __init__(self, file_name) :
		self.file_name = file_name
		self.children = set()
		self.parents = set()
		self.funcs = set()
		self.doct = set()

	def add_child(self, node) :
		self.children.add(node)
		node.parents.add(self)

	def remove_child(self, node) :
		self.children.remove(node)
		node.parents.remove(self)

		if len(node.parents) <= 0 :
			nodes.pop(node.file_name)

	def remove_all_children_and_funcs(self) :
		for child in self.children :
			self.remove_child(node)
		self.funcs.clear()
		self.doct.clear()
#}

class TextReader:
#{
	def __init__(self, text):
		self.text = text.splitlines()
		self.position = -1

	def readline(self) :
	#{
		self.position += 1

		if self.position < len(self.text) :
			retval = self.text[self.position]
			if retval == '' :
				return '\n'
			else :
				return retval
		else :
			return ''
	#}
#}

class pawnParse :
#{
	def __init__(self) :
		self.save_const_timer = None
		self.constants_count = 0

	def start(self, pFile, node) :
	#{
		print_debug(2, "(analyzer) CODE PARSE Start [%s]" % node.file_name)

		self.file 				= pFile
		self.file_name			= os.path.basename(node.file_name)
		self.node 				= node
		self.found_comment 		= False
		self.found_enum 		= False
		self.skip_brace_found 	= False
		self.skip_next_dataline = False
		self.enum_contents 		= ''
		self.brace_level 		= 0

		self.restore_buffer 	= None

		self.node.funcs.clear()
		self.node.doct.clear()

		self.start_parse()

		if self.constants_count != len(g_constants_list) :
		#{
			if self.save_const_timer :
				self.save_const_timer.cancel()

			self.save_const_timer = Timer(4.0, self.save_constants)
			self.save_const_timer.start()
		#}

		print_debug(2, "(analyzer) CODE PARSE End [%s]" % node.file_name)
	#}

	def save_constants(self) :
	#{
		self.save_const_timer 	= None
		self.constants_count 	= len(g_constants_list)

		constants = "___test"
		for const in g_constants_list :
			constants += "|" + const

		syntax = "%YAML 1.2\n---\nscope: source.sma\ncontexts:\n  main:\n    - match: \\b(" + constants + ")\\b\n      scope: constant.vars.pawn"

		file_name = sublime.packages_path() + "/amxmodx/const.sublime-syntax"

		f = open(file_name, 'w')
		f.write(syntax)
		f.close()

		print_debug(2, "(analyzer) call save_constants()")
	#}

	def read_line(self) :
	#{
		if self.restore_buffer :
			line = self.restore_buffer
			self.restore_buffer = None
		else :
			line = self.file.readline()

		if len(line) > 0 :
			return line
		else :
			return None
	#}

	def read_string(self, buffer) :
	#{
		buffer = buffer.replace('\t', ' ').strip()
		while '  ' in buffer :
			buffer = buffer.replace('  ', ' ')

		buffer = buffer.lstrip()

		result = ''
		i = 0

		while i < len(buffer) :
			if buffer[i] == '/' and i + 1 < len(buffer):
				if buffer[i + 1] == '/' :
					self.brace_level +=  result.count('{') - result.count('}')
					return result
				elif buffer[i + 1] == '*' :
					self.found_comment = True
					i += 1
				elif not self.found_comment :
					result += '/'
			elif self.found_comment :
				if buffer[i] == '*' and i + 1 < len(buffer) and buffer[i + 1] == '/' :
					self.found_comment = False
					i += 1
			elif not (i > 0 and buffer[i] == ' ' and buffer[i - 1] == ' '):
				result += buffer[i]

			i += 1

		self.brace_level +=  result.count('{') - result.count('}')
		return result
	#}

	def skip_function_block(self, buffer) :
	#{
		num_brace = 0
		inString = False
		self.skip_brace_found = False

		buffer = buffer + ' '

		while buffer is not None and buffer.isspace() :
			buffer = self.read_line()

		while buffer is not None :
		#{
			i = 0
			pos = 0
			oldChar = ''

			for c in buffer :
			#{
				i += 1

				if (c == '"') :
				#{
					if inString and oldChar != '^' :
						inString = False
					else :
						inString = True
				#}

				if (inString == False) :
				#{
					if (c == '{') :
						num_brace += 1
						self.skip_brace_found = True
					elif (c == '}') :
						num_brace -= 1
						pos = i
				#}

				oldChar = c
			#}

			if num_brace == 0 :
				self.restore_buffer = buffer[pos:]
				return

			buffer = self.read_line()
		#}
	#}

	def valid_name(self, name) :
	#{
		if not name or not name[0].isalpha() and name[0] != '_' :
			return False

		return re.match('^[\w_]+$', name) is not None
	#}

	def add_constant(self, name) :
	#{
		fixname = re.search('(\\w*)', name)
		if fixname :
			name = fixname.group(1)
			g_constants_list.add(name)
	#}

	def add_enum(self, buffer) :
	#{
		buffer = buffer.strip()
		if buffer == '' :
			return

		split = buffer.split('[')

		self.add_autocomplete(buffer, 'enum', split[0])
		self.add_constant(split[0])

		print_debug(2, "(analyzer) parse_enum add: [%s] -> [%s]" % (buffer, split[0]))
	#}

	def add_autocomplete(self, name, info, autocomplete) :
	#{
		self.node.funcs.add((name +'  \t'+  self.file_name +' - '+ info, autocomplete))
	#}

	def start_parse(self) :
	#{
		while True :
		#{
			buffer = self.read_line()

			if buffer is None :
				break

			buffer = self.read_string(buffer)
			if len(buffer) <= 0 :
				continue

			#if "sma" in self.node.file_name :
			#	print("read: skip:[%d] brace_level:[%d] buff:[%s]" % (self.skip_next_dataline, self.brace_level, buffer))

			if self.skip_next_dataline :
				self.skip_next_dataline = False
				continue

			if buffer.startswith('#pragma deprecated') :
				buffer = self.read_line()
				if buffer is not None and buffer.startswith('stock ') :
					self.skip_function_block(buffer)
			elif buffer.startswith('#define ') :
				buffer = self.parse_define(buffer)
			elif buffer.startswith('const ') :
				buffer = self.parse_const(buffer)
			elif buffer.startswith('enum ') :
				self.found_enum = True
				self.enum_contents = ''
			elif buffer.startswith('new ') :
				self.parse_variable(buffer)
			elif buffer.startswith('public ') :
				self.parse_function(buffer, 1)
			elif buffer.startswith('stock ') :
				self.parse_function(buffer, 2)
			elif buffer.startswith('forward ') :
				self.parse_function(buffer, 3)
			elif buffer.startswith('native ') :
				self.parse_function(buffer, 4)
			elif not self.found_enum and not buffer[0] == '#' :
				self.parse_function(buffer, 0)

			if self.found_enum :
				self.parse_enum(buffer)
		#}
	#}

	def parse_define(self, buffer) :
	#{
		define = re.search('#define[\\s]+([^\\s]+)[\\s]+(.+)', buffer)
		if define :
		#{
			buffer = ''
			name = define.group(1)
			value = define.group(2).strip()
			self.add_autocomplete(name, 'define: '+value, name)
			self.add_constant(name)

			print_debug(2, "(analyzer) parse_define add: [%s]" % name)
		#}
	#}

	def parse_const(self, buffer) :
	#{
		buffer = buffer[6:]

		split 	= buffer.split('=', 1)
		if len(split) < 2 :
			return

		name 	= split[0].strip()
		value 	= split[1].strip()

		newline = value.find(';')
		if (newline != -1) :
		#{
			self.restore_buffer = value[newline+1:].strip()
			value = value[0:newline]
		#}

		self.add_autocomplete(name, 'const: '+value, name)
		self.add_constant(name)
		print_debug(2, "(analyzer) parse_const add: [%s]" % name)
	#}

	def parse_variable(self, buffer) :
	#{
		if buffer.startswith('new const ') :
			buffer = buffer[10:]
		else :
			buffer = buffer[4:]

		varName = ""
		oldChar = ''
		i = 0
		pos = 0
		num_brace = 0
		multiLines = True
		skipSpaces = False
		parseName = True
		inBrackets = False
		inBraces = False
		inString = False

		while multiLines :
		#{
			multiLines = False

			for c in buffer :
			#{
				i += 1

				if (c == '"') :
				#{
					if (inString and oldChar != '^') :
						inString = False
					else :
						inString = True
				#}

				if (inString == False) :
				#{
					if (c == '{') :
						num_brace += 1
						inBraces = True
					elif (c == '}') :
						num_brace -= 1
						if (num_brace == 0) :
							inBraces = False
				#}

				if skipSpaces :
				#{
					if c.isspace() :
						continue
					else :
						skipSpaces = False
						parseName = True
				#}

				if parseName :
				#{
					if (c == ':') :
						varName = ''
					elif (c == ' ' or c == '=' or c == ';' or c == ',') :
						varName = varName.strip()

						if (varName != '') :
							self.add_autocomplete(varName, 'var', varName)
							print_debug(2, "(analyzer) parse_variable add: [%s]" % varName)

						varName = ''
						parseName = False
						inBrackets = False
					elif (c == '[') :
						inBrackets = True
					elif (inBrackets == False) :
						varName += c
				#}

				if (inString == False and inBrackets == False and inBraces == False) :
				#{
					if not parseName and c == ';' :
						self.restore_buffer = buffer[i:].strip()
						return

					if (c == ',') :
						skipSpaces = True
				#}

				oldChar = c
			#}

			if (c != ',') :
			#{
				varName = varName.strip()
				if varName != '' :
					self.add_autocomplete(varName, 'var', varName)
					print_debug(2, "(analyzer) parse_variable add: [%s]" % varName)
			#}
			else :
			#{
				multiLines = True
				buffer = ' '

				while buffer is not None and buffer.isspace() :
					buffer = self.read_line()
			#}
		#}
	#}

	def parse_enum(self, buffer) :
	#{
		pos = buffer.find('}')
		if pos != -1 :
			buffer = buffer[0:pos]
			self.found_enum = False

		self.enum_contents = '%s\n%s' % (self.enum_contents, buffer)
		buffer = ''

		ignore = False
		if not self.found_enum :
		#{
			pos = self.enum_contents.find('{')
			self.enum_contents = self.enum_contents[pos + 1:]

			for c in self.enum_contents :
			#{
				if c == '=' or c == '#' :
					ignore = True
				elif c == '\n':
					ignore = False
				elif c == ':' :
					buffer = ''
					continue
				elif c == ',' :
					self.add_enum(buffer)
					buffer = ''

					ignore = False
					continue

				if not ignore :
					buffer += c
			#}

			self.add_enum(buffer)
			buffer = ''
		#}
	#}

	def parse_function(self, buffer, type) :
	#{
		multi_line = False
		temp = ''
		full_func_str = None
		open_paren_found = False

		while buffer is not None :
		#{

			buffer = buffer.strip()
			if not open_paren_found :
			#{
				parenpos = buffer.find('(')

				if parenpos == -1 :
					return

				open_paren_found = True
			#}
			if open_paren_found :
			#{
				pos = buffer.find(')')
				if pos != -1 :
					full_func_str = buffer[0:pos + 1]
					buffer = buffer[pos+1:]

					if (multi_line) :
						full_func_str = '%s%s' % (temp, full_func_str)

					break

				multi_line = True
				temp = '%s%s' % (temp, buffer)
			#}

			buffer = self.read_line()
			if buffer is None :
				return

			buffer = self.read_string(buffer)
		#}

		if full_func_str is not None :
		#{
			error = self.parse_function_params(full_func_str, type)
			if not error and type <= 2 :
				self.skip_function_block(buffer)
				if not self.skip_brace_found :
					self.skip_next_dataline = True

			#print("skip_brace: error:[%d] type:[%d] found:[%d] skip:[%d] func:[%s]" % (error, type, self.skip_brace_found, self.skip_next_dataline, full_func_str))
		#}
	#}

	def parse_function_params(self, func, type) :
	#{
		if type == 0 :
			remaining = func
		else :
			split = func.split(' ', 1)
			remaining = split[1]

		split = remaining.split('(', 1)
		if len(split) < 2 :
			print_debug(1, "(analyzer) parse_params return1: [%s]" % split)
			return 1

		remaining = split[1]
		returntype = ''
		funcname_and_return = split[0].strip()
		split_funcname_and_return = funcname_and_return.split(':')
		if len(split_funcname_and_return) > 1 :
			funcname = split_funcname_and_return[1].strip()
			returntype = split_funcname_and_return[0].strip()
		else :
			funcname = split_funcname_and_return[0].strip()

		if funcname.startswith("operator") :
			return 0

		if not self.valid_name(funcname) :
			print_debug(1, "(analyzer) parse_params invalid name: [%s]" % funcname)
			return 1

		remaining = remaining.strip()
		if remaining == ')' :
			params = []
		else :
			params = remaining.strip()[:-1].split(',')

		autocomplete = funcname + '('
		i = 1
		for param in params :
			if i > 1 :
				autocomplete += ', '
			autocomplete += '${%d:%s}' % (i, param.strip())
			i += 1

		autocomplete += ')'

		self.add_autocomplete(funcname, FUNC_TYPES[type].lower(), autocomplete)
		self.node.doct.add((funcname, func[func.find("(")+1:-1], self.node.file_name, type, returntype))

		print_debug(2, "(analyzer) parse_params add: [%s]" % func)
		return 0
	#}

#}

def process_buffer(text, node) :
#{
	text_reader = TextReader(text)
	pawnparse.start(text_reader, node)
#}

def process_include_file(node) :
#{
	with open(node.file_name) as file :
		pawnparse.start(file, node)
#}

def simple_escape(html) :
#{
    return html.replace('&', '&amp;')
#}

def print_debug(level, msg) :
#{
	if g_debug_level >= level :
		print("[AMXX-Editor]: " + msg)
#}

EDITOR_VERSION = "2.2"
FUNC_TYPES = [ "Function", "Public", "Stock", "Forward", "Native" ]

g_default_schemes = [ "atomic", "dark", "mistrick", "npp", "twlight", "white" ]
g_color_schemes = { "list": g_default_schemes[:], "count":0, "active":0 }
g_constants_list = set()
g_inteltip_style = ""
g_enable_inteltip = False
g_enable_buildversion = False
g_debug_level = 0
g_delay_time = 1.0
g_include_dir = "."

to_process = OrderedSetQueue()
nodes = dict()
file_observer = watchdog.observers.Observer()
process_thread = ProcessQueueThread()
file_event_handler = IncludeFileEventHandler()
includes_re = re.compile('^[\\s]*#include[\\s]+[<"]([^>"]+)[>"]', re.MULTILINE)
local_re = re.compile('\\.(sma|inc)$')
pawnparse = pawnParse()

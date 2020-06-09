#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

#
# Licensing
#
# Copyright (C) 2013-2016 ppalex7 <https://github.com/ppalex7/SourcePawnCompletions>
# Copyright (C) 2016-2017 AMXX-Editor by Destro <https://forums.alliedmods.net/showthread.php?t=284385>
# Copyright (C) 2017-2018 Evandro Coan <https://github.com/evandrocoan/AmxxEditor>
#
#  Redistributions of source code must retain the above
#  copyright notice, this list of conditions and the
#  following disclaimer.
#
#  Redistributions in binary form must reproduce the above
#  copyright notice, this list of conditions and the following
#  disclaimer in the documentation and/or other materials
#  provided with the distribution.
#
#  Neither the name Evandro Coan nor the names of any
#  contributors may be used to endorse or promote products
#  derived from this software without specific prior written
#  permission.
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation; either version 3 of the License, or ( at
#  your option ) any later version.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import re
import sys
import sublime
import sublime_plugin
import webbrowser
import time
import threading

from io import StringIO
from functools import wraps
from collections import deque
from xml.etree import ElementTree

sys.path.append(os.path.dirname(__file__))
from enum34 import Enum
import watchdog.events
import watchdog.observers
import watchdog.utils
from watchdog.utils.bricks import OrderedSetQueue

# Enable editor debug messages: (bitwise)
#
# 0  - Disabled debugging.
# 1  - Errors messages.
# 2  - Outputs when it starts a file parsing.
# 4  - General messages.
# 8  - Analyzer parser.
# 16 - Autocomplete debugging.
# 32 - Function parsing debugging.
# 63 - All debugging levels at the same time.
from debug_tools import getLogger
from debug_tools.utilities import wrap_text

log = getLogger( 1, __name__ )
# log = getLogger( 1, __name__, file="amxxeditor.txt", mode='w' )

EDITOR_VERSION = "3.0_zz"
CURRENT_PACKAGE_NAME = __package__
g_is_package_loading = True

class FUNC_TYPES(Enum):
    function = 0
    public   = 1
    stock    = 2
    forward  = 3
    native   = 4
    define   = 5

# print( FUNC_TYPES(0) )
g_constants_list = set()
g_inteltip_style = ""
g_enable_inteltip = False
g_enable_inteltip_calls = False
g_enable_inteltip_name = False
g_enable_buildversion = False
g_delay_time = 1.0
g_include_dir = set()
g_add_paremeters = False
g_new_file_syntax = "Packages/%s/%sPawn.sublime-syntax" % (CURRENT_PACKAGE_NAME, CURRENT_PACKAGE_NAME)
g_word_autocomplete = False
g_function_autocomplete = False
g_enable_inteltip_color = "inteltip.pawn"

g_processing_set_queue = OrderedSetQueue()
g_processing_set_queue_set = set()
g_nodes = dict()
g_file_observer = watchdog.observers.Observer()
includes_regex = re.compile('^[\\s]*#include[\\s]+[<"]([^>"]+)[>"]', re.MULTILINE)
local_regex = re.compile('\\.(sma|inc)$')
function_regex = re.compile(r'(?:\s*\[.*\]\s*)?[\w_\d: ]*[\w_\d]\(')
function_return_regex = re.compile(r'(.+:\[.*\]|.+:)\s*(.+)')
function_return_array_regex = re.compile(r'(\[.*\])(.+)')
new_line_regex = re.compile(r'\n')
space_clean_regex = re.compile(r'\t+|  +')
amxx_build_ver_regex = re.compile("(.*\"(?:v)?\\d{1,2}\\.\\d{1,2}\\.(?:\\d{1,2}-)?)(\\d+)(b(?:eta)?)?\"")
sort_nicely_regex = re.compile('([0-9]+)')
is_valid_name_regex = re.compile('^[\\w_]+$')
add_constant_regex = re.compile('(\\w*)')
parse_define_regex = re.compile(r'#define[\s]+([^\s]+)[\s]+((?:\\\n|.)+)')
has_define_next_line_regex = re.compile(r'[^\\]*(?:\\)+')


def plugin_unloaded():
    global g_is_package_loading
    g_is_package_loading=True

    settings = sublime.load_settings("%s.sublime-settings" % CURRENT_PACKAGE_NAME)
    settings.clear_on_change(CURRENT_PACKAGE_NAME)
    log.delete()


def plugin_loaded():
    threading.Thread(target=_plugin_loaded).start()
    threading.Thread(target=force_popup_to_show_first).start()


def force_popup_to_show_first():
    """ API to handle popups with predefined priorities to avoid popup fighting
    https://github.com/sublimehq/sublime_text/issues/2079 """
    if '_is_force_popup_to_show_first' not in globals():
        global _is_force_popup_to_show_first
        _is_force_popup_to_show_first = True
        time.sleep(10)
        sublime_plugin.reload_plugin( "AmxxEditor.AmxxEditor" )


def _plugin_loaded():
    settings = sublime.load_settings("%s.sublime-settings" % CURRENT_PACKAGE_NAME)

    install_build_systens("AmxxEditor.sh")
    install_build_systens("AmxxEditor.bat")

    install_setting_file("%s.sublime-settings" % CURRENT_PACKAGE_NAME)
    install_setting_file("AmxxEditorConsole.sublime-settings")

    # Fixes the settings dialog showing up when installing the package for the first time
    global g_is_package_loading

    g_is_package_loading=True
    sublime.set_timeout( unlock_is_package_loading, 10000 )

    _on_settings_modified()
    settings.add_on_change(CURRENT_PACKAGE_NAME, on_settings_modified)


def unlock_is_package_loading():
    global g_is_package_loading
    g_is_package_loading = False


def install_build_systens(target_file_name):
    target_folder     = CURRENT_PACKAGE_NAME
    target_file       = os.path.join( sublime.packages_path(), "User", target_folder, target_file_name )
    input_file_string = sublime.load_resource( "Packages/%s/%s" % ( CURRENT_PACKAGE_NAME, target_file_name ) )

    target_directory = os.path.join( sublime.packages_path(), "User", target_folder )
    attempt_to_install_file( target_directory, target_file, input_file_string )


def install_setting_file( target_file_name ):
    target_file       = os.path.join( sublime.packages_path(), "User", target_file_name )
    input_file_string = sublime.load_resource( "Packages/%s/%s" % ( CURRENT_PACKAGE_NAME, target_file_name ) )

    target_directory = os.path.join( sublime.packages_path(), "User" )
    attempt_to_install_file( target_directory, target_file, input_file_string )


def attempt_to_install_file( target_directory, target_file, input_file_string ):
    if not os.path.exists( target_directory ):
        os.makedirs( target_directory )

    # How can I force Python's file.write() to use the same newline format in Windows as in Linux (“\r\n” vs. “\n”)?
    # https://stackoverflow.com/questions/9184107/how-can-i-force-pythons-file-write-to-use-the-same-newline-format-in-windows
    #
    # TypeError: 'str' does not support the buffer interface
    # https://stackoverflow.com/questions/5471158/typeerror-str-does-not-support-the-buffer-interface
    if not os.path.exists( target_file ):
        text_file = open( target_file, "wb" )
        text_file.write( bytes(input_file_string, 'UTF-8') )
        text_file.close()


def unload_handler() :
    g_file_observer.stop()
    process_thread.stop()

    g_processing_set_queue.put(("", ""))
    sublime.load_settings("%s.sublime-settings" % CURRENT_PACKAGE_NAME).clear_on_change(CURRENT_PACKAGE_NAME)


class NewAmxxIncludeCommand(sublime_plugin.WindowCommand):
    def run(self):
        new_file("inc")


class NewAmxxPluginCommand(sublime_plugin.WindowCommand):
    def run(self):
        new_file("sma")


def new_file(file_type):
    view = sublime.active_window().new_file()
    view.set_name("untitled."+file_type)

    plugin_template = sublime.load_resource("Packages/%s/default.%s" % (CURRENT_PACKAGE_NAME, file_type))
    plugin_template = plugin_template.replace("\r", "")

    view.run_command("insert_snippet", {"contents": plugin_template})
    sublime.set_timeout_async( lambda: set_new_file_syntax( view ), 0 )


def set_new_file_syntax( view ):
    view.set_syntax_file(g_new_file_syntax)


# https://stackoverflow.com/questions/2865250/python-textwrap-forcing-hard-breaks
def hard_wrap(text, width, indent='    '):
    for line in StringIO(text):
        indent_width = width - len(indent)
        yield line[:width]
        line = line[width:]
        while line:
            yield '\n' + indent + line[:indent_width]
            line = line[indent_width:]


class AboutAmxxEditorCommand(sublime_plugin.WindowCommand):
    def run(self):
        about = "Sublime AmxxEditor v"+ EDITOR_VERSION +" by Destro\n\n\n"

        about += "CREDITs:\n"
        about += "- Great:\n"
        about += "   ppalex7     (SourcePawn Completions)\n\n"

        about += "- Contributors:\n"
        about += "   sasske        (white color scheme)\n"
        about += "   addons_zz     (npp color scheme)\n"
        about += "   KliPPy        (build version)\n"
        about += "   Mistrick      (mistrick color scheme)\n"

        about += "\nhttps://amxmodx-es.com/showthread.php?tid=12316\n"

        sublime.message_dialog(about)


class AmxxBuildVerCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        region = self.view.find("^#define\s+(?:PLUGIN_)?VERSION\s+\".+\"", 0, sublime.IGNORECASE)
        if region == None :
            region = self.view.find("new\s+const\s+(?:PLUGIN_)?VERSION\s*\[\s*\]\s*=\s*\".+\"", 0, sublime.IGNORECASE)
            if region == None :
                return

        line = self.view.substr(region)
        result = amxx_build_ver_regex.match(line)
        if not result :
            return

        build = int(result.group(2))
        build += 1

        beta = result.group(3)
        if not beta :
            beta = ""

        self.view.replace(edit, region, result.group(1) + str(build) + beta + '\"')


class AmxxEditor(sublime_plugin.EventListener):
    def __init__(self) :
        process_thread.start()
        self.delay_queue = None
        g_file_observer.start()

    def on_window_command(self, window, cmd, args) :
        if cmd != "build" :
            return

        view = window.active_view()
        if not is_amxmodx_file(view) or not g_enable_buildversion :
            return

        view.run_command("amxx_build_ver")

    def on_hover(self, view, location, hover_zone):
        if hover_zone != sublime.HOVER_TEXT:
            return
        if not is_amxmodx_file(view) or not g_enable_inteltip :
            return
        region = view.word(location)
        begin = region.begin()

        # log('location', location, region, view.substr(region))
        region = sublime.Region(begin, begin)
        html, location, word_region, scope = self.is_valid_location(view, region)

        if not scope:
            return

        self.show_popup(view, html, location, word_region)

    def show_popup(self, view, html, location, word_region):
        def on_hide_hover():
            view.add_regions("inteltip", [ ])

        view.show_popup(
            html,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            location=location,
            max_width=700,
            on_navigate=self.on_navigate,
            on_hide=on_hide_hover
        )

        if g_enable_inteltip_color:
            view.add_regions("inteltip", [ word_region ], g_enable_inteltip_color)

    def is_valid_location(self, view, region):
        scope = view.scope_name(region.begin())
        # log(1, "scope_name: [%s]" % scope)

        if ( not "support.function" in scope and not "include_path.pawn" in scope ) \
                or region.size() > 1 :
            return None, None, None, None

        if "include_path.pawn" in scope :
            html, location, word_region = self.inteltip_include(view, region)
        else :
            html, location, word_region = self.inteltip_function(view, region)

        return html, location, word_region, scope

    def on_selection_modified(self, view) :
        if not is_amxmodx_file(view):
            return
        if not g_enable_inteltip:
            return

        region = view.sel()[0]
        html, location, word_region, scope = self.is_valid_location(view, region)

        if not html or ( not g_enable_inteltip_calls and not g_enable_inteltip_name ):
            view.erase_phantoms("AmxxEditor")
            return

        if g_enable_inteltip_name:
            if not "keyword.brackets.paren.begin" in scope and not "support.function.call.pawn" in scope:
                if "function.call.paren" in scope:
                    view.erase_phantoms("AmxxEditor")
                    return

        if g_enable_inteltip_calls:
            self.show_phantom(view, html, location, word_region)

        else:
            self.show_popup(view, html, location, word_region)

    def show_phantom(self, view, html, location, word_region):
        view.erase_phantoms("AmxxEditor")
        row, col = view.rowcol(word_region.begin())

        if col > 80:
            new_begin = view.text_point(row, 80)
            word_region = sublime.Region(new_begin, new_begin)

        view.add_phantom(
            "AmxxEditor",
            word_region,
            html.replace("margin: -5px;", "margin: +5px; height: 125px; overflow: scroll;"),
            sublime.LAYOUT_BELOW,
            self.on_navigate,
        )

    def inteltip_function(self, view, region) :
        file_name = view.file_name()
        if not file_name:
            return None, None, None

        word_region = view.word(region)
        search_func = view.substr(word_region)
        doctset     = dict()
        visited     = set()
        found       = None
        node        = g_nodes.get(file_name, Node(view.file_name()))

        self.generate_doctset_recur(node, doctset, visited)
        found = doctset.get(search_func)
        location = word_region.end()
        actual_parameter = -1

        # log('search_func', search_func)
        if not found:
            scope = view.scope_name(region.begin())

            if "function.call.paren" in scope:
                counter = 100
                actual_parameter += 1

                while counter > 0 and not found:
                    counter -= 1
                    begin = word_region.begin() - 1;
                    word_region = view.word(begin)
                    search_func = view.substr(word_region)
                    scope = view.scope_name(word_region.begin())

                    # log('search_func', search_func)
                    if search_func.strip() == ',':
                        actual_parameter += 1

                    if "function.call" not in scope:
                        break

                    elif "function.call.paren" in scope:
                        continue

                    else:
                        found = doctset.get(search_func)

        if found:
            parameters = simple_escape(found.parameters)
            filename = os.path.basename(found.file_name)
            log(4, "param2: [%s] '%s'", parameters, filename)

            if found.function_type :

                if found.return_type :
                    link_local = found.file_name + '#' + FUNC_TYPES(found.function_type).name + ' ' + found.return_type + ':' + found.function_name

                else :
                    link_local = found.file_name + '#' + FUNC_TYPES(found.function_type).name + ' ' + found.function_name

                link_web = filename.rsplit('.', 1)[0] + '#' + found.function_name

            else :

                link_local = found.file_name + '#' + '^' + found.function_name
                link_web = ''

            log( 4, "link_local: %s", link_local )
            html  = '<style>'+ g_inteltip_style + '</style>'
            html += '<div class="top">'                         ############################## TOP

            html += '<a class="file" href="' + link_local + '\\(">' + os.path.basename(found.file_name) + '</a>'
            if link_web:
                html += ' | <a class="file" href="' + link_web + '">WebAPI</a>'

            html += '</div><div class="bottom">'        ############################## BOTTOM

            html += '<span class="func_type">' + FUNC_TYPES(found.function_type).name \
                    +':</span> <span class="func_name">' + found.function_name + '</span>'

            if found.return_type :
                html += '<span class="file"> -> </span>'
                html += '<span class="return">Return:</span> <span class="return_type">' + found.return_type + '</span>'

            html += '<br>'
            html += '<span class="params">Params:</span> '
            html += '<span class="params_definition">'

            # log('actual_parameter', actual_parameter, 'parameters', parameters)
            if actual_parameter != -1 and parameters:
                parameters = parameters.split(",")
                if actual_parameter < len( parameters ):
                    parameters[actual_parameter] = '<span class="file">' + parameters[actual_parameter] + '</span>'
                html += ", ".join(parameters)
            else:
                html += parameters

            html += '</span>'
            html += '<br>'

            html += '</div>'                                    ############################## END

            html += '<div class="file" style="margin-top: 7px;">'
            html += html_newline( wrap_text( found.doc_comment, wrap=100 ) )
            html += '</div>'

            # log( 1, "html: %s", html )
            return html, location, word_region
        return None, None, None

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

    def inteltip_include(self, view, region) :
        word_region = view.word(region)
        location = word_region.end() + 1
        text     = view.substr(view.line(region))
        include  = includes_regex.match(text).group(1)

        file_name_view = view.file_name()

        if file_name_view is None:
            return None, None, None
        else:
            ( file_name, the_include_exists ) = get_file_name( file_name_view, include )

            if not the_include_exists :
                return None, None, None

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
        html += '<span class="func_name">'
        html += html_newline( simple_escape( "".join( hard_wrap( file_name, 80, '' ) ) ) )
        html += '</span>'
        html += '</div>'

        return html, location, word_region

    def on_activated_async(self, view) :
        view_size = view.size()

        log(4, "")
        log(4, "view.match_selector(0, 'source.sma'): " + str( view.match_selector(0, 'source.sma') ))

        # log(4, "g_nodes:", g_nodes)
        log(4, "view.substr(): \n", view.substr( sublime.Region( 0, view_size if view_size < 200 else 200 ) ))

        if not is_amxmodx_file(view):
            log(4, "returning on` if not is_amxmodx_file(view)")
            return

        if not view.file_name() in g_nodes :
            log(4, "returning on` if not view.file_name() in g_nodes")
            add_to_queue(view)

    def on_modified_async(self, view) :
        self.add_to_queue_delayed(view)

    def on_post_save_async(self, view) :
        self.add_to_queue_now(view)

    def on_load_async(self, view) :
        self.add_to_queue_now(view)

    def add_to_queue_now(self, view) :
        if not is_amxmodx_file(view):
            return
        add_to_queue(view)

    def add_to_queue_delayed(self, view) :
        if not is_amxmodx_file(view):
            return

        if self.delay_queue is not None :
            self.delay_queue.cancel()

        if g_delay_time > 0.3:
            self.delay_queue = threading.Timer( float( g_delay_time ), add_to_queue_forward, [ view ] )
            self.delay_queue.start()

    def on_query_completions(self, view, prefix, locations):
        """
            This is a forward called by Sublime Text when it is about to show the use completions.
            See: https://www.sublimetext.com/docs/3/api_reference.html#sublime_plugin.ViewEventListener
        """
        view_file_name = view.file_name()

        if is_amxmodx_file(view):
            # # # Autocompletion issue
            # # # https://github.com/evandrocoan/AmxxEditor/issues/9
            # # temporarily masking word_separators
            # # https://github.com/SublimeTextIssues/Core/issues/819
            # word_separators = view.settings().get("word_separators")
            # view.settings().set("word_separators", "")
            # sublime.set_timeout(lambda: view.settings().set("word_separators", word_separators), 0)

            if view_file_name is None:
                view_file_name = str( view.buffer_id() )

                # Just in case it is not processed yet
                if not view_file_name in g_nodes:

                    log(4, "Adding buffer id", view_file_name, " in g_nodes")
                    add_to_queue_forward( view )

                    # The queue is not processed yet, so there is nothing to show
                    if g_word_autocomplete:
                        log( 16, "(new buffer) Word autocomplete")
                        return None
                    else:
                        log( 16, "(new buffer) Without word autocomplete")
                        return ( [], sublime.INHIBIT_WORD_COMPLETIONS )

                if g_word_autocomplete:
                    log( 16, "(Buffer) Word autocomplete + function")
                    return self.generate_funcset( view_file_name, view, prefix, locations )
                else:
                    log( 16, "(Buffer) Without word autocomplete + function")
                    return ( self.generate_funcset( view_file_name, view, prefix, locations ), sublime.INHIBIT_WORD_COMPLETIONS )
            else:

                if g_word_autocomplete:
                    log( 16, "(File) Word autocomplete + function")
                    return self.generate_funcset( view_file_name, view, prefix, locations )
                else:
                    log( 16, "(File) Without word autocomplete + function")
                    return ( self.generate_funcset( view_file_name, view, prefix, locations ), sublime.INHIBIT_WORD_COMPLETIONS )

        log( 16, "No completions")
        return None

    def generate_funcset( self, file_name, view, prefix, locations ) :
        words_list = []
        funcs_list = []
        funcs_word_list = []

        if file_name in g_nodes:
            node    = g_nodes[file_name]
            visited = set()

            if not view.match_selector(locations[0], 'string') :
                self.generate_funcset_recur( node, visited, funcs_list, funcs_word_list )

        if g_word_autocomplete:
            start_time = time.time()

            if len( locations ) > 0:
                view_words = view.extract_completions( prefix, locations[0] )

            else:
                view_words = view.extract_completions( prefix )

            # This view goes first to prioritize matches close to cursor position.
            for word in view_words:
                # Remove the annoying `(` on the string
                word = word.replace('$', '\\$').split('(')[0]

                if word not in funcs_word_list:
                    words_list.append( ( word, word ) )

                if time.time() - start_time > 0.05:
                    break

        # log( 16, "( generate_funcset ) funcs_list size: %d" % len( funcs_list ) )
        # log( 16, "( generate_funcset ) funcs_list items: " + str( sort_nicely( funcs_list ) ) )
        return words_list + funcs_list

    def generate_funcset_recur( self, node, visited, funcs_list, funcs_word_list ) :

        if node in visited :
            return

        visited.add( node )

        for child in node.children :
            self.generate_funcset_recur( child, visited, funcs_list, funcs_word_list )

        funcs_list.extend( node.funcs_list )
        funcs_word_list.extend( node.words_list )

    def generate_doctset_recur(self, node, doctset, visited) :
        if node in visited :
            return

        visited.add(node)
        for child in node.children :
            self.generate_doctset_recur(child, doctset, visited)

        doctset.update(node.doct)


def is_amxmodx_file(view) :
    return view.match_selector(0, 'source.sma')


def check_color_scope_setting():
    """ https://stackoverflow.com/questions/45734287/list-of-colors-for-highlightwords-sublime-plugin """
    global g_enable_inteltip_color
    found_scope = False

    active_window = sublime.active_window()
    settings = active_window.active_view().settings()

    try:
        color_scheme = settings.get("color_scheme")
        xml_file = sublime.load_resource(color_scheme)
        xml_tree = ElementTree.fromstring(xml_file)
        xml_subtree = xml_tree.find("./dict/array")

        if xml_subtree is None:
            print("No color scheme xml_subtree found")
            return

        for child in xml_subtree:

            for i in range(0, len(child), 2):

                if child[i].tag == "key" and child[i].text == "scope":

                    if g_enable_inteltip_color in child[i + 1].text:
                        found_scope = True

        if not found_scope:
            g_enable_inteltip_color = ""

    except Exception as error:
        print("Error loading color scheme", error)


def on_settings_modified():
    threading.Thread(target=_on_settings_modified).start()


def _on_settings_modified():
    log(4, "")
    global g_enable_inteltip
    global g_enable_inteltip_calls
    global g_enable_inteltip_name
    global g_enable_inteltip_color
    global g_new_file_syntax
    global g_word_autocomplete
    global g_function_autocomplete

    settings = sublime.load_settings("%s.sublime-settings" % CURRENT_PACKAGE_NAME)
    invalid  = is_invalid_settings(settings)

    if invalid:
        if not g_is_package_loading:
            sublime.message_dialog("AmxxEditor:\n\n" + invalid)

        g_enable_inteltip = False
        g_enable_inteltip_calls = False
        g_enable_inteltip_name = False
        return

    # check package path
    packages_path = os.path.join( sublime.packages_path(), CURRENT_PACKAGE_NAME )
    if not os.path.isdir(packages_path) :
        os.mkdir(packages_path)

    # fix-path
    fix_path(settings, 'include_directory')

    # Get the set color scheme
    popup_color_scheme = settings.get('popup_color_scheme')

    # popUp.CSS
    global g_inteltip_style
    g_inteltip_style = sublime.load_resource("Packages/%s/%s-popup.css" % (CURRENT_PACKAGE_NAME, popup_color_scheme))
    g_inteltip_style = g_inteltip_style.replace("\r", "") # fix win/linux newlines

    # cache setting
    global g_enable_buildversion, g_delay_time, g_add_paremeters

    g_enable_inteltip       = settings.get('enable_inteltip', True)
    g_enable_inteltip_calls = settings.get('enable_inteltip_calls', True)
    g_enable_inteltip_name  = settings.get('enable_inteltip_name', False)
    g_enable_inteltip_color = settings.get('enable_inteltip_color', "inteltip.pawn")
    g_enable_buildversion   = settings.get('enable_buildversion', False)
    g_word_autocomplete     = settings.get('word_autocomplete', False)
    g_function_autocomplete = settings.get('function_autocomplete', False)
    g_new_file_syntax       = settings.get('amxx_file_syntax', g_new_file_syntax)
    log.debug_level         = settings.get('debug_level', 1)
    g_delay_time            = settings.get('live_refresh_delay', 1.0)
    g_add_paremeters        = settings.get('add_function_parameters', False)

    check_color_scope_setting()
    g_include_dir.clear()
    include_directory = settings.get('include_directory', './include')

    if isinstance( include_directory, list ):

        for path in include_directory:
            real_path = os.path.realpath( path )
            if os.path.isdir( real_path ): g_include_dir.add( real_path )

    else:
        real_path = os.path.realpath( include_directory )
        if os.path.isdir( real_path ): g_include_dir.add( real_path )

    g_file_observer.unschedule_all()
    log(4, "debug_level: %d", log.debug_level)
    log(4, "g_include_dir: %s", g_include_dir)
    log(4, "g_add_paremeters: %s", g_add_paremeters)

    for directory in g_include_dir:
        g_file_observer.schedule( file_event_handler, directory, True )

    for window in sublime.windows():
        for view in window.views():
            view.erase_phantoms("AmxxEditor")


def is_invalid_settings(settings):
    general_error = "You are not set correctly settings for AmxxEditor.\n\n"
    setting_names = [ "include_directory", "popup_color_scheme", "amxx_file_syntax" ]

    for setting_name in setting_names:
        result = general_settings_checker( settings, setting_name, general_error )

        if result:
            return result

    path_prefix = ""
    setting_name = "include_directory"
    default_value = "F:\\SteamCMD\\steamapps\\common\\Half-Life\\czero\\addons\\amxmodx\\scripting\\include"

    checker = lambda file_path: os.path.exists( file_path )
    result = path_settings_checker( settings, setting_name, default_value, path_prefix, checker )

    if result:
        return result

    path_prefix = os.path.dirname( sublime.packages_path() )
    setting_name = "amxx_file_syntax"
    default_value = g_new_file_syntax

    checker = lambda file_path: os.path.exists( file_path ) or is_inside_sublime_package( file_path )
    result = path_settings_checker( settings, setting_name, default_value, path_prefix, checker )

    if result:
        return result


def general_settings_checker(settings, setting_name, general_error):
    setting_value = settings.get( setting_name )

    if setting_value is None:
        return general_error + "Missing `%s` value." % setting_name


def path_settings_checker(settings, setting_name, default_value, prefix_path, checker):
    setting_value = settings.get( setting_name )

    if setting_value != default_value:
        full_path = os.path.normpath( os.path.join( prefix_path, setting_value ) )

        if not checker( full_path ):
            lines = \
            [
                "The setting `%s` is not configured correctly. The following path does not exists:\n\n" % setting_name,
                "%s (%s)" % (setting_value, full_path),
                "\n\nPlease, go to the following menu and fix the setting:\n\n"
                "`AmxxEditor -> Configure AMXX-Autocompletion Settings`\n\n",
                "`Preferences -> Packages Settings -> AmxxEditor -> Configure AMXX-Autocompletion Settings`",
            ]

            text = "".join( lines )
            print( "\n" + text.replace( "\n\n", "\n" ) )
            return text


def is_inside_sublime_package(file_path):

    try:
        packages_start = file_path.find( "Packages" )
        packages_relative_path = file_path[packages_start:].replace( "\\", "/" )

        # log( 1, "is_inside_sublime_package, packages_relative_path: " + str( packages_relative_path ) )
        sublime.load_binary_resource( packages_relative_path )
        return True

    except IOError:
        return False


def fix_path(settings, key) :
    org_path = settings.get(key)

    if org_path is "${file_path}" :
        return

    path = os.path.normpath(org_path)
    if os.path.isdir(path):
        path += '/'

    settings.set(key, path)


def sort_nicely( words_set ):
    """
        Sort the given iterable in the way that humans expect.
    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in sort_nicely_regex.split(key[0]) ]

    return sorted( words_set, key = alphanum_key )


def add_to_queue_forward(view) :
    if g_delay_time > 0.3:
        sublime.set_timeout_async( lambda: add_to_queue( view ), float( g_delay_time ) * 1000.0 )


def add_to_queue(view) :
    """
        The view can only be accessed from the main thread, so run the regex
        now and process the results later
    """
    log( 4, "( add_to_queue ) view.file_name(): %s", view.file_name() )

    # When the view is not saved, we need to use its buffer id, instead of its file name.
    view_file_name = view.file_name()

    if view_file_name is None :
        view_file_name = str( view.buffer_id() )

    if view_file_name not in g_processing_set_queue_set:
        g_processing_set_queue_set.add( view_file_name )
        g_processing_set_queue.put( ( view_file_name, view.substr( sublime.Region( 0, view.size() ) ) ) )

        include_directory = os.path.realpath( os.path.join( os.path.dirname( view_file_name ), "include" ) )

        if include_directory not in g_include_dir:

            if os.path.isdir( include_directory ):
                g_include_dir.add( include_directory )
                g_file_observer.schedule( file_event_handler, include_directory, True )


def add_include_to_queue(file_name) :
    if file_name not in g_processing_set_queue_set:
        g_processing_set_queue_set.add( file_name )
        g_processing_set_queue.put((file_name, None))


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

    node = g_nodes.get(file_path)
    if node is None :
        return

    node.remove_all_children_and_funcs()


def is_active(file_name) :
    return sublime.active_window().active_view().file_name() == file_name


class ProcessQueueThread(watchdog.utils.DaemonThread) :
    def run(self) :
        while self.should_keep_running() :
            (file_name, view_buffer) = g_processing_set_queue.get()

            try:
                g_processing_set_queue_set.remove( file_name )
            except:
                pass

            # When the `view_buffer` is None, it means we are processing a file on the disk, instead
            # of a file on an Sublime Text View (its text buffer).
            if view_buffer is None :
                self.process_existing_include(file_name)
            else :
                self.process(file_name, view_buffer)

    def process(self, view_file_name, view_buffer) :
        base_includes = set()
        (current_node, node_added) = get_or_add_node(view_file_name)

        # Here we parse the text file to know which modules it is including.
        includes = includes_regex.findall(view_buffer)

        # Now for each module it is including we load that include file to the autocomplete list.
        for include in includes:
            self.load_from_file(view_file_name, include, current_node, current_node, base_includes)

        # For each module it was loaded but it not present on the current file we just switched,
        # we remove that include file to the autocomplete list.
        for removed_node in current_node.children.difference(base_includes) :
            current_node.remove_child(removed_node)

        # To process the current file functions for autocomplete
        process_buffer(view_buffer, current_node)

    def process_existing_include(self, file_name) :
        current_node = g_nodes.get(file_name)
        if current_node is None or not os.path.exists( file_name ):
            return

        base_includes = set()

        with open(file_name, 'r') as f :
            log(2, "Processing Include File %s" % file_name)
            includes = includes_regex.findall(f.read())

        for include in includes:
            self.load_from_file(file_name, include, current_node, current_node, base_includes)

        for removed_node in current_node.children.difference(base_includes) :
            current_node.remove_child(removed_node)

        process_include_file(current_node)

    def load_from_file(self, view_file_name, base_file_name, parent_node, base_node, base_includes) :
        (file_name, exists) = get_file_name(view_file_name, base_file_name)

        if not exists :
            log(1, "Include File Not Found: %s" % base_file_name)
            return

        (node, node_added) = get_or_add_node(file_name)
        parent_node.add_child(node)

        if parent_node == base_node :
            base_includes.add(node)

        if not node_added :
            return

        with open(file_name, 'r') as f :
            log(2, "Processing Include File %s" % file_name)
            includes = includes_regex.findall(f.read())

        for include in includes :
            self.load_from_file(view_file_name, include, node, base_node, base_includes)

        process_include_file(node)


def get_file_name(view_file_name, base_file_name) :
    log(4, "g_include_dir: %s", g_include_dir)
    path_exists = False

    # True, if `base_file_name` is a include file name, instead of full file path
    if local_regex.search(base_file_name) == None:

        for directory in g_include_dir:
            file_name = os.path.join(directory, base_file_name + '.inc')

            if os.path.exists(file_name):
                path_exists = True
                break

    else:
        file_name = os.path.join(os.path.dirname(view_file_name), base_file_name)
        path_exists = os.path.exists(file_name)

    return (file_name, path_exists)


def get_or_add_node(file_name) :
    """
        Here if `file_name` is a buffer id as a string, I just check if the buffer exists.

        However if it is a file name, I need to check if its a buffer id is present here, and
        if so, I must to remove it and create a new node with the file name. This is necessary
        because the file could be just create, parsed and then saved. Therefore after did so,
        we need to keep reusing its buffer. But as it is saved we are using its file name instead
        of its buffer id, then we need to remove the buffer id in order to avoid duplicated entries.

        Though I am not implementing this here to save time and performance
    """

    node = g_nodes.get(file_name)
    if node is None :
        node = Node(file_name)
        g_nodes[file_name] = node
        return (node, True)

    return (node, False)


# ============= NEW CODE ------------------------------------------------------------------------------------------------------------
class TooltipDocumentation(object):
    def __init__(self, function_name, parameters, file_name, function_type, return_type, doc_comment):
        """
            For `function_type` see FUNC_TYPES.
        """
        self.function_name = function_name
        self.parameters = parameters.strip()
        self.file_name = file_name
        self.function_type = function_type
        self.return_type = return_type
        self.doc_comment = wrap_text( doc_comment, trim_spaces=" ", trim_plus="*" )


class Node(object):
    def __init__(self, file_name) :
        self.file_name = file_name

        self.doct = dict()
        self.children = set()
        self.parents = set()

        # They are list to keep ordering
        self.funcs_list = []
        self.words_list = []
        self.words_set = set()

        try:
            float(file_name)
            self.isFromBufferOnly = True
        except ValueError:
            self.isFromBufferOnly = False

    def add_child(self, node) :
        self.children.add(node)
        node.parents.add(self)

    def remove_child(self, node) :
        self.children.remove(node)
        node.parents.remove(self)

        if len(node.parents) <= 0 :
            g_nodes.pop(node.file_name)

    def remove_all_children_and_funcs(self) :
        for child in self.children :
            self.remove_child(node)

        self.doct.clear()
        self.funcs_list.clear()
        self.words_list.clear()


def set_is_parsing_function(func):
    @wraps(func)
    def wrapping(self, *args, **kwargs):
        self.is_parsing_function = True
        result = func(self, *args, **kwargs)
        self.is_parsing_function = False
        return result
    return wrapping


def clear_doc_comment(func):
    @wraps(func)
    def wrapping(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.clearDocComment()
        return result
    return wrapping


class PawnParse(object):
    def __init__(self) :
        self.node = None
        self.isTheCurrentFile = False
        self.save_const_timer = None
        self.constants_count = 0

    def start( self, file, node, isTheCurrentFile=False ) :
        """
            When the buffer is not None, it is always the current file.
        """
        log(8, "CODE PARSE Start [%s]" % node.file_name)
        self.is_parsing_function = False

        if hasattr( file, "readline" ):
            self.file = file
        else:
            self.file = StringIO(file)

        self.isTheCurrentFile   = isTheCurrentFile
        self.file_name          = os.path.basename(node.file_name)
        self.node               = node
        self.found_comment      = False
        self.found_enum         = False
        self.is_to_skip_brace   = False
        self.enum_contents      = ''
        self.brace_level        = 0
        self._restore_buffer    = deque()

        self.is_to_skip_next_line     = False
        self.if_define_brace_level    = 0
        self.else_defined_brace_level = 0

        self.if_define_level   = 0
        self.else_define_level = 0

        self.doc_comment       = ""
        self.is_on_if_define   = []
        self.is_on_else_define = []

        self.node.doct.clear()
        self.node.funcs_list.clear()
        self.node.words_list.clear()
        self.node.words_set.clear()

        self.start_parse()

        if self.constants_count != len(g_constants_list) :
            if self.save_const_timer :
                self.save_const_timer.cancel()

            self.save_const_timer = threading.Timer(4.0, self.save_constants)
            self.save_const_timer.start()

        log(8, "CODE PARSE End [%s]" % node.file_name)

    def save_constants(self) :
        self.save_const_timer = None
        self.constants_count  = len(g_constants_list)
        windows               = sublime.windows()

        # If you have a project within 10000 files, each time this is updated, will for sublime to
        # process again all the files. Therefore only allow this on project with no files to index.
        #
        # If someone is calling this, it means there are some windows with a AMXX file open. Therefore
        # we do not care to check whether that window has a project or not and there will always be
        # constants to save.
        for window in windows:
            # log(4, "window.id(): " + str( window.id() ) )
            # log(4, "window.folders(): " + str( window.folders() ) )
            # log(4, "window.project_file_name(): " + str( window.project_file_name() ) )

            if len( window.folders() ) > 0:
                log( 4, "Not saving this time." )
                return

        constants = "___test"
        for const in g_constants_list :
            constants += "|" + const

        syntax = "%YAML 1.2\n---\nscope: source.sma\nhidden: true\ncontexts:\n  main:\n    - match: \\b(" \
                + constants + ")\\b\s*(?!\()\n      scope: constant.vars.pawn\n\n"

        file_name = os.path.join(sublime.packages_path(), CURRENT_PACKAGE_NAME, "AmxxEditorConsts.sublime-syntax")

        f = open(file_name, 'w')
        f.write(syntax)
        f.close()

        log(8, "end")

    def restoreBuffer(self, line):
        self._restore_buffer.append( line )
        # log(repr(line))
        # assert line

    def read_line(self, peek=0) :
        if peek:
            peek -= 1
            if peek < len( self._restore_buffer ):
                line = self._restore_buffer[peek]
                if line == "": line = "\n"
            else:
                line = self.file.readline()
                self.restoreBuffer( line )
        elif len( self._restore_buffer ):
            line = self._restore_buffer.popleft()
            if line == "": line = "\n"
        else:
            line = self.file.readline()

        # log(1, repr(line))
        if line == "":
            return None
        return line

    def read_string(self, current_line) :
        current_line = space_clean_regex.sub( " ", current_line.strip( " \t" ) )
        result = ''
        doc_comment = ''
        sindex = 0

        # log( 1, repr( current_line ) )
        buffer_length = len(current_line)

        while sindex < buffer_length :
            if current_line[sindex] == '/' and sindex + 1 < len(current_line):
                if current_line[sindex + 1] == '/' :
                    self.addDocComment( current_line.lstrip( '/' ), force=True )
                    self.brace_level += result.count('{') - result.count('}')
                    return result
                elif current_line[sindex + 1] == '*' :
                    self.found_comment = True
                    self.clearDocComment()
                    sindex += 1
                elif not self.found_comment :
                    result += '/'
            elif self.found_comment :
                if current_line[sindex] == '*' and sindex + 1 < len(current_line) and current_line[sindex + 1] == '/' :
                    self.addDocComment( doc_comment )
                    self.found_comment = False
                    sindex += 1
                else:
                    doc_comment += current_line[sindex]
            elif not (sindex > 0 and current_line[sindex] == ' ' and current_line[sindex - 1] == ' '):
                result += current_line[sindex]

            sindex += 1

        self.brace_level +=  result.count('{') - result.count('}')
        self.addDocComment( doc_comment )
        return result

    def addDocComment(self, comment_line, force=False) :
        if ( comment_line and self.found_comment and not self.is_parsing_function ) \
                or ( force and not self.is_parsing_function ):
            self.doc_comment += comment_line

    def clearDocComment(self) :
        if not self.is_parsing_function:
            self.doc_comment = ''

    def skip_function_block(self, current_line) :
        inChar    = False
        inString  = False
        num_brace = 0
        self.is_to_skip_brace = False

        while current_line is not None and ( current_line.isspace() or not len(current_line) ) :
            current_line = self.read_line()

        while current_line is not None :
            # log( 1, repr(current_line) )

            pos = 0
            sindex = 0
            lastChar = ''
            penultimateChar = ''

            for c in current_line :
                sindex += 1

                if not inString and not inChar and lastChar == '*' and c == '/' :
                    self.found_comment = False

                if not inString and not inChar and self.found_comment:
                    penultimateChar = lastChar
                    lastChar        = c
                    continue

                if not inString and not inChar and lastChar == '/' and c == '*' :
                    self.found_comment = True
                    penultimateChar    = lastChar
                    lastChar           = c
                    continue

                if not inString and not inChar and c == '/' and lastChar == '/' :
                    break

                if c == '"' :

                    if inString and lastChar != '^' :
                        inString = False

                    else :
                        inString = True

                if not inString and c == '\'' :

                    if inChar and lastChar != '^' :
                        inChar = False

                    else :
                        inChar = True

                # This is hard stuff. We need to fix the parsing for the following problem:
                #
                # public on_damage(id)
                # {
                # #if defined DAMAGE_RECIEVED
                #     if ( is_user_connected(id) && is_user_connected(attacker) )
                #     {
                # #else
                #     if ( is_user_connected(attacker) )
                #     {
                # #endif
                #     }
                #     return PLUGIN_CONTINUE
                # }
                # public death_hook()
                # {
                #     {
                #         new kuid = get_user_userid(killer)
                #     }
                # }
                #
                # Above here we may notice, there are 2 braces opening but only one brace close.
                # Therefore, we will skip the rest of the source code if we do not handle the braces
                # definitions between the `#if` and `#else` macro clauses.
                #
                # To keep track about where we are, we need to keep track about how much braces
                # levels are being opened and closed using the variables `self.if_define_brace_level`
                # and `self.else_defined_brace_level`. And finally at the end of it all on the `#endif`,
                # we update the `num_brace` with the correct brace level.
                #
                if not inString and not inChar :
                    # Flags when we enter and leave the `#if ... #else ... #endif` blocks
                    if penultimateChar == '#':

                        # Cares of `#if`
                        if lastChar == 'i' and c == 'f':
                            ++self.if_define_level
                            self.is_on_if_define.append( True )

                        # Cares of `#else` and `#end`
                        elif lastChar == 'e':

                            if c == 'l':
                                ++self.else_define_level
                                self.is_on_if_define.append( False )
                                self.is_on_else_define.append( True )

                            elif c == 'n':

                                # Decrement the `#else` level, only if it exists
                                if len( self.is_on_if_define ) > 0:

                                    if not self.is_on_if_define[ -1 ]:
                                        self.is_on_if_define.pop()

                                        if len( self.is_on_else_define ) > 0:
                                            --self.else_define_level
                                            self.is_on_else_define.pop()

                                    if len( self.is_on_if_define ) > 0:
                                        --self.if_define_level
                                        self.is_on_if_define.pop()

                                    # If there are unclosed levels on the preprocessor, fix the `num_brace` level
                                    extra_levels = max( self.else_defined_brace_level, self.if_define_brace_level )
                                    num_brace   -= extra_levels

                                    # Both must to be equals, so just reset their levels.
                                    self.if_define_brace_level   -= extra_levels
                                    self.else_defined_brace_level -= extra_levels

                    # Flags when we enter and leave the braces `{ ... }` blocks
                    if c == '{':
                        num_brace            += 1
                        self.is_to_skip_brace = True

                        if len( self.is_on_if_define ) > 0:

                            if self.is_on_if_define[ -1 ] :
                                self.if_define_brace_level += 1

                            else:
                                self.else_defined_brace_level += 1

                    elif c == '}':
                        pos = sindex
                        num_brace -= 1

                        if len( self.is_on_if_define ) > 0:

                            if self.is_on_if_define[ -1 ] :
                                self.if_define_brace_level -= 1

                            else:
                                self.else_defined_brace_level -= 1

                penultimateChar = lastChar
                lastChar        = c

            # log( 1, "num_brace:                %d" % num_brace )
            # log( 1, "if_define_brace_level:    %d" % self.if_define_brace_level )
            # log( 1, "else_defined_brace_level: %d" % self.else_defined_brace_level )

            # log( 1, "is_on_if_define:          " + str( self.is_on_if_define ) )
            # log( 1, "is_on_else_define:        " + str( self.is_on_else_define ) )
            # log( 1, "" )

            if num_brace == 0 :
                self.restoreBuffer(current_line[pos:])
                return

            current_line = self.read_line()

    def is_valid_name(self, name) :
        if not name or not name[0].isalpha() and name[0] != '_' :
            return False

        return is_valid_name_regex.match(name) is not None

    def add_constant(self, name) :
        fixname = add_constant_regex.search(name)

        if fixname :
            name = fixname.group(1)
            g_constants_list.add(name)

    def add_enum(self, current_line) :
        current_line = current_line.strip()
        if current_line == '' :
            return

        split = current_line.split('[')
        self.add_constant(split[0])

        self.add_general_autocomplete(current_line, 'enum', split[0])
        log(8, "add: [%s] -> [%s]" % (current_line, split[0]))

    def add_general_autocomplete(self, name, info, autocomplete) :

        if name not in self.node.words_set:
            self.node.words_set.add( name )
            self.node.words_list.append( name )

        if self.node.isFromBufferOnly or self.isTheCurrentFile:
            self.node.funcs_list.append( ["{}\t {}".format( name, info ), autocomplete] )
        else:
            self.node.funcs_list.append( ["{} \t{} - {}".format( name, self.file_name, info ), autocomplete] )

    def add_function_autocomplete(self, name, info, autocomplete, param_count) :
        show_name = name + "(" + str( param_count ) + ")"
        self.node.words_set.add( name )
        self.node.words_list.append( name )

        # We do not check whether `if name in words` because we can have several functions
        # with the same name but different parameters
        if self.node.isFromBufferOnly or self.isTheCurrentFile:
            self.node.funcs_list.append( ["{}\t {}".format( show_name, info ), autocomplete] )

        else:
            self.node.funcs_list.append( ["{} \t{} - {}".format( show_name, self.file_name, info ), autocomplete] )

    def add_word_autocomplete(self, name) :
        """
            Used to add a word to the auto completion of the current current_line. Therefore, it does not
            need the file name as the auto completion for words from other files/sources.
        """

        if name not in self.node.words_list:
            self.node.words_set.add( name )
            self.node.words_list.append( name )

            if self.isTheCurrentFile:
                self.node.funcs_list.append( [name, name] )

            else:
                self.node.funcs_list.append( ["{}\t {}".format( name, self.file_name ), name] )

    def start_parse(self) :

        while True :
            current_line = self.read_line()
            # log( 1, repr( current_line ) )

            if current_line is None :
                break

            current_line = self.read_string(current_line).rstrip('\n')
            if len(current_line) <= 0 :
                continue

            #if "sma" in self.node.file_name :
            #   print("read: skip:[%d] brace_level:[%d] buff:[%s]" % (self.is_to_skip_next_line, self.brace_level, current_line))

            if self.is_to_skip_next_line :
                self.is_to_skip_next_line = False
                continue

            if current_line.startswith('#define ') :
                self.parse_define(current_line)
            elif current_line.startswith('const ') :
                self.parse_const(current_line)
            elif current_line.startswith('enum ') or current_line == 'enum':
                self.found_enum = True
                self.enum_contents = ''
            elif current_line.startswith('new ') :
                self.parse_variable(current_line)

            elif current_line.startswith('public ') :
                self.parse_function(current_line, 1)

            elif current_line.startswith('stock ') :
                """
                    new STOCK_TEST1[] = "something";
                    const STOCK_TEST2[] = "something";
                    stock STOCK_TEST3[] = "something";
                    stock const STOCK_TEST4[] = "something";

                    stock bool:xs_vec_equal(const Float:vec1[], const Float:vec2[]) { }
                    stock xs_vec_add(const Float:in1[], const Float:in2[], Float:out[]) { }
                """
                if current_line.split('(')[0].find(" const ") > -1:
                    current_line = current_line[6:]
                    self.parse_const(current_line)

                else:
                    matches = function_regex.search(current_line)
                    # log( 1, 'current_line: %s', current_line )
                    # log( 1, 'matches: %s', matches )

                    if matches == None:
                        current_line = "new " + current_line[6:]
                        self.parse_variable(current_line)

                    else:
                        self.parse_function(current_line, 2)

            elif current_line.startswith('forward ') :
                self.parse_function(current_line, 3)
            elif current_line.startswith('native ') :
                self.parse_function(current_line, 4)
            elif not self.found_enum and not current_line[0] == '#' and function_regex.search(current_line) :
                self.parse_function(current_line, 0)

            if self.found_enum :
                self.parse_enum(current_line)

    @clear_doc_comment
    def parse_define(self, current_line) :
        full_line = current_line.strip('\\ \n') + ' '
        has_next = has_define_next_line_regex.match(current_line)

        if has_next:
            while True:
                next_line = self.read_line()
                if next_line is None : break

                full_line += next_line.strip('\\ \n') + ' '
                has_next = has_define_next_line_regex.match(next_line)
                if not has_next:
                    break

        define = parse_define_regex.search(full_line)
        # log(1, full_line, define)

        if define :
            current_line = ''
            name   = define.group(1)
            value  = define.group(2).strip()

            count        = 0
            params_raw   = name.split('(')
            name         = params_raw[0]
            params_count = 0

            if len( params_raw ) == 2:
                params_raw   = params_raw[1].strip(')')
                params       = params_raw.split(',')
                comma_count  = len( params )
                params_count = comma_count

                # If we entered here, there are at least one parameter
                params = "${1:param1}"
                items  = range( 2, comma_count + 1 )

                for item in items:
                    params += ", " + '${%d:param%d}' % ( item, item )
            else:
                params = ""
                params_raw = ""

            if params_count > 0:
                param_value = name + "(" + params + ")"
                self.add_function_autocomplete( name, 'define: ' + value, param_value, params_count )
                self.node.doct[name] = TooltipDocumentation( name, params_raw, self.node.file_name, 5, "", self.doc_comment )
            else:
                self.add_general_autocomplete( name, 'define: ' + value, name )
                self.node.doct[name] = TooltipDocumentation( name, params_raw, self.node.file_name, 5, "", self.doc_comment )

            self.add_constant( name )
            # log(1, "add: [%s]" % name)

    @clear_doc_comment
    def parse_const(self, current_line) :
        current_line = current_line[6:]
        log(8, "[%s]" % current_line)

        split   = current_line.split('=', 1)
        if len(split) < 2 :
            return

        name    = split[0].strip()
        value   = split[1].strip()

        newline = value.find(';')
        if (newline != -1) :
            self.restoreBuffer( value[newline+1:].strip() )
            value = value[0:newline]

        self.add_constant(name)
        self.add_general_autocomplete(name, 'const: ' + value, name)

        log(8, "add: [%s]" % name)

    @clear_doc_comment
    def parse_variable(self, current_line) :
        if current_line.startswith('new const ') :
            current_line = current_line[10:]
        else :
            current_line = current_line[4:]

        varName = ""
        lastChar = ''
        sindex = 0
        pos = 0
        num_brace = 0
        multiLines = True
        skipSpaces = False
        parseName = True
        inBrackets = False
        inBraces = False
        inString = False

        while multiLines :
            multiLines = False

            for c in current_line :
                sindex += 1

                if (c == '"') :
                    if (inString and lastChar != '^') :
                        inString = False
                    else :
                        inString = True

                if (inString == False) :
                    if (c == '{') :
                        num_brace += 1
                        inBraces = True
                    elif (c == '}') :
                        num_brace -= 1
                        if (num_brace == 0) :
                            inBraces = False

                if skipSpaces :
                    if c.isspace() :
                        continue
                    else :
                        skipSpaces = False
                        parseName = True

                if parseName :
                    if (c == ':') :
                        varName = ''
                    elif (c == ' ' or c == '=' or c == ';' or c == ',') :
                        varName = varName.strip()

                        if (varName != '') :
                            self.add_word_autocomplete( varName )
                            log(8, "add: [%s]" % varName)

                        varName = ''
                        parseName = False
                        inBrackets = False
                    elif (c == '[') :
                        inBrackets = True
                    elif (inBrackets == False) :
                        varName += c

                if (inString == False and inBrackets == False and inBraces == False) :
                    if not parseName and c == ';' :
                        self.restoreBuffer( current_line[sindex:].strip() )
                        return

                    if (c == ',') :
                        skipSpaces = True

                lastChar = c

            if (c != ',') :
                varName = varName.strip()
                if varName != '' :
                    self.add_word_autocomplete( varName )
                    log(8, "add: [%s]" % varName)
            else :
                multiLines = True
                current_line = ' '

                while current_line is not None and current_line.isspace() :
                    current_line = self.read_line()

    @clear_doc_comment
    def parse_enum(self, current_line) :
        pos = current_line.find('}')
        if pos != -1 :
            current_line = current_line[0:pos]
            self.found_enum = False

        self.enum_contents = '%s\n%s' % (self.enum_contents, current_line)
        current_line = ''

        ignore = False
        if not self.found_enum :
            pos = self.enum_contents.find('{')
            self.enum_contents = self.enum_contents[pos + 1:]

            for c in self.enum_contents :
                if c == '=' or c == '#' :
                    ignore = True
                elif c == '\n':
                    ignore = False
                elif c == ':' :
                    current_line = ''
                    continue
                elif c == ',' :
                    self.add_enum(current_line)
                    current_line = ''

                    ignore = False
                    continue

                if not ignore :
                    current_line += c

            self.add_enum(current_line)
            current_line = ''

    @clear_doc_comment
    @set_is_parsing_function
    def parse_function(self, current_line, ftype) :
        multi_line = False
        temp = ''
        full_func_str = None
        open_paren_found = 0
        # log(repr(current_line), 'doc_comment', repr(self.doc_comment)[:10])

        while current_line is not None :
            current_line = current_line.strip()
            count = current_line.count('(')

            if count:
                open_paren_found += count

            elif open_paren_found == 0:
                next_line = self.read_line()
                self.restoreBuffer( next_line )

                if next_line is None :
                    return

                next_line = self.read_string(next_line)
                if not next_line or next_line[0] != '(':
                    return

            if open_paren_found:
                count = current_line.count(')')

                if count:
                    open_paren_found -= count

                if open_paren_found == 0:
                    last_paren = current_line.rfind(')')
                    full_func_str = current_line[0:last_paren + 1]
                    current_line = current_line[last_paren+1:]

                    if (multi_line) :
                        full_func_str = '%s%s' % (temp, full_func_str)

                    break

                multi_line = True
                temp = '%s%s' % (temp, current_line)

            current_line = self.read_line()

            if current_line is None :
                return

            current_line = self.read_string(current_line)

        if full_func_str is not None :
            if ftype <= 2:
                next_line = current_line
                count = 1
                peek_index = 1

                while count >= 0:
                    count -= 1
                    if '{' in next_line:
                        break
                    next_line = self.read_line(peek=peek_index)
                    peek_index += 1

                    if next_line is None :
                        return
                    next_line = self.read_string(next_line)

                    if '(' in next_line:
                        return
                else:
                    return

            error = self.parse_function_params(full_func_str, ftype)

            if not error and ftype <= 2 :
                self.skip_function_block(current_line)

                if not self.is_to_skip_brace :
                    self.is_to_skip_next_line = True

            # log(1, "skip_brace: error:[%d] ftype:[%d] found:[%d] skip:[%d] func:[%s]" % (error, ftype, self.is_to_skip_brace, self.is_to_skip_next_line, full_func_str))


    def parse_function_params(self, func, function_type) :
        if function_type == 0 :
            remaining = func
        else :
            split = func.split(' ', 1)
            remaining = split[1]

        split = remaining.split('(', 1)

        if len(split) < 2 :
            log(4, "return1: [%s]" % split)
            return 1

        remaining = split[1]
        returntype = ''
        funcname_and_return = split[0].strip()

        # Float:rg_fire_bullets3(...
        # Float:[3] rg_fire_bullets3(...
        match = function_return_regex.search(funcname_and_return)
        if match :
            funcname = match.group(2).strip()
            returntype = match.group(1).strip()

        else :
            match = function_return_array_regex.search(funcname_and_return)
            if match :
                funcname = match.group(2).strip()
                returntype = match.group(1).strip()

            else :
                funcname = funcname_and_return.strip()

        if funcname.startswith("operator") :
            return 0

        if not self.is_valid_name(funcname) :
            log(4, "invalid name: [%s]" % funcname)
            return 1

        remaining = remaining.strip()

        if remaining == ')':
            params = []

        else:
            params = remaining.strip()[:-1].split(',')

        if g_add_paremeters:
            sindex = 1
            autocomplete = funcname + '('

            for param in params:

                if sindex > 1:
                    autocomplete += ', '

                autocomplete += '${%d:%s}' % (sindex, param.strip())
                sindex += 1

            autocomplete += ')'

        else:
            autocomplete = funcname + "()"

        self.add_function_autocomplete(funcname, FUNC_TYPES(function_type).name, autocomplete, len( params ))
        self.node.doct[funcname] = TooltipDocumentation(
            funcname,
            func[func.find("(")+1:-1],
            self.node.file_name,
            function_type,
            returntype,
            self.doc_comment
        )

        log(8, "add: [%s]" % func)
        return 0


def process_buffer(text, node) :
    if g_function_autocomplete:
        pawnParse.start(text, node, True)


def process_include_file(node) :
    with open(node.file_name) as file :
        pawnParse.start(file, node)


def simple_escape(html) :
    return html.replace('&', '&amp;')


def html_newline(html) :
    return new_line_regex.sub( "<br />", html )


pawnParse = PawnParse()
process_thread = ProcessQueueThread()
file_event_handler = IncludeFileEventHandler()


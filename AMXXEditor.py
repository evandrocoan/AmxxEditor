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

sys.path.append( os.path.dirname( __file__ ) )
import watchdog.events
import watchdog.observers
import watchdog.utils
from watchdog.utils.bricks import OrderedSetQueue

import datetime



def main():

    # The keyword `global` is only useful to change or create `global` variables in a local context.
    global EDITOR_VERSION
    global FUNC_TYPES

    global startTime
    global print_debug_lastTime

    global g_constants_list
    global g_debug_level
    global g_delay_time
    global g_include_dir

    global to_process
    global nodes
    global file_observer
    global process_thread
    global file_event_handler
    global includes_re
    global local_re
    global pawnparse
    global amxxPawnSyntax

    amxxPawnSyntax = 'source.AmxxPawn'
    g_debug_level  = 10

    startTime            = datetime.datetime.now()
    print_debug_lastTime = startTime.microsecond

    print_debug( 1, "" )
    print_debug( 1, "" )
    # print_debug( 1, startTime.strftime("%Y-%m-%d %H:%M:%S") )

    print_debug( 1, startTime.isoformat() )
    print_debug( 1, "Entering on the main(0) function." )

    EDITOR_VERSION = "3.0"
    FUNC_TYPES     = [ "Function", "Public", "Stock", "Forward", "Native" ]

    g_constants_list = set()
    g_delay_time     = 1.0
    g_include_dir    = "."

    to_process         = OrderedSetQueue()
    nodes              = dict()
    file_observer      = watchdog.observers.Observer()
    process_thread     = ProcessQueueThread()
    file_event_handler = IncludeFileEventHandler()
    includes_re        = re.compile( '^[\\s]*#include[\\s]+[<"]([^>"]+)[>"]', re.MULTILINE )
    local_re           = re.compile( '\\.(sma|inc)$' )
    pawnparse          = PawnParse()



def plugin_loaded():

    print_debug( 1, "Entering on the plugin_loaded(0) function." )
    settings = sublime.load_settings( "amxx.sublime-settings" )

    on_settings_modified()
    settings.add_on_change( 'amxx', on_settings_modified )



def unload_handler():

    print_debug( 1, "Entering on the unload_handler(0) function." )

    file_observer.stop()
    process_thread.stop()

    to_process.put( ( "", "" ) )
    sublime.load_settings( "amxx.sublime-settings" ).clear_on_change( "amxx" )



class NewAmxxIncludeCommand( sublime_plugin.WindowCommand ):

    def run( self ):

        print_debug( 1, "Entering on the NewAmxxIncludeCommand::run(1) function." )
        new_file( "inc" )



class NewAmxxPluginCommand( sublime_plugin.WindowCommand ):

    def run( self ):

        print_debug( 1, "Entering on the NewAmxxPluginCommand::run(1) function." )
        new_file( "sma" )



def new_file( type ):

    print_debug( 1, "Entering on the new_file(1) function." )
    view = sublime.active_window().new_file()

    view.set_syntax_file( "AMXX-Pawn.sublime-syntax" )
    view.set_name( "untitled." + type )

    plugin_template = sublime.load_resource( "Packages/amxmodx/default." + type )
    plugin_template = plugin_template.replace( "\r", "" )

    view.run_command( "insert_snippet", {"contents": plugin_template} )



class AboutAmxxEditorCommand( sublime_plugin.WindowCommand ):

    def run( self ):

        print_debug( 1, "Entering on the AboutAmxxEditorCommand::run(1) function." )

        about  = "Sublime AMXX-Editor v"+ EDITOR_VERSION +" by Destro\n\n\n"
        about += "CREDITs:\n"
        about += "- Great:\n"
        about += "   ppalex7     ( SourcePawn Completions )\n\n"

        about += "- Contributors:\n"
        about += "   sasske        ( white color scheme )\n"
        about += "   addons_zz      ( npp color scheme )\n"
        about += "   KliPPy           ( build version )\n"
        about += "   Mistrick     ( mistrick color scheme )\n"

        sublime.message_dialog( about )



class AMXXEditor( sublime_plugin.EventListener ):

    def __init__( self ):

        print_debug( 1, "Entering on the AMXXEditor::__init__(1) function." )

        try:

            print_debug( 1, "Starting the Thread process_thread..." )
            process_thread.start()

            print_debug( 1, "Starting the Thread file_observer..." )
            file_observer.start()

        except Exception:

            pass

        self.delay_queue = None


    def on_navigate( self, link ):

        print_debug( 1, "Entering on the AMXXEditor::on_navigate(2) function." )
        ( file, search ) = link.split( '#' )

        if "." in file:

            view = sublime.active_window().open_file( file );

            def do_position():

                if view.is_loading():

                    sublime.set_timeout( do_position, 100 )

                else:

                    r = view.find( search, 0, sublime.IGNORECASE )

                    view.sel().clear()
                    view.sel().add( r )


                    view.show( r )

            do_position()

        else:

            webbrowser.open_new_tab( "http://www.amxmodx.org/api/"+file+"/"+search )


    # Sublime Text event listeners/forwards
    def on_activated_async( self, view ):

        print_debug( 1, "Entering on the AMXXEditor::on_activated_async(2) function." )

        if not self.is_amxmodx_file( view ):

            return

        if not view.file_name():

            return

        if not view.file_name() in nodes:

            add_to_queue( view )


    def on_modified_async( self, view ):

        print_debug( 1, "Entering on the AMXXEditor::on_modified_async(2) function." )
        # self.add_to_queue_delayed( view )


    def on_post_save_async( self, view ):

        print_debug( 1, "Entering on the AMXXEditor::on_post_save_async(2) function." )
        self.add_to_queue_now( view )


    def on_load_async( self, view ):

        print_debug( 1, "Entering on the AMXXEditor::on_load_async(2) function." )
        self.add_to_queue_now( view )


    def add_to_queue_now( self, view ):

        print_debug( 1, "Entering on the AMXXEditor::add_to_queue_now(2) function." )

        if not self.is_amxmodx_file( view ):

            return

        add_to_queue( view )

    def add_to_queue_delayed( self, view ):

        print_debug( 1, "Entering on the AMXXEditor::add_to_queue_delayed(2) function." )

        if not self.is_amxmodx_file( view ):

            return

        if self.delay_queue is not None:

            self.delay_queue.cancel()

        self.delay_queue = Timer( float( g_delay_time ), add_to_queue_forward, [ view ] )
        self.delay_queue.start()


    def is_amxmodx_file( self, view ):

        print_debug( 1, "Entering on the AMXXEditor::is_amxmodx_file(2) function." )

        if view.file_name() is not None:

            if view.match_selector( 0, amxxPawnSyntax ):

                print_debug( 1, "    ( AMXXEditor::is_amxmodx_file ) Returning True." )
                return True

        print_debug( 1, "    ( AMXXEditor::is_amxmodx_file ) Returning False." )
        return False

    def on_query_completions( self, view, prefix, locations ):

        print_debug( 1, "Entering on the AMXXEditor::on_query_completions(4) function." )
        print_debug( 1, "( AMXXEditor::on_query_completions ) view.file_name(): %s " % view.file_name() )

        if not self.is_amxmodx_file( view ):

            return None

        if view.match_selector( locations[0], amxxPawnSyntax + ' string' ):

            return ( [], sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS )

        return ( self.generate_funcset( view.file_name() ), sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS )


    def generate_funcset( self, file_name ):

        print_debug( 1, "Entering on the AMXXEditor::generate_funcset(2) function." )

        funcset = set()
        visited = set()

        node = nodes[file_name]

        self.generate_funcset_recur( node, funcset, visited )
        return sorted_nicely( funcset )


    def generate_funcset_recur( self, node, funcset, visited ):

        print_debug( 1, "Entering on the AMXXEditor::generate_funcset_recur(2) function." )

        if node in visited:
            return

        visited.add( node )

        for child in node.children:

            self.generate_funcset_recur( child, funcset, visited )

        funcset.update( node.funcs )


    def generate_doctset_recur( self, node, doctset, visited ):

        print_debug( 1, "Entering on the AMXXEditor::generate_doctset_recur(2) function." )

        if node in visited:

            return

        visited.add( node )

        for child in node.children:

            self.generate_doctset_recur( child, doctset, visited )

        doctset.update( node.doct )



def on_settings_modified():

    print_debug( 1, "Entering on the on_settings_modified(0) function." )

    global g_delay_time
    settings = sublime.load_settings( "amxx.sublime-settings" )

    # check package path
    packages_path = sublime.packages_path() + "/amxmodx"

    if not os.path.isdir( packages_path ):

        os.mkdir( packages_path )

    # cache setting
    get_the_include_directory()
    g_delay_time = settings.get( 'live_refresh_delay', 1.0 )

    file_observer.unschedule_all()
    file_observer.schedule( file_event_handler, g_include_dir, True )



def get_the_include_directory():

    print_debug( 1, "Entering on the get_the_include_directory(0) function." )

    global g_include_dir
    g_include_dir = 'F:/SteamCMD/steamapps/common/Half-Life/czero/addons/amxmodx/scripting/include'

    g_include_dir = os.path.normpath( g_include_dir )
    print_debug( 1, "    ( get_the_include_directory ) g_include_dir: %s" % g_include_dir )



def sorted_nicely( l ):
    """ Sort the given iterable in the way that humans expect."""

    print_debug( 1, "Entering on the sorted_nicely(1) function." )

    convert      = lambda text: int( text ) if text.isdigit() else text
    alphanum_key = lambda key: [ convert( c ) for c in re.split( '( [0-9]+ )', key[0] ) ]

    return sorted( l, key = alphanum_key )



def add_to_queue_forward( view ):

    print_debug( 1, "Entering on the add_to_queue_forward(1) function." )
    sublime.set_timeout( lambda: add_to_queue( view ), 0 )



def add_to_queue( view ):
    """
        The view can only be accessed from the main thread, so run the regex
        now and process the results later
    """

    print_debug( 1, "Entering on the add_to_queue(1) function." )
    print_debug( 1, "( add_to_queue ) view.size(): %d" % view.size() )
    print_debug( 1, "( add_to_queue ) view.file_name(): %s" % view.file_name() )

    to_process.put( ( view.file_name(), view.substr( sublime.Region( 0, view.size() ) ) ) )



def add_include_to_queue( file_name ):

    print_debug( 1, "Entering on the add_include_to_queue(1) function." )
    to_process.put( ( file_name, None ) )



class IncludeFileEventHandler( watchdog.events.FileSystemEventHandler ):

    def __init__( self ):

        print_debug( 1, "Entering on the IncludeFileEventHandler::__init__(2) function." )
        watchdog.events.FileSystemEventHandler.__init__( self )


    def on_created( self, event ):

        print_debug( 1, "Entering on the IncludeFileEventHandler::on_created(2) function." )
        sublime.set_timeout( lambda: on_modified_main_thread( event.src_path ), 0 )


    def on_modified( self, event ):

        print_debug( 1, "Entering on the IncludeFileEventHandler::on_modified(2) function." )
        sublime.set_timeout( lambda: on_modified_main_thread( event.src_path ), 0 )


    def on_deleted( self, event ):

        print_debug( 1, "Entering on the IncludeFileEventHandler::on_deleted(2) function." )
        sublime.set_timeout( lambda: on_deleted_main_thread( event.src_path ), 0 )



def on_modified_main_thread( file_path ):

    print_debug( 1, "Entering on the on_modified_main_thread(1) function." )

    if not is_active( file_path ):

        add_include_to_queue( file_path )



def on_deleted_main_thread( file_path ):

    print_debug( 1, "Entering on the on_deleted_main_thread(1) function." )

    if is_active( file_path ):

        return

    node = nodes.get( file_path )

    if node is None:

        return

    node.remove_all_children_and_funcs()



def is_active( file_name ):

    print_debug( 1, "Entering on the is_active(1) function." )
    return sublime.active_window().active_view().file_name() == file_name



class ProcessQueueThread( watchdog.utils.DaemonThread ):

    def run( self ):

        print_debug( 1, "Entering on the ProcessQueueThread::run(1) function." )

        while self.should_keep_running():

            ( file_name, view_buffer ) = to_process.get()

            if view_buffer is None:

                self.process_existing_include( file_name )

            else:

                self.process( file_name, view_buffer )

    def process( self, view_file_name, view_buffer ):

        print_debug( 1, "Entering on the ProcessQueueThread::process(3) function." )
        print_debug( 1, "( ProcessQueueThread::process ) %s" % view_file_name )

        ( current_node, node_added ) = get_or_add_node( view_file_name )

        base_includes = set()
        includes      = includes_re.findall( view_buffer )

        for include in includes:

            self.load_from_file( view_file_name, include, current_node, current_node, base_includes )

        for removed_node in current_node.children.difference( base_includes ):

            current_node.remove_child( removed_node )

        process_buffer( view_buffer, current_node )


    def process_existing_include( self, file_name ):

        print_debug( 1, "Entering on the ProcessQueueThread::process_existing_include(2) function." )
        current_node = nodes.get( file_name )

        if current_node is None:

            return

        base_includes = set()

        with open( file_name, 'r' ) as f:

            print_debug( 0, "( ProcessQueueThread::process_existing_include ) Processing Include File %s" % file_name )
            includes = include_re.findall( f.read() )

        for include in includes:

            self.load_from_file( view_file_name, include, current_node, current_node, base_includes )

        for removed_node in current_node.children.difference( base_includes ):

            current_node.remove_child( removed_node )

        process_include_file( current_node )


    def load_from_file( self, view_file_name, base_file_name, parent_node, base_node, base_includes ):

        print_debug( 1, "Entering on the ProcessQueueThread::load_from_file(6) function." )
        ( file_name, exists ) = get_file_name( view_file_name, base_file_name )

        if not exists:

            print_debug( 0, "( ProcessQueueThread::load_from_file ) Include File Not Found: %s" % base_file_name )

        ( node, node_added ) = get_or_add_node( file_name )

        parent_node.add_child( node )

        if parent_node == base_node:

            base_includes.add( node )

        if not node_added or not exists:

            return

        with open( file_name, 'r' ) as f:

            print_debug( 0, "( ProcessQueueThread::load_from_file ) Processing Include File %s" % file_name )
            includes = includes_re.findall( f.read() )

        for include in includes:

            self.load_from_file( view_file_name, include, node, base_node, base_includes )

        process_include_file( node )



def get_file_name( view_file_name, base_file_name ):

    print_debug( 1, "Entering on the get_file_name(2) function." )

    if local_re.search( base_file_name ) == None:

        file_name = os.path.join( g_include_dir, base_file_name + '.inc' )

    else:

        file_name = os.path.join( os.path.dirname( view_file_name ), base_file_name )

    return ( file_name, os.path.exists( file_name ) )



def get_or_add_node( file_name ):

    print_debug( 1, "Entering on the get_or_add_node(1) function." )
    node = nodes.get( file_name )

    if node is None:

        node = Node( file_name )
        nodes[file_name] = node
        return ( node, True )

    return ( node, False )



# ============= NEW CODE ------------------------------------------------------------------------------------------------------------
class Node:

    def __init__( self, file_name ):

        print_debug( 1, "Entering on the Node::__init__(2) function." )

        self.file_name = file_name
        self.children = set()
        self.parents = set()
        self.funcs = set()
        self.doct = set()

    def add_child( self, node ):

        print_debug( 1, "Entering on the Node::add_child(2) function." )

        self.children.add( node )
        node.parents.add( self )

    def remove_child( self, node ):

        print_debug( 1, "Entering on the Node::remove_child(2) function." )

        self.children.remove( node )
        node.parents.remove( self )

        if len( node.parents ) <= 0:

            nodes.pop( node.file_name )

    def remove_all_children_and_funcs( self ):

        print_debug( 1, "Entering on the Node::remove_all_children_and_funcs(1) function." )

        for child in self.children:

            self.remove_child( node )

        self.funcs.clear()
        self.doct.clear()


class TextReader:

    def __init__( self, text ):

        print_debug( 1, "Entering on the TextReader::__init__(2) function." )

        self.text = text.splitlines()
        self.position = -1

    def readline( self ):

        print_debug( 1, "Entering on the TextReader::readline(1) function." )
        self.position += 1

        if self.position < len( self.text ):

            retval = self.text[self.position]

            if retval == '':

                return '\n'

            else:

                return retval

        else:

            return ''



class PawnParse:

    def __init__( self ):

        print_debug( 1, "Entering on the PawnParse::__init__(1) function." )

        self.save_const_timer = None
        self.constants_count = 0

    def start( self, pFile, node ):

        print_debug( 1, "" )
        print_debug( 1, "" )
        print_debug( 1, "" )
        print_debug( 1, "Entering on the PawnParse::start(3) function." )
        print_debug( 2, "( PawnParse::start ) CODE PARSE Start [%s]" % node.file_name )

        self.file               = pFile
        self.file_name          = os.path.basename( node.file_name )
        self.node               = node
        self.found_comment      = False
        self.found_enum         = False
        self.skip_brace_found   = False
        self.skip_next_dataline = False
        self.enum_contents      = ''
        self.brace_level        = 0
        self.restore_buffer     = None

        self.node.funcs.clear()
        self.node.doct.clear()

        self.start_parse()

        if self.constants_count != len( g_constants_list ):

            if self.save_const_timer:

                self.save_const_timer.cancel()

            self.save_const_timer = Timer( 4.0, self.save_constants )
            self.save_const_timer.start()

        print_debug( 2, "    ( PawnParse::start ) Returning [%s]" % node.file_name )
        print_debug( 1, "" )
        print_debug( 1, "" )
        print_debug( 1, "" )


    def save_constants( self ):

        print_debug( 1, "Entering on the PawnParse::save_constants(1) function." )

        self.save_const_timer   = None
        self.constants_count    = len( g_constants_list )

        constants = "___test"

        for const in g_constants_list:

            constants += "|" + const

        syntax = "%YAML 1.2\n---\nscope: " + amxxPawnSyntax + " \ncontexts:\n  main:\n    - match: \\b( " + \
                constants + " )\\b\n      scope: constant.vars.AmxxPawn"

        file_name = sublime.packages_path() + "/amxmodx/const.sublime-syntax"
        f         = open( file_name, 'w' )

        f.write( syntax )
        f.close()

        print_debug( 2, "( PawnParse::save_constants ) call save_constants()" )


    def read_line( self ):

        print_debug( 1, "Entering on the PawnParse::read_line(1) function." )

        if self.restore_buffer:

            line = self.restore_buffer
            self.restore_buffer = None

        else:

            line = self.file.readline()

        if len( line ) > 0:

            return line

        else:

            return None



    def read_string( self, buffer ):

        print_debug( 1, "Entering on the PawnParse::read_string(2) function." )
        buffer = buffer.replace( '\t', ' ' ).strip()

        while '  ' in buffer:

            buffer = buffer.replace( '  ', ' ' )

        buffer = buffer.lstrip()

        result = ''
        i = 0

        while i < len( buffer ):

            if buffer[i] == '/' and i + 1 < len( buffer ):

                if buffer[i + 1] == '/':

                    self.brace_level +=  result.count( '{' ) - result.count( '}' )
                    return result

                elif buffer[i + 1] == '*':

                    self.found_comment = True
                    i += 1

                elif not self.found_comment:

                    result += '/'

            elif self.found_comment:

                if buffer[i] == '*' and i + 1 < len( buffer ) and buffer[i + 1] == '/':

                    self.found_comment = False
                    i += 1

            elif not ( i > 0 and buffer[i] == ' ' and buffer[i - 1] == ' ' ):

                result += buffer[i]

            i += 1

        self.brace_level +=  result.count( '{' ) - result.count( '}' )
        return result


    def skip_function_block( self, buffer ):

        print_debug( 1, "Entering on the PawnParse::skip_function_block(2) function." )

        num_brace = 0
        inString = False
        self.skip_brace_found = False

        buffer = buffer + ' '

        while buffer is not None and buffer.isspace():

            buffer = self.read_line()

        while buffer is not None:

            i = 0
            pos = 0
            oldChar = ''

            for c in buffer:

                i += 1

                if ( c == '"' ):

                    if inString and oldChar != '^':
                        inString = False
                    else:
                        inString = True


                if ( inString == False ):

                    if ( c == '{' ):
                        num_brace += 1
                        self.skip_brace_found = True
                    elif ( c == '}' ):
                        num_brace -= 1
                        pos = i


                oldChar = c

            if num_brace == 0:

                self.restore_buffer = buffer[pos:]
                return

            buffer = self.read_line()


    def valid_name( self, name ):

        print_debug( 1, "Entering on the PawnParse::valid_name(2) function." )

        if not name or not name[0].isalpha() and name[0] != '_':

            return False

        return re.match( '^[\w_]+$', name ) is not None


    def add_constant( self, name ):

        print_debug( 1, "Entering on the PawnParse::add_constant(2) function." )
        fixname = re.search( '( \\w* )', name )

        if fixname:

            name = fixname.group( 1 )
            g_constants_list.add( name )


    def add_enum( self, buffer ):

        print_debug( 1, "Entering on the PawnParse::add_enum(2) function." )
        buffer = buffer.strip()

        if buffer == '':

            return

        split = buffer.split( '[' )

        self.add_autocomplete( buffer, 'enum', split[0] )
        self.add_constant( split[0] )

        print_debug( 2, "( PawnParse::add_enum ) parse_enum add: [%s] -> [%s]" % ( buffer, split[0] ) )


    def add_autocomplete( self, name, info, autocomplete ):

        print_debug( 1, "Entering on the PawnParse::add_autocomplete(2) function." )
        self.node.funcs.add( ( name +'  \t'+  self.file_name +' - '+ info, autocomplete ) )


    def start_parse( self ):

        print_debug( 1, "Entering on the PawnParse::start_parse(1) function." )

        while True:

            buffer = self.read_line()

            if buffer is None:

                break

            buffer = self.read_string( buffer )

            if len( buffer ) <= 0:

                continue

            #if "sma" in self.node.file_name:
            #   print( "read: skip:[%d] brace_level:[%d] buff:[%s]" % ( self.skip_next_dataline, self.brace_level, buffer ) )
            if self.skip_next_dataline:

                self.skip_next_dataline = False
                continue

            # To start the file parsing
            if buffer.startswith( '#include ' ):

                buffer = self.parse_include( buffer )

            elif buffer.startswith( '#pragma deprecated' ):

                buffer = self.read_line()

                if buffer is not None and buffer.startswith( 'stock ' ):

                    self.skip_function_block( buffer )

            elif buffer.startswith( '#define ' ):

                buffer = self.parse_define( buffer )

            elif buffer.startswith( 'const ' ):

                buffer = self.parse_const( buffer )

            elif buffer.startswith( 'enum ' ):

                self.found_enum    = True
                self.enum_contents = ''

            elif buffer.startswith( 'new ' ):

                self.parse_variable( buffer )

            elif buffer.startswith( 'public ' ):

                self.parse_function( buffer, 1 )

            elif buffer.startswith( 'stock ' ):

                self.parse_function( buffer, 2 )

            elif buffer.startswith( 'forward ' ):

                self.parse_function( buffer, 3 )

            elif buffer.startswith( 'native ' ):

                self.parse_function( buffer, 4 )

            elif not self.found_enum and not buffer[0] == '#':

                self.parse_function( buffer, 0 )

            if self.found_enum:

                self.parse_enum( buffer )


    def parse_include( self, buffer ):

        print_debug( 1, "Entering on the PawnParse::parse_include(2) function." )
        include_line = re.search( '#include[\\s]+[<"](.*)[">]', buffer )

        if include_line:

            buffer            = ''
            include_file_name = include_line.group( 1 )

            print_debug( 2, "( PawnParse::parse_include ) parse_include add: [%s]" % include_file_name )


    def parse_define( self, buffer ):

        print_debug( 1, "Entering on the PawnParse::parse_define(2) function." )
        define = re.search( '#define[\\s]+( [^\\s]+ )[\\s]+( .+ )', buffer )

        if define:

            buffer = ''
            name   = define.group( 1 )
            value  = define.group( 2 ).strip()

            self.add_autocomplete( name, 'define: '+value, name )
            self.add_constant( name )

            print_debug( 2, "( PawnParse::parse_define ) parse_define add: [%s]" % name )


    def parse_const( self, buffer ):

        print_debug( 1, "Entering on the PawnParse::parse_const(2) function." )

        buffer = buffer[6:]
        split  = buffer.split( '=', 1 )

        if len( split ) < 2:

            return

        name  = split[0].strip()
        value = split[1].strip()

        newline = value.find( ';' )

        if ( newline != -1 ):

            self.restore_buffer = value[newline+1:].strip()
            value = value[0:newline]


        self.add_autocomplete( name, 'const: '+value, name )
        self.add_constant( name )
        print_debug( 2, "( PawnParse::parse_const ) parse_const add: [%s]" % name )


    def parse_variable( self, buffer ):

        print_debug( 1, "Entering on the PawnParse::parse_variable(2) function." )

        if buffer.startswith( 'new const ' ):

            buffer = buffer[10:]

        else:

            buffer = buffer[4:]

        varName = ""
        oldChar = ''

        i   = 0
        pos = 0

        num_brace  = 0
        multiLines = True
        skipSpaces = False
        parseName  = True
        inBrackets = False
        inBraces   = False
        inString   = False

        while multiLines:

            multiLines = False

            for c in buffer:

                i += 1

                if ( c == '"' ):

                    if ( inString and oldChar != '^' ):

                        inString = False

                    else:

                        inString = True


                if ( inString == False ):

                    if ( c == '{' ):

                        num_brace += 1
                        inBraces  = True

                    elif ( c == '}' ):

                        num_brace -= 1

                        if ( num_brace == 0 ):

                            inBraces = False


                if skipSpaces:

                    if c.isspace():

                        continue

                    else:

                        skipSpaces = False
                        parseName = True


                if parseName:

                    if ( c == ':' ):

                        varName = ''

                    elif ( c == ' ' or c == '=' or c == ';' or c == ',' ):

                        varName = varName.strip()

                        if ( varName != '' ):

                            self.add_autocomplete( varName, 'var', varName )
                            print_debug( 2, "( PawnParse::parse_variable ) add: [%s]" % varName )

                        varName    = ''
                        parseName  = False
                        inBrackets = False

                    elif ( c == '[' ):

                        inBrackets = True

                    elif ( inBrackets == False ):

                        varName += c

                if ( inString == False and inBrackets == False and inBraces == False ):

                    if not parseName and c == ';':

                        self.restore_buffer = buffer[i:].strip()
                        return

                    if ( c == ',' ):

                        skipSpaces = True

                oldChar = c

            if ( c != ',' ):

                varName = varName.strip()

                if varName != '':

                    self.add_autocomplete( varName, 'var', varName )
                    print_debug( 2, "( PawnParse::parse_variable ) add: [%s]" % varName )

            else:

                multiLines = True
                buffer = ' '

                while buffer is not None and buffer.isspace():

                    buffer = self.read_line()



    def parse_enum( self, buffer ):

        print_debug( 1, "Entering on the PawnParse::parse_enum(2) function." )
        pos = buffer.find( '}' )

        if pos != -1:

            buffer          = buffer[0:pos]
            self.found_enum = False

        self.enum_contents = '%s\n%s' % ( self.enum_contents, buffer )
        buffer             = ''

        ignore = False

        if not self.found_enum:

            pos                = self.enum_contents.find( '{' )
            self.enum_contents = self.enum_contents[pos + 1:]

            for c in self.enum_contents:

                if c == '=' or c == '#':

                    ignore = True

                elif c == '\n':

                    ignore = False

                elif c == ':':

                    buffer = ''
                    continue

                elif c == ',':

                    self.add_enum( buffer )
                    buffer = ''

                    ignore = False
                    continue

                if not ignore:

                    buffer += c

            self.add_enum( buffer )
            buffer = ''



    def parse_function( self, buffer, type ):

        print_debug( 1, "Entering on the PawnParse::parse_function(3) function." )

        multi_line       = False
        temp             = ''
        full_func_str    = None
        open_paren_found = False

        while buffer is not None:


            buffer = buffer.strip()

            if not open_paren_found:

                parenpos = buffer.find( '( ' )

                if parenpos == -1:

                    return

                open_paren_found = True

            if open_paren_found:

                pos = buffer.find( ' )' )

                if pos != -1:

                    full_func_str = buffer[0:pos + 1]
                    buffer        = buffer[pos+1:]

                    if ( multi_line ):

                        full_func_str = '%s%s' % ( temp, full_func_str )

                    break

                multi_line = True
                temp       = '%s%s' % ( temp, buffer )

            buffer = self.read_line()

            if buffer is None:

                return

            buffer = self.read_string( buffer )

        if full_func_str is not None:

            error = self.parse_function_params( full_func_str, type )

            if not error and type <= 2:

                self.skip_function_block( buffer )

                if not self.skip_brace_found:

                    self.skip_next_dataline = True

            #print( "skip_brace: error:[%d] type:[%d] found:[%d] skip:[%d] func:[%s]" % ( error, type, self.skip_brace_found, self.skip_next_dataline, full_func_str ) )



    def parse_function_params( self, func, type ):

        print_debug( 1, "Entering on the PawnParse::parse_function_params(3) function." )

        if type == 0:

            remaining = func

        else:

            split = func.split( ' ', 1 )
            remaining = split[1]

        split = remaining.split( '( ', 1 )

        if len( split ) < 2:

            print_debug( 1, "( PawnParse::parse_function_params ) parse_params return1: [%s]" % split )
            return 1

        remaining  = split[1]
        returntype = ''

        funcname_and_return       = split[0].strip()
        split_funcname_and_return = funcname_and_return.split( ':' )

        if len( split_funcname_and_return ) > 1:

            funcname   = split_funcname_and_return[1].strip()
            returntype = split_funcname_and_return[0].strip()

        else:

            funcname = split_funcname_and_return[0].strip()

        if funcname.startswith( "operator" ):

            return 0

        if not self.valid_name( funcname ):

            print_debug( 1, "( PawnParse::parse_function_params ) parse_params invalid name: [%s]" % funcname )
            return 1

        remaining = remaining.strip()

        if remaining == ' )':

            params = []

        else:

            params = remaining.strip()[:-1].split( ',' )

        autocomplete = funcname + '( '

        i = 1

        for param in params:

            if i > 1:

                autocomplete += ', '

            autocomplete += '${%d:%s}' % ( i, param.strip() )
            i            += 1

        autocomplete += ' )'

        self.add_autocomplete( funcname, FUNC_TYPES[type].lower(), autocomplete )
        self.node.doct.add( ( funcname, func[func.find( "(" )+1:-1], self.node.file_name, type, returntype ) )

        print_debug( 2, "( PawnParse::parse_function_params ) parse_params add: [%s]" % func )
        return 0



def process_buffer( text, node ):

    print_debug( 1, "Entering on the process_buffer(2) function." )

    text_reader = TextReader( text )
    pawnparse.start( text_reader, node )



def process_include_file( node ):

    print_debug( 1, "Entering on the process_include_file(1) function." )

    with open( node.file_name ) as file:

        pawnparse.start( file, node )



def simple_escape( html ):

    print_debug( 1, "Entering on the simple_escape(1) function." )
    return html.replace( '&', '&amp;' )



def print_debug( level, msg ):

    global print_debug_lastTime
    currentTime = datetime.datetime.now().microsecond

    # You can access global variables without the global keyword.
    if g_debug_level >= level:

        print( "[AMXX-Editor] " \
                + str( datetime.datetime.now().hour ) + ":" \
                + str( datetime.datetime.now().minute ) + ":" \
                + str( datetime.datetime.now().second ) + ":" \
                + str( currentTime ) \
                + "%7s " % str( currentTime - print_debug_lastTime ) \
                + msg )

        print_debug_lastTime = currentTime


# When the Python interpreter reads a source file, it executes all of the code found in it.
#
# Before executing the code, it will define a few special variables.  For example, if the python
#
# interpreter is running that module (the source file) as the main program, it sets the special
# `__name__` variable to have a value `"__main__"`.  If this file is being imported from another
# module, `__name__` will be set to the module's name.
#
# if __name__ == "__main__":
#
#     main();
main()







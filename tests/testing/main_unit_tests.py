#! /usr/bin/env python
# -*- coding: utf-8 -*-

####################### Licensing #######################################################
#
#   Copyright 2018 @ Evandro Coan
#   Project Unit Tests
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
#
#########################################################################################
#

import re
import os

import sys
import unittest
import inspect
import traceback


is_python2 = False

if sys.version_info[0] < 3:
    is_python2 = True

try:
    import sublime_plugin

    import debug_tools.logger
    from DebugTools.all.debug_tools.utilities import wrap_text

    # Import and reload the debugger
    sublime_plugin.reload_plugin( "debug_tools.logger" )
    sublime_plugin.reload_plugin( "debug_tools.utilities" )

except ImportError:
    import os
    import sys

    def assert_path(module):

        if module not in sys.path:
            sys.path.append( module )

    # Import the debug tools
    assert_path( os.path.join( os.path.dirname( os.path.dirname( os.path.dirname( os.path.realpath( __file__ ) ) ) ), 'all' ) )

    import debug_tools.logger
    from debug_tools.utilities import wrap_text

# Relative imports in Python 3
# https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
try:
    from .std_err_capture import TeeNoFile

except (ImportError, ValueError, SystemError):
    from std_err_capture import TeeNoFile

# We need to keep a global reference to this because the logging module internally grabs an
# reference to the first `sys.strerr` it can get its hands on it.
#
# We could make the logger recreate the `stderr` output StreamHandler by passing `force=True` to
# to `Debugger.setup()`, removing the old reference to `sys.stderr`.
_stderr = TeeNoFile()


def getLogger(debug_level=127, logger_name=None, **kwargs):
    global log
    global line
    log = debug_tools.logger.getLogger( debug_level, logger_name, **kwargs )
    _stderr.clear( log )

    frameinfo = inspect.getframeinfo( sys._getframe(1) )
    line = frameinfo.lineno


def log_traceback(ex, ex_traceback=None):
    """
        Best way to log a Python exception
        https://stackoverflow.com/questions/5191830/best-way-to-log-a-python-exception
    """

    if ex_traceback is None:
        ex_traceback = ex.__traceback__

    tb_lines = [ line.rstrip('\n') for line in
                 traceback.format_exception(ex.__class__, ex, ex_traceback)]

    # print( "\n".join( tb_lines ) )
    sys.stderr.write( "\n".join( tb_lines ) )


class MainUnitTests(unittest.TestCase):
    """
        How to assert output with nosetest/unittest in python?
        https://stackoverflow.com/questions/4219717/how-to-assert-output-with-nosetest-unittest-in-python
    """

    def setUp(self):
        self.maxDiff = None
        sys.stderr.write("\n")
        sys.stderr.write("\n")

    def tearDown(self):
        log.clear( True )
        log.reset()

    def contents(self, date_regex):
        return _stderr.contents( date_regex )

    def file_contents(self, date_regex):
        return _stderr.file_contents( date_regex, log )

    def test_function_name(self):
        getLogger( 127, "testing.main_unit_tests", date=True )

        log( 1, "Bitwise" )
        log( 8, "Bitwise" )
        log.warn( "Warn" )
        log.info( "Info" )
        log.debug( "Debug" )
        log.newline()

        def function_name():
            log( 1, "Bitwise" )
            log( 8, "Bitwise" )
            log.warn( "Warn" )
            log.info( "Info" )
            log.debug( "Debug" )

        function_name()
        output = self.contents( r"\d{4}\-\d{2}-\d{2} \d{2}:\d{2}:\d{2}:\d{3}\.\d{6} \d\.\d{2}e.\d{2} \- " )

        offset1 = 1
        offset2 = 4

        self.assertEqual( wrap_text( """\
            testing.main_unit_tests.test_function_name:{} - Bitwise
            testing.main_unit_tests.test_function_name:{} - Bitwise
            testing.main_unit_tests.test_function_name:{} - Warn
            testing.main_unit_tests.test_function_name:{} - Info
            testing.main_unit_tests.test_function_name:{} - Debug

            testing.main_unit_tests.function_name:{} - Bitwise
            testing.main_unit_tests.function_name:{} - Bitwise
            testing.main_unit_tests.function_name:{} - Warn
            testing.main_unit_tests.function_name:{} - Info
            testing.main_unit_tests.function_name:{} - Debug
            """.format(
                    line+offset1+1, line+offset1+2, line+offset1+3, line+offset1+4, line+offset1+5,
                    line+offset2+6, line+offset2+7, line+offset2+8, line+offset2+9, line+offset2+10,
            ) ), output )

    def test_no_function_name_and_level(self):
        getLogger( 127, "testing.main_unit_tests", date=True, function=False, level=True )

        log( 1, "Bitwise" )
        log( 8, "Bitwise" )
        log.warn( "Warn" )
        log.info( "Info" )
        log.debug( "Debug" )

        output = self.contents( r"\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2}:\d{3}\.\d{6} \d\.\d{2}e.\d{2} \- " )
        self.assertEqual( wrap_text( """\
            testing.main_unit_tests DEBUG(1) - Bitwise
            testing.main_unit_tests DEBUG(8) - Bitwise
            testing.main_unit_tests WARNING - Warn
            testing.main_unit_tests INFO - Info
            testing.main_unit_tests DEBUG - Debug
            """ ),
            output )

    def test_date_disabled(self):
        getLogger( "testing.main_unit_tests", 127, function=False )

        log( 1, "Bitwise" )
        log( 8, "Bitwise" )
        log.warn( "Warn" )
        log.info( "Info" )
        log.debug( "Debug" )

        output = self.contents( r"\d{2}:\d{2}:\d{2}:\d{3}\.\d{6} \d\.\d{2}e.\d{2} \- " )
        self.assertEqual( wrap_text( """\
            testing.main_unit_tests - Bitwise
            testing.main_unit_tests - Bitwise
            testing.main_unit_tests - Warn
            testing.main_unit_tests - Info
            testing.main_unit_tests - Debug
            """ ),
            output )

    def test_get_logger_empty(self):
        getLogger( function=False )

        log( 1, "Bitwise" )
        log( 8, "Bitwise" )
        log.warn( "Warn" )
        log.info( "Info" )
        log.debug( "Debug" )

        output = self.contents( r"\d{2}:\d{2}:\d{2}:\d{3}\.\d{6} \d\.\d{2}e.\d{2} \- " )
        self.assertEqual( wrap_text( """\
            logger - Bitwise
            logger - Bitwise
            logger - Warn
            logger - Info
            logger - Debug
            """ ),
            output )

    def test_get_logger_more_empty(self):
        getLogger( function=False, name=False )

        log( 1, "Bitwise" )
        log( 8, "Bitwise" )
        log.warn( "Warn" )
        log.info( "Info" )
        log.debug( "Debug" )

        output = self.contents( r"\d{2}:\d{2}:\d{2}:\d{3}\.\d{6} \d\.\d{2}e.\d{2} \- " )
        self.assertEqual( wrap_text( """\
            Bitwise
            Bitwise
            Warn
            Info
            Debug
            """ ),
            output )

    def test_basic_formatter(self):
        getLogger( 127, "testing.main_unit_tests" )
        log.setup_basic( function=True, separator=" " )

        log.basic( 1, "Debug" )

        output = self.contents( r"\d{2}:\d{2}:\d{2}:\d{3}\.\d{6} \d\.\d{2}e.\d{2} \- " )
        self.assertEqual( "testing.main_unit_tests.test_basic_formatter:{} Debug".format( line + 3 ), output )

    def test_exception_throwing(self):
        getLogger( "testing.main_unit_tests", 127 )

        try:
            raise Exception( "Test Error" )
        except Exception:
            log.exception( "I am catching you" )

        regex_pattern = re.compile( r"File \".*\", line \d+," )
        output = self.contents( r"\d{2}:\d{2}:\d{2}:\d{3}\.\d{6} \d\.\d{2}e.\d{2} \- " )

        self.assertEqual( wrap_text( """\
                testing.main_unit_tests.test_exception_throwing:{} - I am catching you
                Traceback (most recent call last):
                   in test_exception_throwing
                    raise Exception( "Test Error" )
                Exception: Test Error            """.format( line + 5 ) ),
            regex_pattern.sub( "", output ) )

    def test_exception_throwing_from_relative_file_path(self):
        getLogger( "testing.main_unit_tests", 127, file="debug_tools_log_test_exception_throwing_from_relative_file_path.txt" )
        throw_file_exception( self )

    def test_exception_throwing_from_absolute_file_path(self):
        getLogger( "testing.main_unit_tests", 127, file=os.path.abspath("debug_tools_log_test_exception_throwing_from_absolute_file_path.txt") )
        throw_file_exception( self )


def throw_file_exception(self):
    line = inspect.getframeinfo( sys._getframe(0) ).lineno

    try:
        log( 1, "I am catching you..." )
        raise Exception( "Test Exception" )

    except Exception as error:

        if is_python2:
            _, _, exception_traceback = sys.exc_info()
            log_traceback( error, exception_traceback )

        else:
            log_traceback( error )

    regex_pattern = re.compile( r"File \".*\"," )
    output = self.file_contents( r"\d{2}:\d{2}:\d{2}:\d{3}\.\d{6} \d\.\d{2}e.\d{2} \- " )

    self.assertEqual( wrap_text( """\
            testing.main_unit_tests.throw_file_exception:{} - I am catching you...
            Traceback (most recent call last):
               line {}, in throw_file_exception
                raise Exception( "Test Exception" )
            Exception: Test Exception            """.format( line + 3, line + 4  ) ),
        regex_pattern.sub( "", output ) )


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


import os
import sys
import unittest

import io
import pstats
import sublime_plugin

from AmxxEditor.AmxxEditor import PawnParse
from AmxxEditor.AmxxEditor import Node
from AmxxEditor.AmxxEditor import _on_settings_modified

# Import and reload the debugger
sublime_plugin.reload_plugin( "AmxxEditor.AmxxEditor" )
_on_settings_modified()

from debug_tools.utilities import get_relative_path
from debug_tools import getLogger

run_benckmark = False
# run_benckmark = True
log = getLogger( __name__.split('.')[-1], 127 )


class MainUnitTests(unittest.TestCase):
    """
        How to assert output with nosetest/unittest in python?
        https://stackoverflow.com/questions/4219717/how-to-assert-output-with-nosetest-unittest-in-python
    """

    def setUp(self):
        log.newline()
        self.maxDiff = None

    def tearDown(self):
        pass

    @unittest.skipIf( not run_benckmark, "Only run it when benchmarking")
    def test_big_file_parse_time(self):
        file_name = get_relative_path( 'galileo.sma', __file__ )
        log( 1, "file_name: %s", file_name )

        def load_tests(loader, standard_tests, pattern):
            suite = unittest.TestSuite()
            return suite

        def run_parse():
            node = Node(file_name)
            pawnParse = PawnParse()

            with open( node.file_name ) as file:
                pawnParse.start(file, node)

        # cProfile can't be imported on Linux - https://github.com/sublimehq/sublime_text/issues/127
        import cProfile
        profiller = cProfile.Profile()
        profiller.enable()

        for index in range(10):
            run_parse()

        profiller.disable()
        outputstream = io.StringIO()

        profiller_status = pstats.Stats( profiller, stream=outputstream )
        profiller_status.sort_stats( "time" )
        profiller_status.print_stats()
        sys.stderr.write( outputstream.getvalue()[:2000] + '\n' )



# https://stackoverflow.com/questions/15971735/running-single-test-from-unittest-testcase-via-command-line/
def load_tests(loader, standard_tests, pattern):
    suite = unittest.TestSuite()
    suite.addTest( MainUnitTests( 'test_big_file_parse_time' ) )
    return suite

# Skip Custom load_tests()
load_tests = None

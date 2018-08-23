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
import re

import sys
import pprint
import textwrap
import unittest

import sublime_plugin

from AmxxEditor.AmxxEditor import PawnParse
from AmxxEditor.AmxxEditor import Node

# Import and reload the debugger
sublime_plugin.reload_plugin( "AmxxEditor.AmxxEditor" )

from debug_tools import getLogger
log = getLogger( __name__.split('.')[-1], 127 )


def get_relative_path(relative_path, script_file):
    """
        Computes a relative path for a file on the same folder as this class file declaration.
        https://stackoverflow.com/questions/4381569/python-os-module-open-file-above-current-directory-with-relative-path
    """
    basepath = os.path.dirname( script_file )
    filepath = os.path.abspath( os.path.join( basepath, relative_path ) )
    return filepath


class MainUnitTests(unittest.TestCase):
    """
        How to assert output with nosetest/unittest in python?
        https://stackoverflow.com/questions/4219717/how-to-assert-output-with-nosetest-unittest-in-python
    """

    def setUp(self):
        self.maxDiff = None

    def tearDown(self):
        pass

    def test_stock_function_defintion(self):
        file_name = get_relative_path( 'stock_functions_include.inc', __file__ )
        # log( 1, "file_name: %s", file_name )

        node = Node(file_name)
        pawnParse = PawnParse()

        with open( node.file_name ) as file:
            pawnParse.start(file, node)

        func_list = '"%s"' % str( node.funcs_list )
        words_list = '"%s"' % str( node.words_list )

        self.assertEqual( repr("['te_create_screen_aligned_beam_ring', 'is_str_num']"), words_list )
        self.assertEqual( repr("[['te_create_screen_aligned_beam_ring(15) \tstock_functions_include.inc - stock', 'te_create_screen_aligned_beam_ring(${1:id}, ${2:origin[3]}, ${3:axis[3]}, ${4:spriteid}, ${5:startframe = 1}, ${6:framerate = 10}, ${7:life = 10}, ${8:width = 10}, ${9:noise = 0}, ${10:r = 0}, ${11:g = 0}, ${12:b = 255}, ${13:a = 75}, ${14:speed = 30}, ${15:bool:reliable = true})'], ['is_str_num(1) \tstock_functions_include.inc - stock', 'is_str_num(${1:const sString[]})']]" ), func_list )

    def test_all_man_style_enum(self):
        file_name = get_relative_path( 'allman_style_enum.sma', __file__ )
        # log( 1, "file_name: %s", file_name )

        node = Node(file_name)
        pawnParse = PawnParse()

        with open( node.file_name ) as file:
            pawnParse.start(file, node)

        func_list = '"%s"' % str( node.funcs_list )
        words_list = '"%s"' % str( node.words_list )

        self.assertEqual( repr("['vvv_start_int', 'vvv_cdAudioTrack', 'vvv_end_pchar', 'ggg_start_int', 'ggg_cdAudioTrack', 'ggg_end_pchar']"), words_list )
        self.assertEqual( repr("[['vvv_start_int \tallman_style_enum.sma - enum', 'vvv_start_int'], ['vvv_cdAudioTrack \tallman_style_enum.sma - enum', 'vvv_cdAudioTrack'], ['vvv_end_pchar \tallman_style_enum.sma - enum', 'vvv_end_pchar'], ['ggg_start_int \tallman_style_enum.sma - enum', 'ggg_start_int'], ['ggg_cdAudioTrack \tallman_style_enum.sma - enum', 'ggg_cdAudioTrack'], ['ggg_end_pchar \tallman_style_enum.sma - enum', 'ggg_end_pchar']]" ), func_list )


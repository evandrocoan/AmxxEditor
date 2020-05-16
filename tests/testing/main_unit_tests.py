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
from AmxxEditor.AmxxEditor import TextReader

# Import and reload the debugger
sublime_plugin.reload_plugin( "AmxxEditor.AmxxEditor" )
sublime_plugin.reload_plugin( "AmxxEditor.tests.testing.main_unit_tests" )

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
            pawnParse.start(TextReader(file.read()), node)

        func_list = '"%s"' % str( node.funcs_list )
        words_list = '"%s"' % str( node.words_list )

        self.assertEqual( repr("['te_create_screen_aligned_beam_ring', 'is_str_num']"), words_list )
        self.assertEqual( repr("[['te_create_screen_aligned_beam_ring(15) \tstock_functions_include.inc - stock', 'te_create_screen_aligned_beam_ring(${1:id}, ${2:origin[3]}, ${3:axis[3]}, ${4:spriteid}, ${5:startframe = 1}, ${6:framerate = 10}, ${7:life = 10}, ${8:width = 10}, ${9:noise = 0}, ${10:r = 0}, ${11:g = 0}, ${12:b = 255}, ${13:a = 75}, ${14:speed = 30}, ${15:bool:reliable = true})'], ['is_str_num(1) \tstock_functions_include.inc - stock', 'is_str_num(${1:const sString[]})']]" ), func_list )

    def test_stock_completion(self):
        file_name = get_relative_path( 'stock_functions_completion.inc', __file__ )
        # log( 1, "file_name: %s", file_name )

        node = Node(file_name)
        pawnParse = PawnParse()

        with open( node.file_name ) as file:
            pawnParse.start(TextReader(file.read()), node)

        func_list = '"%s"' % str( node.funcs_list )
        words_list = '"%s"' % str( node.words_list )

        self.assertEqual( repr("[['xs_vec_equal(2) \tstock_functions_completion.inc - stock', 'xs_vec_equal(${1:const Float:vec1[]}, ${2:const Float:vec2[]})'], ['xs_vec_add(3) \tstock_functions_completion.inc - stock', 'xs_vec_add(${1:const Float:in1[]}, ${2:const Float:in2[]}, ${3:Float:out[]})']]"), func_list )
        self.assertEqual( repr("['xs_vec_equal', 'xs_vec_add']"), words_list )

    def test_all_man_style_enum(self):
        file_name = get_relative_path( 'allman_style_enum.sma', __file__ )
        # log( 1, "file_name: %s", file_name )

        node = Node(file_name)
        pawnParse = PawnParse()

        with open( node.file_name ) as file:
            pawnParse.start(TextReader(file.read()), node)

        func_list = '"%s"' % str( node.funcs_list )
        words_list = '"%s"' % str( node.words_list )

        self.assertEqual( repr("['vvv_start_int', 'vvv_cdAudioTrack', 'vvv_end_pchar', 'ggg_start_int', 'ggg_cdAudioTrack', 'ggg_end_pchar']"), words_list )
        self.assertEqual( repr("[['vvv_start_int \tallman_style_enum.sma - enum', 'vvv_start_int'], ['vvv_cdAudioTrack \tallman_style_enum.sma - enum', 'vvv_cdAudioTrack'], ['vvv_end_pchar \tallman_style_enum.sma - enum', 'vvv_end_pchar'], ['ggg_start_int \tallman_style_enum.sma - enum', 'ggg_start_int'], ['ggg_cdAudioTrack \tallman_style_enum.sma - enum', 'ggg_cdAudioTrack'], ['ggg_end_pchar \tallman_style_enum.sma - enum', 'ggg_end_pchar']]" ), func_list )

    def test_native_function_return_array(self):
        file_name = get_relative_path( 'native_functions_completion.inc', __file__ )
        # log( 1, "file_name: %s", file_name )

        node = Node(file_name)
        pawnParse = PawnParse()

        with open( node.file_name ) as file:
            pawnParse.start(TextReader(file.read()), node)

        func_list = '"%s"' % str( node.funcs_list )
        words_list = '"%s"' % str( node.words_list )

        self.assertEqual( repr("[['rg_fire_bullets3(1) \tnative_functions_completion.inc - native', 'rg_fire_bullets3(${1:const inflictor})'], ['fmt(2) \tnative_functions_completion.inc - native', 'fmt(${1:const format[]}, ${2:any:...})']]"), func_list )

        self.assertEqual( repr("['rg_fire_bullets3', 'fmt']"), words_list )

    def test_doc_strings(self):
        file_name = get_relative_path( 'doc_string.inc', __file__ )
        # log( 1, "file_name: %s", file_name )

        node = Node(file_name)
        pawnParse = PawnParse()

        with open( node.file_name ) as file:
            pawnParse.start(TextReader(file.read()), node)

        func_list = dict((func, item) for func, item in node.funcs_list)
        doc_list = dict((func, item.doc_comment) for func, item in node.doct.items())

        self.assertEqual( {
            'rg_fire_bullets3':
                    'single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string.\nsingle rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string.\nsingle rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string.\nsingle rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string.\nsingle rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string. single rg_fire_bullets3 line doc string.',
            'rg_fire_bullets2':
                    'single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string. single rg_fire_bullets2 line doc string.',
            'rg_fire_bullets1':
                    'single rg_fire_bullets1 line doc string. single rg_fire_bullets1 line doc string. single rg_fire_bullets1 line doc string. single rg_fire_bullets1 line doc string. single rg_fire_bullets1 line doc string.',
            'fmt4': '',
            'fmt3': 'single fmt3 line doc string 1.\nsingle fmt3 line doc string 2.',
            'fmt2':
                    'single fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.\nsingle fmt2 line doc string.',
            'fmt1':
                    'single fmt1 line doc string.\nsingle fmt1 line doc string.\nsingle fmt1 line doc string.\nsingle fmt1 line doc string.',
            'REMOVE_CODE_COLOR_TAGS':
                    "\nRemove the colored strings codes '^4 for green', '^1 for yellow', '^3 for team' and\n'^2 for unknown'.\n\n@param string[]    a string pointer to be formatted.",
            'startNominationMenuVariables': '\nThe startNominationMenuVariables() macro definition.',
            'nomination_menu': '\nGather all maps that match the nomination.',
            'nomination_menuHook':
                    '\nUsed to allow the menu nomination_menu(1) to have parameters within a default value.\nIt is because public functions are not allow to have a default value and we need this function\nbe public to allow it to be called from a set_task().',
        }, doc_list )

        self.assertEqual( {
            'rg_fire_bullets3(1) \tdoc_string.inc - native': 'rg_fire_bullets3(${1:const inflictor})',
            'rg_fire_bullets1(1) \tdoc_string.inc - native': 'rg_fire_bullets1(${1:const inflictor})',
            'rg_fire_bullets2(1) \tdoc_string.inc - native': 'rg_fire_bullets2(${1:const inflictor})',
            'fmt4(2) \tdoc_string.inc - stock': 'fmt4(${1:const format[]}, ${2:any:...})',
            'fmt3(2) \tdoc_string.inc - native': 'fmt3(${1:const format[]}, ${2:any:...})',
            'fmt2(2) \tdoc_string.inc - native': 'fmt2(${1:const format[]}, ${2:any:...})',
            'fmt1(2) \tdoc_string.inc - native': 'fmt1(${1:const format[]}, ${2:any:...})',
            'isRecentMapNomBlocked\t doc_string.inc': 'isRecentMapNomBlocked',
            'isWhiteListNomBlock\t doc_string.inc': 'isWhiteListNomBlock',
            'mapIndex\t doc_string.inc': 'mapIndex',
            'nomination_menu(1) \tdoc_string.inc - stock': 'nomination_menu(${1:player_id})',
            'nomination_menuHook(1) \tdoc_string.inc - public': 'nomination_menuHook(${1:player_id})',
            'REMOVE_CODE_COLOR_TAGS(1) \tdoc_string.inc - define: { replace_all( %1, MAX_COLOR_MESSAGE - 1, "^4", "" ); replace_all( %1, MAX_COLOR_MESSAGE - 1, "^3", "" ); replace_all( %1, MAX_COLOR_MESSAGE - 1, "^2", "" ); replace_all( %1, MAX_COLOR_MESSAGE - 1, "^1", "" ); }': 'REMOVE_CODE_COLOR_TAGS(${1:param1})',
            'startNominationMenuVariables(1) \tdoc_string.inc - define: new      mapIndex; new bool:isRecentMapNomBlocked; new bool:isWhiteListNomBlock; getRecentMapsAndWhiteList( %1, isRecentMapNomBlocked, isWhiteListNomBlock )':
                    'startNominationMenuVariables(${1:param1})',
        }, func_list )


# https://stackoverflow.com/questions/15971735/running-single-test-from-unittest-testcase-via-command-line/
def load_tests(loader, standard_tests, pattern):
    suite = unittest.TestSuite()
    suite.addTest( MainUnitTests( 'test_doc_strings' ) )
    return suite

# Skip Custom load_tests()
load_tests = None


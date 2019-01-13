#! /usr/bin/env python
# -*- coding: utf-8 -*-

####################### Licensing #######################################################
#
#   Copyright 2018 @ Evandro Coan
#   Helper functions and classes
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

import pprint
from debug_tools import getLogger
from debug_tools.utilities import assert_path

try:
    # To run this file, run on the Sublime Text console:
    # import imp; import AmxxEditor.tests.allman_style_enum; imp.reload( AmxxEditor.tests.allman_style_enum )
    import sublime_api

except (ImportError):
    assert_path( os.path.join( os.path.dirname( os.path.dirname( os.path.dirname( os.path.realpath( __file__ ) ) ) ) ) )

# Import and reload
from AmxxEditor.AmxxEditor import PawnParse
from AmxxEditor.AmxxEditor import Node

log = getLogger( __name__.split('.')[-1], 127 )

current_directory = os.path.dirname(__file__)
file_name = os.path.join( current_directory, 'testing', 'allman_style_enum.sma' )
log( 1, "file_name: %s", file_name )

node = Node(file_name)
pawnParse = PawnParse()

with open( node.file_name ) as file:
    pawnParse.start(file, node)

log( 1, "func_list: \n%s", pprint.pformat( node.funcs_list ) )
log( 1, "words_list: \n%s", pprint.pformat( node.words_list ) )

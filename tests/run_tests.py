#! /usr/bin/env python
# -*- coding: utf-8 -*-

####################### Licensing #######################################################
#
#   Copyright 2018 @ Evandro Coan
#   Custom Main Unit Tests Runner
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

# To run this file, run on the Sublime Text console:
# import imp; import AmxxEditor.tests.run_tests; imp.reload( AmxxEditor.tests.run_tests )
PACKAGE_ROOT_DIRECTORY = os.path.dirname( os.path.realpath( __file__ ) )

loader = unittest.TestLoader()
start_dir = os.path.join( PACKAGE_ROOT_DIRECTORY, 'testing' )

suite = loader.discover( start_dir, "*unit_tests.py" )
runner = unittest.TextTestRunner( verbosity=2 )
results = runner.run( suite )

print( "results: %s" % results )
print( "results.wasSuccessful: %s" % results.wasSuccessful() )


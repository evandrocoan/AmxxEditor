#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

#
# Licensing
#
# Install AmxxEditor Main Menus, install and uninstall package menus
# Copyright (C) 2018 Evandro Coan <https://github.com/evandrocoan>
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

"""

# Fix Main Menus

Delete the default main menu for the `Amxmodx` package, because when it updates
we would get duplicated menu entries as the default menu for that package is set
on the `User/Main.sublime-menu` file.

"""


import os
import sublime
import sublime_plugin

from debug_tools import getLogger

# Debugger settings: 0 - disabled, 127 - enabled
log = getLogger( 1, __name__ )


AMXX_CHANNEL = "AmxxChannel"
MENU_FILE_NAME = "Main.sublime-menu"

CURRENT_PACKAGE_NAME = __package__
PACKAGE_ROOT_DIRECTORY = os.path.dirname( os.path.realpath( __file__ ) )


def plugin_loaded():
    global USER_MENU_FILES_DIRECTORY
    USER_MENU_FILES_DIRECTORY = os.path.join( sublime.packages_path(), "User", CURRENT_PACKAGE_NAME )
    install_amxx_editor_menu_on_first_run()


def install_amxx_editor_menu_on_first_run():
    # https://packagecontrol.io/docs/events
    from package_control import events

    if events.install( CURRENT_PACKAGE_NAME ):
        log( 1, 'Installed %s!', events.install( CURRENT_PACKAGE_NAME ) )
        from package_control.package_manager import PackageManager

        package_manager = PackageManager()
        all_packages = set( package_manager.list_packages() )

        if AMXX_CHANNEL in all_packages:
            amxx_channel_path = os.path.join( PACKAGE_ROOT_DIRECTORY, AMXX_CHANNEL )

            if not os.path.exists( amxx_channel_path ):
                add_main_menu()


class AmxxEditorInstallMainAmxxEditorMenu( sublime_plugin.ApplicationCommand ):

    def run(self):
        add_main_menu()


class AmxxEditorUninstallMainAmxxEditorMenu( sublime_plugin.ApplicationCommand ):

    def run(self):
        remove_main_menu()


def remove_main_menu():
    """
        This can only be called after `plugin_loaded()` as being called by Sublime Text.
    """
    package_menu_files = os.path.join( USER_MENU_FILES_DIRECTORY, MENU_FILE_NAME )
    log( 1, "Removing the file menu file: %s", package_menu_files )

    # print( log )
    if os.path.exists( package_menu_files ):
        os.remove( package_menu_files )


def add_main_menu():
    """
        This can only be called after `plugin_loaded()` as being called by Sublime Text.
    """
    base_file = os.path.join( PACKAGE_ROOT_DIRECTORY, MENU_FILE_NAME + ".hide" )
    destine_file = os.path.join( USER_MENU_FILES_DIRECTORY, MENU_FILE_NAME )

    packages_start = base_file.find( "Packages" )
    packages_relative_path = base_file[packages_start:].replace( "\\", "/" )

    log( 1, "load_data_file, packages_relative_path: " + str( packages_relative_path ) )
    resource_bytes = sublime.load_binary_resource( packages_relative_path )
    text = resource_bytes.decode('utf-8')

    with open( destine_file, "w", newline='\n', encoding='utf-8' ) as file:
        file.write( text )



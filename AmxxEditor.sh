#!/bin/bash

# AMXX Plugin Compiler Script
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation; either version 2 of the License, or ( at
#  your option ) any later version.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


printf "\\nCompiling %s... " "$2"

# Put here the paths to the folders where do you want to install the plugin.
# You must to provide at least one folder.
#
# Declare an array variable.
# You can access them using echo "${arr[0]}", "${arr[1]}"
declare -a folders_list=(
"F:/SteamCMD/steamapps/common/Half-Life/czero/addons/amxmodx/plugins"
"F:/SteamCMD/steamapps/common/Half-Life/cstrike/addons/amxmodx/plugins"
"F:/SteamLibrary/steamapps/common/Sven Co-op Dedicated Server/svencoop/addons/amxmodx/plugins"
)

# Where is your compiler?
#
# Examples:
#
# "F:/SteamCMD/steamapps/common/Half-Life/czero/addons/amxmodx/scripting/amxxpc.exe"
# "/home/jack/steam/steamapps/common/Half-Life/czero/addons/amxmodx/scripting/compiler.sh"
#
AMXX_COMPILER_PATH="F:/SteamCMD/steamapps/common/Half-Life/czero/addons/amxmodx/scripting/amxxpc.exe"




# Import the helper functions.

# The time flag file path
updateFlagFilePath="/tmp/.amxx_flag_file.txt"

# Save the current seconds, only if it is not already saved
if ! [ -f $updateFlagFilePath ]
then
    # Create a flag file to avoid override the initial time and save it.
    printf "%s" "$(date +%s.%N)" > $updateFlagFilePath

    # printf "$1\\n"
    printf "Current time: %s\\n" "$(date)"
fi

# Clean the flag file
cleanUpdateFlagFile()
{
    if [ -f $updateFlagFilePath ]
    then
        cat $updateFlagFilePath
        rm $updateFlagFilePath
    fi
}

# Calculates and prints to the screen the seconds elapsed since this script started.
showTheElapsedSeconds()
{
    # Clean the flag file and read the time
    scriptStartSecond=$(cleanUpdateFlagFile)

    # Calculates whether the seconds program parameter is an integer number
    isFloatNumber "$scriptStartSecond"

    # `$?` captures the return value of the previous function call command
    # Print help when it is not passed a second command line argument integer
    if [ $? -eq 1 ]
    then
        scripExecutionTimeResult=$(awk "BEGIN {printf \"%.2f\",$(date +%s.%N)-$scriptStartSecond}")
        integer_time="$(float_to_integer "$scripExecutionTimeResult")"

        printf "Took '%s' " "$(convert_seconds "$integer_time" "$scripExecutionTimeResult")"
        printf "seconds to run the script, %s.\\n" "$(date +%H:%M:%S)"
    else
        printf "Could not calculate the seconds to run '%s'.\\n" "$1"
    fi
}

# Convert seconds to hours, minutes, seconds, milliseconds
# https://stackoverflow.com/questions/12199631/convert-seconds-to-hours-minutes-seconds
#
# Awk printf number in width and round it up
# https://unix.stackexchange.com/questions/131073/awk-printf-number-in-width-and-round-it-up
convert_seconds()
{
    # printf "$1$2\\n"
    printf "%s %s" "$1" "$2" | awk '{printf("%d:%02d:%02d:%02d.%02.0f", ($1/60/60/24), ($1/60/60%24), ($1/60%60), ($1%60), (($2-$1)*100))}'
}

# Bash: Float to Integer
# https://unix.stackexchange.com/questions/89712/bash-float-to-integer
float_to_integer()
{
    awk 'BEGIN{for (i=1; i<ARGC;i++)
        printf "%.0f\\n", ARGV[i]}' "$@"
}

# Determine whether its first parameter is empty or not.
#
# Returns 1 if empty, otherwise returns 0.
isEmpty()
{
    if [ -z ${1+x} ]
    then
        return 1
    fi

    return 0
}


# Determine whether the first parameter is an integer or not.
#
# Returns 1 if the specified string is an integer, otherwise returns 0.
isInteger()
{
    # Calculates whether the first function parameter $1 is a number
    isEmpty "$1"

    # `$?` captures the return value of the previous function call command
    # Notify an invalid USB port number passed as parameter.
    if ! [ $? -eq 1 ]
    then
        if [ "$1" -eq "$1" ] 2>/dev/null
        then
            return 1
        fi
    fi

    return 0
}


# Determine whether the first parameter is an integer or not.
#
# Returns 1 if the specified string is an integer, otherwise returns 0.
isFloatNumber()
{
    # Calculates whether the first function parameter $1 is a number
    isEmpty "$1"

    # `$?` captures the return value of the previous function call command
    # Notify an invalid USB port number passed as parameter.
    if ! [ $? -eq 1 ]
    then
        # Removed the file extension, just in case there exists.
        firstFloatNumberPart=$(printf "%s" "$1" | cut -d'.' -f 1)
        secondFloatNumberPart=$(printf "%s" "$1" | cut -d'.' -f 2)

        # Checks whether the first float number part is an integer.
        isInteger "$firstFloatNumberPart"

        if ! [ $# -eq 1 ]
        then
            return 0
        fi

        # Checks whether the second float number part is an integer.
        isInteger "$secondFloatNumberPart"

        if [ $# -eq 1 ]
        then
            return 1
        fi
    fi

    return 0
}



# $1 is the first shell argument and $2 is the second shell argument passed by AmxxEditor.sublime-build
# Usually they should be the plugin's file full path and the plugin's file name without extension.
#
# Example: $1="F:/SteamCMD/steamapps/common/Half-Life/czero/addons/my_plugin.sma"
PLUGIN_SOURCE_CODE_FILE_PATH=$1

# %4 is the path of the folder where the plugin source code is.
# Example F:\SteamCMD\steamapps\common\Half-Life\czero\addons\
SOURCE_CODE_FOLDER=$4
SOURCE_CODE_INCLUDE_FOLDER=$SOURCE_CODE_FOLDER/include

# Build the compiler include folder path
COMPILER_FOLDER_PATH=$(dirname "${AMXX_COMPILER_PATH}")
COMPILER_INCLUDE_FOLDER_PATH=$COMPILER_FOLDER_PATH/include



# Example: $2="my_plugin"
printf "\\n"
PLUGIN_BASE_FILE_NAME="$2"
PLUGIN_BINARY_FILE_PATH=${folders_list[0]}/$PLUGIN_BASE_FILE_NAME.amxx

if [[ $PLUGIN_BASE_FILE_NAME == "" ]]
then
    printf "You must to save the plugin before to compile it.\\n"

else
    # Delete the old binary in case some crazy problem on the compiler, or in the system while copy it.
    # So, this way there is not way you are going to use the wrong version of the plugin without knowing it.
    if [ -f "$PLUGIN_BINARY_FILE_PATH" ]
    then
        rm "$PLUGIN_BINARY_FILE_PATH"
    fi

    # To call the compiler to compile the plugin to the output folder $PLUGIN_BINARY_FILE_PATH
    # Comment the following line and uncomment the next line to it, if you not want to override your compiler files
    "$AMXX_COMPILER_PATH" -i"$SOURCE_CODE_INCLUDE_FOLDER" -o"$PLUGIN_BINARY_FILE_PATH" "$PLUGIN_SOURCE_CODE_FILE_PATH"
    # "$AMXX_COMPILER_PATH" -i"$COMPILER_INCLUDE_FOLDER_PATH" -i"$SOURCE_CODE_INCLUDE_FOLDER" -o"$PLUGIN_BINARY_FILE_PATH" "$PLUGIN_SOURCE_CODE_FILE_PATH"

    # If there was a compilation error, there is nothing more to be done.
    if [ -f "$PLUGIN_BINARY_FILE_PATH" ]
    then
        printf "\\nInstalling the plugin to the folder %s\\n" "${folders_list[0]}"

        # Remove the first element, as it was already processed and it is the source file.
        unset "folders_list[0]"

        # Now loop through the above array
        for current_output_folder in "${folders_list[@]}"
        do
            printf "Installing the plugin to the folder %s\\n" "$current_output_folder"

            rm "$current_output_folder/$PLUGIN_BASE_FILE_NAME.amxx"
            cp "$PLUGIN_BINARY_FILE_PATH" "$current_output_folder"
        done
    fi
fi

FULL_PATH_TO_SCRIPT=$(echo "$0" | sed -r 's|\\|\/|g' | sed -r 's|:||g')

printf "\\n"
showTheElapsedSeconds "$FULL_PATH_TO_SCRIPT"


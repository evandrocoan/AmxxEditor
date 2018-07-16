


# Amxmodx Version 2.0.0

The new version of the AMXXEditor package has just been installed in your machine.

On this version, the package have been renamed from `amxmodx` to `Amxmodx`. Also, its settings files
have been renamed. You will need to copy them from the old file to the new file:

1. `User/amxx.sublime-settings` to `User/Amxmodx.sublime-settings`
1. `User/AMXX-Console.sublime-settings` to `User/AmxmodxConsole.sublime-settings`

The standard syntax file has also been renamed from `amxmodx/AMXX-Pawn.sublime-syntax` to `Amxmodx/Amxmodx.sublime-syntax`.

If you need help, you can post your problem on the AlliedModders forum thread:
https://forums.alliedmods.net/showthread.php?t=293376


___

By default,this version do not create the `Amxmodx` menu, because not everybody want that menu showing up.

You can add the menu going on the Sublime Text menu `Preferences -> Browse Packages...` and creating the
file `Main.sublime-menu` on the `User/` directory or any subfolder/directory inside it:

    [
        {
            "caption": "Amx Mod X",
            "id": "amxmodx",
            "children":
            [
                {
                    "command": "new_amxx_include",
                    "caption": "New Include"
                },
                {
                    "command": "new_amxx_plugin",
                    "caption": "New Plug-In"
                },
                {
                    "command": "open_file",
                    "args": {"file": "${packages}/User/Amxmodx/AmxxPawn.sh"},
                    "caption": "Configure Linux/Cygwin Compiler"
                },
                {
                    "command": "open_file",
                    "args": {"file": "${packages}/User/Amxmodx/AmxxPawn.bat"},
                    "caption": "Configure Windows/Bat Compiler"
                },
                { "caption": "-" },
                {
                    "command": "open_file",
                    "args": { "file": "${packages}/User/AmxmodxConsole.sublime-settings" },
                    "caption": "Edit Amxmodx Console Settings"
                },
                {
                    "command": "open_file",
                    "args": { "file": "${packages}/User/Amxmodx.sublime-settings" },
                    "caption": "Edit Amxmodx Autocompletion Settings"
                },
            ]
        },
    ]

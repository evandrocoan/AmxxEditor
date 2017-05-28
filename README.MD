# Sublime AMXX-Editor

This was initially a mirror from the Sublime AMXX-Editor available on:

1. [[Editor] Sublime AMXX-Editor v2.2](https://forums.alliedmods.net/showthread.php?t=284385)


Now it is a fork filled within new settings and improvements. You can some of its features on:

1. [[TUT] Compiling AMXX plugins with Sublime Text](https://forums.alliedmods.net/showthread.php?t=293376)

Its feature is auto-complete. This is the settings file:
```javascript
{
    // Example:
    // Path to includes folder, the files here will be used for auto completion.
    "include_directory": "C:\\amxmodx\\scripting\\include\\",

    // ( true / false ) Enable the parameters addition when auto completing.
    "add_function_parameters": true,

    // ( true / false ) Enable IntelTip PopUp
    "enable_inteltip": false,

    // ( true / false ) Enable Auto-Increment Build/Version
    "enable_buildversion": false,

    // ( true / false ) Enable auto completing functions and global variables from the current file.
    // If you change this setting, you need to restart Sublime Text before it can take effect.
    "function_autocomplete": true,

    // ( true / false ) Enable auto completing words from the current file.
    "word_autocomplete": true,

    // ( true / false ) Enable to add word completions from all opened files.
    "use_all_autocomplete": true,

    // Enable editor debug messages, see the file `amxmodx/AMXXEditor.py` for all debugging levels.
    //
    // 0 - Disabled debugging.
    // 1 - Errors messages.
    //
    "debug_level": 1,

    // ( color name ) Set color scheme ( dark / twlight / atomic / white / npp )
    "color_scheme": "dark",

    // The new file syntax when using the menu `Amx Mod X -> New Plug-in`. Possible values are:
    //
    // "Packages/Amxx Pawn/AmxxPawn.sublime-syntax"
    // "Packages/amxmodx/AMXX-Pawn.sublime-syntax"
    //
    "amxx_file_syntax": "Packages/Amxx Pawn/AmxxPawn.sublime-syntax",

    // ( 0.5 ~ 5.0 ) Delay before regenerating auto-completion snippets
    "live_refresh_delay":   1.0
}
```


It had the purpose to be that's project fork, as it is not available on github at the moment.
To be used as a submodule at My Sublime Text Settings: https://github.com/evandrocoan/SublimeTextStudio


## Installation

1. Download & Install Sublime 3.
1. Install Sublime Package Manager (https://packagecontrol.io/installation)
1. Installation is performed via Package Control.


### Manual Installation

1. Go to <i>Preferences > Browse Packages...</i> and clone this package into there.
<pre><code>
git clone https://github.com/evandrocoan/SublimeAMXX_Editor amxmodx
</code></pre>
1. Restart Sublime





# Sublime AmxxEditor

[![Build Status](https://travis-ci.org/evandrocoan/AmxxEditor.svg?branch=master)](https://travis-ci.org/evandrocoan/AmxxEditor)
[![Build status](https://ci.appveyor.com/api/projects/status/github/evandrocoan/AmxxEditor?branch=master&svg=true)](https://ci.appveyor.com/project/evandrocoan/AmxxEditor/branch/master)
[![codecov](https://codecov.io/gh/evandrocoan/AmxxEditor/branch/master/graph/badge.svg)](https://codecov.io/gh/evandrocoan/AmxxEditor)
[![Coverage Status](https://coveralls.io/repos/github/evandrocoan/AmxxEditor/badge.svg?branch=master)](https://coveralls.io/github/evandrocoan/AmxxEditor?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/9191d17b91814f8caf17c9e537a22904)](https://www.codacy.com/app/evandrocoan/AmxxEditor?utm_source=github.com&utm_medium=referral&utm_content=evandrocoan/AmxxEditor&utm_campaign=badger)
[![Latest Release](https://img.shields.io/github/tag/evandrocoan/AmxxEditor.svg?label=version)](https://github.com/evandrocoan/AmxxEditor/releases)
<a href="https://packagecontrol.io/packages/AmxxEditor"><img src="https://packagecontrol.herokuapp.com/downloads/AmxxEditor.svg"></a>


This was initially a mirror from the Sublime AMXX-Editor available on:

1. [[Editor] Sublime AMXX-Editor v2.2](https://forums.alliedmods.net/showthread.php?t=284385)


Now it is a fork filled within new settings and improvements. You can some of its features on:

1. [[TUT] Compiling AMXX plugins with Sublime Text](https://forums.alliedmods.net/showthread.php?t=293376)

Its feature is auto-complete. This is the settings file: [AmxxEditor.sublime-settings](AmxxEditor.sublime-settings)


It had the purpose to be that's project fork, as it is not available on github at the moment.
To be used as a submodule at My Sublime Text Settings: https://github.com/evandrocoan/SublimeTextStudio


## Installation

### By Package Control

1. Download & Install **`Sublime Text 3`** (https://www.sublimetext.com/3)
1. Go to the menu **`Tools -> Install Package Control`**, then,
    wait few seconds until the installation finishes up
1. Now,
    Go to the menu **`Preferences -> Package Control`**
1. Type **`Add Channel`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
    input the following address and press <kbd>Enter</kbd>
    ```
    https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json
    ```
1. Go to the menu **`Tools -> Command Palette...
    (Ctrl+Shift+P)`**
1. Type **`Preferences:
    Package Control Settings – User`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
    find the following setting on your **`Package Control.sublime-settings`** file:
    ```js
    "channels":
    [
        "https://packagecontrol.io/channel_v3.json",
        "https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json",
    ],
    ```
1. And,
    change it to the following, i.e.,
    put the **`https://raw.githubusercontent...`** line as first:
    ```js
    "channels":
    [
        "https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json",
        "https://packagecontrol.io/channel_v3.json",
    ],
    ```
    * The **`https://raw.githubusercontent...`** line must to be added before the **`https://packagecontrol.io...`** one, otherwise,
      you will not install this forked version of the package,
      but the original available on the Package Control default channel **`https://packagecontrol.io...`**
1. Now,
    go to the menu **`Preferences -> Package Control`**
1. Type **`Install Package`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
    search for **`AmxxEditor`** and press <kbd>Enter</kbd>

See also:

1. [ITE - Integrated Toolset Environment](https://github.com/evandrocoan/ITE)
1. [Package control docs](https://packagecontrol.io/docs/usage) for details.


### Manual Installation

1. Go to <i>Preferences > Browse Packages...</i> and clone this package into there.
<pre><code>
git clone https://github.com/evandrocoan/AmxxEditor AmxxEditor
</code></pre>
1. Restart Sublime



___
## License

"Sublime AMXX-Editor"  is a modification of "SourcePawn Completions" for SublimeText 3 by

```
Copyright (C) 2013-2016 ppalex7 <https://github.com/ppalex7/SourcePawnCompletions>
Copyright (C) 2016-2017 AMXX-Editor by Destro <https://forums.alliedmods.net/showthread.php?t=284385>
Copyright (C) 2017-2018 Evandro Coan <https://github.com/evandrocoan/AmxxEditor>

 Redistributions of source code must retain the above
 copyright notice, this list of conditions and the
 following disclaimer.

 Redistributions in binary form must reproduce the above
 copyright notice, this list of conditions and the following
 disclaimer in the documentation and/or other materials
 provided with the distribution.

 Neither the name Evandro Coan nor the names of any
 contributors may be used to endorse or promote products
 derived from this software without specific prior written
 permission.

 This program is free software; you can redistribute it and/or modify it
 under the terms of the GNU General Public License as published by the
 Free Software Foundation; either version 3 of the License, or ( at
 your option ) any later version.

 This program is distributed in the hope that it will be useful, but
 WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
```

See:

1. The [LICENSE](LICENSE) file
1. The website https://www.gnu.org/licenses/gpl-3.0.en.html
1. https://amxmodx-es.com/Thread-Editor-Sublime-Text-3-auto-completion-pawn-syntax-compiler



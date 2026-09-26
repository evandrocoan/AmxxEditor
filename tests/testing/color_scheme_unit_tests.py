"""Focused color scheme checks without loading the Sublime plugin host."""

import io
import json
import os
import unittest
from xml.etree import ElementTree


class FakeSublime(object):
    def __init__(self):
        self.resources = {}
        self.window = None

    def load_resource(self, name):
        return self.resources[name]

    def find_resources(self, filename):
        return [name for name in self.resources if name.rsplit("/", 1)[-1] == filename]

    def decode_value(self, data):
        return json.loads(data)

    def score_selector(self, scope, selector):
        return int(scope in [part.strip() for part in selector.split(",")])

    def active_window(self):
        return self.window


class FakeWindow(object):
    def __init__(self, view):
        self.view = view

    def active_view(self):
        return self.view


class FakeView(object):
    def __init__(self, scheme):
        self.scheme = scheme

    def settings(self):
        return {"color_scheme": self.scheme}


class ColorSchemeTests(unittest.TestCase):
    def setUp(self):
        self.sublime = FakeSublime()
        path = os.path.join(os.path.dirname(__file__), "..", "..", "AmxxEditor.py")
        with io.open(path, "r", encoding="utf-8") as source_file:
            source = source_file.read()
        start = source.index("def _color_scheme_has_scope(")
        end = source.index("def on_settings_modified():", start)
        self.namespace = {
            "sublime": self.sublime,
            "ElementTree": ElementTree,
            "g_enable_inteltip_color": "inteltip.pawn",
        }
        exec(compile(source[start:end], path, "exec"), self.namespace)

    def check(self, scheme):
        self.sublime.window = FakeWindow(FakeView(scheme))
        self.namespace["check_color_scope_setting"]()
        return self.namespace["g_enable_inteltip_color"]

    def test_json_scope_keeps_highlight(self):
        scheme = "Packages/Example/Example.sublime-color-scheme"
        self.sublime.resources[scheme] = json.dumps({
            "rules": [{"scope": "comment, inteltip.pawn", "foreground": "#ff0000"}]
        })
        self.assertEqual("inteltip.pawn", self.check(scheme))

    def test_json_missing_scope_disables_highlight(self):
        scheme = "Packages/Example/Example.sublime-color-scheme"
        self.sublime.resources[scheme] = json.dumps({
            "rules": [{"scope": "comment", "foreground": "#ff0000"}]
        })
        self.assertEqual("", self.check(scheme))

    def test_json_user_customization_adds_scope(self):
        scheme = "Packages/Example/Example.sublime-color-scheme"
        self.sublime.resources[scheme] = json.dumps({"rules": []})
        self.sublime.resources["Packages/User/Example.sublime-color-scheme"] = json.dumps({
            "rules": [{"scope": "inteltip.pawn", "foreground": "#ff0000"}]
        })
        self.assertEqual("inteltip.pawn", self.check(scheme))

    def test_tmtheme_scope_keeps_highlight(self):
        scheme = "Packages/Example/Example.tmTheme"
        self.sublime.resources[scheme] = (
            "<plist><dict><array><dict><key>scope</key>"
            "<string>inteltip.pawn</string></dict></array></dict></plist>"
        )
        self.assertEqual("inteltip.pawn", self.check(scheme))

    def test_missing_window_or_view_does_not_raise(self):
        self.namespace["check_color_scope_setting"]()
        self.sublime.window = FakeWindow(None)
        self.namespace["check_color_scope_setting"]()
        self.assertEqual("inteltip.pawn", self.namespace["g_enable_inteltip_color"])


if __name__ == "__main__":
    unittest.main()

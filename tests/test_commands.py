import unittest

from econsole.app import EConsoleApp

from ._tmpenv import TempEnvTestCase


class CommandTest(TempEnvTestCase):
    def setUp(self):
        super().setUp()
        self.app = EConsoleApp()

    def run_cmd(self, line):
        return self.app.run_command(line)

    def test_help_lists_commands(self):
        result = self.run_cmd("help")
        self.assertTrue(result.ok)
        self.assertIn("help", result.message)
        self.assertIn("parabash", result.message)

    def test_version(self):
        self.assertIn("UNISHELL", self.run_cmd("version").message)

    def test_calc_inline(self):
        self.assertIn("714", self.run_cmd("calc 42*17").message)

    def test_calc_error(self):
        self.assertFalse(self.run_cmd("calc 1 +").ok)

    def test_parabash_new_creates_pane(self):
        before = len(self.app.manager.panes)
        result = self.run_cmd("parabash new")
        self.assertTrue(result.ok)
        self.assertEqual(len(self.app.manager.panes), before + 1)

    def test_theme_apply(self):
        self.assertTrue(self.run_cmd("theme apply eink-dark").ok)
        self.assertEqual(self.app.theme.name, "eink-dark")

    def test_theme_apply_unknown(self):
        self.assertFalse(self.run_cmd("theme apply nope").ok)

    def test_theme_list(self):
        self.assertIn("eink-dark", self.run_cmd("theme list").message)

    def test_profile_switch_changes_theme(self):
        self.run_cmd("profile set eink")
        self.assertEqual(self.app.profile.name, "eink")
        # Switching profile adopts the profile's default theme.
        self.assertEqual(self.app.theme.name, "eink-light")

    def test_activity_new_with_quotes(self):
        result = self.run_cmd('activity new project "OS Development"')
        self.assertTrue(result.ok)
        projects = self.app.activity.by_type("project")
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["title"], "OS Development")

    def test_tasks_and_notes(self):
        self.run_cmd("tasks new Buy milk")
        self.run_cmd("notes new Remember this")
        self.assertEqual(len(self.app.activity.by_type("task")), 1)
        self.assertEqual(len(self.app.notes.all()), 1)

    def test_firewall_status_and_toggle(self):
        self.assertIn("ENABLED", self.run_cmd("firewall status").message)
        self.run_cmd("firewall disable")
        self.assertFalse(self.app.config.get("firewall_enabled"))

    def test_unknown_command_marked(self):
        result = self.run_cmd("definitely-not-a-command")
        self.assertTrue(result.unknown)

    def test_open_app_reuses_pane(self):
        self.run_cmd("app calculator")
        self.run_cmd("app calculator")
        calculators = [p for p in self.app.manager.panes if p.kind == "calculator"]
        self.assertEqual(len(calculators), 1)

    def test_open_unknown_app(self):
        self.assertFalse(self.run_cmd("app nope").ok)

    def test_zoom_toggle(self):
        self.run_cmd("zoom")
        self.assertTrue(self.app.manager.zoom)

    def test_quit(self):
        self.run_cmd("quit")
        self.assertFalse(self.app.running)

    def test_run_system_echo(self):
        code, output = self.app.run_system("echo hello-econsole")
        self.assertEqual(code, 0)
        self.assertIn("hello-econsole", output)

    def test_handlers_never_raise(self):
        # A malformed command must produce an error result, not a traceback.
        result = self.run_cmd('activity new')
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()

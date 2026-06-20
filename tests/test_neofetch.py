import unittest

from econsole import neofetch
from econsole.app import EConsoleApp

from ._tmpenv import TempEnvTestCase


class NeofetchGatherTest(unittest.TestCase):
    def test_gather_returns_label_value_pairs(self):
        info = neofetch.gather(None)
        self.assertTrue(info)
        labels = [label for label, _ in info]
        self.assertIn("OS", labels)
        self.assertIn("Kernel", labels)
        # Packages is disabled by default.
        self.assertNotIn("Packages", labels)

    def test_disabled_fields_excluded(self):
        cfg = {"logo": "auto", "color_blocks": True, "disabled": ["os", "cpu"]}
        labels = [label for label, _ in neofetch.gather(None, cfg)]
        self.assertNotIn("OS", labels)
        self.assertNotIn("CPU", labels)
        self.assertIn("Kernel", labels)

    def test_enabling_packages(self):
        cfg = {"logo": "auto", "color_blocks": True, "disabled": []}
        labels = [label for label, _ in neofetch.gather(None, cfg)]
        self.assertIn("Packages", labels)

    def test_render_text_has_logo_and_blocks(self):
        cfg = {"logo": "econsole", "color_blocks": True, "disabled": []}
        lines = neofetch.render_text(None, cfg)
        roles = {role for _, role in lines}
        self.assertIn("accent", roles)   # logo / title
        self.assertIn("accent2", roles)  # colour blocks
        self.assertTrue(any("OS:" in text for text, _ in lines))

    def test_render_text_no_colors(self):
        cfg = {"logo": "econsole", "color_blocks": False, "disabled": []}
        lines = neofetch.render_text(None, cfg)
        self.assertNotIn("accent2", {role for _, role in lines})

    def test_pick_logo_high_contrast_uses_ascii(self):
        class Ctx:
            class theme:
                high_contrast = True
        self.assertEqual(neofetch.pick_logo({"logo": "auto"}, Ctx()), neofetch.LOGOS["ascii"])

    def test_all_logos_nonempty(self):
        for name, rows in neofetch.LOGOS.items():
            self.assertTrue(rows, f"logo {name} is empty")


class NeofetchConfigTest(TempEnvTestCase):
    def test_config_defaults(self):
        app = EConsoleApp()
        cfg = neofetch.config_for(app)
        self.assertEqual(cfg["logo"], "auto")
        self.assertTrue(cfg["color_blocks"])
        self.assertIn("packages", cfg["disabled"])

    def test_save_and_reload(self):
        app = EConsoleApp()
        cfg = neofetch.config_for(app)
        cfg["logo"] = "pi"
        cfg["color_blocks"] = False
        cfg["disabled"] = ["cpu"]
        neofetch.save_config(app, cfg)

        reloaded = neofetch.config_for(EConsoleApp())
        self.assertEqual(reloaded["logo"], "pi")
        self.assertFalse(reloaded["color_blocks"])
        self.assertEqual(reloaded["disabled"], ["cpu"])

    def test_gather_with_context(self):
        app = EConsoleApp()
        info = dict(neofetch.gather(app))
        self.assertEqual(info["Profile"], "desktop")
        self.assertTrue(info["Shell"].startswith("UNISHELL"))


if __name__ == "__main__":
    unittest.main()

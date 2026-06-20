import unittest

from econsole.profile import PROFILES, get_profile
from econsole.theme import PALETTE, ROLES, THEMES, get_theme, list_themes


class ThemeTest(unittest.TestCase):
    def test_expected_themes_present(self):
        for name in ("econsole-dark", "econsole-light", "eink-dark", "eink-light", "ar-dark"):
            self.assertIn(name, THEMES)

    def test_every_role_resolves_to_palette(self):
        for theme in list_themes():
            pairs = theme.role_pairs()
            for role in ROLES:
                self.assertIn(role, pairs, f"{theme.name} missing role {role}")
                fg, bg = pairs[role]
                self.assertIn(fg, PALETTE, f"{theme.name}.{role} fg '{fg}' not in palette")
                self.assertIn(bg, PALETTE, f"{theme.name}.{role} bg '{bg}' not in palette")

    def test_eink_themes_high_contrast(self):
        self.assertTrue(THEMES["eink-dark"].high_contrast)
        self.assertTrue(THEMES["eink-light"].high_contrast)

    def test_get_theme_fallback(self):
        self.assertEqual(get_theme("does-not-exist").name, "econsole-dark")

    def test_secret_theme_hidden_but_appliable(self):
        # rainbow exists and resolves, but is excluded from the public list.
        self.assertIn("rainbow", THEMES)
        self.assertEqual(get_theme("rainbow").name, "rainbow")
        self.assertNotIn("rainbow", [t.name for t in list_themes()])
        self.assertIn("rainbow", [t.name for t in list_themes(include_hidden=True)])


class ProfileTest(unittest.TestCase):
    def test_profiles_present(self):
        for name in ("desktop", "eink", "ar"):
            self.assertIn(name, PROFILES)

    def test_eink_profile_low_power(self):
        eink = PROFILES["eink"]
        self.assertTrue(eink.grayscale)
        self.assertFalse(eink.animations)
        self.assertLessEqual(eink.video_fps, 4)
        self.assertGreater(eink.refresh_ms, PROFILES["desktop"].refresh_ms)

    def test_get_profile_fallback(self):
        self.assertEqual(get_profile("nope").name, "desktop")


if __name__ == "__main__":
    unittest.main()

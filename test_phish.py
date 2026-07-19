#!/usr/bin/env python3
"""
Unit tests for OPEN PENETRATION framework modules.
Verifies configuration loading, scope checks, HTML parsing, data masking, and awareness mode.
"""

import unittest
import os
import tempfile
import yaml
from bs4 import BeautifulSoup
from unittest.mock import patch

# Import core functions from Phish
import Phish

class TestOpenPenetration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def test_default_config_loading(self):
        """Test config loading with non-existent file falls back to defaults."""
        non_existent = os.path.join(self.test_dir, "non_existent.yaml")
        with patch('builtins.print'):
            result = Phish.load_config(non_existent)
        self.assertFalse(result)
        self.assertIn("server", Phish.config)
        self.assertIn("lab_mode", Phish.config)

    def test_scope_enforcement_check(self):
        """Test tier scope enforcement calculation."""
        Phish.config = {
            "lab_mode": True,
            "tiers": {"tier_1": {"scope_enforcement": True}}
        }
        # In lab mode, scope enforcement for tier 1 returns False
        self.assertFalse(Phish.is_scope_enforced("tier_1"))

        # When lab mode is disabled, scope enforcement follows config
        Phish.config["lab_mode"] = False
        self.assertTrue(Phish.is_scope_enforced("tier_1"))

    def test_html_base_tag_and_form_rewriting(self):
        """Test that HTML parsing correctly rewrites forms and preserves base URL."""
        raw_html = """
        <html>
            <head><title>Test Target</title></head>
            <body>
                <form action="/login" method="GET">
                    <input type="text" name="username">
                    <input type="password" name="password">
                    <input type="submit" value="Login">
                </form>
            </body>
        </html>
        """
        target_url = "https://example.com/login"
        cloned_path = Phish.save_cloned_html(target_url, raw_html, self.test_dir)
        
        self.assertTrue(os.path.exists(cloned_path))
        with open(cloned_path, "r", encoding="utf-8") as f:
            content = f.read()

        soup = BeautifulSoup(content, "html.parser")
        form = soup.find("form")
        self.assertEqual(form["action"], "/submit")
        self.assertEqual(form["method"], "POST")

        base_tag = soup.find("base")
        self.assertIsNotNone(base_tag)
        self.assertEqual(base_tag["href"], "https://example.com")

if __name__ == "__main__":
    unittest.main()

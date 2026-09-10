"""Synthetic regression checks for the public deferrals CLI."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "deferrals.py"


def run(root, *args):
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--project-key=-project",
            *args,
        ],
        capture_output=True,
        text=True,
    )


spec = importlib.util.spec_from_file_location("deferrals_under_test", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RepairBodyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        result = run(
            self.root,
            "add",
            "--id",
            "ddf_b0000001",
            "--title",
            "Ticket",
            "--thread",
            "thread-a",
            "--lane",
            "H",
            "--priority",
            "normal",
            "--body",
            "**Background:** duplicated",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def tearDown(self):
        self.temporary.cleanup()

    def repair(self, old, new):
        return run(
            self.root,
            "repair-body",
            "ddf_b0000001",
            "--old",
            old,
            "--new",
            new,
        )

    def test_repairs_body_and_reseals_hash(self):
        result = self.repair("**Background:** **Background:**", "**Background:**")
        self.assertEqual(result.returncode, 0, result.stderr)
        record = module.find_record((self.root / "-project.md").read_text(), "ddf_b0000001")
        self.assertIs(module.hash_valid(record.text), True)

    def test_refuses_injected_managed_field(self):
        result = self.repair("duplicated", "duplicated\n  - status: resolved")
        self.assertEqual(result.returncode, 2)
        self.assertIn("body bytes only", result.stderr)

    def test_refuses_injected_record_boundary(self):
        result = self.repair(
            "duplicated",
            "duplicated\n- [ ] **ddf_b0000002** — Injected",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("body bytes only", result.stderr)


class RootSelectionTests(unittest.TestCase):
    def test_default_preserves_canonical_shared_location(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            module.Path, "home", return_value=Path("/safe-home")
        ):
            args = module.parser().parse_args(["--project-key=-project", "list"])
        self.assertEqual(args.root, "/safe-home/.claude/deferrals")

    def test_environment_override_wins(self):
        with patch.dict(os.environ, {"DEFERRALS_ROOT": "/configured"}, clear=True):
            args = module.parser().parse_args(["--project-key=-project", "list"])
        self.assertEqual(args.root, "/configured")


if __name__ == "__main__":
    unittest.main()

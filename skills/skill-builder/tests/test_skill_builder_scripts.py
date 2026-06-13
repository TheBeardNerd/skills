"""Behavior tests for scaffold_skill.py and validate_skill.py.

Run from the skill root:  python3 -m unittest discover -s tests
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import scaffold_skill  # noqa: E402
import validate_skill  # noqa: E402


class ScaffoldThenValidateTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _make(self, name="demo-skill", description=None):
        description = description or (
            "Use when the user wants to demo a skill, or asks to test the demo skill."
        )
        skill_dir, _ = scaffold_skill.scaffold(
            name=name, description=description, base=self.base
        )
        return skill_dir

    def test_scaffold_passes_validator(self):
        skill_dir = self._make()
        report = validate_skill.validate(skill_dir)
        self.assertTrue(report.passed(), msg="; ".join(report.failures))

    def test_scaffold_is_idempotent(self):
        skill_dir = self._make()
        # second run should create nothing new and not raise
        again, created = scaffold_skill.scaffold(
            name="demo-skill",
            description="Use when the user wants to demo a skill again.",
            base=self.base,
        )
        self.assertEqual(skill_dir, again)
        self.assertEqual(created, [])

    def test_bad_name_rejected(self):
        with self.assertRaises(ValueError):
            scaffold_skill.scaffold(
                name="Bad_Name", description="Use when ...", base=self.base
            )

    def test_missing_description_fails(self):
        skill_dir = self._make()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\nname: demo-skill\n---\n\n# Demo\n", encoding="utf-8"
        )
        report = validate_skill.validate(skill_dir)
        self.assertFalse(report.passed())
        self.assertTrue(any("description" in f for f in report.failures))

    def test_first_person_description_fails(self):
        skill_dir = self._make(
            description="I help the user when they want to demo something for me."
        )
        report = validate_skill.validate(skill_dir)
        self.assertFalse(report.passed())
        self.assertTrue(any("first person" in f for f in report.failures))

    def test_name_dir_mismatch_fails(self):
        skill_dir = self._make()
        skill_md = skill_dir / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8").replace(
            "name: demo-skill", "name: other-name"
        )
        skill_md.write_text(text, encoding="utf-8")
        report = validate_skill.validate(skill_dir)
        self.assertFalse(report.passed())
        self.assertTrue(any("directory name" in f for f in report.failures))

    def test_oversized_skill_md_fails(self):
        skill_dir = self._make()
        skill_md = skill_dir / "SKILL.md"
        bloat = skill_md.read_text(encoding="utf-8") + "\nx" * 0 + "\n".join(
            f"line {i}" for i in range(validate_skill.MAX_SKILL_LINES + 10)
        )
        skill_md.write_text(bloat, encoding="utf-8")
        report = validate_skill.validate(skill_dir)
        self.assertFalse(report.passed())
        self.assertTrue(any("lines" in f for f in report.failures))

    def test_broken_link_fails(self):
        skill_dir = self._make()
        skill_md = skill_dir / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8") + "\nSee [missing](./references/nope.md)\n"
        skill_md.write_text(text, encoding="utf-8")
        report = validate_skill.validate(skill_dir)
        self.assertFalse(report.passed())
        self.assertTrue(any("missing files" in f for f in report.failures))

    def test_secret_detected(self):
        skill_dir = self._make()
        (skill_dir / "references").mkdir(exist_ok=True)
        (skill_dir / "references" / "leak.md").write_text(
            "token = ghp_" + "A" * 30 + "\n", encoding="utf-8"
        )
        report = validate_skill.validate(skill_dir)
        self.assertFalse(report.passed())
        self.assertTrue(any("secret" in f for f in report.failures))


if __name__ == "__main__":
    unittest.main()

"""Behavior tests for the agent-builder scripts (Claude Code subagent builder).

Run from the skill root: python3 -m unittest discover -s tests
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclass/typing lookups need the module registered
    spec.loader.exec_module(mod)
    return mod


recommend = load("recommend_structure")
scaffold = load("scaffold_agent")
validate = load("validate_agent")


class TestRecommend(unittest.TestCase):
    def test_no_signals_is_unclear(self):
        r = recommend.recommend({})
        self.assertEqual(r["category"], "unclear")

    def test_always_on_rule_is_claude_md(self):
        r = recommend.recommend({"always_on_rule": True})
        self.assertEqual(r["category"], "claude-md")

    def test_event_triggered_is_hook(self):
        r = recommend.recommend({"event_triggered": True})
        self.assertEqual(r["category"], "hook")

    def test_reusable_prompt_is_skill(self):
        r = recommend.recommend({"reusable_prompt_main": True})
        self.assertEqual(r["category"], "skill")

    def test_back_and_forth_is_main_conversation(self):
        r = recommend.recommend({"needs_main_context": True})
        self.assertEqual(r["category"], "main-conversation")

    def test_verbose_side_work_is_single_subagent(self):
        r = recommend.recommend({"verbose_side_work": True})
        self.assertEqual(r["category"], "subagent")
        self.assertEqual(r["recommendation"], "single subagent")

    def test_tool_restriction_overrides_main_context(self):
        # A capability wall is a real subagent payoff even with some back-and-forth.
        r = recommend.recommend({"needs_main_context": True, "needs_tool_restriction": True})
        self.assertEqual(r["category"], "subagent")

    def test_independent_subtasks_is_parallel(self):
        r = recommend.recommend({"self_contained": True, "independent_subtasks": True})
        self.assertIn("parallel", r["recommendation"])

    def test_sequential_stages_is_chained(self):
        r = recommend.recommend({"reusable_worker": True, "sequential_stages": True})
        self.assertIn("chained", r["recommendation"])

    def test_fanout_with_noise_is_coordinator(self):
        r = recommend.recommend({
            "verbose_side_work": True, "subtask_fans_out": True, "intermediate_noise": True,
        })
        self.assertIn("coordinator", r["recommendation"])
        self.assertTrue(r["escalation"])  # nesting must carry an escalation note

    def test_template_has_all_keys(self):
        tpl = json.loads(recommend.template())
        self.assertEqual(set(tpl), set(recommend.SIGNAL_KEYS))


class TestScaffoldAndValidate(unittest.TestCase):
    def _spec(self, **over):
        spec = json.loads(json.dumps(scaffold.STARTER_SPEC))  # deep copy
        spec.update(over)
        return spec

    def test_scaffold_passes_validation(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            spec = self._spec(name="code-reviewer", description="Reviews code for quality. Use proactively after changes.")
            path = scaffold.scaffold(spec, out)
            self.assertEqual(path.name, "code-reviewer.md")
            report = validate.validate_file(path)
            self.assertTrue(report.passed(), report.failures)

    def test_emitted_frontmatter_parses(self):
        with tempfile.TemporaryDirectory() as d:
            spec = self._spec(name="parses", tools=["Read", "Bash"], model="haiku")
            path = scaffold.scaffold(spec, Path(d))
            meta, body = validate.parse_frontmatter(path.read_text())
            self.assertEqual(meta["name"], "parses")
            self.assertEqual(meta["model"], "haiku")
            self.assertEqual(validate.as_tool_list(meta["tools"]), ["Read", "Bash"])
            self.assertTrue(body.strip())

    def test_inherit_all_tools_omits_field_and_warns(self):
        with tempfile.TemporaryDirectory() as d:
            spec = self._spec(name="inheritor", tools=[])
            path = scaffold.scaffold(spec, Path(d))
            meta, _ = validate.parse_frontmatter(path.read_text())
            self.assertNotIn("tools", meta)
            report = validate.validate_file(path)
            self.assertTrue(report.passed())  # still passes (warning, not fail)
            self.assertTrue(any("inherit" in w.lower() for w in report.warnings))

    def test_forbidden_tool_rejected_at_scaffold(self):
        with tempfile.TemporaryDirectory() as d:
            spec = self._spec(name="bad", tools=["Read", "AskUserQuestion"])
            with self.assertRaises(ValueError):
                scaffold.scaffold(spec, Path(d))

    def test_rejects_non_kebab_name(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                scaffold.scaffold(self._spec(name="Bad_Name"), Path(d))

    def test_no_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as d:
            scaffold.scaffold(self._spec(name="dup"), Path(d))
            with self.assertRaises(FileExistsError):
                scaffold.scaffold(self._spec(name="dup"), Path(d))
            scaffold.scaffold(self._spec(name="dup"), Path(d), force=True)  # ok

    def test_missing_description_fails(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "x.md"
            path.write_text("---\nname: x\nmodel: inherit\n---\n\nA body here.\n")
            report = validate.validate_file(path)
            self.assertFalse(report.passed())

    def test_empty_body_fails(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "y.md"
            path.write_text("---\nname: y\ndescription: Use this when needed to do work.\n---\n\n")
            report = validate.validate_file(path)
            self.assertFalse(report.passed())

    def test_bad_model_fails(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "z.md"
            path.write_text("---\nname: z\ndescription: Use when reviewing code carefully.\nmodel: gpt-4\n---\n\nBody.\n")
            report = validate.validate_file(path)
            self.assertFalse(report.passed())

    def test_forbidden_tool_in_handwritten_file_fails(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "w.md"
            path.write_text(
                "---\nname: w\ndescription: Use when you must ask the user something.\n"
                "tools: Read, AskUserQuestion\n---\n\nBody.\n"
            )
            report = validate.validate_file(path)
            self.assertFalse(report.passed())

    def test_no_frontmatter_fails(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "plain.md"
            path.write_text("Just a plain markdown file, no frontmatter.\n")
            report = validate.validate_file(path)
            self.assertFalse(report.passed())

    def test_block_sequence_tools_parse(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "seq.md"
            path.write_text(
                "---\nname: seq\ndescription: Use when researching the codebase for facts.\n"
                "tools:\n  - Read\n  - Grep\n---\n\nWhen invoked: 1. read. 2. grep.\n"
            )
            meta, _ = validate.parse_frontmatter(path.read_text())
            self.assertEqual(validate.as_tool_list(meta["tools"]), ["Read", "Grep"])
            self.assertTrue(validate.validate_file(path).passed())


if __name__ == "__main__":
    unittest.main()

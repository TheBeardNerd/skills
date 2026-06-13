"""Behavior tests for the agent-builder scripts.

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
    def test_no_signals_is_not_an_agent(self):
        r = recommend.recommend({})
        self.assertEqual(r["category"], "not-an-agent")

    def test_complex_dynamic_is_single_loop(self):
        r = recommend.recommend({"complex_decision": True, "dynamic_tool_loop": True})
        self.assertEqual(r["recommendation"], "single-loop")
        self.assertEqual(r["category"], "agent")

    def test_predictable_categories_is_routing(self):
        r = recommend.recommend({
            "brittle_rules": True, "steps_predictable": True,
            "distinct_input_categories": True,
        })
        self.assertEqual(r["recommendation"], "routing")
        self.assertEqual(r["category"], "workflow")

    def test_one_pass_is_not_an_agent_call(self):
        r = recommend.recommend({
            "unstructured_data": True, "steps_predictable": True, "one_pass": True,
        })
        self.assertIn("single augmented call", r["recommendation"])

    def test_unpredictable_synthesis_is_manager(self):
        r = recommend.recommend({
            "complex_decision": True, "dynamic_tool_loop": True,
            "subtasks_unpredictable": True, "needs_central_synthesis": True,
        })
        self.assertIn("manager", r["recommendation"])

    def test_handoff_is_decentralized(self):
        r = recommend.recommend({
            "complex_decision": True, "dynamic_tool_loop": True,
            "specialist_handoff": True,
        })
        self.assertIn("decentralized", r["recommendation"])

    def test_unbounded_high_trust_is_autonomous(self):
        r = recommend.recommend({
            "complex_decision": True, "dynamic_tool_loop": True,
            "steps_unbounded": True, "high_trust": True,
        })
        self.assertEqual(r["recommendation"], "autonomous")
        self.assertTrue(r["escalation"])  # autonomous must carry guardrail warnings

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
            out = Path(d) / "a"
            scaffold.scaffold(self._spec(name="my-agent"), out)
            for f in ("agent.py", "tools.py", "guardrails.py", "config.py"):
                self.assertTrue((out / f).is_file(), f)
            report = validate.validate(out)
            self.assertTrue(report.passed(), report.failures)

    def test_high_risk_requires_approval_path(self):
        spec = self._spec(name="hr-agent", tools=[{
            "name": "issue_refund", "description": "Refund an order; irreversible.",
            "type": "action", "risk": "high",
            "parameters": {"order_id": {"type": "string"}}, "required": ["order_id"],
        }])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "a"
            scaffold.scaffold(spec, out)
            report = validate.validate(out)
            self.assertTrue(report.passed(), report.failures)
            self.assertTrue(any("approval path" in p for p in report.passes))

    def test_missing_max_turns_fails(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "a"
            scaffold.scaffold(self._spec(name="b"), out)
            # Break the hard cap and confirm the gate catches it.
            (out / "config.py").write_text("MODEL='x'\nINSTRUCTIONS='you are done when x'\n")
            report = validate.validate(out)
            self.assertFalse(report.passed())

    def test_empty_tool_description_fails(self):
        spec = self._spec(name="c", tools=[{
            "name": "bad", "description": "", "type": "data", "risk": "low",
            "parameters": {}, "required": [],
        }])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "a"
            scaffold.scaffold(spec, out)
            report = validate.validate(out)
            self.assertFalse(report.passed())

    def test_rejects_non_kebab_name(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                scaffold.scaffold(self._spec(name="Bad_Name"), Path(d) / "a")

    def test_input_guardrail_always_present(self):
        # Even if the spec gives only an output guardrail, one input guardrail is added.
        spec = self._spec(name="g", guardrails=[
            {"name": "pii_redact", "type": "pii", "stage": "output", "action": "redact"}])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "a"
            scaffold.scaffold(spec, out)
            report = validate.validate(out)
            self.assertTrue(report.passed(), report.failures)


if __name__ == "__main__":
    unittest.main()

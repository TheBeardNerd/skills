import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"


def run_script(name: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPTS_DIR / name), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


class SessionHandoffScriptTests(unittest.TestCase):
    def test_create_handoff_creates_ai_handoffs_and_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = run_script("create_handoff.py", "auth-fix", cwd=project)
            self.assertEqual(result.returncode, 0, result.stderr)
            handoff_dir = project / ".ai" / "handoffs"
            files = list(handoff_dir.glob("*.md"))
            self.assertEqual(len(files), 1)
            self.assertIn("Current State Summary", files[0].read_text())

    def test_list_handoffs_sorts_newest_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            handoff_dir = project / ".ai" / "handoffs"
            handoff_dir.mkdir(parents=True)
            older = handoff_dir / "2026-04-20-090000-old.md"
            newer = handoff_dir / "2026-04-21-090000-new.md"
            older.write_text("# old\n")
            newer.write_text("# new\n")
            result = run_script("list_handoffs.py", cwd=project)
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            self.assertGreaterEqual(len(lines), 2)
            self.assertEqual(lines[:2], [newer.name, older.name])

    def test_validate_handoff_rejects_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            handoff = Path(tmp) / "bad.md"
            handoff.write_text("# Handoff\n\n[TODO: fill me]\n")
            result = run_script("validate_handoff.py", str(handoff))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("placeholder", (result.stdout + result.stderr).lower())

    def test_check_staleness_flags_missing_referenced_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            handoff = project / "sample.md"
            handoff.write_text(
                textwrap.dedent(
                    """\
                    # Handoff

                    ## Critical Files
                    - `src/missing.ts`: important file
                    """
                )
            )
            result = run_script("check_staleness.py", str(handoff), cwd=project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("STALE", result.stdout)
            self.assertIn("src/missing.ts", result.stdout)

    def test_check_staleness_ignores_backticks_outside_critical_files_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "README.md").write_text("ok\n")
            handoff = project / "sample.md"
            handoff.write_text(
                textwrap.dedent(
                    """\
                    # Handoff

                    ## Current State Summary
                    Run `npm test` before shipping.

                    ## Critical Files
                    - `README.md`: overview
                    """
                )
            )
            result = run_script("check_staleness.py", str(handoff), cwd=project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("FRESH", result.stdout)
            self.assertNotIn("STALE", result.stdout)

    def test_check_staleness_fail_on_stale_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            handoff = project / "sample.md"
            handoff.write_text(
                textwrap.dedent(
                    """\
                    # Handoff

                    ## Critical Files
                    - `src/missing.ts`: important file
                    """
                )
            )
            result = run_script("check_staleness.py", "--fail-on-stale", str(handoff), cwd=project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("STALE", result.stdout)

    def test_check_staleness_blocks_absolute_paths_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            handoff = project / "sample.md"
            handoff.write_text(
                textwrap.dedent(
                    """\
                    # Handoff

                    ## Critical Files
                    - `/etc/hosts`: system file
                    """
                )
            )
            result = run_script("check_staleness.py", str(handoff), cwd=project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("BLOCKED", result.stdout)
            self.assertIn("/etc/hosts", result.stdout)

    def test_check_staleness_can_opt_in_to_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            handoff = project / "sample.md"
            handoff.write_text(
                textwrap.dedent(
                    """\
                    # Handoff

                    ## Critical Files
                    - `/definitely-not-real-xyz`: system file
                    """
                )
            )
            result = run_script("check_staleness.py", "--allow-absolute-paths", str(handoff), cwd=project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("STALE", result.stdout)
            self.assertIn("/definitely-not-real-xyz", result.stdout)

    def test_validate_handoff_accepts_complete_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            handoff = Path(tmp) / "good.md"
            handoff.write_text(
                textwrap.dedent(
                    """\
                    # Handoff

                    ## Current State Summary
                    Ready to resume.

                    ## Important Context
                    Uses project-local handoffs.

                    ## Immediate Next Steps
                    1. Run the tests.

                    ## Decisions Made
                    - Store files in `.ai/handoffs/`.

                    ## Critical Files
                    - `README.md`: overview
                    """
                )
            )
            result = run_script("validate_handoff.py", str(handoff))
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_validate_handoff_rejects_subheadings_for_required_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            handoff = Path(tmp) / "bad-levels.md"
            handoff.write_text(
                textwrap.dedent(
                    """\
                    # Handoff

                    ### Current State Summary
                    Ready to resume.

                    ### Important Context
                    Uses project-local handoffs.

                    ### Immediate Next Steps
                    1. Run the tests.

                    ### Decisions Made
                    - Store files in `.ai/handoffs/`.

                    ### Critical Files
                    - `README.md`: overview
                    """
                )
            )
            result = run_script("validate_handoff.py", str(handoff))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing required section", result.stdout)

    def test_validate_handoff_rejects_section_name_only_in_body_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            handoff = Path(tmp) / "bad-body-text.md"
            handoff.write_text(
                textwrap.dedent(
                    """\
                    # Handoff

                    ## Summary
                    The phrase ## Current State Summary appears here, but not as a real heading.

                    ## Important Context
                    Uses project-local handoffs.

                    ## Immediate Next Steps
                    1. Run the tests.

                    ## Decisions Made
                    - Store files in `.ai/handoffs/`.

                    ## Critical Files
                    - `README.md`: overview
                    """
                )
            )
            result = run_script("validate_handoff.py", str(handoff))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing required section", result.stdout)

    def test_create_handoff_succeeds_without_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = run_script("create_handoff.py", "nogit", cwd=project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(".ai/handoffs", result.stdout)


if __name__ == "__main__":
    unittest.main()

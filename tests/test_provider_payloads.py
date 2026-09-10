"""Direct provider-render checks for provider-sensitive public skills."""

from pathlib import Path
import re
import sys
import unittest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lib.provider_blocks import render_for_provider  # noqa: E402


TAG = re.compile(r"\[/?(?:SHARED|PROVIDER:[A-Z]+)\]")


def render(relative, provider):
    text = (REPO / relative).read_text(encoding="utf-8")
    output = render_for_provider(text, provider)
    assert not TAG.search(output)
    return output


class OrchestratorPayloadTests(unittest.TestCase):
    def test_stance_is_coherent_for_every_provider(self):
        path = "skills/orchestrator-posture/references/stance.md"
        phrases = {
            "claude": "Prefer gpt-5.6-sol direct exec",
            "codex": "Run bounded work in child codex sessions",
            "gemini": "host's supported child-agent or isolated-session mechanism",
        }
        for provider, expected in phrases.items():
            with self.subTest(provider=provider):
                output = render(path, provider)
                self.assertIn(expected, output)
                self.assertIn("A lane's \"done\" is not delivery", output)
                for other, excluded in phrases.items():
                    if other != provider:
                        self.assertNotIn(excluded, output)
        gemini = render(path, "gemini")
        self.assertNotIn("codex write-back lanes reject", gemini.lower())
        self.assertNotIn("Fable allowance", gemini)
        self.assertNotIn("GPT allowance", gemini)
        self.assertIn("capacity, rate-limit, quota, or usage", gemini)

    def test_gemini_entrypoint_has_explicit_recorder_fallback(self):
        output = render("skills/orchestrator-posture/SKILL.md", "gemini")
        self.assertIn("There is no automatic Stop-hook collector for Gemini", output)
        self.assertIn("--session <id>", output)
        self.assertNotIn("dispatch bounded work to child `codex exec` sessions", output)


class GovernancePayloadTests(unittest.TestCase):
    def test_each_provider_keeps_range_and_proposal_contracts(self):
        path = "skills/governance-read-access/SKILL.md"
        for provider in ("claude", "codex", "gemini"):
            with self.subTest(provider=provider):
                output = render(path, provider)
                self.assertIn("projection, then ranged read", output)
                self.assertIn("request_type: GOVERNANCE_UPDATE_REQUEST", output)
                self.assertIn("A request is a proposal, never a commitment", output)

        claude = render(path, "claude")
        self.assertIn("Read(offset=M, limit=<count>)", claude)
        self.assertIn("Route Governance Requests", claude)
        self.assertNotIn("Gemini Boundary", claude)

        codex = render(path, "codex")
        self.assertIn("sed -n 'M,Np'", codex)
        self.assertIn("Codex Boundary: Read Only", codex)
        self.assertNotIn("Gemini Boundary", codex)

        gemini = render(path, "gemini")
        self.assertIn("sed -n 'M,Np'", gemini)
        self.assertIn("Gemini Boundary: Read and Propose Only", gemini)
        self.assertIn("configured applier", gemini)
        self.assertNotIn("Codex Boundary", gemini)
        self.assertNotIn("dr_gate", gemini)
        self.assertNotIn("permanently rejected", gemini)


if __name__ == "__main__":
    unittest.main()

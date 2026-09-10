"""Run the real installer in temporary provider directories: python3 tests/test_install.py."""

import hashlib
import json
import re
import shutil
from pathlib import Path
import subprocess
import tempfile


REPO = Path(__file__).resolve().parents[1]


def run(target, *args):
    result = subprocess.run(
        ["bash", str(REPO / "install.sh"), f"--target={target}", *args],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def snapshot(root):
    return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file()}


def main():
    sources = snapshot(REPO / "skills")
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary) / "providers"
        providers = ("claude", "codex", "gemini")
        flags = [f"--create-provider={p}" for p in providers]
        run(target)
        assert not target.exists(), "providers must opt in"
        run(target, "--dry-run", *flags)
        assert not target.exists(), "dry run wrote targets"
        run(target, *flags)
        count = 0
        for provider in providers:
            for source in sorted((REPO / "skills").iterdir()):
                if not source.is_dir():
                    continue
                installed = target / provider / source.name
                skill = (installed / "SKILL.md").read_bytes()
                metadata = json.loads((installed / "VERSION.json").read_bytes())
                expected = json.loads((source / "VERSION.json").read_bytes())
                expected["content_hash_sha256"] = hashlib.sha256(skill).hexdigest()
                assert metadata == expected, f"installed metadata mismatch: {provider}/{source.name}"
                source_hash = hashlib.sha256((source / "SKILL.md").read_bytes()).hexdigest()
                assert f"sha256:{source_hash}".encode() in skill
                assert f"Target provider: {provider}".encode() in skill
                assert skill.startswith(b"---\n")
                assert b"[PROVIDER:" not in skill and b"[/PROVIDER:" not in skill
                assert not (installed / "REFRESH.md").exists()
                assert not (installed / "_archive").exists()
                for asset in source.rglob("*"):
                    relative = asset.relative_to(source)
                    if not asset.is_file() or any(part in ("_archive", "__pycache__", ".pytest_cache", ".git") for part in relative.parts):
                        continue
                    if asset.name in ("SKILL.md", "REFRESH.md", ".DS_Store") or asset.suffix == ".pyc" or relative == Path("VERSION.json"):
                        continue
                    output = (installed / relative).read_bytes()
                    tagged = asset.suffix == ".md" and re.search(br"\[(?:/?PROVIDER:|/?SHARED\]|(?:CLAUDE|CODEX|GEMINI)\]\[CRITICAL\])", asset.read_bytes())
                    if tagged:
                        assert b"[PROVIDER:" not in output and b"[/PROVIDER:" not in output
                        assert f"Target provider: {provider}".encode() in output
                        assert hashlib.sha256(asset.read_bytes()).hexdigest().encode() in output
                    else:
                        assert output == asset.read_bytes(), f"asset changed: {provider}/{source.name}/{relative}"
                count += 1
        before = snapshot(target)
        run(target, *flags)
        assert snapshot(target) == before, "repeat install changed bytes or mtimes"
        assert snapshot(REPO / "skills") == sources, "canonical sources changed"
        fixture_repo = Path(temporary) / "fixture-repo"
        fixture_repo.mkdir()
        for file in ("install.sh", "publish-skill.py"):
            shutil.copy2(REPO / file, fixture_repo / file)
        shutil.copytree(REPO / "lib", fixture_repo / "lib")
        fixture = fixture_repo / "skills/demo"
        fixture.mkdir(parents=True)
        (fixture / "SKILL.md").write_text("---\nname: demo\n---\nShared skill\n")
        for index, bad in enumerate(("[provider:claude]hidden[/provider:claude]", "[ PROVIDER:CLAUDE ]hidden", "[PROVIDER:UNKNOWN]hidden")):
            (fixture / "bad.md").write_text(bad)
            bad_target = Path(temporary) / f"invalid-{index}"
            result = subprocess.run(["bash", str(fixture_repo / "install.sh"), f"--target={bad_target}", "--create-provider=claude"], capture_output=True, text=True)
            assert result.returncode != 0, "malformed supporting tags were accepted"
            assert not (bad_target / "claude/demo/bad.md").exists()
        print(f"PASS: {count} skill/provider installs; hashes, provenance, source preservation, opt-in, dry-run and idempotence")


if __name__ == "__main__":
    main()

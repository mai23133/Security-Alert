"""Verify the current source in a fresh temporary Python 3.11 environment.

This copies the reviewable working tree, including uncommitted implementation,
not .env, .git, an existing virtualenv, or generated KB. No deployment occurs.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError("Clean acceptance requires Python 3.11")
    target = Path(tempfile.mkdtemp(prefix="security-alert-clean-"))
    print(f"Clean verification directory: {target}", flush=True)
    for name in ("src", "eval", "tests", "prompts", "ui", "data/raw", "data/eval", "data/dev", "data/subset"):
        shutil.copytree(ROOT / name, target / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("requirements.txt", "requirements.lock"):
        shutil.copy2(ROOT / name, target / name)
    subprocess.run([sys.executable, "-m", "venv", str(target / ".venv")], check=True)
    python = str(target / ".venv/bin/python")
    env = {**os.environ, "GOOGLE_API_KEY":"", "GEMINI_API_KEY":"", "PROVIDER_CONSENT":"",
           "APP_ENV":"sandbox", "SECURITY_ALERT_API_KEY":""}
    env.pop("PYTHONPATH", None)
    commands = [
        ("install", [python, "-m", "pip", "install", "-r", "requirements.lock"]),
        ("dependency_check", [python, "-m", "pip", "check"]),
        ("ingestion", [python, "-m", "src.rag.ingest_stix"]),
        ("tests", [python, "-m", "pytest", "-q"]),
        ("fixture", [python, "-m", "eval.run_eval", "--mode", "fixture", "--subset", "full"]),
        ("development", [python, "-m", "eval.run_eval", "--mode", "runtime", "--development", "--require-quality-gates"]),
        ("runtime_quality", [python, "-m", "eval.run_eval", "--mode", "runtime", "--subset", "full", "--require-quality-gates"]),
    ]
    results = {}
    for name, command in commands:
        result = subprocess.run(command, cwd=target, env=env, text=True, capture_output=True, timeout=240)
        results[name] = {"exit_code": result.returncode}
        # These commands process bundled synthetic data only. Retain aggregate
        # outputs for verification in /tmp, never production alert narratives.
        (target / f"{name}.log").write_text(result.stdout + result.stderr)
        print(f"{name}: exit {result.returncode}", flush=True)
        if result.returncode and name != "runtime_quality":
            break
    report = {"source_kind":"working_tree_copy_without_generated_data", "python":sys.version.split()[0],
              "provider_mode":"disabled", "results":results, "directory":str(target)}
    output = ROOT / "docs/reports/clean-verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return int(len(results) != len(commands) or any(r["exit_code"] for r in results.values()))


if __name__ == "__main__":
    raise SystemExit(main())

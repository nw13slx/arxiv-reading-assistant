#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# ArXiv Reading Assistant
# Copyright (C) 2026 nw13slx
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DISCLAIMER: This code was generated with assistance from GitHub Copilot
# (Claude Opus 4.5, February 2026). The authors make no warranties regarding
# accuracy or reliability. AI-generated code may contain errors or biases.
# USE AT YOUR OWN RISK.
#
# See LICENSE file for full terms.
# -----------------------------------------------------------------------------

"""
Staging Skill - Privacy scan, update docs, and commit.

Usage:
    python stage_commit.py [--message "commit message"] [--dry-run]

Workflow:
    1. Run privacy scan (abort if HIGH severity issues)
    2. Auto-update README.md with current state
    3. Auto-update skill docs if needed
    4. Show diff and prompt for commit
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_command(cmd: list, capture: bool = True) -> tuple[int, str]:
    """Run a command and return exit code and output."""
    result = subprocess.run(cmd, capture_output=capture, text=True)
    output = result.stdout + result.stderr if capture else ""
    return result.returncode, output


def run_privacy_scan(repo_dir: Path) -> bool:
    """Run privacy scan and return True if passed."""
    print("=" * 60)
    print("Step 1: Privacy Scan")
    print("=" * 60)
    
    script = repo_dir / "scripts" / "privacy_scan.py"
    code, output = run_command([sys.executable, str(script), str(repo_dir)])
    print(output)
    
    if code != 0:
        print("❌ Privacy scan failed with HIGH severity issues!")
        print("   Fix the issues above before staging.")
        return False
    
    print("✅ Privacy scan passed\n")
    return True


def get_repo_stats(repo_dir: Path) -> dict:
    """Gather repository statistics."""
    stats = {
        'scripts': [],
        'skills': [],
        'tests': 0,
        'papers': [],
    }
    
    # Count scripts
    scripts_dir = repo_dir / "scripts"
    if scripts_dir.exists():
        for py in scripts_dir.glob("*.py"):
            stats['scripts'].append(py.stem)
    
    # Count skills
    skills_dir = repo_dir / "skills"
    if skills_dir.exists():
        for md in skills_dir.glob("*.md"):
            stats['skills'].append(md.stem)
    
    # Count tests
    test_file = repo_dir / "tests" / "test_parsing.py"
    if test_file.exists():
        content = test_file.read_text()
        stats['tests'] = content.count("def test_")
    
    # Check for papers (in data repo or local)
    papers_dir = repo_dir / "papers"
    if papers_dir.exists():
        for paper in papers_dir.iterdir():
            if paper.is_dir() and (paper / "index.json").exists():
                index = json.loads((paper / "index.json").read_text())
                stats['papers'].append({
                    'id': index['paper_id'],
                    'sections': index['summary']['total_sections'],
                })
    
    return stats


def generate_readme_content(repo_dir: Path, stats: dict) -> str:
    """Generate updated README content."""
    skills_list = "\n".join(f"- `/{s}` - See [skills/{s}.md](skills/{s}.md)" 
                           for s in sorted(stats['skills']))
    
    scripts_list = "\n".join(f"- `{s}.py`" for s in sorted(stats['scripts']))
    
    content = f"""# ArXiv Reading Assistant

A focused reading workflow for ML/AI papers, tailored for a physicist's intuition.

## Quick Start

```bash
# Initialize a paper
python -m skills.paper_init 2510.21890

# Or use the full pipeline
python scripts/process_paper.py <arxiv_id>
```

## Configuration

Set the data directory (defaults to `./papers` in current directory):
```bash
export ARXIV_DATA_DIR=/path/to/arxiv-reading-data/papers
```

Or create symlinks:
```bash
ln -s /path/to/arxiv-reading-data/papers papers
ln -s /path/to/arxiv-reading-data/notes notes
ln -s /path/to/arxiv-reading-data/sessions sessions
```

## Structure

```
papers/          # (symlink to data repo)
notes/           # (symlink to data repo)
sessions/        # (symlink to data repo)
scripts/         # Processing scripts
skills/          # Reusable skills for Copilot
tests/           # Unit tests ({stats['tests']} tests)
```

## Skills

{skills_list}

## Scripts

{scripts_list}

## Workflow

1. **Start a session**: Begin each day fresh
2. **Load a paper**: Use `/paper-init <arxiv_id>` to prepare a paper
3. **Read together**: Copilot keeps you focused, explains CS/ML in physics terms
4. **Save notes**: Key insights saved to `notes/paper-id.notes.md`

## Copilot's Role

- **Focus**: Guide you section-by-section, flag what matters
- **Translate**: Map ML concepts → physics analogies (stat mech, optimization landscapes, etc.)
- **Summarize**: Compress insights into notes for future reference

## Quick Commands

- "Let's read [paper-id]" - Start/resume a paper
- "Show me the index" - See paper structure
- "Explain this like I'm a physicist" - Get physics-friendly explanation
- "What's the key idea?" - TL;DR of current section
- "Save this insight" - Add to paper notes

## Running Tests

```bash
python -m pytest tests/ -v
```

## Pre-Push Privacy Check

```bash
# Manual scan
python scripts/privacy_scan.py .

# Or install hook
cp scripts/hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

---
*Last updated: {datetime.now().strftime('%Y-%m-%d')}*
"""
    return content


def check_readme_current(repo_dir: Path) -> list[str]:
    """Check if README.md reflects current repo state. Returns list of issues."""
    readme_path = repo_dir / "README.md"
    if not readme_path.exists():
        return ["README.md does not exist"]
    
    content = readme_path.read_text()
    issues = []
    
    # Check skills are documented
    skills_dir = repo_dir / "skills"
    if skills_dir.exists():
        for md in skills_dir.glob("*.md"):
            skill_name = md.stem
            # Check if skill is mentioned in README
            if f"/{skill_name}" not in content and skill_name not in content:
                issues.append(f"Skill /{skill_name} not documented in README")
    
    # Check scripts are mentioned (at least the main ones)
    scripts_dir = repo_dir / "scripts"
    key_scripts = ['paper_init', 'privacy_scan', 'process_paper']
    if scripts_dir.exists():
        for script in key_scripts:
            if (scripts_dir / f"{script}.py").exists():
                if script not in content and script.replace('_', '-') not in content:
                    issues.append(f"Script {script}.py not mentioned in README")
    
    return issues


def update_readme(repo_dir: Path, dry_run: bool = False) -> bool:
    """Check README.md is current and optionally update stats."""
    print("=" * 60)
    print("Step 2: Check Documentation")
    print("=" * 60)
    
    # First check if README reflects current state
    issues = check_readme_current(repo_dir)
    if issues:
        print("  ⚠️  README.md may be outdated:")
        for issue in issues:
            print(f"     - {issue}")
        print("  Consider updating README.md manually to document new features.")
    else:
        print("  ✅ README.md appears current")
    
    stats = get_repo_stats(repo_dir)
    print(f"  Scripts: {len(stats['scripts'])}")
    print(f"  Skills: {len(stats['skills'])}")
    print(f"  Tests: {stats['tests']}")
    
    return len(issues) > 0


def show_staged_changes(repo_dir: Path):
    """Show what will be committed."""
    print("\n" + "=" * 60)
    print("Step 3: Review Changes")
    print("=" * 60)
    
    # Stage all changes
    run_command(["git", "-C", str(repo_dir), "add", "-A"])
    
    # Show status
    code, output = run_command(["git", "-C", str(repo_dir), "status", "--short"])
    
    if not output.strip():
        print("  No changes to commit")
        return False
    
    print("  Changes to be committed:")
    for line in output.strip().split('\n'):
        print(f"    {line}")
    
    return True


def do_commit(repo_dir: Path, message: str) -> bool:
    """Perform the commit."""
    print("\n" + "=" * 60)
    print("Step 4: Commit")
    print("=" * 60)
    
    code, output = run_command([
        "git", "-C", str(repo_dir), 
        "commit", "-m", message
    ])
    
    if code == 0:
        print(f"  ✅ Committed: {message}")
        # Show commit hash
        code, hash_out = run_command([
            "git", "-C", str(repo_dir), 
            "log", "--oneline", "-1"
        ])
        print(f"  {hash_out.strip()}")
        return True
    else:
        print(f"  ❌ Commit failed: {output}")
        return False


def do_amend(repo_dir: Path) -> bool:
    """Amend the previous commit."""
    print("\n" + "=" * 60)
    print("Step 4: Amend Commit")
    print("=" * 60)
    
    code, output = run_command([
        "git", "-C", str(repo_dir), 
        "commit", "--amend", "--no-edit"
    ])
    
    if code == 0:
        print("  ✅ Amended previous commit")
        code, hash_out = run_command([
            "git", "-C", str(repo_dir), 
            "log", "--oneline", "-1"
        ])
        print(f"  {hash_out.strip()}")
        return True
    else:
        print(f"  ❌ Amend failed: {output}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Stage and commit with checks')
    parser.add_argument('--message', '-m', default=None,
                        help='Commit message (default: auto-generate)')
    parser.add_argument('--amend', '-a', action='store_true',
                        help='Amend previous commit instead of new commit')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--skip-privacy', action='store_true',
                        help='Skip privacy scan (not recommended)')
    parser.add_argument('--skip-docs', action='store_true',
                        help='Skip documentation update')
    parser.add_argument('directory', nargs='?', default='.',
                        help='Repository directory (default: current)')
    args = parser.parse_args()
    
    repo_dir = Path(args.directory).resolve()
    
    print(f"\n🚀 Staging: {repo_dir}\n")
    
    # Step 1: Privacy scan
    if not args.skip_privacy:
        if not run_privacy_scan(repo_dir):
            sys.exit(1)
    
    # Step 2: Update docs
    if not args.skip_docs:
        update_readme(repo_dir, dry_run=args.dry_run)
    
    # Step 3: Show changes
    if args.dry_run:
        print("\n[DRY RUN] Would stage and show changes")
        sys.exit(0)
    
    has_changes = show_staged_changes(repo_dir)
    
    if not has_changes:
        print("\n✅ Nothing to commit, working tree clean")
        sys.exit(0)
    
    # Step 4: Commit or amend
    if args.amend:
        do_amend(repo_dir)
    else:
        message = args.message or f"Update {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        do_commit(repo_dir, message)
    
    print("\n✅ Done!")


if __name__ == '__main__':
    main()

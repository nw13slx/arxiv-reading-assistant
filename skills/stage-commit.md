# Stage Commit Skill

Automated staging workflow: privacy scan → check docs → commit.

## Usage

```
/stage-commit [--message "msg"] [--amend]
```

## What It Does

1. **Privacy Scan** - Checks for sensitive info (HOME, USER, emails, keys)
   - Aborts if HIGH severity issues found
   
2. **Check Docs** - Verifies README.md is current:
   - All skills documented
   - Key scripts mentioned
   - Warns if outdated (does not auto-update)
   
3. **Review Changes** - Shows staged files

4. **Commit** - Creates commit (or amends previous)

## Examples

```bash
# Full workflow with new commit
python scripts/stage_commit.py -m "Add new feature"

# Amend previous commit (squash changes)
python scripts/stage_commit.py --amend

# Dry run - see what would happen
python scripts/stage_commit.py --dry-run

# Skip privacy scan (not recommended)
python scripts/stage_commit.py --skip-privacy -m "Quick fix"

# Skip doc check
python scripts/stage_commit.py --skip-docs -m "Code only change"
```

## Workflow Integration

Before pushing to GitHub:
```bash
# Stage and commit
python scripts/stage_commit.py -m "Ready for release"

# Push
git push origin main
```

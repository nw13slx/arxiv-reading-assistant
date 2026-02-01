# Stage Commit Skill

Automated staging workflow: privacy scan → update docs → commit.

## Usage

```
/stage-commit [--message "msg"] [--amend]
```

## What It Does

1. **Privacy Scan** - Checks for sensitive info (HOME, USER, emails, keys)
   - Aborts if HIGH severity issues found
   
2. **Update Docs** - Auto-updates README.md with:
   - Current list of scripts
   - Current list of skills
   - Test count
   - Last updated date
   
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

# Skip doc updates
python scripts/stage_commit.py --skip-docs -m "Code only change"
```

## Workflow Integration

Before pushing to GitHub:
```bash
# Stage and commit
python scripts/stage_commit.py -m "Ready for release"

# Final privacy check
python scripts/privacy_scan.py .

# Push
git push origin master
```

## For Squashing History

When preparing for initial push:
```bash
# Make changes...
python scripts/stage_commit.py --amend

# Repeat until satisfied, then push
git push -u origin master
```

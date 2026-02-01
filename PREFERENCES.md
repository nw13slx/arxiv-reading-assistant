# Project Preferences

Settings and conventions for this project.

## Git

- **Default branch**: `main` (not master)
- **Author**: `nw13slx <nw13slx@users.noreply.github.com>`
- **Remote host**: `github.com-personal` (uses personal SSH key)

## Before Creating New Repos

```bash
# Set local config (not global - don't affect work repos)
git config --local user.name "nw13slx"
git config --local user.email "nw13slx@users.noreply.github.com"

# Rename branch to main
git branch -m master main

# Use personal SSH host
git remote add origin git@github.com-personal:nw13slx/<repo>.git
```

## Privacy

- Always run privacy scan before pushing
- Never commit paths containing $HOME or $USER
- Use `nw13slx@users.noreply.github.com` (not real email)

## Data Separation

- `arxiv-reading-assistant` - Public tools repo
- `arxiv-reading-data` - Private data repo (papers, notes, sessions)

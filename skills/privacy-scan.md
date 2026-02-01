# Privacy Scan Skill

Scan repositories for sensitive information before publishing.

## Usage

```
/privacy-scan [directory]
```

## Quick Check Before Push

```bash
# Scan current repo
python scripts/privacy_scan.py .

# If clean, push
git push
```

## Install Pre-Push Hook

```bash
cp scripts/hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

This automatically scans before every push.

## What It Detects

### High Severity (blocks push)
- **HOME_PATH**: Your home directory path (e.g., `/home/username`)
- **HOME_USERNAME**: Username from home path
- **USER_ENV**: USER environment variable value
- **USERNAME_PART**: Username portion of email-style USER
- **EMAIL_CORPORATE**: Corporate email addresses (@microsoft.com, @google.com, etc.)
- **API_KEY**: API keys and secrets
- **AWS_KEY**: AWS access key IDs
- **PRIVATE_KEY**: SSH/RSA private key headers

### Medium Severity (warning only)
- **EMAIL_ANY**: Any email address
- **ABSOLUTE_PATH_UNIX**: Unix paths with usernames
- **WINDOWS_PATH**: Windows user paths

### Low Severity (info only)
- **IP_ADDRESS**: Private IP addresses

## Examples

```bash
# Scan with verbose output
python scripts/privacy_scan.py . -v

# Scan data repo
python scripts/privacy_scan.py ../arxiv-reading-data -v

# Generate JSON report
python scripts/privacy_scan.py . --report privacy_report.json

# Exclude certain patterns
python scripts/privacy_scan.py . -e "papers/.*" -e ".*\.log"
```

## Custom Patterns

Create `privacy_config.json`:
```json
{
  "patterns": [
    {
      "name": "CUSTOM_SECRET",
      "pattern": "my-secret-prefix-[a-z0-9]+",
      "description": "Custom secret pattern",
      "severity": "high"
    }
  ]
}
```

Run with:
```bash
python scripts/privacy_scan.py . --config privacy_config.json
```

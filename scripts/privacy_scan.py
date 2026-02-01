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
Privacy Scanner - Scan files for sensitive information before publishing.

Usage:
    python privacy_scan.py <directory> [--fix] [--config config.json]

Example:
    python privacy_scan.py ../arxiv-reading-assistant
    python privacy_scan.py ../arxiv-reading-data --fix
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SensitivePattern:
    """A pattern to detect sensitive information."""
    name: str
    pattern: str  # regex
    description: str
    severity: str = "high"  # high, medium, low
    replacement: Optional[str] = None  # for auto-fix


@dataclass 
class Finding:
    """A detected sensitive item."""
    file: str
    line_no: int
    line: str
    pattern_name: str
    match: str
    severity: str


def get_default_patterns() -> list[SensitivePattern]:
    """Get default sensitive patterns based on environment."""
    patterns = []
    
    # Environment-based patterns
    home = os.environ.get('HOME', '')
    user = os.environ.get('USER', '')
    
    if home:
        # Full home path
        patterns.append(SensitivePattern(
            name="HOME_PATH",
            pattern=re.escape(home),
            description="Home directory path",
            severity="high",
            replacement="/home/$USER"
        ))
        # Just the username from home (e.g., /home/johndoe -> johndoe)
        home_user = Path(home).name
        if home_user and len(home_user) > 2:
            patterns.append(SensitivePattern(
                name="HOME_USERNAME",
                pattern=rf'\b{re.escape(home_user)}\b',
                description="Username from HOME path",
                severity="high",
                replacement="$USER"
            ))
    
    if user:
        # Full USER value (might include domain like johndoe@company.com)
        patterns.append(SensitivePattern(
            name="USER_ENV",
            pattern=re.escape(user),
            description="USER environment variable",
            severity="high",
            replacement="$USER"
        ))
        # Just username part if it contains @
        if '@' in user:
            username_part = user.split('@')[0]
            if len(username_part) > 2:
                patterns.append(SensitivePattern(
                    name="USERNAME_PART",
                    pattern=rf'\b{re.escape(username_part)}\b',
                    description="Username part of USER env",
                    severity="high",
                    replacement="$USER"
                ))
    
    # Common sensitive patterns
    patterns.extend([
        SensitivePattern(
            name="EMAIL_CORPORATE",
            pattern=r'\b[a-zA-Z0-9._%+-]+@(microsoft|google|amazon|apple|meta|facebook)\.com\b',
            description="Corporate email address",
            severity="high",
            replacement="user@example.com"
        ),
        SensitivePattern(
            name="EMAIL_ANY",
            pattern=r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
            description="Email address",
            severity="medium",
            replacement="user@example.com"
        ),
        SensitivePattern(
            name="API_KEY",
            pattern=r'(?i)(api[_-]?key|apikey|secret[_-]?key|auth[_-]?token)\s*[=:]\s*["\']?[a-zA-Z0-9_-]{20,}["\']?',
            description="Potential API key or secret",
            severity="high",
        ),
        SensitivePattern(
            name="AWS_KEY",
            pattern=r'AKIA[0-9A-Z]{16}',
            description="AWS Access Key ID",
            severity="high",
        ),
        SensitivePattern(
            name="PRIVATE_KEY",
            pattern=r'-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----',
            description="Private key header",
            severity="high",
        ),
        SensitivePattern(
            name="IP_ADDRESS",
            pattern=r'\b(?:10\.|172\.(?:1[6-9]|2[0-9]|3[01])\.|192\.168\.)\d{1,3}\.\d{1,3}\b',
            description="Private IP address",
            severity="low",
        ),
        SensitivePattern(
            name="ABSOLUTE_PATH_UNIX",
            pattern=r'/(?:home|Users|data|datadisk)/[a-zA-Z0-9_.-]+/',
            description="Absolute path with username",
            severity="medium",
        ),
        SensitivePattern(
            name="WINDOWS_PATH",
            pattern=r'[Cc]:\\Users\\[a-zA-Z0-9_.-]+\\',
            description="Windows user path",
            severity="medium",
        ),
    ])
    
    return patterns


def should_scan_file(path: Path) -> bool:
    """Check if file should be scanned."""
    # Skip binary and large files
    skip_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx',
        '.zip', '.tar', '.gz', '.bz2', '.7z',
        '.pyc', '.pyo', '.so', '.dll', '.exe',
        '.mp3', '.mp4', '.avi', '.mov', '.wav',
        '.ttf', '.woff', '.woff2', '.eot',
    }
    
    if path.suffix.lower() in skip_extensions:
        return False
    
    # Skip hidden and common non-text directories
    skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.pytest_cache'}
    if any(part in skip_dirs for part in path.parts):
        return False
    
    # Check file size (skip > 1MB)
    try:
        if path.stat().st_size > 1_000_000:
            return False
    except:
        return False
    
    return True


def scan_file(path: Path, patterns: list[SensitivePattern]) -> list[Finding]:
    """Scan a single file for sensitive patterns."""
    findings = []
    
    try:
        content = path.read_text(errors='replace')
    except Exception as e:
        return findings
    
    lines = content.split('\n')
    
    for pattern in patterns:
        regex = re.compile(pattern.pattern, re.IGNORECASE if pattern.name.startswith('EMAIL') else 0)
        
        for line_no, line in enumerate(lines, 1):
            for match in regex.finditer(line):
                findings.append(Finding(
                    file=str(path),
                    line_no=line_no,
                    line=line.strip()[:100],  # Truncate long lines
                    pattern_name=pattern.name,
                    match=match.group()[:50],  # Truncate long matches
                    severity=pattern.severity,
                ))
    
    return findings


def scan_directory(directory: Path, patterns: list[SensitivePattern], 
                   exclude_patterns: list[str] = None) -> list[Finding]:
    """Scan all files in directory."""
    findings = []
    exclude_patterns = exclude_patterns or []
    
    for path in directory.rglob('*'):
        if not path.is_file():
            continue
        
        # Check exclusions
        rel_path = str(path.relative_to(directory))
        if any(re.match(ep, rel_path) for ep in exclude_patterns):
            continue
        
        if not should_scan_file(path):
            continue
        
        findings.extend(scan_file(path, patterns))
    
    return findings


def print_findings(findings: list[Finding], verbose: bool = False):
    """Print findings in a readable format."""
    if not findings:
        print("✅ No sensitive information found!")
        return
    
    # Group by severity
    by_severity = {'high': [], 'medium': [], 'low': []}
    for f in findings:
        by_severity[f.severity].append(f)
    
    print(f"\n⚠️  Found {len(findings)} potential issues:\n")
    
    for severity in ['high', 'medium', 'low']:
        items = by_severity[severity]
        if not items:
            continue
        
        icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[severity]
        print(f"{icon} {severity.upper()} ({len(items)} items):")
        
        # Group by pattern
        by_pattern = {}
        for f in items:
            if f.pattern_name not in by_pattern:
                by_pattern[f.pattern_name] = []
            by_pattern[f.pattern_name].append(f)
        
        for pattern_name, pattern_findings in by_pattern.items():
            print(f"   {pattern_name}: {len(pattern_findings)} occurrences")
            if verbose:
                for f in pattern_findings[:3]:  # Show first 3
                    print(f"      {f.file}:{f.line_no} - '{f.match}'")
                if len(pattern_findings) > 3:
                    print(f"      ... and {len(pattern_findings) - 3} more")
        print()


def save_report(findings: list[Finding], output_path: Path):
    """Save findings to JSON report."""
    report = {
        'total_findings': len(findings),
        'by_severity': {
            'high': len([f for f in findings if f.severity == 'high']),
            'medium': len([f for f in findings if f.severity == 'medium']),
            'low': len([f for f in findings if f.severity == 'low']),
        },
        'findings': [
            {
                'file': f.file,
                'line_no': f.line_no,
                'pattern': f.pattern_name,
                'match': f.match,
                'severity': f.severity,
            }
            for f in findings
        ]
    }
    
    output_path.write_text(json.dumps(report, indent=2))
    print(f"📄 Report saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Scan for sensitive information')
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed findings')
    parser.add_argument('--report', '-r', help='Save JSON report to file')
    parser.add_argument('--exclude', '-e', action='append', default=[], 
                        help='Regex patterns to exclude (can be repeated)')
    parser.add_argument('--config', '-c', help='JSON config file with custom patterns')
    args = parser.parse_args()
    
    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist")
        sys.exit(1)
    
    print(f"🔍 Scanning {directory}...")
    
    # Load patterns
    patterns = get_default_patterns()
    
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            custom = json.loads(config_path.read_text())
            for p in custom.get('patterns', []):
                patterns.append(SensitivePattern(**p))
    
    # Scan
    findings = scan_directory(directory, patterns, args.exclude)
    
    # Output
    print_findings(findings, verbose=args.verbose)
    
    if args.report:
        save_report(findings, Path(args.report))
    
    # Exit code based on severity
    high_count = len([f for f in findings if f.severity == 'high'])
    if high_count > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()

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
Session logging for paper reading sessions.

Logs:
- Daily session logs (sessions/YYYY-MM-DD.md)
- Weekly insights: gaps (notes/YYYY-Www-gaps.md) 
- Weekly insights: mastered (notes/YYYY-Www-mastered.md)

Usage:
    python session_logger.py log-session --paper 2510.21890 --section 12 --summary "..."
    python session_logger.py log-gap --concept "score function" --context "..."
    python session_logger.py log-mastered --concept "ELBO" --context "..."
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path


def get_default_data_dir() -> Path:
    """Get default data directory from env or use sibling data repo."""
    if os.environ.get('ARXIV_DATA_DIR'):
        return Path(os.environ['ARXIV_DATA_DIR']).parent  # Go up from papers/
    return Path(__file__).parent.parent.parent / 'arxiv-reading-data'


def get_week_string() -> str:
    """Get ISO week string like 2026-W05."""
    now = datetime.now()
    return now.strftime('%Y-W%W')


def get_date_string() -> str:
    """Get date string like 2026-02-01."""
    return datetime.now().strftime('%Y-%m-%d')


def get_time_string() -> str:
    """Get time string like 14:30."""
    return datetime.now().strftime('%H:%M')


def log_session(paper_id: str, section: str, summary: str, 
                data_dir: Path = None) -> dict:
    """
    Log a reading session to daily log.
    
    Args:
        paper_id: arXiv paper ID
        section: Section identifier
        summary: Session summary
        data_dir: Optional data directory override
    
    Returns:
        dict with log file path
    """
    if data_dir is None:
        data_dir = get_default_data_dir()
    
    sessions_dir = data_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = get_date_string()
    time_str = get_time_string()
    log_file = sessions_dir / f"{date_str}.md"
    
    # Create or append to log
    if log_file.exists():
        content = log_file.read_text()
    else:
        content = f"# Reading Session: {date_str}\n\n"
    
    # Add session entry
    entry = f"""## {time_str} - {paper_id} / {section}

{summary}

---

"""
    
    content += entry
    log_file.write_text(content)
    
    return {"logged": True, "file": str(log_file)}


def log_gap(concept: str, context: str, paper_id: str = None,
            data_dir: Path = None) -> dict:
    """
    Log a concept gap (something not understood).
    
    Args:
        concept: The concept that wasn't understood
        context: Context about why/where it came up
        paper_id: Optional paper ID for reference
        data_dir: Optional data directory override
    
    Returns:
        dict with log file path
    """
    if data_dir is None:
        data_dir = get_default_data_dir()
    
    notes_dir = data_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    
    week_str = get_week_string()
    date_str = get_date_string()
    log_file = notes_dir / f"{week_str}-gaps.md"
    
    # Create or append to log
    if log_file.exists():
        content = log_file.read_text()
    else:
        content = f"# Knowledge Gaps: {week_str}\n\nConcepts to revisit and strengthen.\n\n"
    
    # Add gap entry
    paper_ref = f" ({paper_id})" if paper_id else ""
    entry = f"""### {concept}{paper_ref}
*{date_str}*

{context}

---

"""
    
    content += entry
    log_file.write_text(content)
    
    return {"logged": True, "file": str(log_file)}


def log_mastered(concept: str, insight: str, paper_id: str = None,
                 data_dir: Path = None) -> dict:
    """
    Log a mastered concept (new understanding).
    
    Args:
        concept: The concept that was mastered
        insight: The key insight or understanding gained
        paper_id: Optional paper ID for reference
        data_dir: Optional data directory override
    
    Returns:
        dict with log file path
    """
    if data_dir is None:
        data_dir = get_default_data_dir()
    
    notes_dir = data_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    
    week_str = get_week_string()
    date_str = get_date_string()
    log_file = notes_dir / f"{week_str}-mastered.md"
    
    # Create or append to log
    if log_file.exists():
        content = log_file.read_text()
    else:
        content = f"# Concepts Mastered: {week_str}\n\nNew understandings and insights.\n\n"
    
    # Add mastered entry
    paper_ref = f" ({paper_id})" if paper_id else ""
    entry = f"""### ✓ {concept}{paper_ref}
*{date_str}*

{insight}

---

"""
    
    content += entry
    log_file.write_text(content)
    
    return {"logged": True, "file": str(log_file)}


def get_weekly_summary(week: str = None, data_dir: Path = None) -> dict:
    """
    Get summary of a week's gaps and mastered concepts.
    
    Args:
        week: Week string like "2026-W05" (default: current week)
        data_dir: Optional data directory override
    
    Returns:
        dict with gaps and mastered counts and lists
    """
    if data_dir is None:
        data_dir = get_default_data_dir()
    
    if week is None:
        week = get_week_string()
    
    notes_dir = data_dir / "notes"
    
    gaps_file = notes_dir / f"{week}-gaps.md"
    mastered_file = notes_dir / f"{week}-mastered.md"
    
    result = {
        "week": week,
        "gaps": {"count": 0, "concepts": []},
        "mastered": {"count": 0, "concepts": []},
    }
    
    if gaps_file.exists():
        content = gaps_file.read_text()
        # Count ### headers
        concepts = [line[4:].split('(')[0].strip() 
                   for line in content.split('\n') 
                   if line.startswith('### ') and not line.startswith('### ✓')]
        result["gaps"]["count"] = len(concepts)
        result["gaps"]["concepts"] = concepts
    
    if mastered_file.exists():
        content = mastered_file.read_text()
        concepts = [line[5:].split('(')[0].strip()  # Skip "### ✓ "
                   for line in content.split('\n') 
                   if line.startswith('### ✓')]
        result["mastered"]["count"] = len(concepts)
        result["mastered"]["concepts"] = concepts
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Session logger')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # log-session command
    session_parser = subparsers.add_parser('log-session', help='Log a reading session')
    session_parser.add_argument('--paper', '-p', required=True, help='Paper ID')
    session_parser.add_argument('--section', '-s', required=True, help='Section')
    session_parser.add_argument('--summary', '-m', required=True, help='Summary')
    session_parser.add_argument('--data-dir', '-d', help='Data directory')
    
    # log-gap command
    gap_parser = subparsers.add_parser('log-gap', help='Log a knowledge gap')
    gap_parser.add_argument('--concept', '-c', required=True, help='Concept')
    gap_parser.add_argument('--context', '-x', required=True, help='Context')
    gap_parser.add_argument('--paper', '-p', help='Paper ID')
    gap_parser.add_argument('--data-dir', '-d', help='Data directory')
    
    # log-mastered command
    mastered_parser = subparsers.add_parser('log-mastered', help='Log a mastered concept')
    mastered_parser.add_argument('--concept', '-c', required=True, help='Concept')
    mastered_parser.add_argument('--insight', '-i', required=True, help='Insight')
    mastered_parser.add_argument('--paper', '-p', help='Paper ID')
    mastered_parser.add_argument('--data-dir', '-d', help='Data directory')
    
    # weekly-summary command
    summary_parser = subparsers.add_parser('weekly-summary', help='Get weekly summary')
    summary_parser.add_argument('--week', '-w', help='Week (e.g., 2026-W05)')
    summary_parser.add_argument('--data-dir', '-d', help='Data directory')
    
    args = parser.parse_args()
    data_dir = Path(args.data_dir) if hasattr(args, 'data_dir') and args.data_dir else None
    
    if args.command == 'log-session':
        result = log_session(args.paper, args.section, args.summary, data_dir)
    elif args.command == 'log-gap':
        result = log_gap(args.concept, args.context, args.paper, data_dir)
    elif args.command == 'log-mastered':
        result = log_mastered(args.concept, args.insight, args.paper, data_dir)
    elif args.command == 'weekly-summary':
        result = get_weekly_summary(args.week, data_dir)
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

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
Okay Skill - End a reading session and log insights.

Usage:
    python -m skills.okay <paper_id> <section> --summary "..." --gaps "..." --mastered "..."

This is typically called by the LLM after analyzing the conversation.
"""

import sys
import json
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.session_logger import log_session, log_gap, log_mastered, get_weekly_summary


def end_session(paper_id: str, section: str, summary: str,
                gaps: list[dict] = None, mastered: list[dict] = None) -> dict:
    """
    End a reading session and log all insights.
    
    Args:
        paper_id: arXiv paper ID
        section: Section identifier
        summary: Session summary
        gaps: List of {"concept": str, "context": str} for things not understood
        mastered: List of {"concept": str, "insight": str} for new understandings
    
    Returns:
        dict with logging results and encouragement
    """
    gaps = gaps or []
    mastered = mastered or []
    
    # Log the session
    session_result = log_session(paper_id, section, summary)
    
    # Log gaps
    for gap in gaps:
        log_gap(
            concept=gap.get('concept', 'Unknown'),
            context=gap.get('context', ''),
            paper_id=paper_id,
        )
    
    # Log mastered concepts
    for m in mastered:
        log_mastered(
            concept=m.get('concept', 'Unknown'),
            insight=m.get('insight', ''),
            paper_id=paper_id,
        )
    
    # Get weekly summary for encouragement
    weekly = get_weekly_summary()
    
    return {
        "session_ended": True,
        "paper_id": paper_id,
        "section": section,
        "gaps_logged": len(gaps),
        "mastered_logged": len(mastered),
        "weekly_stats": weekly,
    }


def generate_encouragement(gaps: list, mastered: list, weekly_stats: dict) -> str:
    """
    Generate encouraging feedback for the user.
    
    This is a helper for the LLM to craft the right message.
    """
    mastered_count = len(mastered)
    gaps_count = len(gaps)
    weekly_mastered = weekly_stats.get('mastered', {}).get('count', 0)
    weekly_gaps = weekly_stats.get('gaps', {}).get('count', 0)
    
    praise = []
    if mastered_count > 0:
        praise.append(f"You nailed {mastered_count} concept(s) today!")
    if weekly_mastered > 0:
        praise.append(f"This week you've mastered {weekly_mastered} concepts total.")
    
    challenge = []
    if gaps_count > 0:
        concepts = [g.get('concept', 'that concept') for g in gaps[:2]]
        challenge.append(
            f"Tomorrow, revisit {', '.join(concepts)} — "
            "your brain is primed to make connections now."
        )
    
    return {
        "praise": ' '.join(praise) if praise else "Good effort today!",
        "challenge": ' '.join(challenge) if challenge else "Keep the momentum going tomorrow!",
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='End reading session')
    parser.add_argument('paper_id', help='Paper ID')
    parser.add_argument('section', help='Section identifier')
    parser.add_argument('--summary', '-s', required=True, help='Session summary')
    parser.add_argument('--gaps', '-g', help='JSON array of gaps')
    parser.add_argument('--mastered', '-m', help='JSON array of mastered concepts')
    args = parser.parse_args()
    
    gaps = json.loads(args.gaps) if args.gaps else []
    mastered = json.loads(args.mastered) if args.mastered else []
    
    result = end_session(
        args.paper_id,
        args.section,
        args.summary,
        gaps=gaps,
        mastered=mastered,
    )
    
    # Add encouragement
    result['encouragement'] = generate_encouragement(gaps, mastered, result['weekly_stats'])
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

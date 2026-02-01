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
Search paper tex files for sections, equations, or text.

Usage:
    python search_paper.py <paper_id> --section 12
    python search_paper.py <paper_id> --equation "3.14"
    python search_paper.py <paper_id> --text "score function"

Returns JSON with location info for token-efficient LLM consumption.
"""

import argparse
import json
import os
import re
from pathlib import Path


def get_default_data_dir() -> Path:
    """Get default data directory from env or use sibling data repo."""
    if os.environ.get('ARXIV_DATA_DIR'):
        return Path(os.environ['ARXIV_DATA_DIR'])
    return Path(__file__).parent.parent.parent / 'arxiv-reading-data' / 'papers'


def get_paper_dir(paper_id: str, data_dir: Path = None) -> Path:
    """Get paper directory path."""
    if data_dir is None:
        data_dir = get_default_data_dir()
    return data_dir / paper_id.replace('/', '_')


def search_by_section(paper_dir: Path, section_query: str) -> dict:
    """
    Search for a section by number or title.
    
    Args:
        paper_dir: Path to paper directory
        section_query: Section number (e.g., "12") or partial title
    
    Returns:
        dict with section info and file path
    """
    sections_dir = paper_dir / "sections"
    index_path = paper_dir / "index.json"
    
    if not sections_dir.exists():
        return {"error": f"Sections not found: {sections_dir}"}
    
    # Load index for metadata
    index = {}
    if index_path.exists():
        index = json.loads(index_path.read_text())
    
    section_files = sorted(sections_dir.glob("*.tex"))
    
    # Try to match by number prefix
    query_lower = section_query.lower().strip()
    
    # Check if query is a number
    if query_lower.isdigit():
        num = int(query_lower)
        # Match files starting with the number
        for f in section_files:
            # Extract number from filename like "12_chapter_foo.tex"
            match = re.match(r'^(\d+)_', f.name)
            if match and int(match.group(1)) == num:
                return {
                    "found": True,
                    "file": str(f),
                    "filename": f.name,
                    "section_number": num,
                    "content_preview": f.read_text(errors='replace')[:500],
                }
    
    # Try partial title match
    matches = []
    for f in section_files:
        fname_lower = f.name.lower()
        if query_lower in fname_lower:
            matches.append(f)
    
    if len(matches) == 1:
        f = matches[0]
        match = re.match(r'^(\d+)_', f.name)
        return {
            "found": True,
            "file": str(f),
            "filename": f.name,
            "section_number": int(match.group(1)) if match else None,
            "content_preview": f.read_text(errors='replace')[:500],
        }
    elif len(matches) > 1:
        return {
            "found": False,
            "error": "Multiple matches",
            "matches": [f.name for f in matches],
        }
    
    return {
        "found": False,
        "error": f"Section not found: {section_query}",
        "available": [f.name for f in section_files[:10]],
    }


def search_by_equation(paper_dir: Path, equation_query: str) -> dict:
    """
    Search for an equation by label or number.
    
    Args:
        paper_dir: Path to paper directory
        equation_query: Equation label (e.g., "eq:elbo") or number pattern
    
    Returns:
        dict with equation location info
    """
    sections_dir = paper_dir / "sections"
    
    if not sections_dir.exists():
        return {"error": f"Sections not found: {sections_dir}"}
    
    query_lower = equation_query.lower().strip()
    results = []
    
    for tex_file in sorted(sections_dir.glob("*.tex")):
        content = tex_file.read_text(errors='replace')
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Search for equation labels
            if f"label{{{query_lower}" in line.lower() or f"\\label{{{query_lower}" in line.lower():
                # Find the enclosing equation environment
                start = max(0, i - 5)
                end = min(len(lines), i + 10)
                context = '\n'.join(lines[start:end])
                
                results.append({
                    "file": str(tex_file),
                    "filename": tex_file.name,
                    "line": i + 1,
                    "match_type": "label",
                    "context": context,
                })
            
            # Search for equation number references
            if query_lower in line.lower() and ('equation' in line.lower() or 'eq.' in line.lower()):
                start = max(0, i - 2)
                end = min(len(lines), i + 5)
                context = '\n'.join(lines[start:end])
                
                results.append({
                    "file": str(tex_file),
                    "filename": tex_file.name,
                    "line": i + 1,
                    "match_type": "reference",
                    "context": context,
                })
    
    if results:
        return {"found": True, "results": results[:5]}  # Limit to first 5
    
    return {"found": False, "error": f"Equation not found: {equation_query}"}


def search_by_text(paper_dir: Path, text_query: str) -> dict:
    """
    Search for exact or fuzzy text match.
    
    Args:
        paper_dir: Path to paper directory
        text_query: Text to search for
    
    Returns:
        dict with text location info
    """
    sections_dir = paper_dir / "sections"
    
    if not sections_dir.exists():
        return {"error": f"Sections not found: {sections_dir}"}
    
    query_lower = text_query.lower().strip()
    results = []
    
    for tex_file in sorted(sections_dir.glob("*.tex")):
        content = tex_file.read_text(errors='replace')
        content_lower = content.lower()
        
        if query_lower in content_lower:
            # Find line number
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if query_lower in line.lower():
                    start = max(0, i - 2)
                    end = min(len(lines), i + 5)
                    context = '\n'.join(lines[start:end])
                    
                    results.append({
                        "file": str(tex_file),
                        "filename": tex_file.name,
                        "line": i + 1,
                        "context": context,
                    })
                    break  # One match per file is enough
    
    if results:
        return {"found": True, "results": results[:5]}
    
    return {"found": False, "error": f"Text not found: {text_query}"}


def search_paper(paper_id: str, section: str = None, equation: str = None, 
                 text: str = None, data_dir: Path = None) -> dict:
    """
    Main search function.
    
    Args:
        paper_id: arXiv paper ID
        section: Section number or title to search
        equation: Equation label or number to search
        text: Text string to search
        data_dir: Optional data directory override
    
    Returns:
        dict with search results
    """
    paper_dir = get_paper_dir(paper_id, data_dir)
    
    if not paper_dir.exists():
        return {"error": f"Paper not found: {paper_id}", "path": str(paper_dir)}
    
    if section:
        return search_by_section(paper_dir, section)
    elif equation:
        return search_by_equation(paper_dir, equation)
    elif text:
        return search_by_text(paper_dir, text)
    else:
        return {"error": "Must specify --section, --equation, or --text"}


def main():
    parser = argparse.ArgumentParser(description='Search paper tex files')
    parser.add_argument('paper_id', help='arXiv paper ID (e.g., 2510.21890)')
    parser.add_argument('--section', '-s', help='Section number or title')
    parser.add_argument('--equation', '-e', help='Equation label or number')
    parser.add_argument('--text', '-t', help='Text to search for')
    parser.add_argument('--data-dir', '-d', help='Data directory override')
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir) if args.data_dir else None
    result = search_paper(
        args.paper_id,
        section=args.section,
        equation=args.equation,
        text=args.text,
        data_dir=data_dir,
    )
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

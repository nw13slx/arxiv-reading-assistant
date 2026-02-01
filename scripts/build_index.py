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
Build an index for a split paper.

Usage:
    python build_index.py <paper_dir>

Example:
    python build_index.py papers/2510.21890
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime


def count_equations(content: str) -> int:
    """Count equation environments."""
    patterns = [
        r'\\begin\{equation',
        r'\\begin\{align',
        r'\\begin\{eqnarray',
        r'\$\$',
        r'\\\[',
    ]
    count = 0
    for pat in patterns:
        count += len(re.findall(pat, content))
    return count


def count_figures(content: str) -> int:
    """Count figure environments."""
    return len(re.findall(r'\\begin\{figure', content))


def count_tables(content: str) -> int:
    """Count table environments."""
    return len(re.findall(r'\\begin\{table', content))


def extract_key_terms(content: str, max_terms: int = 10) -> list[str]:
    """Extract potential key terms from content."""
    # Look for \textbf, \emph, \textit in definitions
    emphasized = re.findall(r'\\(?:textbf|emph|textit)\{([^}]+)\}', content)
    
    # Look for terms being defined
    defined = re.findall(r'(?:called|denoted|defined as|known as)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', content)
    
    # Combine and deduplicate
    terms = []
    seen = set()
    for term in emphasized + defined:
        term_clean = term.strip().lower()
        if len(term_clean) > 2 and term_clean not in seen:
            seen.add(term_clean)
            terms.append(term.strip())
            if len(terms) >= max_terms:
                break
    
    return terms


def estimate_reading_time(content: str, wpm: int = 200) -> int:
    """Estimate reading time in minutes."""
    # Rough word count (excluding latex commands)
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', content)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    words = len(text.split())
    return max(1, words // wpm)


def build_index(paper_dir: Path) -> dict:
    """Build comprehensive index for a paper."""
    sections_dir = paper_dir / "sections"
    
    if not sections_dir.exists():
        raise FileNotFoundError(f"No sections directory in {paper_dir}. Run split_sections.py first.")
    
    # Load raw section data if available
    raw_data = {}
    raw_path = paper_dir / "sections_raw.json"
    if raw_path.exists():
        raw_data = json.loads(raw_path.read_text())
    
    # Process each section file
    sections = []
    total_lines = 0
    total_equations = 0
    total_figures = 0
    
    for tex_file in sorted(sections_dir.glob("*.tex")):
        content = tex_file.read_text(errors='replace')
        
        # Parse filename for metadata
        # Format: XX_level_title.tex
        parts = tex_file.stem.split('_', 2)
        number = parts[0] if parts else "00"
        level = parts[1] if len(parts) > 1 else "section"
        title_slug = parts[2] if len(parts) > 2 else tex_file.stem
        
        # Extract actual title from content
        title_match = re.search(r'\\(?:section|chapter|part)\*?\s*\{([^}]+)\}', content)
        title = title_match.group(1) if title_match else title_slug.replace('_', ' ').title()
        title = re.sub(r'\\[a-zA-Z]+', '', title).strip()
        
        lines = content.count('\n') + 1
        equations = count_equations(content)
        figures = count_figures(content)
        tables = count_tables(content)
        key_terms = extract_key_terms(content)
        reading_time = estimate_reading_time(content)
        
        total_lines += lines
        total_equations += equations
        total_figures += figures
        
        sections.append({
            'number': number,
            'level': level,
            'title': title,
            'file': tex_file.name,
            'lines': lines,
            'equations': equations,
            'figures': figures,
            'tables': tables,
            'reading_time_min': reading_time,
            'key_terms': key_terms,
        })
    
    index = {
        'paper_id': paper_dir.name,
        'indexed_at': datetime.now().isoformat(),
        'summary': {
            'total_sections': len(sections),
            'total_lines': total_lines,
            'total_equations': total_equations,
            'total_figures': total_figures,
            'estimated_reading_time_hours': sum(s['reading_time_min'] for s in sections) / 60,
        },
        'sections': sections,
    }
    
    return index


def write_markdown_index(index: dict, output_path: Path):
    """Write human-readable markdown index."""
    lines = [
        f"# Index: {index['paper_id']}",
        "",
        f"*Indexed: {index['indexed_at'][:10]}*",
        "",
        "## Summary",
        "",
        f"- **Sections**: {index['summary']['total_sections']}",
        f"- **Lines**: {index['summary']['total_lines']:,}",
        f"- **Equations**: {index['summary']['total_equations']}",
        f"- **Figures**: {index['summary']['total_figures']}",
        f"- **Est. reading time**: {index['summary']['estimated_reading_time_hours']:.1f} hours",
        "",
        "## Sections",
        "",
        "| # | Title | Lines | Eqs | Figs | Time |",
        "|---|-------|-------|-----|------|------|",
    ]
    
    for s in index['sections']:
        title = s['title'][:40] + "..." if len(s['title']) > 40 else s['title']
        lines.append(f"| {s['number']} | {title} | {s['lines']} | {s['equations']} | {s['figures']} | {s['reading_time_min']}m |")
    
    lines.extend([
        "",
        "## Key Terms by Section",
        "",
    ])
    
    for s in index['sections']:
        if s['key_terms']:
            lines.append(f"**{s['number']}. {s['title'][:30]}**: {', '.join(s['key_terms'][:5])}")
    
    lines.extend([
        "",
        "---",
        "",
        "## Reading Guide",
        "",
        "To read a section:",
        "```",
        f"\"Let's read section XX\" (replace XX with section number)",
        "```",
    ])
    
    output_path.write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description='Build paper index')
    parser.add_argument('paper_dir', help='Paper directory (e.g., papers/2510.21890)')
    args = parser.parse_args()
    
    paper_dir = Path(args.paper_dir)
    
    print(f"Building index for {paper_dir}...")
    
    index = build_index(paper_dir)
    
    # Write JSON index
    json_path = paper_dir / "index.json"
    json_path.write_text(json.dumps(index, indent=2))
    print(f"Wrote {json_path}")
    
    # Write Markdown index
    md_path = paper_dir / "index.md"
    write_markdown_index(index, md_path)
    print(f"Wrote {md_path}")
    
    # Print summary
    print(f"\n=== Index Summary ===")
    print(f"Sections: {index['summary']['total_sections']}")
    print(f"Lines: {index['summary']['total_lines']:,}")
    print(f"Equations: {index['summary']['total_equations']}")
    print(f"Est. reading time: {index['summary']['estimated_reading_time_hours']:.1f} hours")


if __name__ == '__main__':
    main()

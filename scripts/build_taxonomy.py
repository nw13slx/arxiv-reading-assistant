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
Build hierarchical taxonomy of a tex section file.

Extracts:
- Section/subsection hierarchy
- Key equations with labels
- Key terms (bold/emphasized text)

Usage:
    python build_taxonomy.py <paper_id> <section_file>

Outputs JSON taxonomy to papers/<paper_id>/taxonomy/<section>.taxonomy.json
"""

import argparse
import json
import os
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


def get_default_data_dir() -> Path:
    """Get default data directory from env or use sibling data repo."""
    if os.environ.get('ARXIV_DATA_DIR'):
        return Path(os.environ['ARXIV_DATA_DIR'])
    return Path(__file__).parent.parent.parent / 'arxiv-reading-data' / 'papers'


@dataclass
class TaxonomyNode:
    """A node in the section taxonomy."""
    type: str  # 'section', 'subsection', 'equation', 'term', 'paragraph'
    title: str
    label: Optional[str] = None
    line: int = 0
    children: list = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


def extract_hierarchy(content: str) -> list[TaxonomyNode]:
    """Extract section/subsection hierarchy from tex content."""
    nodes = []
    lines = content.split('\n')
    
    # Patterns for different heading levels
    patterns = [
        (r'\\part\*?\{([^}]+)\}', 'part'),
        (r'\\chapter\*?\{([^}]+)\}', 'chapter'),
        (r'\\section\*?\{([^}]+)\}', 'section'),
        (r'\\subsection\*?\{([^}]+)\}', 'subsection'),
        (r'\\subsubsection\*?\{([^}]+)\}', 'subsubsection'),
        (r'\\paragraph\*?\{([^}]+)\}', 'paragraph'),
    ]
    
    for i, line in enumerate(lines):
        for pattern, node_type in patterns:
            match = re.search(pattern, line)
            if match:
                title = match.group(1).strip()
                # Clean up LaTeX commands in title
                title = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', title)
                title = re.sub(r'\\[a-zA-Z]+', '', title)
                
                # Check for label on next line
                label = None
                if i + 1 < len(lines):
                    label_match = re.search(r'\\label\{([^}]+)\}', lines[i + 1])
                    if label_match:
                        label = label_match.group(1)
                
                nodes.append(TaxonomyNode(
                    type=node_type,
                    title=title,
                    label=label,
                    line=i + 1,
                ))
                break
    
    return nodes


def extract_equations(content: str) -> list[TaxonomyNode]:
    """Extract labeled equations from tex content."""
    nodes = []
    lines = content.split('\n')
    
    # Track equation environments
    in_equation = False
    eq_start = 0
    eq_content = []
    
    equation_envs = ['equation', 'align', 'gather', 'multline', 'eqnarray']
    
    for i, line in enumerate(lines):
        # Check for equation environment start
        for env in equation_envs:
            if f'\\begin{{{env}' in line:
                in_equation = True
                eq_start = i + 1
                eq_content = [line]
                break
            if f'\\end{{{env}' in line:
                if in_equation:
                    eq_content.append(line)
                    full_eq = '\n'.join(eq_content)
                    
                    # Extract label
                    label_match = re.search(r'\\label\{([^}]+)\}', full_eq)
                    label = label_match.group(1) if label_match else None
                    
                    # Create a short title from the equation
                    # Remove label and extract first meaningful part
                    eq_clean = re.sub(r'\\label\{[^}]+\}', '', full_eq)
                    eq_clean = re.sub(r'\\begin\{[^}]+\}', '', eq_clean)
                    eq_clean = re.sub(r'\\end\{[^}]+\}', '', eq_clean)
                    eq_clean = eq_clean.strip()[:80]
                    
                    title = label if label else f"Equation at line {eq_start}"
                    
                    nodes.append(TaxonomyNode(
                        type='equation',
                        title=title,
                        label=label,
                        line=eq_start,
                    ))
                    
                in_equation = False
                eq_content = []
                break
        
        if in_equation:
            eq_content.append(line)
    
    return nodes


def extract_key_terms(content: str) -> list[TaxonomyNode]:
    """Extract key terms (bold/emphasized) from tex content."""
    nodes = []
    lines = content.split('\n')
    seen_terms = set()
    
    # Patterns for emphasized text
    patterns = [
        r'\\textbf\{([^}]+)\}',
        r'\\emph\{([^}]+)\}',
        r'\\textit\{([^}]+)\}',
        r'\\term\{([^}]+)\}',
        r'\\define\{([^}]+)\}',
    ]
    
    for i, line in enumerate(lines):
        for pattern in patterns:
            for match in re.finditer(pattern, line):
                term = match.group(1).strip()
                # Clean up nested commands
                term = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', term)
                term = re.sub(r'\\[a-zA-Z]+', '', term)
                term = term.strip()
                
                # Skip short terms or already seen
                if len(term) < 3 or term.lower() in seen_terms:
                    continue
                
                seen_terms.add(term.lower())
                nodes.append(TaxonomyNode(
                    type='term',
                    title=term,
                    line=i + 1,
                ))
    
    return nodes


def build_taxonomy(tex_file: Path) -> dict:
    """
    Build complete taxonomy for a tex file.
    
    Args:
        tex_file: Path to tex file
    
    Returns:
        dict with taxonomy structure
    """
    content = tex_file.read_text(errors='replace')
    
    hierarchy = extract_hierarchy(content)
    equations = extract_equations(content)
    terms = extract_key_terms(content)
    
    # Build nested structure based on hierarchy levels
    level_order = ['part', 'chapter', 'section', 'subsection', 'subsubsection', 'paragraph']
    
    def node_to_dict(node: TaxonomyNode) -> dict:
        d = {
            'type': node.type,
            'title': node.title,
            'line': node.line,
        }
        if node.label:
            d['label'] = node.label
        if node.children:
            d['children'] = [node_to_dict(c) for c in node.children]
        return d
    
    return {
        'file': tex_file.name,
        'hierarchy': [node_to_dict(n) for n in hierarchy],
        'equations': [node_to_dict(n) for n in equations],
        'key_terms': [node_to_dict(n) for n in terms],
        'stats': {
            'sections': len(hierarchy),
            'equations': len(equations),
            'key_terms': len(terms),
            'lines': len(content.split('\n')),
        }
    }


def get_or_build_taxonomy(paper_id: str, section_file: str, 
                          data_dir: Path = None, force: bool = False) -> dict:
    """
    Get existing taxonomy or build new one.
    
    Args:
        paper_id: arXiv paper ID
        section_file: Section filename (e.g., "12_chapter_variational.tex")
        data_dir: Optional data directory override
        force: Force rebuild even if exists
    
    Returns:
        dict with taxonomy
    """
    if data_dir is None:
        data_dir = get_default_data_dir()
    
    paper_dir = data_dir / paper_id.replace('/', '_')
    sections_dir = paper_dir / "sections"
    taxonomy_dir = paper_dir / "taxonomy"
    
    # Determine tex file path
    if Path(section_file).is_absolute():
        tex_path = Path(section_file)
    else:
        tex_path = sections_dir / section_file
    
    if not tex_path.exists():
        return {"error": f"Section file not found: {tex_path}"}
    
    # Check for cached taxonomy
    taxonomy_file = taxonomy_dir / f"{tex_path.stem}.taxonomy.json"
    
    if taxonomy_file.exists() and not force:
        return json.loads(taxonomy_file.read_text())
    
    # Build taxonomy
    taxonomy = build_taxonomy(tex_path)
    
    # Cache it
    taxonomy_dir.mkdir(parents=True, exist_ok=True)
    taxonomy_file.write_text(json.dumps(taxonomy, indent=2))
    
    return taxonomy


def main():
    parser = argparse.ArgumentParser(description='Build section taxonomy')
    parser.add_argument('paper_id', help='arXiv paper ID')
    parser.add_argument('section_file', help='Section filename')
    parser.add_argument('--data-dir', '-d', help='Data directory override')
    parser.add_argument('--force', '-f', action='store_true', help='Force rebuild')
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir) if args.data_dir else None
    taxonomy = get_or_build_taxonomy(
        args.paper_id,
        args.section_file,
        data_dir=data_dir,
        force=args.force,
    )
    
    print(json.dumps(taxonomy, indent=2))


if __name__ == '__main__':
    main()

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
Paper Init Skill - Quick entry point for initializing papers.

Usage:
    python -m skills.paper_init <arxiv_id>
    
Or import and use:
    from skills.paper_init import init_paper
    init_paper("2510.21890")
"""

import sys
import json
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.download_arxiv import parse_arxiv_id, download_source, extract_source, find_main_tex
from scripts.split_sections import (
    get_main_tex, read_tex_with_inputs, find_sections, 
    assign_section_numbers, extract_section_content, write_sections
)
from scripts.build_index import build_index, write_markdown_index


def get_default_output_dir() -> str:
    """Get default output directory from env or use sibling data repo."""
    import os
    if os.environ.get('ARXIV_DATA_DIR'):
        return os.environ['ARXIV_DATA_DIR']
    # Default to sibling data repo
    return str(Path(__file__).parent.parent.parent / 'arxiv-reading-data' / 'papers')


def init_paper(arxiv_id: str, output_dir: str = None, split_level: int = 2) -> dict:
    """
    Initialize a paper for reading.
    
    Args:
        arxiv_id: arXiv ID or URL (e.g., "2510.21890" or "https://arxiv.org/abs/2510.21890")
        output_dir: Directory to store papers (default: ARXIV_DATA_DIR or ../arxiv-reading-data/papers)
        split_level: Section level to split at (0=part, 1=chapter, 2=section)
    
    Returns:
        dict with paper info including index
    """
    if output_dir is None:
        output_dir = get_default_output_dir()
    output_dir = Path(output_dir)
    
    # Parse ID
    paper_id = parse_arxiv_id(arxiv_id)
    paper_dir = output_dir / paper_id.replace('/', '_')
    
    print(f"📥 Initializing paper: {paper_id}")
    
    # Step 1: Download
    if not (paper_dir / "src").exists():
        print("  Downloading source...")
        archive_path = download_source(paper_id, output_dir)
        extract_source(archive_path, paper_dir)
    else:
        print("  Source already downloaded, skipping...")
    
    # Step 2: Parse and split
    print("  Parsing and splitting sections...")
    main_tex = get_main_tex(paper_dir)
    
    # Update metadata with correct main file
    meta_path = paper_dir / "metadata.txt"
    meta_path.write_text(f"arxiv_id: {paper_id}\nmain_tex: {main_tex.relative_to(paper_dir)}\n")
    
    full_content = read_tex_with_inputs(main_tex, main_tex.parent)
    sections = find_sections(full_content)
    sections = assign_section_numbers(sections)
    sections = extract_section_content(full_content, sections)
    
    sections_dir = paper_dir / "sections"
    written = write_sections(sections, sections_dir, min_level=split_level)
    
    # Step 3: Build index
    print("  Building index...")
    index = build_index(paper_dir)
    
    # Write outputs
    (paper_dir / "index.json").write_text(json.dumps(index, indent=2))
    write_markdown_index(index, paper_dir / "index.md")
    
    # Summary
    summary = index['summary']
    print(f"\n✅ Paper ready: {paper_id}")
    print(f"   📂 {paper_dir}")
    print(f"   📑 {summary['total_sections']} sections")
    print(f"   📐 {summary['total_equations']} equations")
    print(f"   🖼️  {summary['total_figures']} figures")
    print(f"   ⏱️  ~{summary['estimated_reading_time_hours']:.1f} hours reading time")
    
    return {
        'paper_id': paper_id,
        'paper_dir': str(paper_dir),
        'index': index,
    }


def show_index(paper_id: str, output_dir: str = None) -> str:
    """Show the markdown index for a paper."""
    if output_dir is None:
        output_dir = get_default_output_dir()
    paper_dir = Path(output_dir) / paper_id.replace('/', '_')
    index_path = paper_dir / "index.md"
    
    if not index_path.exists():
        return f"Paper {paper_id} not initialized. Run: /paper-init {paper_id}"
    
    return index_path.read_text()


def list_papers(output_dir: str = None) -> list:
    """List all initialized papers."""
    if output_dir is None:
        output_dir = get_default_output_dir()
    output_dir = Path(output_dir)
    papers = []
    
    for paper_dir in output_dir.iterdir():
        if paper_dir.is_dir() and (paper_dir / "index.json").exists():
            index = json.loads((paper_dir / "index.json").read_text())
            papers.append({
                'paper_id': index['paper_id'],
                'sections': index['summary']['total_sections'],
                'reading_time': f"{index['summary']['estimated_reading_time_hours']:.1f}h",
            })
    
    return papers


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m skills.paper_init <arxiv_id>")
        print("Example: python -m skills.paper_init 2510.21890")
        sys.exit(1)
    
    init_paper(sys.argv[1])

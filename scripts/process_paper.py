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
Full pipeline: download, split, and index an arXiv paper.

Usage:
    python process_paper.py <arxiv_id_or_url>

Example:
    python process_paper.py 2510.21890
    python process_paper.py https://arxiv.org/abs/2510.21890
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def get_default_output_dir() -> str:
    """Get default output directory from env or use sibling data repo."""
    if os.environ.get('ARXIV_DATA_DIR'):
        return os.environ['ARXIV_DATA_DIR']
    # Default to sibling data repo
    return str(Path(__file__).parent.parent.parent / 'arxiv-reading-data' / 'papers')


def run_script(script_name: str, *args):
    """Run a script from the scripts directory."""
    script_path = Path(__file__).parent / script_name
    cmd = [sys.executable, str(script_path)] + list(args)
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print('='*60 + '\n')
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Error: {script_name} failed with code {result.returncode}")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description='Process an arXiv paper')
    parser.add_argument('arxiv_id', help='arXiv ID or URL')
    parser.add_argument('--output-dir', '-o', default=None,
                        help='Output directory (default: ARXIV_DATA_DIR or ../arxiv-reading-data/papers)')
    parser.add_argument('--level', '-l', type=int, default=2,
                        help='Split level (0=part, 1=chapter, 2=section). Default: 2')
    args = parser.parse_args()
    
    output_dir = args.output_dir if args.output_dir else get_default_output_dir()
    
    # Normalize arxiv ID for directory name
    import re
    arxiv_id = args.arxiv_id
    match = re.search(r'(\d+\.\d+)', arxiv_id)
    if match:
        paper_id = match.group(1)
    else:
        paper_id = arxiv_id.replace('/', '_')
    
    paper_dir = Path(output_dir) / paper_id
    
    # Step 1: Download
    run_script('download_arxiv.py', args.arxiv_id, '-o', output_dir)
    
    # Step 2: Split
    run_script('split_sections.py', str(paper_dir), '-l', str(args.level))
    
    # Step 3: Index
    run_script('build_index.py', str(paper_dir))
    
    print(f"\n{'='*60}")
    print("DONE!")
    print(f"Paper ready at: {paper_dir}")
    print(f"Index: {paper_dir / 'index.md'}")
    print(f"Sections: {paper_dir / 'sections/'}")
    print('='*60)


if __name__ == '__main__':
    main()

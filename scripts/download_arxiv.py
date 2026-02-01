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
Download arXiv source files.

Usage:
    python download_arxiv.py <arxiv_id> [--output-dir papers/]

Example:
    python download_arxiv.py 2510.21890
"""

import argparse
import os
import re
import tarfile
import gzip
import shutil
import urllib.request
from pathlib import Path


def get_default_output_dir() -> str:
    """Get default output directory from env or use sibling data repo."""
    if os.environ.get('ARXIV_DATA_DIR'):
        return os.environ['ARXIV_DATA_DIR']
    # Default to sibling data repo
    return str(Path(__file__).parent.parent.parent / 'arxiv-reading-data' / 'papers')


def parse_arxiv_id(identifier: str) -> str:
    """Extract arxiv ID from URL or raw ID."""
    # Handle URLs like https://arxiv.org/src/2510.21890
    patterns = [
        r'arxiv\.org/(?:abs|src|pdf)/(\d+\.\d+)',
        r'arxiv\.org/(?:abs|src|pdf)/([a-z-]+/\d+)',
        r'^(\d+\.\d+)$',
        r'^([a-z-]+/\d+)$',
    ]
    for pattern in patterns:
        match = re.search(pattern, identifier)
        if match:
            return match.group(1)
    raise ValueError(f"Cannot parse arXiv ID from: {identifier}")


def download_source(arxiv_id: str, output_dir: Path) -> Path:
    """Download arXiv source tar/gz file."""
    url = f"https://arxiv.org/src/{arxiv_id}"
    paper_dir = output_dir / arxiv_id.replace('/', '_')
    paper_dir.mkdir(parents=True, exist_ok=True)
    
    download_path = paper_dir / "source.tar.gz"
    
    print(f"Downloading {url} ...")
    
    # arXiv requires a User-Agent header
    request = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (arXiv reading assistant)'}
    )
    
    with urllib.request.urlopen(request) as response:
        with open(download_path, 'wb') as f:
            f.write(response.read())
    
    print(f"Saved to {download_path}")
    return download_path


def extract_source(archive_path: Path, extract_dir: Path) -> Path:
    """Extract tar.gz or gz file."""
    src_dir = extract_dir / "src"
    src_dir.mkdir(exist_ok=True)
    
    # Try as tar.gz first
    try:
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(src_dir)
            print(f"Extracted tar.gz to {src_dir}")
            return src_dir
    except tarfile.TarError:
        pass
    
    # Try as plain gzip (single file)
    try:
        with gzip.open(archive_path, 'rb') as f_in:
            content = f_in.read()
            # Single .tex file
            tex_path = src_dir / "main.tex"
            with open(tex_path, 'wb') as f_out:
                f_out.write(content)
            print(f"Extracted single file to {tex_path}")
            return src_dir
    except gzip.BadGzipFile:
        pass
    
    # Maybe it's uncompressed?
    shutil.copy(archive_path, src_dir / "main.tex")
    print(f"Copied as plain tex to {src_dir}")
    return src_dir


def find_main_tex(src_dir: Path) -> Path:
    """Find the main tex file in extracted source."""
    tex_files = list(src_dir.rglob("*.tex"))
    
    if not tex_files:
        raise FileNotFoundError(f"No .tex files found in {src_dir}")
    
    # Common main file names (ordered by priority)
    main_names = ['main.tex', 'main_v2.tex', 'main_v1.tex', 'paper.tex', 'article.tex', 'manuscript.tex', 'book.tex']
    for name in main_names:
        for tex in tex_files:
            if tex.name.lower() == name.lower():
                return tex
    
    # Look for \documentclass (prefer files with more \input commands = likely main)
    candidates = []
    for tex in tex_files:
        try:
            content = tex.read_text(errors='ignore')
            if r'\documentclass' in content:
                input_count = content.count(r'\input')
                candidates.append((tex, input_count))
        except:
            continue
    
    if candidates:
        # Return the one with most \input commands
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    # Fall back to first tex file
    return tex_files[0]


def main():
    parser = argparse.ArgumentParser(description='Download arXiv source files')
    parser.add_argument('arxiv_id', help='arXiv ID or URL (e.g., 2510.21890)')
    parser.add_argument('--output-dir', '-o', default=None, 
                        help='Output directory (default: ARXIV_DATA_DIR or ../arxiv-reading-data/papers)')
    args = parser.parse_args()
    
    arxiv_id = parse_arxiv_id(args.arxiv_id)
    output_dir = Path(args.output_dir if args.output_dir else get_default_output_dir())
    
    print(f"arXiv ID: {arxiv_id}")
    
    # Download
    archive_path = download_source(arxiv_id, output_dir)
    
    # Extract
    paper_dir = archive_path.parent
    src_dir = extract_source(archive_path, paper_dir)
    
    # Find main file
    main_tex = find_main_tex(src_dir)
    print(f"Main tex file: {main_tex}")
    
    # Write metadata
    meta_path = paper_dir / "metadata.txt"
    with open(meta_path, 'w') as f:
        f.write(f"arxiv_id: {arxiv_id}\n")
        f.write(f"main_tex: {main_tex.relative_to(paper_dir)}\n")
    
    print(f"\nDone! Paper downloaded to: {paper_dir}")
    print(f"Main tex: {main_tex.relative_to(paper_dir)}")


if __name__ == '__main__':
    main()

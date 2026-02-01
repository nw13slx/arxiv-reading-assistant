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
Split a LaTeX document into sections/chapters.

Usage:
    python split_sections.py <paper_dir>

Example:
    python split_sections.py papers/2510.21890
"""

import argparse
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Section:
    """Represents a document section."""
    level: int  # 0=part, 1=chapter, 2=section, 3=subsection, etc.
    number: int  # sequential number at this level
    title: str
    label: Optional[str] = None
    start_line: int = 0
    end_line: int = 0
    content: str = ""
    children: list = field(default_factory=list)
    
    @property
    def level_name(self) -> str:
        names = ['part', 'chapter', 'section', 'subsection', 'subsubsection']
        return names[self.level] if self.level < len(names) else f'level{self.level}'


# LaTeX sectioning commands in hierarchical order
SECTION_COMMANDS = [
    (r'\\part\*?\s*\{', 0),
    (r'\\chapter\*?\s*\{', 1),
    (r'\\section\*?\s*\{', 2),
    (r'\\subsection\*?\s*\{', 3),
    (r'\\subsubsection\*?\s*\{', 4),
]


def read_tex_with_inputs(tex_path: Path, base_dir: Path, seen: set = None) -> str:
    """Read tex file and recursively expand \input and \include commands."""
    if seen is None:
        seen = set()
    
    if tex_path in seen:
        return f"% [CIRCULAR: {tex_path.name}]\n"
    seen.add(tex_path)
    
    try:
        content = tex_path.read_text(errors='replace')
    except FileNotFoundError:
        return f"% [FILE NOT FOUND: {tex_path.name}]\n"
    
    # Pattern for \input{file} or \include{file}
    input_pattern = r'\\(?:input|include)\s*\{([^}]+)\}'
    
    def replace_input(match):
        filename = match.group(1).strip()
        # Add .tex extension if missing
        if not filename.endswith('.tex'):
            filename += '.tex'
        
        # Try relative to current file first, then base_dir
        input_path = tex_path.parent / filename
        if not input_path.exists():
            input_path = base_dir / filename
        
        marker = f"\n% === INPUT: {filename} ===\n"
        end_marker = f"\n% === END INPUT: {filename} ===\n"
        return marker + read_tex_with_inputs(input_path, base_dir, seen) + end_marker
    
    return re.sub(input_pattern, replace_input, content)


def extract_brace_content(text: str, start_pos: int) -> tuple[str, int]:
    """Extract content within braces, handling nested braces."""
    depth = 0
    content_start = None
    
    for i, char in enumerate(text[start_pos:], start_pos):
        if char == '{':
            if depth == 0:
                content_start = i + 1
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[content_start:i], i + 1
    
    return "", len(text)


def find_sections(content: str) -> list[Section]:
    """Find all section commands in the content."""
    sections = []
    lines = content.split('\n')
    
    # Build a combined pattern
    combined_pattern = '|'.join(f'({pat})' for pat, _ in SECTION_COMMANDS)
    
    current_line = 0
    for line_no, line in enumerate(lines):
        for cmd_pattern, level in SECTION_COMMANDS:
            match = re.search(cmd_pattern, line)
            if match:
                # Extract the title
                title, _ = extract_brace_content(line, match.end() - 1)
                
                # Clean up title (remove commands, newlines, etc.)
                title = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', title)
                title = re.sub(r'\\[a-zA-Z]+', '', title)
                title = title.strip()
                
                # Look for \label on same or next line
                label = None
                label_match = re.search(r'\\label\{([^}]+)\}', line)
                if not label_match and line_no + 1 < len(lines):
                    label_match = re.search(r'\\label\{([^}]+)\}', lines[line_no + 1])
                if label_match:
                    label = label_match.group(1)
                
                sections.append(Section(
                    level=level,
                    number=0,  # Will be assigned later
                    title=title,
                    label=label,
                    start_line=line_no,
                ))
                break
    
    return sections


def assign_section_numbers(sections: list[Section]) -> list[Section]:
    """Assign hierarchical section numbers."""
    counters = [0] * 10  # Support up to 10 levels
    
    for section in sections:
        level = section.level
        counters[level] += 1
        # Reset lower-level counters
        for i in range(level + 1, len(counters)):
            counters[i] = 0
        section.number = counters[level]
    
    return sections


def extract_section_content(content: str, sections: list[Section]) -> list[Section]:
    """Extract content for each section."""
    lines = content.split('\n')
    
    for i, section in enumerate(sections):
        start = section.start_line
        if i + 1 < len(sections):
            end = sections[i + 1].start_line
        else:
            end = len(lines)
        
        section.end_line = end
        section.content = '\n'.join(lines[start:end])
    
    return sections


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """Convert section title to safe filename."""
    # Remove special characters
    name = re.sub(r'[^\w\s-]', '', title)
    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)
    # Truncate
    name = name[:max_length].rstrip('_')
    return name.lower() or 'untitled'


def write_sections(sections: list[Section], output_dir: Path, min_level: int = 2):
    """Write sections to individual files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter to requested level (default: section level and above)
    top_sections = [s for s in sections if s.level <= min_level]
    
    written = []
    for i, section in enumerate(top_sections):
        # Find content up to next section of same or higher level
        start_idx = sections.index(section)
        end_idx = start_idx + 1
        while end_idx < len(sections) and sections[end_idx].level > section.level:
            end_idx += 1
        
        # Combine content
        combined_content = '\n'.join(s.content for s in sections[start_idx:end_idx])
        
        # Generate filename
        filename = f"{i+1:02d}_{section.level_name}_{sanitize_filename(section.title)}.tex"
        filepath = output_dir / filename
        
        filepath.write_text(combined_content)
        written.append({
            'file': filename,
            'title': section.title,
            'level': section.level_name,
            'lines': combined_content.count('\n') + 1,
        })
        print(f"  {filename}")
    
    return written


def get_main_tex(paper_dir: Path) -> Path:
    """Get main tex file from metadata or find it."""
    meta_path = paper_dir / "metadata.txt"
    if meta_path.exists():
        for line in meta_path.read_text().split('\n'):
            if line.startswith('main_tex:'):
                rel_path = line.split(':', 1)[1].strip()
                return paper_dir / rel_path
    
    # Fallback: find it
    src_dir = paper_dir / "src"
    if src_dir.exists():
        for tex in src_dir.rglob("*.tex"):
            content = tex.read_text(errors='ignore')
            if r'\documentclass' in content:
                return tex
    
    raise FileNotFoundError(f"Cannot find main tex in {paper_dir}")


def main():
    parser = argparse.ArgumentParser(description='Split LaTeX into sections')
    parser.add_argument('paper_dir', help='Paper directory (e.g., papers/2510.21890)')
    parser.add_argument('--level', '-l', type=int, default=2,
                        help='Split at this level (0=part, 1=chapter, 2=section). Default: 2')
    args = parser.parse_args()
    
    paper_dir = Path(args.paper_dir)
    main_tex = get_main_tex(paper_dir)
    
    print(f"Reading {main_tex}...")
    
    # Read and expand all inputs
    full_content = read_tex_with_inputs(main_tex, main_tex.parent)
    
    print(f"Total content: {len(full_content)} chars, {full_content.count(chr(10))} lines")
    
    # Find sections
    sections = find_sections(full_content)
    print(f"Found {len(sections)} sectioning commands")
    
    # Assign numbers and extract content
    sections = assign_section_numbers(sections)
    sections = extract_section_content(full_content, sections)
    
    # Show summary
    for s in sections[:20]:  # First 20
        indent = "  " * s.level
        print(f"{indent}{s.level_name} {s.number}: {s.title[:50]}")
    if len(sections) > 20:
        print(f"  ... and {len(sections) - 20} more")
    
    # Write sections
    output_dir = paper_dir / "sections"
    print(f"\nWriting sections to {output_dir}...")
    written = write_sections(sections, output_dir, min_level=args.level)
    
    print(f"\nDone! Wrote {len(written)} section files.")
    
    # Save section list for build_index.py
    import json
    index_data = {
        'paper_dir': str(paper_dir),
        'main_tex': str(main_tex.relative_to(paper_dir)),
        'total_sections': len(sections),
        'sections': written,
    }
    (paper_dir / "sections_raw.json").write_text(json.dumps(index_data, indent=2))


if __name__ == '__main__':
    main()

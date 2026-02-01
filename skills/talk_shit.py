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
Talk Shit Skill - Start a focused reading session.

Usage:
    python -m skills.talk_shit <paper_id> section <number>
    python -m skills.talk_shit <paper_id> equation <label>
    python -m skills.talk_shit <paper_id> text "search terms"

Returns section content and taxonomy for LLM consumption.
"""

import sys
import json
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.search_paper import search_paper, get_paper_dir
from scripts.build_taxonomy import get_or_build_taxonomy


def start_session(paper_id: str, query_type: str, query: str) -> dict:
    """
    Start a reading session on a specific location.
    
    Args:
        paper_id: arXiv paper ID
        query_type: 'section', 'equation', or 'text'
        query: The search query
    
    Returns:
        dict with section content, taxonomy, and session info
    """
    # Search for the location
    if query_type == 'section':
        result = search_paper(paper_id, section=query)
    elif query_type == 'equation':
        result = search_paper(paper_id, equation=query)
    elif query_type == 'text':
        result = search_paper(paper_id, text=query)
    else:
        return {"error": f"Unknown query type: {query_type}"}
    
    if not result.get('found'):
        return result
    
    # Get the section file
    if query_type == 'section':
        section_file = result.get('filename')
        file_path = result.get('file')
    else:
        # For equation/text, get from first result
        results = result.get('results', [])
        if not results:
            return {"error": "No results found"}
        section_file = results[0].get('filename')
        file_path = results[0].get('file')
    
    if not section_file:
        return {"error": "Could not determine section file"}
    
    # Build or get taxonomy
    taxonomy = get_or_build_taxonomy(paper_id, section_file)
    
    # Read full section content
    content = ""
    if file_path and Path(file_path).exists():
        content = Path(file_path).read_text(errors='replace')
    
    return {
        "session_started": True,
        "paper_id": paper_id,
        "section_file": section_file,
        "query_type": query_type,
        "query": query,
        "taxonomy": taxonomy,
        "content": content,
        "instructions": (
            "Session locked to this section. "
            "Answer questions using physics analogies when helpful. "
            "Track concepts the user struggles with vs. masters. "
            "End session with /okay."
        ),
    }


def main():
    if len(sys.argv) < 4:
        print("Usage: python -m skills.talk_shit <paper_id> <type> <query>")
        print("Types: section, equation, text")
        print("Example: python -m skills.talk_shit 2510.21890 section 12")
        sys.exit(1)
    
    paper_id = sys.argv[1]
    query_type = sys.argv[2].lower()
    query = ' '.join(sys.argv[3:])
    
    result = start_session(paper_id, query_type, query)
    
    # Print compact JSON for LLM consumption
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

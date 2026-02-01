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
Unit tests for paper processing scripts.

Run with: python -m pytest tests/ -v
Or: python tests/test_parsing.py
"""

import sys
import json
import tempfile
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

import pytest

# Import functions to test
from split_sections import (
    extract_brace_content,
    find_sections,
    assign_section_numbers,
    extract_section_content,
    sanitize_filename,
    read_tex_with_inputs,
    Section,
)
from build_index import (
    count_equations,
    count_figures,
    count_tables,
    extract_key_terms,
    estimate_reading_time,
)
from download_arxiv import parse_arxiv_id, download_source, extract_source, find_main_tex


class TestArxivIdParsing:
    """Test arXiv ID extraction from various formats."""
    
    def test_plain_id_new_format(self):
        assert parse_arxiv_id("2312.07511") == "2312.07511"
    
    def test_plain_id_with_version(self):
        assert parse_arxiv_id("2510.21890") == "2510.21890"
    
    def test_abs_url(self):
        assert parse_arxiv_id("http://arxiv.org/abs/2312.07511") == "2312.07511"
        assert parse_arxiv_id("https://arxiv.org/abs/2510.21890") == "2510.21890"
    
    def test_src_url(self):
        assert parse_arxiv_id("https://arxiv.org/src/2312.07511") == "2312.07511"
    
    def test_pdf_url(self):
        assert parse_arxiv_id("https://arxiv.org/pdf/2312.07511") == "2312.07511"
    
    def test_old_format_id(self):
        assert parse_arxiv_id("hep-th/9901001") == "hep-th/9901001"
        assert parse_arxiv_id("https://arxiv.org/abs/hep-th/9901001") == "hep-th/9901001"
    
    def test_invalid_format(self):
        with pytest.raises(ValueError):
            parse_arxiv_id("not-an-arxiv-id")


class TestDownloadWithMock:
    """Test download functions with mocked network calls."""
    
    def test_download_source_creates_directory(self, monkeypatch):
        """Test that download_source creates the paper directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Mock urlopen to return fake tar.gz content
            def mock_urlopen(request):
                class MockResponse:
                    def __enter__(self):
                        return self
                    def __exit__(self, *args):
                        pass
                    def read(self):
                        # Return minimal gzip content (empty)
                        import gzip
                        import io
                        buf = io.BytesIO()
                        with gzip.GzipFile(fileobj=buf, mode='wb') as f:
                            f.write(b"\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}")
                        return buf.getvalue()
                return MockResponse()
            
            monkeypatch.setattr('urllib.request.urlopen', mock_urlopen)
            
            archive_path = download_source("2312.07511", tmpdir)
            
            assert archive_path.exists()
            assert archive_path.name == "source.tar.gz"
            assert (tmpdir / "2312.07511").exists()
    
    def test_extract_source_gzip_single_file(self):
        """Test extracting a single gzipped tex file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a gzipped tex file
            import gzip
            archive_path = tmpdir / "source.tar.gz"
            with gzip.open(archive_path, 'wb') as f:
                f.write(b"\\documentclass{article}\n\\begin{document}\nTest\n\\end{document}")
            
            src_dir = extract_source(archive_path, tmpdir)
            
            assert src_dir.exists()
            assert (src_dir / "main.tex").exists()
            content = (src_dir / "main.tex").read_text()
            assert "\\documentclass" in content
    
    def test_extract_source_tarball(self):
        """Test extracting a tar.gz with multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a tar.gz with tex files
            import tarfile
            archive_path = tmpdir / "source.tar.gz"
            
            # Create temp tex files to add to tarball
            tex1 = tmpdir / "main.tex"
            tex1.write_text("\\documentclass{article}\n\\input{intro}")
            tex2 = tmpdir / "intro.tex"
            tex2.write_text("\\section{Introduction}\nHello")
            
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(tex1, arcname="main.tex")
                tar.add(tex2, arcname="intro.tex")
            
            # Clean up temp files before extraction
            tex1.unlink()
            tex2.unlink()
            
            src_dir = extract_source(archive_path, tmpdir)
            
            assert src_dir.exists()
            assert (src_dir / "main.tex").exists()
            assert (src_dir / "intro.tex").exists()
    
    def test_find_main_tex_by_name(self):
        """Test finding main.tex by conventional name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            (tmpdir / "main.tex").write_text("\\documentclass{article}")
            (tmpdir / "appendix.tex").write_text("\\section{Appendix}")
            
            main = find_main_tex(tmpdir)
            assert main.name == "main.tex"
    
    def test_find_main_tex_by_documentclass(self):
        """Test finding main tex by \\documentclass presence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            (tmpdir / "paper.tex").write_text("\\documentclass{article}\n\\input{ch1}\n\\input{ch2}")
            (tmpdir / "ch1.tex").write_text("\\chapter{One}")
            (tmpdir / "ch2.tex").write_text("\\chapter{Two}")
            
            main = find_main_tex(tmpdir)
            assert main.name == "paper.tex"
    
    def test_find_main_tex_prefers_more_inputs(self):
        """Test that main tex with more \\input commands is preferred."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Both have documentclass, but one has more inputs
            (tmpdir / "a.tex").write_text("\\documentclass{article}\n\\input{x}")
            (tmpdir / "b.tex").write_text("\\documentclass{book}\n\\input{x}\n\\input{y}\n\\input{z}")
            
            main = find_main_tex(tmpdir)
            assert main.name == "b.tex"


class TestBraceExtraction:
    """Test LaTeX brace content extraction."""
    
    def test_simple_braces(self):
        text = r"\section{Introduction}"
        content, end = extract_brace_content(text, 8)
        assert content == "Introduction"
    
    def test_nested_braces(self):
        text = r"\section{A \textbf{Bold} Title}"
        content, end = extract_brace_content(text, 8)
        assert content == r"A \textbf{Bold} Title"
    
    def test_deeply_nested(self):
        text = r"\section{Foo {Bar {Baz}}}"
        content, end = extract_brace_content(text, 8)
        assert content == "Foo {Bar {Baz}}"
    
    def test_empty_braces(self):
        text = r"\section{}"
        content, end = extract_brace_content(text, 8)
        assert content == ""


class TestSectionFinding:
    """Test section detection in LaTeX content."""
    
    def test_find_section(self):
        content = r"""
\section{Introduction}
Some text here.
\section{Methods}
More text.
"""
        sections = find_sections(content)
        assert len(sections) == 2
        assert sections[0].title == "Introduction"
        assert sections[1].title == "Methods"
        assert sections[0].level == 2  # section level
    
    def test_find_chapter(self):
        content = r"""
\chapter{First Chapter}
Intro text.
\section{Section One}
Details.
"""
        sections = find_sections(content)
        assert len(sections) == 2
        assert sections[0].level == 1  # chapter
        assert sections[1].level == 2  # section
    
    def test_find_part(self):
        content = r"""
\part{Part One}
\chapter{Chapter in Part}
"""
        sections = find_sections(content)
        assert len(sections) == 2
        assert sections[0].level == 0  # part
        assert sections[1].level == 1  # chapter
    
    def test_starred_sections(self):
        content = r"""
\section*{Acknowledgments}
Thanks.
"""
        sections = find_sections(content)
        assert len(sections) == 1
        assert sections[0].title == "Acknowledgments"
    
    def test_section_with_label(self):
        content = r"""
\section{Methods}
\label{sec:methods}
Text.
"""
        sections = find_sections(content)
        assert len(sections) == 1
        assert sections[0].label == "sec:methods"
    
    def test_subsections(self):
        content = r"""
\section{Main}
\subsection{Sub One}
\subsubsection{Sub Sub}
"""
        sections = find_sections(content)
        assert len(sections) == 3
        assert sections[0].level == 2
        assert sections[1].level == 3
        assert sections[2].level == 4


class TestSectionNumbering:
    """Test hierarchical section numbering."""
    
    def test_simple_numbering(self):
        sections = [
            Section(level=2, number=0, title="A", start_line=0),
            Section(level=2, number=0, title="B", start_line=10),
            Section(level=2, number=0, title="C", start_line=20),
        ]
        numbered = assign_section_numbers(sections)
        assert [s.number for s in numbered] == [1, 2, 3]
    
    def test_hierarchical_numbering(self):
        sections = [
            Section(level=1, number=0, title="Ch1", start_line=0),
            Section(level=2, number=0, title="Sec1", start_line=10),
            Section(level=2, number=0, title="Sec2", start_line=20),
            Section(level=1, number=0, title="Ch2", start_line=30),
            Section(level=2, number=0, title="Sec1", start_line=40),
        ]
        numbered = assign_section_numbers(sections)
        assert numbered[0].number == 1  # Ch1
        assert numbered[3].number == 2  # Ch2
        assert numbered[1].number == 1  # Ch1/Sec1
        assert numbered[2].number == 2  # Ch1/Sec2
        assert numbered[4].number == 1  # Ch2/Sec1


class TestContentExtraction:
    """Test section content extraction."""
    
    def test_extract_content(self):
        content = """Line 0
\\section{First}
Line 2
Line 3
\\section{Second}
Line 5
Line 6"""
        sections = find_sections(content)
        sections = extract_section_content(content, sections)
        
        assert "Line 2" in sections[0].content
        assert "Line 3" in sections[0].content
        assert "Line 5" in sections[1].content
        assert "Line 6" in sections[1].content


class TestFilenameSanitization:
    """Test filename generation from titles."""
    
    def test_simple_title(self):
        assert sanitize_filename("Introduction") == "introduction"
    
    def test_spaces(self):
        assert sanitize_filename("My Great Section") == "my_great_section"
    
    def test_special_chars(self):
        result = sanitize_filename("Methods: A & B")
        # Colons and ampersands removed, spaces become underscores
        assert "methods" in result
        assert "a" in result
        assert "b" in result
    
    def test_truncation(self):
        long_title = "A" * 100
        result = sanitize_filename(long_title, max_length=50)
        assert len(result) <= 50
    
    def test_empty_becomes_untitled(self):
        assert sanitize_filename("") == "untitled"
        assert sanitize_filename("   ") == "untitled"


class TestInputExpansion:
    """Test \\input{} and \\include{} expansion."""
    
    def test_input_expansion(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            main = tmpdir / "main.tex"
            main.write_text(r"""
\documentclass{article}
\begin{document}
\input{intro}
\end{document}
""")
            intro = tmpdir / "intro.tex"
            intro.write_text(r"\section{Introduction}" + "\nHello world.")
            
            content = read_tex_with_inputs(main, tmpdir)
            
            assert "Introduction" in content
            assert "Hello world" in content
    
    def test_nested_inputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            main = tmpdir / "main.tex"
            main.write_text(r"\input{a}")
            
            a = tmpdir / "a.tex"
            a.write_text(r"A\input{b}A")
            
            b = tmpdir / "b.tex"
            b.write_text("B")
            
            content = read_tex_with_inputs(main, tmpdir)
            assert "A" in content
            assert "B" in content
    
    def test_circular_input_protection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            a = tmpdir / "a.tex"
            a.write_text(r"\input{b}")
            
            b = tmpdir / "b.tex"
            b.write_text(r"\input{a}")  # Circular!
            
            content = read_tex_with_inputs(a, tmpdir)
            assert "CIRCULAR" in content


class TestEquationCounting:
    """Test equation environment counting."""
    
    def test_equation_env(self):
        content = r"""
\begin{equation}
E = mc^2
\end{equation}
"""
        assert count_equations(content) == 1
    
    def test_align_env(self):
        content = r"""
\begin{align}
a &= b \\
c &= d
\end{align}
"""
        assert count_equations(content) == 1
    
    def test_display_math(self):
        content = r"$$x^2$$ and \[y^2\]"
        # $$ counts as 2 (opening and closing), \[ counts as 1
        assert count_equations(content) >= 2
    
    def test_multiple_types(self):
        content = r"""
\begin{equation}a\end{equation}
\begin{align}b\end{align}
$$c$$
"""
        # At least 3 equation-like environments
        assert count_equations(content) >= 3


class TestFigureCounting:
    """Test figure environment counting."""
    
    def test_figure_env(self):
        content = r"""
\begin{figure}
\includegraphics{img.png}
\end{figure}
\begin{figure}[h]
\includegraphics{img2.png}
\end{figure}
"""
        assert count_figures(content) == 2


class TestTableCounting:
    """Test table environment counting."""
    
    def test_table_env(self):
        content = r"""
\begin{table}
\begin{tabular}{cc}
a & b
\end{tabular}
\end{table}
"""
        assert count_tables(content) == 1


class TestKeyTermExtraction:
    """Test key term extraction."""
    
    def test_textbf_extraction(self):
        content = r"The \textbf{score function} is important."
        terms = extract_key_terms(content)
        assert "score function" in terms
    
    def test_emph_extraction(self):
        content = r"We use \emph{variational inference}."
        terms = extract_key_terms(content)
        assert "variational inference" in terms
    
    def test_max_terms(self):
        content = r"\textbf{a} \textbf{b} \textbf{c} \textbf{d}"
        terms = extract_key_terms(content, max_terms=2)
        assert len(terms) <= 2


class TestReadingTimeEstimation:
    """Test reading time estimation."""
    
    def test_short_content(self):
        content = "Hello world. " * 100  # ~200 words
        time = estimate_reading_time(content, wpm=200)
        assert time == 1  # 1 minute minimum
    
    def test_longer_content(self):
        content = "Word " * 1000  # 1000 words
        time = estimate_reading_time(content, wpm=200)
        assert time == 5  # 5 minutes


class TestRealPaperParsing:
    """Integration tests using actual downloaded papers."""
    
    @pytest.fixture
    def paper_2510(self):
        paper_dir = Path(__file__).parent.parent / "papers" / "2510.21890"
        if not paper_dir.exists():
            pytest.skip("Paper 2510.21890 not downloaded")
        return paper_dir
    
    @pytest.fixture
    def paper_2312(self):
        paper_dir = Path(__file__).parent.parent / "papers" / "2312.07511"
        if not paper_dir.exists():
            pytest.skip("Paper 2312.07511 not downloaded")
        return paper_dir
    
    def test_2510_index_exists(self, paper_2510):
        index_path = paper_2510 / "index.json"
        assert index_path.exists()
        
        index = json.loads(index_path.read_text())
        assert index['summary']['total_sections'] == 22
        assert index['summary']['total_equations'] > 3000
    
    def test_2510_sections_exist(self, paper_2510):
        sections_dir = paper_2510 / "sections"
        assert sections_dir.exists()
        
        tex_files = list(sections_dir.glob("*.tex"))
        assert len(tex_files) == 22
    
    def test_2510_section_content_valid(self, paper_2510):
        first_section = paper_2510 / "sections" / "01_chapter_preface_and_roadmap.tex"
        if first_section.exists():
            content = first_section.read_text()
            assert r"\chapter" in content or r"\section" in content
    
    def test_2312_index_exists(self, paper_2312):
        index_path = paper_2312 / "index.json"
        assert index_path.exists()
        
        index = json.loads(index_path.read_text())
        assert index['summary']['total_sections'] == 14
    
    def test_2312_sections_exist(self, paper_2312):
        sections_dir = paper_2312 / "sections"
        assert sections_dir.exists()
        
        tex_files = list(sections_dir.glob("*.tex"))
        assert len(tex_files) == 14
    
    def test_index_structure(self, paper_2510):
        index = json.loads((paper_2510 / "index.json").read_text())
        
        assert 'paper_id' in index
        assert 'indexed_at' in index
        assert 'summary' in index
        assert 'sections' in index
        
        for section in index['sections']:
            assert 'number' in section
            assert 'title' in section
            assert 'file' in section
            assert 'lines' in section
            assert 'equations' in section


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

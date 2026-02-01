# Copilot Instructions for arxiv-reading-assistant

## Build and Test

```bash
# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_parsing.py -v

# Run a specific test class or method
python -m pytest tests/test_parsing.py::TestBraceExtraction -v
python -m pytest tests/test_parsing.py::TestArxivIdParsing::test_abs_url -v
```

No external dependencies beyond pytest. Python standard library only.

## Architecture

**Two-repo design (sibling directories):**
- `arxiv-reading-assistant/` — **Public, generic tools.** Scripts, skill definitions, and tests that are reusable across users. This is the repo you're in.
- `arxiv-reading-data/` — **Private, personal data.** Downloaded papers, reading session logs, and notes. Contains cached arXiv sources and user-specific history. Never committed to the public repo.

**Paper processing pipeline:**
1. `download_arxiv.py` — Downloads arXiv source tar.gz, extracts tex files
2. `split_sections.py` — Expands `\input{}` includes, splits by section/chapter
3. `build_index.py` — Counts equations/figures, extracts key terms, estimates reading time

**Entry points:**
- `python -m skills.paper_init <arxiv_id>` — Full pipeline
- `python scripts/process_paper.py <arxiv_id>` — Alternative full pipeline
- Individual scripts can run standalone

**Output directory:** All scripts default to `../arxiv-reading-data/papers/` (sibling data repo). Override with `ARXIV_DATA_DIR` env var or `--output-dir` flag.

**Skills system:** Markdown files in `skills/` define slash commands that the AI assistant recognizes:
- `/paper-init <arxiv_id>` — Download and parse a paper
- `/privacy-scan` — Check for sensitive data before pushing
- `/stage-commit` — Privacy scan + commit workflow
- `/talk-shit <paper_id> section <n>` — Start focused reading session
- `/okay` — End session, log insights, get encouragement

## Key Conventions

**Privacy-first workflow:** Always run `python scripts/privacy_scan.py .` before pushing. The pre-push hook in `scripts/hooks/pre-push` automates this. High-severity findings (HOME paths, usernames, API keys) block commits.

**File header:** All Python files include GPL-3.0 license header with AI-generation disclaimer.

**Target audience context:** This tool translates ML concepts to physics analogies. When explaining code or features, use mappings like:
- Loss landscape → potential energy surface
- Gradient descent → steepest descent / relaxation
- Attention → weighted averaging / kernel
- Dropout → ensemble averaging

**Session management:** 
- Daily logs: `sessions/YYYY-MM-DD.md`
- Weekly insights: `notes/YYYY-Www-gaps.md` and `notes/YYYY-Www-mastered.md`
- Section taxonomy cached in `papers/<id>/taxonomy/`

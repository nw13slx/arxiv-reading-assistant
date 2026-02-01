# Paper Init Skill

Initialize a paper for reading by downloading, parsing, and indexing it.

## Usage

```
/paper-init <arxiv_id_or_url>
```

## Examples

```
/paper-init 2510.21890
/paper-init https://arxiv.org/abs/2312.07511
```

## What It Does

1. Downloads the arXiv source (tex files)
2. Finds the main tex file and expands all \input{} includes
3. Splits into sections/chapters for focused reading
4. Builds an index with:
   - Section titles and file paths
   - Line counts, equation counts, figure counts
   - Estimated reading time per section
   - Key terms per section

## Output

After init, you'll have:
```
papers/<arxiv_id>/
├── src/              # Raw tex source
├── sections/         # Split section files
├── index.md          # Human-readable index
├── index.json        # Machine-readable index
└── metadata.txt      # Paper metadata
```

## Then Say

- "Show me the index" - See paper structure
- "Let's read section 3" - Start focused reading
- "What's this paper about?" - Get overview

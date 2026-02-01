# Talk Shit Skill

Start a focused reading session on a specific section, equation, or passage.

## Usage

```
/talk-shit <paper_id> section <number_or_title>
/talk-shit <paper_id> equation <label_or_number>
/talk-shit <paper_id> "exact text to find"
```

## Examples

```
/talk-shit 2510.21890 section 12
/talk-shit 2510.21890 section variational
/talk-shit 2510.21890 equation eq:elbo
/talk-shit 2510.21890 "score function"
```

## What It Does

1. **Locates** the target in parsed tex files (via Python, token-efficient)
2. **Builds taxonomy** of the section if not cached:
   - Section/subsection hierarchy
   - Key equations with labels
   - Key terms (bold/emphasized)
3. **Loads** the section content for discussion
4. **Locks** the session to this section until `/okay`

## During Session

Ask anything about the section:
- "What's the main idea here?"
- "Explain equation 3.14 like I'm a physicist"
- "What's the relationship between X and Y?"
- "I don't understand this paragraph..."

The assistant will:
- Answer using physics analogies when helpful
- Stay focused on this section
- Track what you understand vs. struggle with

## Ending Session

Say `/okay` to:
- Summarize the conversation
- Log to daily session file
- Record gaps and mastered concepts
- Get encouragement and tomorrow's focus

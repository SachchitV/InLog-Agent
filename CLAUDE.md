# Inlog-Agent

## Project Overview
- (TODO: describe the project)

## Tech Stack
- **Language**: Python 3.11+

## Common Commands
- `pip install -r requirements.txt` - Install dependencies
- `pytest -v` - Run tests

## Virtual Environment
Always activate a Python virtual environment before running any Python commands or installing dependencies.

---

# Coding Guidelines

## Incremental Development
- **40-50 lines max per step**: Break tasks into small chunks
- **One change at a time**: Complete each step before moving on

## Code Quality
- **Comments**:
  - Function docstrings: Explain both the logic (what it does) and intention (why it exists)
  - Inline comments: Use one-liner comments at regular intervals for easy readability
- **Spacing**: Blank lines between logical blocks

## Logging
- Use `logging.getLogger(__name__)` in every module — never `print()`

## Error Handling
- **Avoid try-except**: Do not use unless absolutely necessary
- Let errors propagate naturally for easier debugging

## Repository Etiquette
- **Main branch**: `main`
- **Commit messages**: Descriptive, include what and why

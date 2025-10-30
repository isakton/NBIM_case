# LLM-Powered Dividend Reconciliation

Hybrid system combining deterministic rules with multi-provider LLM agents for intelligent dividend break analysis.

## Quick Start
```bash
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
jupyter notebook demo.ipynb
```

## What It Does

- Rules engine detects breaks (deterministic, auditable)
- OpenAI classifies severity (fast, cheap)
- Claude analyzes root causes (thorough, smart)
- Caching minimizes costs (~$0.0001 per run after first)

## Results

Analyzes 2 test breaks: Samsung (complex multi-factor) and Nestlé (quantity mismatch).

See `ARCHITECTURE.md` for design decisions.

## Requirements

- Python 3.9+
- OpenAI API key
- Anthropic API key
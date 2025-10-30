# NBIM Dividend Reconciliation - LLM-Powered System

An intelligent reconciliation system using multi-provider LLM agents (OpenAI + Anthropic) to automatically detect, classify, and explain dividend booking discrepancies.

## Setup

### 1. Prerequisites
- Python 3.9+
- OpenAI API account
- Anthropic API account

### 2. Installation
```bash
# Clone repository
git clone <your-repo-url>
cd nbim-reconciliation

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Run Demo
```bash
# Start Jupyter notebook
jupyter notebook

# Open demo.ipynb and run all cells
```

## Project Structure
```
nbim-reconciliation/
├── demo.ipynb              # Live demonstration notebook
├── reconciliation.py       # Core reconciliation logic
├── llm_analyzer.py        # Multi-provider LLM integration
├── data/                  # Test data (2 CSV files)
└── cache/                 # LLM response cache (auto-generated)
```

## Features

- **Multi-provider LLM agents**: OpenAI for classification, Claude for analysis
- **Intelligent caching**: Avoid redundant API calls
- **Cost tracking**: Monitor API usage in real-time
- **Structured output**: JSON-formatted break analysis

## Architecture

1. **Rules Engine**: Deterministic break detection
2. **Classifier Agent** (GPT-4o-mini): Fast severity classification
3. **Analyzer Agent** (Claude Sonnet): Deep root cause analysis
4. **Prioritization**: Risk-based break ranking

## Cost Analysis

Estimated API costs for 3 test cases: ~$0.50
- OpenAI (classification): ~$0.10
- Anthropic (analysis): ~$0.40

## Interview Demo

Run `demo.ipynb` for 8-minute live demonstration covering:
1. Data loading & reconciliation
2. Multi-agent break analysis
3. Innovation showcase
4. Risk & safeguards discussion
# LLM-Powered Dividend Reconciliation - Architecture

## What I Built

A working prototype demonstrating how LLMs can enhance dividend reconciliation through intelligent analysis and prioritization, not just automation.

**Core Insight:** LLMs shouldn't replace deterministic processes - they should add intelligence where humans currently struggle: explaining complex breaks, prioritizing work, and suggesting actions.

---

## System Design

### Rules Engine (Python + Pandas)
**What it does:** Compares NBIM and custodian data field-by-field

**Why rules, not LLM:**
- Numerical comparison must be exact and auditable
- Zero cost, sub-second performance
- No risk of hallucination on arithmetic

**Output:** List of breaks with exact differences

---

### Multi-Agent LLM Layer

I implemented a 2-agent system using different providers for different tasks:

#### Agent 1: Classifier (OpenAI GPT-4o-mini)
**Task:** Quick severity assessment

**Why GPT-4o-mini:**
- 10x cheaper than Claude ($0.15 vs $3 per 1M tokens)
- Classification is simpler than analysis
- Fast response time

**Cost:** ~$0.0001 per break

#### Agent 2: Analyzer (Anthropic Claude Sonnet 4.5)
**Task:** Root cause analysis and remediation suggestions

**Why Claude:**
- Better at complex financial reasoning
- More detailed explanations
- Larger context window for full break details

**Cost:** ~$0.01 per break

---

## Key Design Decisions

### 1. Why Multi-Provider?
**Cost optimization:** Use cheap model for simple tasks, expensive model for complex reasoning

**Redundancy:** If one API is down, the other can take over

**Best-of-breed:** Each provider has strengths

### 2. Why Hybrid (Rules + LLM)?
**Rules for:** Detection, calculation, validation (must be deterministic)

**LLMs for:** Explanation, prioritization, remediation advice (benefit from intelligence)

**Example:** Rules detect "shares differ by 2,000" - LLM explains "this matches securities lending quantity, likely not recalled before ex-date"

### 3. Caching Strategy
Every LLM response is cached to disk (JSON files)

**Why:**
- Development doesn't burn budget
- Re-running demos is free
- Production would cache common break patterns

**Cost savings:** After first run, subsequent runs cost $0

---

## What's Actually Implemented

**reconciliation.py:**
- Load CSV files
- Match records by event key + ISIN + bank account
- Calculate differences in shares, amounts, taxes, dates
- Flag securities lending scenarios
- Output structured Break objects

**llm_analyzer.py:**
- Call OpenAI for severity classification
- Call Claude for detailed analysis
- Cache all responses to avoid repeat costs
- Track API costs in real-time
- Parse JSON responses with fallback handling

**demo.ipynb:**
- Interactive demonstration of full pipeline
- Shows break detection, LLM analysis, prioritization
- Documents actual API costs

---

## Safeguards I'd Add for Production

### Confidence Thresholds
```python
if confidence < 70:
    # Escalate to human analyst
elif severity in ['CRITICAL', 'HIGH']:
    # Require human approval
else:
    # Can auto-process
```

### Financial Gates
- Breaks > $100K: Always human review
- Breaks $10K-$100K: Senior analyst
- Breaks < $10K: Auto-process if confident

### Audit Trail
- Log every LLM input/output
- Track which decisions were automated vs manual
- Version control all prompts

---

## Production Architecture Vision

**What I'd build next:**

1. **Remediation Agent:** Draft emails to custodians
2. **Risk Agent:** Compliance checking and impact calculation  
3. **Monitoring Agent:** Track accuracy vs human baseline

**Rollout strategy:**
- Month 1-2: Shadow mode (LLM suggests, human decides)
- Month 3-4: Auto-process LOW severity only
- Month 5-6: Expand to MEDIUM severity
- Always keep human in loop for HIGH/CRITICAL

---

## Cost Analysis

**This demo:** $0.0001 total (first run with 2 breaks)

**At scale (400 breaks/month):**
- Triage: 400 × $0.0001 = $0.04
- Analysis: 400 × $0.01 = $4.00
- **Total: ~$5/month in API costs**

**Compare to:** 400 breaks × 30 min = 200 analyst hours/month

**If 70% automated:** Save 140 hours/month

---

## Risk Mitigation

**Risk: LLM hallucination**
- Structured JSON output reduces this
- Confidence scoring flags uncertain analysis
- Rules engine still catches all breaks

**Risk: API downtime**
- Multi-provider setup provides fallback
- Can queue breaks for later processing

**Risk: Over-automation**
- Start with shadow mode
- Gradual rollout by severity level
- Always require human approval for material amounts

---

## What I Learned Building This

1. **Multi-provider is practical:** Different models have different strengths and costs
2. **Caching is essential:** Development would be expensive otherwise
3. **Structured output matters:** JSON schema helps prevent hallucinations
4. **Rules vs LLM is about auditability:** Financial operations need deterministic foundations

---

## Technical Stack

- Python 3.9
- pandas for data manipulation
- OpenAI API (gpt-4o-mini)
- Anthropic API (claude-sonnet-4.5)
- Simple file-based caching

**Total development time:** ~10 hours

**Lines of code:** ~800 (clean, readable, well-documented)

---

## Next Steps for Production

**Technical:**
1. Add more robust error handling
2. Implement retry logic for API failures
3. Build analyst dashboard UI
4. Add database for audit trail

**Operational:**
1. Run 3-month pilot on LOW severity breaks
2. Measure accuracy against human baseline
3. Collect analyst feedback on suggestions
4. Iterate on prompts based on real data

**Business:**
1. Calculate actual ROI from pilot
2. Get audit/compliance sign-off on approach
3. Present results to leadership
4. Scale if successful
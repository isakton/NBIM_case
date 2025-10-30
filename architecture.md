# Architecture

## What I Built

A prototype showing how LLMs add intelligence to dividend reconciliation - not replacing deterministic processes, but enhancing them with explanation and prioritization.

---

## Design

### Rules Engine
- Compares NBIM vs custodian data field-by-field
- Detects all breaks deterministically
- Zero cost, sub-second, auditable

### LLM Layer (2 agents)

**Agent 1: Classifier (OpenAI GPT-4o-mini)**
- Fast severity assessment
- 10x cheaper than Claude
- Cost: $0.0001 per break

**Agent 2: Analyzer (Claude Sonnet 4.5)**
- Root cause analysis
- Better at complex reasoning
- Cost: $0.01 per break

---

## Key Decisions

**Why multi-provider?**
- Cost: Use cheap model for simple tasks
- Redundancy: Fallback if one API fails
- Quality: Each provider has strengths

**Why rules + LLM hybrid?**
- Rules for detection (deterministic, auditable)
- LLMs for intelligence (explanation, context)
- Example: Rules find "2,000 share difference" → LLM explains "matches securities lending, likely not recalled"

**Why caching?**
- First run costs money, subsequent runs free
- Essential for development without burning budget

---

## What's Implemented

`reconciliation.py` - Rules-based break detection  
`llm_analyzer.py` - Multi-provider LLM calls with caching  
`demo.ipynb` - Interactive demonstration

---

## Production Safeguards

**Confidence thresholds:**
- < 70% confidence → human review
- CRITICAL/HIGH severity → human approval
- > 90% confidence + LOW severity → can auto-process

**Financial gates:**
- > $100K → always human
- $10K-$100K → senior analyst
- < $10K → auto if confident

**Audit trail:**
- Log all LLM inputs/outputs
- Track automated vs manual decisions

---

## Next Steps

**Rollout:**
1. Shadow mode (2 months) - LLM suggests, human decides
2. Auto-process LOW severity only
3. Expand to MEDIUM after validation
4. Always human-in-loop for HIGH/CRITICAL

**Additional agents:**
- Remediation: Draft custodian emails
- Risk: Compliance checks
- Monitor: Track accuracy vs humans

---

## Cost Analysis

**Demo:** $0.0001 (with caching)

**At scale (400 breaks/month):**
- API costs: ~$5/month
- Human review (30%): 60 hours/month
- vs Manual (100%): 200 hours/month
- **Savings: 140 hours/month**
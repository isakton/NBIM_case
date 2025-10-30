# LLM-Powered Dividend Reconciliation System - Architecture

## Executive Summary

This system combines deterministic rules-based reconciliation with multi-provider LLM intelligence to automate dividend break detection, classification, and remediation for NBIM's 8,000+ annual dividend events.

**Key Design Principles:**
- Rules for detection (fast, deterministic, auditable)
- LLMs for explanation (intelligent, contextual, scalable)
- Human-in-loop for high-risk decisions (safe, compliant)

---

## Current Implementation: 2-Agent System

### Agent 1: Classifier (OpenAI GPT-4o-mini)
**Role:** Fast severity classification of breaks

**Input:** Break data (shares, amounts, tax rates, dates)

**Output:** 
```json
{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "confidence": 85,
  "reasoning": "Brief explanation"
}
```

**Rationale:** 
- GPT-4o-mini is 10x cheaper than Claude ($0.15 vs $3 per 1M input tokens)
- Classification is a simpler task requiring less reasoning depth
- Fast response time for high-volume processing

**Cost:** ~$0.0001 per break

---

### Agent 2: Analyzer (Anthropic Claude Sonnet 4.5)
**Role:** Deep root cause analysis and remediation guidance

**Input:** Break data + classification

**Output:**
```json
{
  "root_cause": "Primary reason in 2-3 sentences",
  "contributing_factors": ["Factor 1", "Factor 2"],
  "recommended_actions": ["Action 1", "Action 2"],
  "risk_assessment": "Impact if unresolved",
  "confidence": 92
}
```

**Rationale:**
- Claude excels at complex reasoning and financial analysis
- Longer context window (200K tokens) handles full market data
- More nuanced understanding of edge cases

**Cost:** ~$0.01 per break

---

### Rules Engine (Deterministic)
**Role:** Break detection through field-by-field comparison

**Process:**
1. Match records by COAC_EVENT_KEY + ISIN + Bank Account
2. Compare: shares, amounts, tax rates, dates
3. Flag discrepancies with exact differences
4. Identify securities lending scenarios

**Rationale:**
- Numerical comparison must be deterministic for audit compliance
- Zero cost, sub-second performance
- No risk of LLM hallucination on basic arithmetic

---

## Production Architecture: 5-Agent System

### Vision for Scale
```
Data Ingestion
      ↓
┌─────────────────────────────────────────┐
│   Rules Engine (Deterministic)          │
│   - Break Detection                      │
│   - Field Comparison                     │
│   - Data Validation                      │
└─────────────────────────────────────────┘
      ↓
   Breaks Found?
      ↓
┌─────────────────────────────────────────┐
│   Agent 1: Triage (GPT-4o-mini)         │
│   - Severity Classification              │
│   - Initial Categorization               │
│   - Priority Scoring                     │
└─────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────┐
│   Agent 2: Analyzer (Claude Opus)       │
│   - Root Cause Analysis                  │
│   - Pattern Recognition                  │
│   - Historical Context                   │
└─────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────┐
│   Agent 3: Remediation (Claude Sonnet)  │
│   - Action Planning                      │
│   - Custodian Communication Drafts       │
│   - Internal Escalation Routing          │
└─────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────┐
│   Agent 4: Risk Assessor (GPT-4)        │
│   - Compliance Check                     │
│   - Financial Impact Calculation         │
│   - Confidence Scoring                   │
└─────────────────────────────────────────┘
      ↓
   Risk Level?
      ↓
   HIGH/CRITICAL → Human Review
      ↓
   LOW/MEDIUM → Auto-Process
      ↓
┌─────────────────────────────────────────┐
│   Agent 5: Monitor (Background)         │
│   - Pattern Learning                     │
│   - Accuracy Tracking                    │
│   - Cost Optimization                    │
└─────────────────────────────────────────┘
```

---

## Agent Responsibilities

### Agent 1: Triage Agent (Fast Classifier)
**Model:** GPT-4o-mini  
**Cost:** $0.15 per 1M input tokens  
**Latency:** 0.5-1 second  

**Responsibilities:**
- Binary severity classification
- Initial break categorization
- Priority queue ordering

**Triggers:** Every break detected by rules engine

**Output:** Structured JSON with severity + confidence

---

### Agent 2: Analysis Agent (Deep Reasoner)
**Model:** Claude Opus 4 or Sonnet 4.5  
**Cost:** $15 per 1M input tokens  
**Latency:** 2-5 seconds  

**Responsibilities:**
- Root cause identification
- Contributing factor analysis
- Market context incorporation
- Pattern recognition across similar breaks

**Triggers:** All MEDIUM+ severity breaks, sample of LOW breaks

**Output:** Detailed analysis with remediation paths

---

### Agent 3: Remediation Agent (Action Planner)
**Model:** Claude Sonnet 4.5  
**Cost:** $3 per 1M input tokens  
**Latency:** 2-3 seconds  

**Responsibilities:**
- Generate custodian communication drafts
- Create internal escalation tickets
- Suggest automated fixes for common patterns
- Track remediation workflows

**Triggers:** After analysis completion

**Output:** Actionable tasks with assignees and deadlines

---

### Agent 4: Risk Agent (Compliance Guardian)
**Model:** GPT-4 or Claude Opus  
**Cost:** $30 per 1M input tokens  
**Latency:** 3-4 seconds  

**Responsibilities:**
- Regulatory compliance checking
- Financial impact quantification
- Confidence score validation
- Fraud pattern detection

**Triggers:** All CRITICAL breaks, random sampling of others

**Output:** Risk score + approval/escalation decision

---

### Agent 5: Monitoring Agent (Learning System)
**Model:** Fine-tuned model on historical data  
**Cost:** Custom pricing  
**Latency:** Background processing  

**Responsibilities:**
- Track LLM accuracy vs human analyst decisions
- Identify new break patterns over time
- Optimize prompt engineering based on feedback
- Cost/benefit analysis and reporting

**Triggers:** Continuous background operation

**Output:** Weekly reports, model improvements

---

## Safeguards & Governance

### 1. Confidence Thresholds
```python
if confidence < 70:
    escalate_to_human()
elif confidence < 90 and severity in ['CRITICAL', 'HIGH']:
    escalate_to_human()
else:
    auto_process()
```

### 2. Financial Impact Gates
- Breaks > $100K: Always require human approval
- Breaks $10K-$100K: Senior analyst review
- Breaks < $10K: Auto-process if confidence > 90%

### 3. Audit Trail
Every LLM decision logged with:
- Timestamp
- Model and version
- Input prompt (sanitized)
- Raw output
- Confidence score
- Human override (if any)

### 4. Human-in-the-Loop
**Required for:**
- CRITICAL severity breaks
- Low confidence classifications (< 70%)
- New break patterns not seen before
- Any custodian communication before sending

**Optional for:**
- MEDIUM severity with high confidence
- Routine break types with established patterns

### 5. Rollback Mechanism
- All automated actions are reversible
- 24-hour review window before finalizing
- Manual override always available
- Version control on all decisions

---

## Data Flow

### Input Sources
1. **NBIM Internal System**
   - Dividend bookings (expected)
   - Position files
   - Tax calculations

2. **Custodian Feed**
   - Actual dividend notifications
   - Settlement confirmations
   - Corporate action alerts

### Processing Pipeline
```
1. Data Ingestion (Daily 6:00 AM)
   ↓
2. Rules Engine (6:05 AM)
   ↓
3. Break Detection (6:10 AM)
   ↓
4. LLM Agent Processing (6:15-7:00 AM)
   ↓
5. Human Review Queue (7:00 AM)
   ↓
6. Remediation Execution (Throughout day)
   ↓
7. Daily Report (5:00 PM)
```

### Output Artifacts
1. **Break Report** (JSON + PDF)
2. **Priority Queue** (for analyst dashboard)
3. **Draft Communications** (emails to custodians)
4. **Escalation Tickets** (in case management system)
5. **Audit Log** (immutable record)

---

## Cost Analysis

### Current System (Manual)
- 8,000 dividend events/year
- ~5% break rate = 400 breaks/month
- Average 30 min per break investigation
- 200 analyst hours/month
- Cost: ~$10,000/month (salary + overhead)

### Proposed System (LLM-Enhanced)
**Per Break Costs:**
- Rules engine: $0
- Triage agent: $0.0001
- Analysis agent: $0.01
- Risk agent: $0.02
- Total: ~$0.03 per break

**Monthly Costs:**
- 400 breaks × $0.03 = $12/month (API costs)
- Human review (30% of breaks): 60 hours/month
- Cost: ~$3,000/month

**Savings:** $7,000/month = $84,000/year

**ROI:** 70% reduction in analyst time, 10-15x return on investment

---

## Scalability Considerations

### Current Implementation (MVP)
- Handles: 3 test cases
- Latency: 5-10 seconds per break
- Cost: $0.01 per break
- Throughput: ~360 breaks/hour

### Production Target
- Handles: 8,000 events/year = ~30 breaks/day
- Latency: < 30 seconds per break
- Cost: $0.03 per break
- Throughput: 120 breaks/hour (sufficient)

### Scale to 10x Volume
- Handles: 80,000 events/year = ~300 breaks/day
- Solution: Parallel agent processing
- Cost: Still $0.03 per break (linear scaling)
- Infrastructure: Add 3-5 additional API workers

---

## Risk Mitigation

### Technical Risks

**Risk 1: LLM Hallucination**
- Mitigation: Confidence scoring, human review thresholds
- Fallback: Rules-based classification when confidence < 70%

**Risk 2: API Downtime**
- Mitigation: Multi-provider setup (OpenAI + Anthropic)
- Fallback: Queue breaks for processing when service returns

**Risk 3: Cost Overruns**
- Mitigation: Cost tracking per break, daily budget alerts
- Fallback: Pause automated processing if budget exceeded

### Operational Risks

**Risk 4: Over-Automation**
- Mitigation: Gradual rollout, start with LOW severity only
- Monitoring: Track error rate vs manual baseline

**Risk 5: Regulatory Compliance**
- Mitigation: Full audit trail, human approval for material breaks
- Documentation: All decisions explainable and traceable

### Financial Risks

**Risk 6: Incorrect Remediation**
- Mitigation: Dry-run mode for first 3 months
- Validation: Compare LLM recommendations to human analyst decisions

**Risk 7: Missing Critical Breaks**
- Mitigation: Rules engine catches ALL discrepancies
- Backup: Daily reconciliation report reviewed by senior analyst

---

## Rollout Strategy

### Phase 1: Pilot (Month 1-2)
- Run in shadow mode alongside manual process
- Process: LOW severity breaks only
- Compare: LLM analysis vs human analyst
- Metrics: Accuracy, latency, cost

### Phase 2: Partial Automation (Month 3-4)
- Auto-process: LOW severity with confidence > 90%
- Human review: MEDIUM+ severity
- Feedback: Analysts rate LLM suggestions
- Iterate: Improve prompts based on feedback

### Phase 3: Full Automation (Month 5-6)
- Auto-process: LOW and MEDIUM severity
- Human review: HIGH and CRITICAL only
- Monitoring: Daily accuracy reports
- Optimization: Cost and latency improvements

### Phase 4: Scale (Month 7+)
- Expand: Additional custodians, asset classes
- Intelligence: Pattern learning from historical data
- Innovation: Predictive break detection

---

## Success Metrics

### Quantitative
- Break detection rate: 100% (same as manual)
- False positive rate: < 5%
- Average processing time: < 30 seconds per break
- Analyst time saved: > 60%
- Cost per break: < $0.05

### Qualitative
- Analyst satisfaction with LLM recommendations
- Custodian feedback on communication quality
- Audit team approval of compliance trail
- Reduction in SLA breaches

---

## Future Enhancements

### Short Term (6 months)
1. **Pattern Recognition**: Identify recurring break types by custodian/market
2. **Predictive Analytics**: Flag high-risk dividends before ex-date
3. **Automated Testing**: Generate synthetic breaks for continuous validation

### Medium Term (12 months)
1. **Multi-Asset Support**: Expand beyond equities to bonds, derivatives
2. **Real-Time Processing**: Move from daily batch to streaming reconciliation
3. **Self-Learning**: Fine-tune models on NBIM-specific data

### Long Term (24 months)
1. **Autonomous Remediation**: Auto-communicate with custodians for routine breaks
2. **Cross-System Integration**: Link to trading, risk, and compliance systems
3. **Industry Collaboration**: Share anonymized patterns with other asset managers

---

## Conclusion

This architecture balances innovation with pragmatism:
- **Deterministic where necessary** (break detection, arithmetic)
- **Intelligent where valuable** (explanation, prioritization, remediation)
- **Human where critical** (high-risk decisions, regulatory compliance)

The system is designed for gradual adoption, full auditability, and linear scalability as NBIM's portfolio grows.

**Key Differentiators:**
1. Multi-provider LLM approach (cost optimization)
2. Hybrid rules + LLM design (reliability + intelligence)
3. Comprehensive safeguards (financial services grade)
4. Clear rollout path (de-risk adoption)

Total development time for MVP: 10 hours  
Estimated production deployment: 3-4 months  
Expected ROI: $84K/year in analyst time savings
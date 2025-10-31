"""
Multi-provider LLM integration for dividend reconciliation analysis.
Uses OpenAI for classification and Anthropic Claude for deep analysis.
"""

import os
import json
import hashlib
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv

from reconciliation import Break


# Load environment variables
load_dotenv()


class LLMCache:
    """Simple file-based cache for LLM responses to save API costs."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _generate_key(self, provider: str, model: str, prompt: str) -> str:
        """Generate cache key from prompt."""
        content = f"{provider}:{model}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, provider: str, model: str, prompt: str) -> Optional[Dict]:
        """Retrieve cached response if exists."""
        key = self._generate_key(provider, model, prompt)
        cache_file = self.cache_dir / f"{key}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                print(f"Cache hit for {provider}/{model}")
                return cached['response']
        return None
    
    def set(self, provider: str, model: str, prompt: str, response: Dict) -> None:
        """Store response in cache."""
        key = self._generate_key(provider, model, prompt)
        cache_file = self.cache_dir / f"{key}.json"
        
        with open(cache_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'provider': provider,
                'model': model,
                'response': response
            }, f, indent=2)


class CostTracker:
    """Track API costs across providers."""
    
    # Pricing per 1M tokens (as of Oct 2024)
    PRICES = {
        'openai': {
            'gpt-4o-mini': {'input': 0.150, 'output': 0.600},
        },
        'anthropic': {
            'claude-sonnet-4.5': {'input': 3.00, 'output': 15.00},
        }
    }
    
    def __init__(self):
        self.costs = []
    
    def add_call(self, provider: str, model: str, input_tokens: int, output_tokens: int):
        """Record an API call."""
        prices = self.PRICES.get(provider, {}).get(model, {'input': 0, 'output': 0})
        
        input_cost = (input_tokens / 1_000_000) * prices['input']
        output_cost = (output_tokens / 1_000_000) * prices['output']
        total_cost = input_cost + output_cost
        
        self.costs.append({
            'provider': provider,
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': total_cost
        })
        
        return total_cost
    
    def get_total(self) -> float:
        """Get total cost across all calls."""
        return sum(c['cost'] for c in self.costs)
    
    def print_summary(self):
        """Print cost breakdown."""
        if not self.costs:
            print("\n No API calls made yet")
            return
        
        print(f"\n{'='*60}")
        print(" API Cost Summary")
        print(f"{'='*60}")
        
        by_provider = {}
        for call in self.costs:
            provider = call['provider']
            if provider not in by_provider:
                by_provider[provider] = {'calls': 0, 'cost': 0, 'tokens': 0}
            by_provider[provider]['calls'] += 1
            by_provider[provider]['cost'] += call['cost']
            by_provider[provider]['tokens'] += call['input_tokens'] + call['output_tokens']
        
        for provider, stats in by_provider.items():
            print(f"\n{provider.upper()}:")
            print(f"  Calls: {stats['calls']}")
            print(f"  Tokens: {stats['tokens']:,}")
            print(f"  Cost: ${stats['cost']:.4f}")
        
        total = self.get_total()
        print(f"\n{'─'*60}")
        print(f"TOTAL COST: ${total:.4f}")
        print(f"Budget remaining: ${15 - total:.4f} / $15.00")
        print(f"{'='*60}\n")


class MultiProviderLLM:
    """Orchestrates multiple LLM providers for different tasks."""
    
    def __init__(self, use_cache: bool = True):
        # Initialize clients
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Initialize cache and cost tracker
        self.cache = LLMCache() if use_cache else None
        self.cost_tracker = CostTracker()
        
        print(" LLM clients initialized")
        print(f"   - OpenAI: {'Connected' if os.getenv('OPENAI_API_KEY') else ' Missing API key'}")
        print(f"   - Anthropic: {'Connected' if os.getenv('ANTHROPIC_API_KEY') else 'Missing API key'}")
        print(f"   - Cache: {'Enabled' if use_cache else 'Disabled'}")
    
    def _call_openai(self, prompt: str, model: str = "gpt-4o-mini") -> Dict:
        """Call OpenAI API with caching."""
        # Check cache first
        if self.cache:
            cached = self.cache.get('openai', model, prompt)
            if cached:
                return cached
        
        # Make API call
        print(f"  Calling OpenAI {model}...")
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a financial reconciliation expert. Provide structured, accurate analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for consistent output
        )
        
        # Extract response
        result = {
            'content': response.choices[0].message.content,
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens
        }
        
        # Track cost
        cost = self.cost_tracker.add_call(
            'openai', model,
            result['input_tokens'],
            result['output_tokens']
        )
        print(f"     Cost: ${cost:.4f}")
        
        # Cache response
        if self.cache:
            self.cache.set('openai', model, prompt, result)
        
        return result
    
    def _call_anthropic(self, prompt: str, model: str = "claude-sonnet-4-20250514") -> Dict:
        """Call Anthropic API with caching."""
        # Check cache first
        if self.cache:
            cached = self.cache.get('anthropic', model, prompt)
            if cached:
                return cached
        
        # Make API call
        print(f" Calling Anthropic {model}...")
        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=2000,
            temperature=0.3,
            system="You are a financial reconciliation expert specializing in dividend processing. Provide clear, actionable analysis.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract response
        result = {
            'content': response.content[0].text,
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens
        }
        
        # Track cost
        cost = self.cost_tracker.add_call(
            'anthropic', model,
            result['input_tokens'],
            result['output_tokens']
        )
        print(f"     Cost: ${cost:.4f}")
        
        # Cache response
        if self.cache:
            self.cache.set('anthropic', model, prompt, result)
        
        return result
    
    def classify_break(self, break_obj: Break) -> Dict:
        """
        Use OpenAI (fast/cheap) to classify break severity.
        
        Returns:
            {
                'severity': 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW',
                'confidence': 0-100,
                'reasoning': 'Brief explanation'
            }
        """
        prompt = f"""Classify the severity of this dividend reconciliation break.

Break Details:
- Company: {break_obj.company_name}
- Event: {break_obj.event_key}
- Type: {break_obj.break_type}
- Amount Difference: {break_obj.amount_difference:,.2f} {break_obj.currency}
- Shares Difference: {break_obj.shares_difference:,.0f}
- Tax Rate Difference: {break_obj.tax_rate_difference:.1f}%
- Payment Date Difference: {break_obj.payment_date_difference_days} days
- Securities Lending: {break_obj.lending_percentage:.1f}% ({break_obj.loan_quantity:,.0f} shares)

Respond in JSON format:
{{
    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "confidence": 85,
    "reasoning": "Brief 1-2 sentence explanation"
}}

Severity Guidelines:
- CRITICAL: >$100k difference, multiple compounding issues, or regulatory risk
- HIGH: $10k-100k difference, or significant operational impact
- MEDIUM: $1k-10k difference, or minor process issues
- LOW: <$1k difference, expected variance, or informational only
"""
        
        response = self._call_openai(prompt)
        
        # Parse JSON response
        try:
            # Remove any markdown code blocks if present
            content = response['content'].strip()
            if content.startswith('```'):
                # Extract content between code blocks
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            content = content.strip()
            
            classification = json.loads(content)
        except Exception as e:
            # Fallback if JSON parsing fails
            classification = {
                'severity': 'MEDIUM',
                'confidence': 50,
                'reasoning': 'Unable to parse classification'
            }
        
        return classification
    


    def analyze_break(self, break_obj: Break, classification: Dict) -> Dict:
        """
        Use Claude (smart/thorough) for deep root cause analysis.
        """
        prompt = f"""Analyze this dividend reconciliation break and provide remediation guidance.

    Break Information:
    - Company: {break_obj.company_name} ({break_obj.isin})
    - Event Key: {break_obj.event_key}
    - Severity: {classification['severity']}
    - Type: {break_obj.break_type}

    NBIM Records:
    - Shares: {break_obj.nbim_shares:,.0f}
    - Net Amount: {break_obj.nbim_net_amount:,.2f} {break_obj.currency}
    - Tax Rate: {break_obj.nbim_tax_rate:.1f}%
    - Payment Date: {break_obj.nbim_payment_date}

    Custodian Records:
    - Shares: {break_obj.custody_shares:,.0f}
    - Net Amount: {break_obj.custody_net_amount:,.2f} {break_obj.currency}
    - Tax Rate: {break_obj.custody_tax_rate:.1f}%
    - Payment Date: {break_obj.custody_payment_date}

    Discrepancies:
    - Shares: {break_obj.shares_difference:+,.0f}
    - Amount: {break_obj.amount_difference:+,.2f} {break_obj.currency}
    - Tax Rate: {break_obj.tax_rate_difference:+.1f}%
    - Payment Date: {break_obj.payment_date_difference_days:+d} days

    Securities Lending:
    - Loan Quantity: {break_obj.loan_quantity:,.0f} shares ({break_obj.lending_percentage:.1f}%)

    Provide ONLY a valid JSON response with this exact structure:
    {{
        "root_cause": "Brief 2-3 sentence explanation of primary cause",
        "contributing_factors": ["Factor 1", "Factor 2"],
        "recommended_actions": ["Action 1", "Action 2"],
        "risk_assessment": "One sentence on risk if unresolved",
        "confidence": 85
    }}

    Do not include markdown, code blocks, or any text outside the JSON."""
        
        response = self._call_anthropic(prompt)
        
        # Parse JSON response
        try:
            # Remove any markdown code blocks if present
            content = response['content'].strip()
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            content = content.strip()
            
            analysis = json.loads(content)
        except Exception as e:
            # Fallback if parsing fails
            analysis = {
                'root_cause': response['content'][:300] if len(response['content']) > 300 else response['content'],
                'contributing_factors': ['Parsing error - see root_cause for details'],
                'recommended_actions': ['Review manually'],
                'risk_assessment': 'Unable to assess',
                'confidence': 50
            }
        
        return analysis


def analyze_all_breaks(breaks: List[Break], use_cache: bool = True) -> List[Dict]:
    """
    Analyze all breaks using multi-provider LLM approach.
    
    Returns:
        List of enriched break dictionaries with LLM analysis
    """
    llm = MultiProviderLLM(use_cache=use_cache)
    results = []
    
    print(f"\n{'='*80}")
    print(f" Analyzing {len(breaks)} break(s) with Multi-Agent LLM System")
    print(f"{'='*80}\n")
    
    for i, break_obj in enumerate(breaks, 1):
        print(f"Break {i}/{len(breaks)}: {break_obj.company_name}")
        print(f"{'─'*60}")
        
        # Step 1: Classify with OpenAI (fast)
        print("  Step 1: Classification (OpenAI)...")
        classification = llm.classify_break(break_obj)
        print(f"    → Severity: {classification['severity']} (confidence: {classification['confidence']}%)")
        
        # Step 2: Deep analysis with Claude (thorough)
        print("  Step 2: Root Cause Analysis (Claude)...")
        analysis = llm.analyze_break(break_obj, classification)
        print(f"    → Confidence: {analysis.get('confidence', 'N/A')}%")
        
        # Combine results
        result = {
            'break': break_obj.to_dict(),
            'classification': classification,
            'analysis': analysis
        }
        results.append(result)
        
        print()
    
    # Print cost summary
    llm.cost_tracker.print_summary()
    
    return results


def print_analysis_report(results: List[Dict]) -> None:
    """Print a beautiful formatted report of all analyses."""
    print(f"\n{'='*80}")
    print("DIVIDEND RECONCILIATION ANALYSIS REPORT")
    print(f"{'='*80}\n")
    
    # Sort by severity
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    sorted_results = sorted(
        results,
        key=lambda x: severity_order.get(x['classification']['severity'], 99)
    )
    
    for i, result in enumerate(sorted_results, 1):
        break_data = result['break']
        classification = result['classification']
        analysis = result['analysis']
        
    
        
        print(f" Break #{i}: {break_data['company_name']} ({break_data['event_key']})")
        print(f"{'─'*80}")
        print(f"Severity: {classification['severity']} (Confidence: {classification['confidence']}%)")
        print(f"Type: {break_data['break_type']}")
        print(f"Amount Impact: {break_data['amount_difference']:+,.2f} {break_data['currency']}")
        
        print(f"\n Root Cause:")
        print(f"   {analysis['root_cause']}")
        
        if analysis.get('contributing_factors'):
            print(f"\n Contributing Factors:")
            for factor in analysis['contributing_factors']:
                print(f"   • {factor}")
        
        if analysis.get('recommended_actions'):
            print(f"\n Recommended Actions:")
            for action in analysis['recommended_actions']:
                print(f"   {action}")
        
        if analysis.get('risk_assessment'):
            print(f"\n  Risk Assessment:")
            print(f"   {analysis['risk_assessment']}")
        
        print(f"\n{'='*80}\n")
"""Test LLM integration with one break."""

from reconciliation import load_data, find_breaks
from llm_analyzer import analyze_all_breaks, print_analysis_report

# Load data and find breaks
nbim_df, custody_df = load_data(
    'data/NBIM_Dividend_Bookings.csv',
    'data/CUSTODY_Dividend_Bookings.csv'
)

breaks = find_breaks(nbim_df, custody_df)

# Analyze just the first break to test
print(f"Testing with {len(breaks)} breaks...")
#results = analyze_all_breaks(breaks[:1], use_cache=True)  # Just first break
results = analyze_all_breaks(breaks, use_cache=True)

# Print report
print_analysis_report(results)
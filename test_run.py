"""Quick test to verify everything works."""

from reconciliation import load_data, find_breaks, print_breaks_summary

# Load data
print("Loading data...")
nbim_df, custody_df = load_data(
    'data/NBIM_Dividend_Bookings.csv',
    'data/CUSTODY_Dividend_Bookings.csv'
)

print(f"NBIM records: {len(nbim_df)}")
print(f"Custody records: {len(custody_df)}")

# Find breaks
print("\nFinding breaks...")
breaks = find_breaks(nbim_df, custody_df)

# Print summary
print_breaks_summary(breaks)

print(f"\nTotal breaks found: {len(breaks)}")
"""
Core reconciliation logic for dividend bookings.
Compares NBIM internal records with custodian statements.
"""

import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Break:
    """Represents a reconciliation break between NBIM and custodian data."""
    
    event_key: str
    isin: str
    company_name: str
    bank_account: str
    break_type: str
    severity: str = "UNKNOWN"
    
    # NBIM data
    nbim_shares: float = 0
    nbim_gross_amount: float = 0
    nbim_net_amount: float = 0
    nbim_tax_rate: float = 0
    nbim_payment_date: str = ""
    
    # Custody data
    custody_shares: float = 0
    custody_gross_amount: float = 0
    custody_net_amount: float = 0
    custody_tax_rate: float = 0
    custody_payment_date: str = ""
    
    # Differences
    shares_difference: float = 0
    amount_difference: float = 0
    tax_rate_difference: float = 0
    payment_date_difference_days: int = 0
    
    # Additional context
    lending_percentage: float = 0
    loan_quantity: float = 0
    currency: str = ""
    custodian: str = ""
    
    def to_dict(self) -> Dict:
        """Convert break to dictionary for LLM processing."""
        return asdict(self)
    
    def summary(self) -> str:
        """Human-readable summary of the break."""
        return f"{self.break_type} break for {self.company_name} ({self.event_key}): {self.amount_difference:,.2f} {self.currency}"


def load_data(nbim_path: str, custody_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load NBIM and custodian dividend booking data.
    
    Args:
        nbim_path: Path to NBIM CSV file
        custody_path: Path to custody CSV file
        
    Returns:
        Tuple of (nbim_df, custody_df)
    """
    # Both files use semicolon delimiter
    nbim_df = pd.read_csv(nbim_path, sep=';')
    custody_df = pd.read_csv(custody_path, sep=';')
    
    # Clean column names
    nbim_df.columns = nbim_df.columns.str.strip()
    custody_df.columns = custody_df.columns.str.strip()
    
    return nbim_df, custody_df


def parse_date(date_str: str) -> datetime:
    """Parse DD.MM.YYYY date format."""
    try:
        return datetime.strptime(str(date_str).strip(), '%d.%m.%Y')
    except:
        return None


def find_breaks(nbim_df: pd.DataFrame, custody_df: pd.DataFrame) -> List[Break]:
    """
    Find all reconciliation breaks between NBIM and custodian data.
    
    Args:
        nbim_df: NBIM internal bookings
        custody_df: Custodian bookings
        
    Returns:
        List of Break objects
    """
    breaks = []
    
    # Group NBIM data by event_key and bank_account
    for event_key in nbim_df['COAC_EVENT_KEY'].unique():
        nbim_event = nbim_df[nbim_df['COAC_EVENT_KEY'] == event_key]
        custody_event = custody_df[custody_df['COAC_EVENT_KEY'] == event_key]
        
        if custody_event.empty:
            # Event exists in NBIM but not in custody (critical issue)
            continue
        
        # For each bank account in this event
        for _, nbim_row in nbim_event.iterrows():
            bank_account = nbim_row['BANK_ACCOUNT']
            
            # Find matching custody record
            custody_row = custody_event[custody_event['BANK_ACCOUNTS'] == bank_account]
            
            if custody_row.empty:
                continue
                
            custody_row = custody_row.iloc[0]
            
            # Extract key fields
            nbim_shares = float(nbim_row['NOMINAL_BASIS'])
            custody_shares = float(custody_row['HOLDING_QUANTITY'])
            
            nbim_gross = float(nbim_row['GROSS_AMOUNT_QUOTATION'])
            custody_gross = float(custody_row['GROSS_AMOUNT'])
            
            nbim_net = float(nbim_row['NET_AMOUNT_QUOTATION'])
            custody_net = float(custody_row['NET_AMOUNT_QC'])
            
            nbim_tax = float(nbim_row['TOTAL_TAX_RATE'])
            custody_tax = float(custody_row['TAX_RATE'])
            
            nbim_payment_date = str(nbim_row['PAYMENT_DATE'])
            custody_payment_date = str(custody_row['PAY_DATE'])
            
            # Calculate differences
            shares_diff = nbim_shares - custody_shares
            amount_diff = nbim_net - custody_net
            tax_diff = nbim_tax - custody_tax
            
            # Date difference
            nbim_date = parse_date(nbim_payment_date)
            custody_date = parse_date(custody_payment_date)
            date_diff_days = 0
            if nbim_date and custody_date:
                date_diff_days = (custody_date - nbim_date).days
            
            # Determine break type
            break_types = []
            if abs(shares_diff) > 0.01:
                break_types.append("QUANTITY")
            if abs(amount_diff) > 0.01:
                break_types.append("AMOUNT")
            if abs(tax_diff) > 0.01:
                break_types.append("TAX")
            if abs(date_diff_days) > 0:
                break_types.append("DATE")
            
            # Check for securities lending
            lending_pct = float(custody_row.get('LENDING_PERCENTAGE', 0))
            loan_qty = float(custody_row.get('LOAN_QUANTITY', 0))
            if lending_pct > 0 or loan_qty > 0:
                break_types.append("SECURITIES_LENDING")
            
            # Only create break if there are issues
            if break_types or abs(amount_diff) > 0.01:
                break_type = ", ".join(break_types) if break_types else "AMOUNT"
                
                break_obj = Break(
                    event_key=str(event_key),
                    isin=str(nbim_row['ISIN']),
                    company_name=str(nbim_row['ORGANISATION_NAME']),
                    bank_account=str(bank_account),
                    break_type=break_type,
                    
                    nbim_shares=nbim_shares,
                    nbim_gross_amount=nbim_gross,
                    nbim_net_amount=nbim_net,
                    nbim_tax_rate=nbim_tax,
                    nbim_payment_date=nbim_payment_date,
                    
                    custody_shares=custody_shares,
                    custody_gross_amount=custody_gross,
                    custody_net_amount=custody_net,
                    custody_tax_rate=custody_tax,
                    custody_payment_date=custody_payment_date,
                    
                    shares_difference=shares_diff,
                    amount_difference=amount_diff,
                    tax_rate_difference=tax_diff,
                    payment_date_difference_days=date_diff_days,
                    
                    lending_percentage=lending_pct,
                    loan_quantity=loan_qty,
                    currency=str(nbim_row['QUOTATION_CURRENCY']),
                    custodian=str(nbim_row['CUSTODIAN'])
                )
                
                breaks.append(break_obj)
    
    return breaks


def print_breaks_summary(breaks: List[Break]) -> None:
    """Print a formatted summary of all breaks."""
    if not breaks:
        print("No breaks found - perfect reconciliation!")
        return
    
    print(f"\n{'='*80}")
    print(f"Found {len(breaks)} reconciliation break(s)")
    print(f"{'='*80}\n")
    
    for i, break_obj in enumerate(breaks, 1):
        print(f"Break #{i}: {break_obj.company_name} ({break_obj.event_key})")
        print(f"  Type: {break_obj.break_type}")
        print(f"  Bank Account: {break_obj.bank_account}")
        print(f"  Currency: {break_obj.currency}")
        
        if abs(break_obj.shares_difference) > 0.01:
            print(f"Shares: {break_obj.nbim_shares:,.0f} (NBIM) vs {break_obj.custody_shares:,.0f} (Custody) = {break_obj.shares_difference:+,.0f}")
        
        if abs(break_obj.amount_difference) > 0.01:
            print(f"Amount: {break_obj.nbim_net_amount:,.2f} (NBIM) vs {break_obj.custody_net_amount:,.2f} (Custody) = {break_obj.amount_difference:+,.2f} {break_obj.currency}")
        
        if abs(break_obj.tax_rate_difference) > 0.01:
            print(f"Tax Rate: {break_obj.nbim_tax_rate:.1f}% (NBIM) vs {break_obj.custody_tax_rate:.1f}% (Custody) = {break_obj.tax_rate_difference:+.1f}%")
        
        if break_obj.payment_date_difference_days != 0:
            print(f"Payment Date: {break_obj.nbim_payment_date} (NBIM) vs {break_obj.custody_payment_date} (Custody) = {break_obj.payment_date_difference_days:+d} days")
        
        if break_obj.lending_percentage > 0:
            print(f"Securities Lending: {break_obj.loan_quantity:,.0f} shares ({break_obj.lending_percentage:.1f}%)")
        
        print()
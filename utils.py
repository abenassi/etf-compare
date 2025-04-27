import pandas as pd
import streamlit as st

def filter_dataframe(df, min_nominal_return=None, min_real_return=None, max_std_dev=None):
    """
    Filter DataFrame based on given criteria.
    
    Args:
        df (pd.DataFrame): DataFrame to filter
        min_nominal_return (float, optional): Minimum nominal return
        min_real_return (float, optional): Minimum real return
        max_std_dev (float, optional): Maximum standard deviation
        
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    filtered_df = df.copy()
    
    if min_nominal_return is not None:
        filtered_df = filtered_df[filtered_df['nominal_30y_return'] >= min_nominal_return]
    
    if min_real_return is not None:
        filtered_df = filtered_df[filtered_df['real_30y_return'] >= min_real_return]
    
    if max_std_dev is not None:
        filtered_df = filtered_df[filtered_df['std_deviation'] <= max_std_dev]
    
    return filtered_df

def highlight_best_nominal_sharpe(s):
    """
    Highlight the row with the best nominal Sharpe ratio.
    
    Args:
        s (pd.Series): Series to highlight
        
    Returns:
        list: Styles for each cell
    """
    is_max = s == s.max()
    return ['background-color: #90EE90' if v else '' for v in is_max]

def highlight_best_real_sharpe(s):
    """
    Highlight the row with the best real Sharpe ratio.
    
    Args:
        s (pd.Series): Series to highlight
        
    Returns:
        list: Styles for each cell
    """
    is_max = s == s.max()
    return ['background-color: #ADD8E6' if v else '' for v in is_max]

def format_dataframe_for_display(df):
    """
    Format DataFrame for display in Streamlit.
    
    Args:
        df (pd.DataFrame): DataFrame to format
        
    Returns:
        pd.DataFrame: Formatted DataFrame
    """
    display_df = df.copy()
    
    # Format numeric columns to show 2 decimal places
    numeric_cols = ['nominal_30y_return', 'real_30y_return', 'std_deviation', 'nominal_sharpe', 'real_sharpe']
    for col in numeric_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(2)
    
    # Rename columns for better display
    column_mapping = {
        'name': 'Asset Name',
        'url': 'URL',
        'nominal_30y_return': '30Y Nominal Return (%)',
        'real_30y_return': '30Y Real Return (%)',
        'std_deviation': 'Std Deviation (%)',
        'nominal_sharpe': 'Nominal Sharpe',
        'real_sharpe': 'Real Sharpe',
        'scrape_time': 'Last Updated'
    }
    
    display_df = display_df.rename(columns=column_mapping)
    
    return display_df

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_default_urls():
    """
    Get default URLs for the dashboard.
    
    Returns:
        list: List of default URLs
    """
    return [
        "https://www.lazyportfolioetf.com/etf/spdr-sp-500-spy/",
        "https://www.lazyportfolioetf.com/allocation/all-country-world-stocks-portfolio/",
        "https://www.lazyportfolioetf.com/etf/invesco-qqq-trust-qqq/",
        "https://www.lazyportfolioetf.com/etf/spdr-sp-500-spy-dividend-yield/",
        "https://www.lazyportfolioetf.com/etf/ishares-7-10-year-treasury-bond-ief/",
        "https://www.lazyportfolioetf.com/allocation/three-fund-portfolio-bogleheads/",
        "https://www.lazyportfolioetf.com/allocation/golden-butterfly/",
        "https://www.lazyportfolioetf.com/allocation/60-40-portfolio/",
        "https://www.lazyportfolioetf.com/allocation/all-weather-portfolio/"
    ]

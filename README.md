# ETF Compare - Portfolio Metrics Dashboard

A Streamlit dashboard for analyzing and comparing financial metrics of ETFs and
lazy portfolios scraped from lazyportfolioetf.com.

## Features

-   Web scraping of financial metrics including 30-year returns (nominal and
    inflation-adjusted), standard deviation, and Sharpe ratios
-   Interactive data filtering based on performance metrics
-   Visual comparison of multiple portfolios via various chart types:
    -   Returns comparison charts
    -   Risk-return scatter plots
    -   Sharpe ratio comparisons
    -   Radar charts for multi-dimensional analysis
-   Customizable portfolio selection
-   Detailed debugging information for scraping issues

## How to Run

1. Install dependencies:

```bash
# Using pip
pip install .

# Or using uv (recommended for faster installation)
uv pip install .
```

2. Run the Streamlit app:

```bash
streamlit run app.py
```

## Components

-   `app.py`: Main Streamlit application with UI components and tabs
-   `scraper.py`: Web scraping functionality for extracting financial metrics
-   `utils.py`: Helper functions for data processing and manipulation
-   `visualization.py`: Components for creating data visualizations
-   `debug_html.py`: Tools to analyze the HTML structure of target websites

## Notes

-   The scraper handles different HTML structures across pages
-   Real (inflation-adjusted) returns are estimated when not explicitly provided
    by the source
-   Estimated values are marked with an asterisk (\*) in the dashboard

import streamlit as st
import pandas as pd
import time
from scraper import scrape_multiple_lazyportfolio_30y_metrics
from utils import (
    filter_dataframe, 
    highlight_best_nominal_sharpe, 
    highlight_best_real_sharpe, 
    format_dataframe_for_display,
    get_default_urls
)
from visualization import (
    create_returns_comparison_chart, 
    create_risk_return_scatter, 
    create_sharpe_comparison_chart,
    create_radar_chart
)

# Page config
st.set_page_config(
    page_title="LazyPortfolio ETF Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("📊 LazyPortfolio ETF Analyzer")
st.markdown("""
This dashboard analyzes and compares financial metrics of ETFs and lazy portfolios 
scraped from [lazyportfolioetf.com](https://www.lazyportfolioetf.com).
""", unsafe_allow_html=False)

# Session state initialization
if 'data' not in st.session_state:
    st.session_state.data = None
if 'urls' not in st.session_state:
    st.session_state.urls = get_default_urls()
if 'errors' not in st.session_state:
    st.session_state.errors = []

# Sidebar
st.sidebar.title("Controls")

# URL Management Section
st.sidebar.header("URL Management")

# Add new URL
new_url = st.sidebar.text_input("Add new URL", placeholder="https://www.lazyportfolioetf.com/...")
if st.sidebar.button("Add URL"):
    if new_url and new_url not in st.session_state.urls:
        st.session_state.urls.append(new_url)
        st.rerun()

# Display and manage existing URLs
st.sidebar.subheader("Current URLs")
urls_to_remove = []

for i, url in enumerate(st.session_state.urls):
    col1, col2 = st.sidebar.columns([4, 1])
    # Truncate URL for display if too long
    display_url = url if len(url) < 40 else url[:37] + "..."
    col1.text(f"{i+1}. {display_url}")
    if col2.button("❌", key=f"remove_{i}"):
        urls_to_remove.append(url)

# Remove URLs that were marked for removal
for url in urls_to_remove:
    st.session_state.urls.remove(url)
    # If we're removing URLs, we need to refresh
    if url in urls_to_remove:
        st.rerun()

# Fetch data button
if st.sidebar.button("Fetch Data"):
    with st.spinner("Fetching data from lazyportfolioetf.com..."):
        # Create a status container to show real-time progress
        status_container = st.empty()
        status_container.info("Starting data scraping process...")
        
        # Scrape data from URLs
        df, errors = scrape_multiple_lazyportfolio_30y_metrics(st.session_state.urls)
        
        # Display results
        if not df.empty:
            st.session_state.data = df
            st.session_state.errors = errors
            
            # Show success message with details
            st.success(f"Successfully fetched data for {len(df)} assets! ({len(errors)} errors)")
            status_container.empty()
            
            # Log the column names and shapes for debugging
            st.session_state.debug_info = {
                "shape": df.shape,
                "columns": list(df.columns),
                "scrape_time": df["scrape_time"].iloc[0] if not df.empty else None
            }
        else:
            # Show detailed error information when no data was fetched
            st.error("Failed to fetch any data from the provided URLs.")
            status_container.error("No data could be scraped. Check the error details below.")
            
            # Store errors for later display
            st.session_state.errors = errors
            
            # Add debugging information
            if errors:
                error_summary = "\n".join([f"• {e['url']}: {e['error']}" for e in errors[:3]])
                st.error(f"First few errors:\n{error_summary}")
                if len(errors) > 3:
                    st.error(f"...and {len(errors) - 3} more errors. See the Errors tab for details.")
            else:
                st.error("No specific errors were reported, but no data was fetched. Check URL format and website structure.")

# Filtering Section
st.sidebar.header("Filters")
if st.session_state.data is not None:
    min_nominal_return = st.sidebar.slider(
        "Min Nominal Return (%)", 
        min_value=float(st.session_state.data['nominal_30y_return'].min()), 
        max_value=float(st.session_state.data['nominal_30y_return'].max()),
        value=float(st.session_state.data['nominal_30y_return'].min())
    )
    
    min_real_return = st.sidebar.slider(
        "Min Real Return (%)", 
        min_value=float(st.session_state.data['real_30y_return'].min()), 
        max_value=float(st.session_state.data['real_30y_return'].max()),
        value=float(st.session_state.data['real_30y_return'].min())
    )
    
    max_std_dev = st.sidebar.slider(
        "Max Standard Deviation (%)", 
        min_value=float(st.session_state.data['std_deviation'].min()), 
        max_value=float(st.session_state.data['std_deviation'].max()),
        value=float(st.session_state.data['std_deviation'].max())
    )
    
    filtered_df = filter_dataframe(
        st.session_state.data,
        min_nominal_return=min_nominal_return,
        min_real_return=min_real_return,
        max_std_dev=max_std_dev
    )
else:
    filtered_df = None

# Attribution
st.sidebar.markdown("---", unsafe_allow_html=False)
st.sidebar.caption("Data Source: [lazyportfolioetf.com](https://www.lazyportfolioetf.com)")
st.sidebar.caption(f"Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Main content area
if st.session_state.data is not None and not filtered_df.empty:
    # Summary metrics
    st.header("Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
        "Total Assets", 
        len(filtered_df),
        delta=f"{len(filtered_df) - len(st.session_state.data)}" if len(filtered_df) != len(st.session_state.data) else None
    )
    
    col2.metric(
        "Avg Nominal Return", 
        f"{filtered_df['nominal_30y_return'].mean():.2f}%"
    )
    
    col3.metric(
        "Avg Real Return", 
        f"{filtered_df['real_30y_return'].mean():.2f}%"
    )
    
    col4.metric(
        "Avg Std Deviation", 
        f"{filtered_df['std_deviation'].mean():.2f}%"
    )
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Data Table", "Returns Comparison", "Risk Analysis", "Asset Comparison", "Debug Info"])
    
    with tab1:
        st.header("Asset Data")
        
        # Sorting options
        sort_col = st.selectbox(
            "Sort by",
            options=[
                "Asset Name", 
                "30Y Nominal Return (%)", 
                "30Y Real Return (%)", 
                "Std Deviation (%)", 
                "Nominal Sharpe", 
                "Real Sharpe"
            ],
            index=4  # Default to nominal Sharpe
        )
        
        # Convert display column name back to DataFrame column name
        sort_col_mapping = {
            "Asset Name": "name",
            "30Y Nominal Return (%)": "nominal_30y_return",
            "30Y Real Return (%)": "real_30y_return",
            "Std Deviation (%)": "std_deviation",
            "Nominal Sharpe": "nominal_sharpe",
            "Real Sharpe": "real_sharpe"
        }
        
        sort_ascending = st.checkbox("Sort Ascending", value=False)
        
        # Format DataFrame for display
        display_df = format_dataframe_for_display(filtered_df)
        
        # Sort the DataFrame
        df_col_name = sort_col_mapping[sort_col]
        display_df = display_df.sort_values(by=sort_col, ascending=sort_ascending)
        
        # Apply styling to highlight best Sharpe ratios
        styled_df = display_df.style.apply(
            highlight_best_nominal_sharpe, 
            subset=['Nominal Sharpe']
        ).apply(
            highlight_best_real_sharpe, 
            subset=['Real Sharpe']
        )
        
        # Display the DataFrame
        st.dataframe(styled_df, use_container_width=True)
        
        # Display info about highlighting
        st.info("📊 **Table Highlights:** Green = Best Nominal Sharpe, Blue = Best Real Sharpe")
    
    with tab2:
        st.header("Returns Comparison")
        
        # Returns bar chart
        returns_chart = create_returns_comparison_chart(filtered_df)
        st.plotly_chart(returns_chart, use_container_width=True)
        
        # Sharpe ratio bar chart
        sharpe_chart = create_sharpe_comparison_chart(filtered_df)
        st.plotly_chart(sharpe_chart, use_container_width=True)
    
    with tab3:
        st.header("Risk Analysis")
        
        # Risk-return scatter plot
        risk_return_chart = create_risk_return_scatter(filtered_df)
        st.plotly_chart(risk_return_chart, use_container_width=True)
        
        # Explanation
        st.markdown("""
        ### Understanding the Risk-Return Chart
        - **X-axis**: Standard Deviation (%) - measures volatility/risk
        - **Y-axis**: Real 30Y Return (%) - shows inflation-adjusted returns
        - **Bubble Size**: Nominal Sharpe Ratio - larger bubbles indicate better risk-adjusted returns
        
        Ideally, you want assets in the upper left (high returns, low risk).
        """, unsafe_allow_html=False)
    
    with tab4:
        st.header("Asset Comparison")
        
        # Select assets to compare
        selected_assets = st.multiselect(
            "Select assets to compare",
            options=filtered_df['name'].tolist(),
            default=filtered_df['name'].tolist()[:min(3, len(filtered_df))]
        )
        
        if selected_assets:
            # Radar chart for comparing assets
            radar_chart = create_radar_chart(filtered_df, selected_assets)
            if radar_chart:
                st.plotly_chart(radar_chart, use_container_width=True)
            
            # Side-by-side comparison table
            comparison_df = filtered_df[filtered_df['name'].isin(selected_assets)]
            st.dataframe(format_dataframe_for_display(comparison_df), use_container_width=True)
        else:
            st.warning("Please select at least one asset to compare.")
    
    with tab5:
        st.header("Debug Information")
        
        # Show debugging information
        st.subheader("Dataset Information")
        if 'debug_info' in st.session_state:
            debug_info = st.session_state.debug_info
            cols = st.columns(3)
            cols[0].metric("Rows", debug_info["shape"][0])
            cols[1].metric("Columns", debug_info["shape"][1])
            cols[2].metric("Last Update", debug_info["scrape_time"])
            
            st.subheader("Columns")
            st.write(debug_info["columns"])
            
            # Show raw data sample
            st.subheader("Raw Data Sample")
            if st.checkbox("Show raw data sample"):
                st.dataframe(st.session_state.data.head(3), use_container_width=True)
        else:
            st.info("No debug information available yet. Run 'Fetch Data' first.")
        
        # Display URLs being used
        st.subheader("Current URLs")
        for i, url in enumerate(st.session_state.urls):
            st.code(f"{i+1}. {url}", language=None)
        
        # Display any scraping errors
        st.subheader("Scraping Errors")
        if st.session_state.errors:
            for i, error in enumerate(st.session_state.errors):
                with st.expander(f"Error {i+1}: {error['url'].split('/')[-2]}"):
                    st.error(f"URL: {error['url']}")
                    st.error(f"Error: {error['error']}")
                    
                    # Provide troubleshooting suggestions based on error
                    if "Missing metrics" in error['error']:
                        st.warning("Possible causes:")
                        st.markdown("- Webpage structure might have changed")
                        st.markdown("- Content might be loading dynamically with JavaScript")
                        st.markdown("- Required metrics might use different naming patterns")
                    elif "Error fetching URL" in error['error']:
                        st.warning("Network or URL issues:")
                        st.markdown("- Check if the URL is accessible in a browser")
                        st.markdown("- The website might be blocking scraping requests")
                        st.markdown("- Network connection issues")
        else:
            st.success("No errors reported during scraping.")

elif st.session_state.data is not None and filtered_df.empty:
    st.warning("No assets match the current filter criteria. Try adjusting the filters.")
else:
    st.info("👈 Click 'Fetch Data' in the sidebar to get started!")
    
    # Show example of what the dashboard will look like
    st.header("Dashboard Preview")
    # Create a simple preview instead of loading an external image
    st.info("👆 Click 'Fetch Data' to see the interactive dashboard with real metrics and visualizations.")
    
    # Instructions
    st.markdown("""
    ### How to use this dashboard:
    1. The sidebar contains a list of default URLs from lazyportfolioetf.com
    2. You can add your own URLs to analyze additional ETFs or portfolios
    3. Click "Fetch Data" to scrape financial metrics from all URLs
    4. Use the filters to narrow down assets based on your criteria
    5. Explore the data in different views:
       - Data Table: Sortable table with all metrics
       - Returns Comparison: Charts comparing nominal and real returns
       - Risk Analysis: Visual analysis of risk vs. return
       - Asset Comparison: Side-by-side comparison of selected assets
       - Debug Info: Detailed information about the data and any scraping errors
    6. If scraping fails, check the "Debug Info" tab for detailed error messages and troubleshooting tips
    """, unsafe_allow_html=False)

# Footer
st.markdown("---", unsafe_allow_html=False)
st.caption("ETF Analyzer Dashboard | Data sourced from lazyportfolioetf.com")

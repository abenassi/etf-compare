import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_returns_comparison_chart(df):
    """
    Create a bar chart comparing nominal and real returns.
    
    Args:
        df (pd.DataFrame): DataFrame with financial metrics
        
    Returns:
        go.Figure: Plotly figure with the chart
    """
    df_melted = pd.melt(
        df, 
        id_vars=['name'], 
        value_vars=['nominal_30y_return', 'real_30y_return'],
        var_name='return_type', 
        value_name='return_value'
    )
    
    # Replace the column names for better display
    df_melted['return_type'] = df_melted['return_type'].replace({
        'nominal_30y_return': '30Y Nominal Return',
        'real_30y_return': '30Y Real Return'
    })
    
    fig = px.bar(
        df_melted, 
        x='name', 
        y='return_value', 
        color='return_type',
        labels={
            'name': 'Asset',
            'return_value': 'Return (%)',
            'return_type': 'Return Type'
        },
        title='Nominal vs Real 30-Year Returns'
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500
    )
    
    return fig

def create_risk_return_scatter(df):
    """
    Create a scatter plot with returns vs standard deviation.
    
    Args:
        df (pd.DataFrame): DataFrame with financial metrics
        
    Returns:
        go.Figure: Plotly figure with the chart
    """
    fig = px.scatter(
        df, 
        x='std_deviation', 
        y='real_30y_return',
        size='nominal_sharpe',
        hover_name='name',
        labels={
            'std_deviation': 'Standard Deviation (%)',
            'real_30y_return': 'Real 30Y Return (%)',
            'nominal_sharpe': 'Nominal Sharpe Ratio'
        },
        title='Risk vs Return Analysis'
    )
    
    fig.update_layout(height=500)
    
    return fig

def create_sharpe_comparison_chart(df):
    """
    Create a bar chart comparing nominal and real Sharpe ratios.
    
    Args:
        df (pd.DataFrame): DataFrame with financial metrics
        
    Returns:
        go.Figure: Plotly figure with the chart
    """
    df_melted = pd.melt(
        df, 
        id_vars=['name'], 
        value_vars=['nominal_sharpe', 'real_sharpe'],
        var_name='sharpe_type', 
        value_name='sharpe_value'
    )
    
    # Replace the column names for better display
    df_melted['sharpe_type'] = df_melted['sharpe_type'].replace({
        'nominal_sharpe': 'Nominal Sharpe',
        'real_sharpe': 'Real Sharpe'
    })
    
    fig = px.bar(
        df_melted, 
        x='name', 
        y='sharpe_value', 
        color='sharpe_type',
        labels={
            'name': 'Asset',
            'sharpe_value': 'Sharpe Ratio',
            'sharpe_type': 'Sharpe Ratio Type'
        },
        title='Nominal vs Real Sharpe Ratios'
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500
    )
    
    return fig

def create_radar_chart(df, selected_assets):
    """
    Create a radar chart comparing multiple metrics for selected assets.
    
    Args:
        df (pd.DataFrame): DataFrame with financial metrics
        selected_assets (list): List of asset names to include in the chart
        
    Returns:
        go.Figure: Plotly figure with the chart
    """
    filtered_df = df[df['name'].isin(selected_assets)]
    
    if filtered_df.empty:
        return None
    
    # Normalize metrics for radar chart
    metrics = ['nominal_30y_return', 'real_30y_return', 'std_deviation', 'nominal_sharpe', 'real_sharpe']
    radar_df = filtered_df.copy()
    
    for metric in metrics:
        max_val = radar_df[metric].max()
        min_val = radar_df[metric].min()
        
        if max_val != min_val:
            radar_df[metric] = (radar_df[metric] - min_val) / (max_val - min_val)
        else:
            radar_df[metric] = 1
    
    # For std_deviation, lower is better, so invert the normalization
    radar_df['std_deviation'] = 1 - radar_df['std_deviation']
    
    fig = go.Figure()
    
    categories = [
        'Nominal Return', 
        'Real Return', 
        'Stability (inverse of Std Dev)', 
        'Nominal Sharpe', 
        'Real Sharpe'
    ]
    
    for _, row in radar_df.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[
                row['nominal_30y_return'],
                row['real_30y_return'],
                row['std_deviation'],
                row['nominal_sharpe'],
                row['real_sharpe']
            ],
            theta=categories,
            fill='toself',
            name=row['name']
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True,
        title='Asset Comparison (Normalized Metrics)',
        height=600
    )
    
    return fig

"""
Chart generation for Merton credit analysis

Creates publication-quality visualizations for:
- Spread comparison (theoretical vs market)
- Distance to default trends
- Sensitivity analysis
- Signal dashboards
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9


def plot_spread_comparison(results_df, save_path=None, show=True):
    """
    Scatter plot: Theoretical vs Market Spreads
    
    Shows which companies have bonds trading rich/cheap
    
    Args:
        results_df (pd.DataFrame): Results from SignalGenerator.analyze_batch()
        save_path (str): Optional path to save figure
        show (bool): Whether to display the plot
    
    Returns:
        matplotlib.figure.Figure
    """
    if results_df.empty:
        warnings.warn("No data to plot")
        return None
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Filter valid data
    df = results_df.dropna(subset=['theo_spread_bps', 'market_spread_bps']).copy()
    
    if df.empty:
        warnings.warn("No valid spread data to plot")
        return None
    
    # Calculate colors based on signal
    colors = []
    for _, row in df.iterrows():
        diff = row['spread_diff_bps']
        if diff > 150:
            colors.append('#e74c3c')  # Strong short (red)
        elif diff > 75:
            colors.append('#e67e22')  # Moderate short (orange)
        elif diff < -150:
            colors.append('#27ae60')  # Strong long (green)
        elif diff < -75:
            colors.append('#2ecc71')  # Moderate long (light green)
        else:
            colors.append('#95a5a6')  # Neutral (gray)
    
    # Scatter plot
    scatter = ax.scatter(
        df['market_spread_bps'],
        df['theo_spread_bps'],
        c=colors,
        s=100,
        alpha=0.6,
        edgecolors='black',
        linewidth=0.5
    )
    
    # Add 45-degree line (fair value)
    max_spread = max(df['market_spread_bps'].max(), df['theo_spread_bps'].max())
    ax.plot([0, max_spread], [0, max_spread], 'k--', alpha=0.3, linewidth=1, label='Fair Value')
    
    # Add threshold lines
    for offset in [75, 150]:
        ax.plot([0, max_spread], [offset, max_spread + offset], 'r:', alpha=0.2, linewidth=0.8)
        ax.plot([offset, max_spread], [0, max_spread - offset], 'g:', alpha=0.2, linewidth=0.8)
    
    # Annotate points
    for _, row in df.iterrows():
        if abs(row['spread_diff_bps']) > 100:  # Only label strong signals
            ax.annotate(
                row['ticker'],
                (row['market_spread_bps'], row['theo_spread_bps']),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8,
                alpha=0.7
            )
    
    # Labels and title
    ax.set_xlabel('Market Spread (bps)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Theoretical Spread (bps)', fontsize=12, fontweight='bold')
    ax.set_title('Credit Spread Comparison: Theoretical vs Market', fontsize=14, fontweight='bold', pad=20)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#e74c3c', label='Strong Short (>150 bps)'),
        Patch(facecolor='#e67e22', label='Moderate Short (75-150 bps)'),
        Patch(facecolor='#95a5a6', label='Neutral'),
        Patch(facecolor='#2ecc71', label='Moderate Long (-75 to -150 bps)'),
        Patch(facecolor='#27ae60', label='Strong Long (<-150 bps)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
    
    # Grid
    ax.grid(True, alpha=0.3)
    
    # Add text box with stats
    n_long = len(df[df['spread_diff_bps'] < -75])
    n_short = len(df[df['spread_diff_bps'] > 75])
    stats_text = f"Total: {len(df)}\nLong Signals: {n_long}\nShort Signals: {n_short}"
    ax.text(0.98, 0.02, stats_text, transform=ax.transAxes,
            fontsize=9, verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    
    return fig


def plot_distance_to_default_history(ticker, dd_history, save_path=None, show=True):
    """
    Time series plot: Distance to Default over time
    
    Args:
        ticker (str): Company ticker
        dd_history (pd.DataFrame): Must have columns ['date', 'distance_to_default']
        save_path (str): Optional save path
        show (bool): Whether to display
    
    Returns:
        matplotlib.figure.Figure
    """
    if dd_history.empty:
        warnings.warn("No history data to plot")
        return None
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Ensure date column is datetime
    dd_history = dd_history.copy()
    if 'date' not in dd_history.columns:
        warnings.warn("Missing 'date' column")
        return None
    
    dd_history['date'] = pd.to_datetime(dd_history['date'])
    dd_history = dd_history.sort_values('date')
    
    # Plot line
    ax.plot(dd_history['date'], dd_history['distance_to_default'], 
            linewidth=2, color='#3498db', label='Distance to Default')
    
    # Add horizontal zones
    ax.axhspan(-2, 0, alpha=0.1, color='red', label='Distressed Zone (DD < 0)')
    ax.axhspan(0, 2, alpha=0.1, color='yellow', label='Warning Zone (0 < DD < 2)')
    ax.axhspan(2, 10, alpha=0.05, color='green', label='Safe Zone (DD > 2)')
    
    # Add zero line
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.5)
    
    # Labels
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Distance to Default (σ)', fontsize=12, fontweight='bold')
    ax.set_title(f'{ticker} - Distance to Default Over Time', fontsize=14, fontweight='bold', pad=20)
    
    # Legend
    ax.legend(loc='best', fontsize=9)
    
    # Grid
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    fig.autofmt_xdate()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    
    return fig


def plot_volatility_sensitivity(vol_sensitivity_df, market_spread, save_path=None, show=True):
    """
    Plot how theoretical spread changes with volatility shocks
    
    Args:
        vol_sensitivity_df (pd.DataFrame): From SensitivityAnalyzer.volatility_sensitivity()
        market_spread (float): Market spread in bps
        save_path (str): Optional save path
        show (bool): Whether to display
    
    Returns:
        matplotlib.figure.Figure
    """
    if vol_sensitivity_df.empty:
        warnings.warn("No sensitivity data to plot")
        return None
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    df = vol_sensitivity_df.copy()
    
    # Plot 1: Theoretical Spread vs Volatility Shock
    ax1.plot(df['shock_pct'], df['theo_spread_bps'], 
             marker='o', linewidth=2, markersize=8, color='#3498db', label='Theoretical Spread')
    ax1.axhline(y=market_spread, color='red', linestyle='--', linewidth=2, label='Market Spread')
    
    # Shade areas
    ax1.fill_between(df['shock_pct'], df['theo_spread_bps'], market_spread, 
                      where=(df['theo_spread_bps'] > market_spread), 
                      alpha=0.2, color='red', label='Short Credit Zone')
    ax1.fill_between(df['shock_pct'], df['theo_spread_bps'], market_spread, 
                      where=(df['theo_spread_bps'] <= market_spread), 
                      alpha=0.2, color='green', label='Long Credit Zone')
    
    ax1.set_xlabel('Volatility Shock (%)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Credit Spread (bps)', fontsize=11, fontweight='bold')
    ax1.set_title('Theoretical Spread vs Volatility', fontsize=12, fontweight='bold')
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.axvline(x=0, color='black', linestyle=':', alpha=0.5)
    
    # Plot 2: Distance to Default vs Volatility Shock
    ax2.plot(df['shock_pct'], df['distance_to_default'], 
             marker='s', linewidth=2, markersize=8, color='#e74c3c')
    ax2.axhline(y=2, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='Warning Threshold')
    ax2.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Default Threshold')
    
    ax2.set_xlabel('Volatility Shock (%)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Distance to Default (σ)', fontsize=11, fontweight='bold')
    ax2.set_title('Distance to Default vs Volatility', fontsize=12, fontweight='bold')
    ax2.legend(loc='best', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.axvline(x=0, color='black', linestyle=':', alpha=0.5)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    
    return fig


def plot_debt_sensitivity(debt_sensitivity_df, save_path=None, show=True):
    """
    Plot how theoretical spread changes with debt shocks
    
    Args:
        debt_sensitivity_df (pd.DataFrame): From SensitivityAnalyzer.debt_sensitivity()
        save_path (str): Optional save path
        show (bool): Whether to display
    
    Returns:
        matplotlib.figure.Figure
    """
    if debt_sensitivity_df.empty:
        warnings.warn("No sensitivity data to plot")
        return None
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    df = debt_sensitivity_df.copy()
    
    # Plot 1: Spread vs Leverage
    ax1.scatter(df['leverage'] * 100, df['theo_spread_bps'], 
                s=100, alpha=0.6, c=df['shock_pct'], cmap='RdYlGn_r', edgecolors='black')
    ax1.plot(df['leverage'] * 100, df['theo_spread_bps'], 
             linewidth=2, alpha=0.5, color='gray')
    
    ax1.set_xlabel('Leverage (D/V %)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Theoretical Spread (bps)', fontsize=11, fontweight='bold')
    ax1.set_title('Credit Spread vs Leverage', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap='RdYlGn_r', 
                                norm=plt.Normalize(vmin=df['shock_pct'].min(), 
                                                   vmax=df['shock_pct'].max()))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax1)
    cbar.set_label('Debt Shock (%)', fontsize=9)
    
    # Plot 2: Distance to Default vs Leverage
    ax2.scatter(df['leverage'] * 100, df['distance_to_default'], 
                s=100, alpha=0.6, c=df['shock_pct'], cmap='RdYlGn_r', edgecolors='black')
    ax2.plot(df['leverage'] * 100, df['distance_to_default'], 
             linewidth=2, alpha=0.5, color='gray')
    
    ax2.axhline(y=2, color='orange', linestyle='--', linewidth=1, alpha=0.5)
    ax2.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.5)
    
    ax2.set_xlabel('Leverage (D/V %)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Distance to Default (σ)', fontsize=11, fontweight='bold')
    ax2.set_title('Distance to Default vs Leverage', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    
    return fig


def plot_stress_test(stress_df, save_path=None, show=True):
    """
    Heatmap: Stress test scenarios
    
    Args:
        stress_df (pd.DataFrame): From SensitivityAnalyzer.combined_stress_test()
        save_path (str): Optional save path
        show (bool): Whether to display
    
    Returns:
        matplotlib.figure.Figure
    """
    if stress_df.empty:
        warnings.warn("No stress test data to plot")
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Prepare data for horizontal bar chart
    df = stress_df.sort_values('theo_spread_bps').copy()
    
    # Color code by severity
    colors = []
    for spread in df['theo_spread_bps']:
        if spread < 50:
            colors.append('#27ae60')  # Green (safe)
        elif spread < 150:
            colors.append('#f39c12')  # Yellow (moderate)
        elif spread < 300:
            colors.append('#e67e22')  # Orange (elevated)
        else:
            colors.append('#e74c3c')  # Red (distressed)
    
    # Horizontal bar chart
    bars = ax.barh(df['scenario'], df['theo_spread_bps'], color=colors, alpha=0.7, edgecolor='black')
    
    # Add value labels
    for i, (idx, row) in enumerate(df.iterrows()):
        ax.text(row['theo_spread_bps'] + 5, i, f"{row['theo_spread_bps']:.0f} bps", 
                va='center', fontsize=9)
    
    ax.set_xlabel('Theoretical Spread (bps)', fontsize=11, fontweight='bold')
    ax.set_title('Stress Test Scenarios', fontsize=12, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    
    return fig


def plot_signal_dashboard(results_df, n_top=10, save_path=None, show=True):
    """
    Dashboard view: Top long and short signals
    
    Args:
        results_df (pd.DataFrame): Results from analyze_batch()
        n_top (int): Number of top signals to show
        save_path (str): Optional save path
        show (bool): Whether to display
    
    Returns:
        matplotlib.figure.Figure
    """
    if results_df.empty:
        warnings.warn("No data for dashboard")
        return None
    
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    df = results_df.dropna(subset=['spread_diff_bps']).copy()
    
    # Top long signals
    long_signals = df[df['spread_diff_bps'] < -75].sort_values('spread_diff_bps').head(n_top)
    
    # Top short signals
    short_signals = df[df['spread_diff_bps'] > 75].sort_values('spread_diff_bps', ascending=False).head(n_top)
    
    # Plot 1: Top Short Signals
    ax1 = fig.add_subplot(gs[0, 0])
    if not short_signals.empty:
        ax1.barh(short_signals['ticker'], short_signals['spread_diff_bps'], 
                 color='#e74c3c', alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Spread Difference (bps)', fontsize=10, fontweight='bold')
        ax1.set_title(f'Top {n_top} SHORT CREDIT Signals', fontsize=11, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='x')
        ax1.invert_yaxis()
    
    # Plot 2: Top Long Signals
    ax2 = fig.add_subplot(gs[0, 1])
    if not long_signals.empty:
        ax2.barh(long_signals['ticker'], long_signals['spread_diff_bps'].abs(), 
                 color='#27ae60', alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Spread Difference (bps)', fontsize=10, fontweight='bold')
        ax2.set_title(f'Top {n_top} LONG CREDIT Signals', fontsize=11, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')
        ax2.invert_yaxis()
    
    # Plot 3: Distance to Default Distribution
    ax3 = fig.add_subplot(gs[1, :])
    dd_data = df['distance_to_default'].dropna()
    ax3.hist(dd_data, bins=30, color='#3498db', alpha=0.7, edgecolor='black')
    ax3.axvline(x=2, color='orange', linestyle='--', linewidth=2, label='Warning Threshold')
    ax3.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Default Threshold')
    ax3.set_xlabel('Distance to Default (σ)', fontsize=10, fontweight='bold')
    ax3.set_ylabel('Frequency', fontsize=10, fontweight='bold')
    ax3.set_title('Distance to Default Distribution', fontsize=11, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Leverage Distribution
    ax4 = fig.add_subplot(gs[2, 0])
    leverage_data = (df['leverage'] * 100).dropna()
    ax4.hist(leverage_data, bins=25, color='#9b59b6', alpha=0.7, edgecolor='black')
    ax4.set_xlabel('Leverage (D/V %)', fontsize=10, fontweight='bold')
    ax4.set_ylabel('Frequency', fontsize=10, fontweight='bold')
    ax4.set_title('Leverage Distribution', fontsize=11, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Summary Statistics
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.axis('off')
    
    stats_text = f"""
    SUMMARY STATISTICS
    {'='*40}
    
    Total Companies: {len(df)}
    
    SIGNALS:
      Strong Short (>150 bps): {len(df[df['spread_diff_bps'] > 150])}
      Moderate Short (75-150): {len(df[(df['spread_diff_bps'] > 75) & (df['spread_diff_bps'] <= 150)])}
      Neutral: {len(df[df['spread_diff_bps'].abs() <= 75])}
      Moderate Long (-75 to -150): {len(df[(df['spread_diff_bps'] < -75) & (df['spread_diff_bps'] >= -150)])}
      Strong Long (<-150 bps): {len(df[df['spread_diff_bps'] < -150])}
    
    RISK METRICS:
      Avg Distance to Default: {df['distance_to_default'].mean():.2f}σ
      Avg Leverage: {df['leverage'].mean() * 100:.1f}%
      
      Companies in Distress (DD < 2): {len(df[df['distance_to_default'] < 2])}
    """
    
    ax5.text(0.1, 0.9, stats_text, transform=ax5.transAxes,
             fontsize=10, verticalalignment='top', family='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    fig.suptitle('MERTON CREDIT SIGNAL DASHBOARD', fontsize=16, fontweight='bold', y=0.98)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    
    return fig
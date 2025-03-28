"""
Dashboard module for the algorithmic trading system.
This module provides a web-based dashboard for monitoring trading strategies.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_fetcher.factory import DataFetcherFactory
from backtesting.base import Backtester
from strategies.advanced import TrendFollowingStrategy, MeanReversionStrategy, BreakoutStrategy
from zerodha_integration.trading_engine import TradingEngine
from ui.config_manager import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dashboard')

# Initialize Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

# Global variables
config_manager = None
data_factory = None
data_fetcher = None
trading_engine = None
strategies = {}
current_data = {}

def initialize_app(config_file=None):
    """
    Initialize the application.
    
    Parameters:
    -----------
    config_file : str, optional
        Path to a config file.
    """
    global config_manager, data_factory, data_fetcher, trading_engine
    
    # Initialize config manager
    config_manager = ConfigManager(config_file)
    
    # Initialize data factory and fetcher
    data_factory = DataFetcherFactory()
    data_fetcher = data_factory.get_yahoo_fetcher()
    
    # Initialize trading engine
    api_key = config_manager.get('zerodha.api_key')
    api_secret = config_manager.get('zerodha.api_secret')
    redirect_url = config_manager.get('zerodha.redirect_url')
    
    trading_engine = TradingEngine(
        api_key=api_key,
        api_secret=api_secret,
        redirect_url=redirect_url,
        config_file=config_file
    )
    
    logger.info("Initialized application")

@app.route('/')
def index():
    """
    Render the dashboard home page.
    """
    return render_template('index.html', 
                          strategies=strategies,
                          is_authenticated=trading_engine.is_authenticated() if trading_engine else False)

@app.route('/config', methods=['GET', 'POST'])
def config():
    """
    Render the configuration page.
    """
    if request.method == 'POST':
        # Update configuration
        for key, value in request.form.items():
            if key.startswith('config.'):
                config_key = key[7:]  # Remove 'config.' prefix
                config_manager.set(config_key, value)
        
        # Save configuration
        config_manager.save_config()
        
        return redirect(url_for('config'))
    
    return render_template('config.html', config=config_manager.config)

@app.route('/data')
def data():
    """
    Render the data management page.
    """
    return render_template('data.html', data=current_data)

@app.route('/api/data/fetch', methods=['POST'])
def fetch_data():
    """
    Fetch historical data.
    """
    symbol = request.form.get('symbol')
    days = int(request.form.get('days', 365))
    interval = request.form.get('interval', '1d')
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    if trading_engine and trading_engine.is_authenticated():
        # Use Zerodha for authenticated users
        data = trading_engine.get_historical_data(
            symbol=symbol,
            from_date=start_date,
            to_date=end_date,
            interval=interval
        )
    else:
        # Use Yahoo Finance as fallback
        data = data_fetcher.fetch_historical_data(
            symbol=symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            interval=interval
        )
    
    if data.empty:
        return jsonify({'success': False, 'message': 'No data fetched'})
    
    current_data[symbol] = data
    
    return jsonify({
        'success': True, 
        'message': f'Fetched {len(data)} data points',
        'data_preview': data.head().to_html()
    })

@app.route('/api/data/chart', methods=['GET'])
def chart_data():
    """
    Generate a chart for the specified symbol.
    """
    symbol = request.args.get('symbol')
    
    if symbol not in current_data:
        return jsonify({'success': False, 'message': f'No data for {symbol}'})
    
    data = current_data[symbol]
    
    # Create candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Price'
    )])
    
    # Add volume as bar chart
    if 'volume' in data.columns:
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['volume'],
            name='Volume',
            yaxis='y2'
        ))
    
    # Add moving averages if available
    if 'sma_20' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['sma_20'],
            name='SMA 20',
            line=dict(color='blue')
        ))
    
    if 'sma_50' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['sma_50'],
            name='SMA 50',
            line=dict(color='orange')
        ))
    
    # Update layout
    fig.update_layout(
        title=f'{symbol} Price Chart',
        yaxis_title='Price',
        xaxis_title='Date',
        yaxis2=dict(
            title='Volume',
            overlaying='y',
            side='right'
        ),
        height=600
    )
    
    return jsonify({
        'success': True,
        'chart': fig.to_json()
    })

@app.route('/strategies')
def strategy_list():
    """
    Render the strategies page.
    """
    return render_template('strategies.html', strategies=strategies)

@app.route('/api/strategies/create', methods=['POST'])
def create_strategy():
    """
    Create a new strategy.
    """
    name = request.form.get('name')
    strategy_type = request.form.get('type')
    symbol = request.form.get('symbol')
    
    if name in strategies:
        return jsonify({'success': False, 'message': f'Strategy {name} already exists'})
    
    # Parse additional parameters
    params = {}
    for key, value in request.form.items():
        if key.startswith('param.'):
            param_name = key[6:]  # Remove 'param.' prefix
            
            # Convert value to appropriate type
            try:
                if '.' in value:
                    params[param_name] = float(value)
                else:
                    params[param_name] = int(value)
            except ValueError:
                params[param_name] = value
    
    # Create strategy based on type
    try:
        if strategy_type.lower() == 'trend':
            strategy = TrendFollowingStrategy(symbol=symbol, **params)
        elif strategy_type.lower() == 'meanreversion':
            strategy = MeanReversionStrategy(symbol=symbol, **params)
        elif strategy_type.lower() == 'breakout':
            strategy = BreakoutStrategy(symbol=symbol, **params)
        else:
            return jsonify({'success': False, 'message': f'Unknown strategy type {strategy_type}'})
        
        strategies[name] = strategy
        
        return jsonify({'success': True, 'message': f'Created {strategy_type} strategy {name} for {symbol}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating strategy: {str(e)}'})

@app.route('/api/strategies/delete', methods=['POST'])
def delete_strategy():
    """
    Delete a strategy.
    """
    name = request.form.get('name')
    
    if name not in strategies:
        return jsonify({'success': False, 'message': f'Strategy {name} not found'})
    
    del strategies[name]
    
    return jsonify({'success': True, 'message': f'Deleted strategy {name}'})

@app.route('/backtest')
def backtest():
    """
    Render the backtesting page.
    """
    return render_template('backtest.html', 
                          strategies=strategies,
                          data=current_data)

@app.route('/api/backtest/run', methods=['POST'])
def run_backtest():
    """
    Run a backtest.
    """
    strategy_name = request.form.get('strategy')
    initial_capital = float(request.form.get('initial_capital', 100000.0))
    commission = float(request.form.get('commission', 0.1))
    
    if strategy_name not in strategies:
        return jsonify({'success': False, 'message': f'Strategy {strategy_name} not found'})
    
    strategy = strategies[strategy_name]
    symbol = strategy.symbol
    
    if symbol not in current_data:
        return jsonify({'success': False, 'message': f'No data for {symbol}'})
    
    # Create a backtester
    backtester = Backtester(
        strategy=strategy,
        data={symbol: current_data[symbol]},
        initial_capital=initial_capital,
        commission=commission / 100.0  # Convert percentage to decimal
    )
    
    # Run the backtest
    results = backtester.run()
    
    # Store results in strategy
    strategy.backtest_results = results
    
    # Create equity curve chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=results['equity_curve'].index,
        y=results['equity_curve'].values,
        name='Equity Curve'
    ))
    
    fig.update_layout(
        title=f'Backtest Results for {strategy_name}',
        yaxis_title='Equity',
        xaxis_title='Date',
        height=400
    )
    
    # Create drawdown chart
    drawdown = 1 - results['equity_curve'] / results['equity_curve'].cummax()
    
    fig_drawdown = go.Figure()
    
    fig_drawdown.add_trace(go.Scatter(
        x=drawdown.index,
        y=drawdown.values * 100,  # Convert to percentage
        name='Drawdown',
        fill='tozeroy',
        line=dict(color='red')
    ))
    
    fig_drawdown.update_layout(
        title='Drawdown',
        yaxis_title='Drawdown (%)',
        xaxis_title='Date',
        height=300
    )
    
    return jsonify({
        'success': True,
        'message': f'Backtest completed for {strategy_name}',
        'results': {
            'total_return': f"{results['total_return']:.2%}",
            'annual_return': f"{results['annual_return']:.2%}",
            'max_drawdown': f"{results['max_drawdown']:.2%}",
            'sharpe_ratio': f"{results['sharpe_ratio']:.2f}",
            'win_rate': f"{results['win_rate']:.2%}",
            'profit_factor': f"{results['profit_factor']:.2f}",
            'num_trades': results['num_trades'],
            'final_equity': f"${results['final_equity']:.2f}"
        },
        'equity_chart': fig.to_json(),
        'drawdown_chart': fig_drawdown.to_json()
    })

@app.route('/trading')
def trading():
    """
    Render the trading page.
    """
    return render_template('trading.html', 
                          strategies=strategies,
                          is_authenticated=trading_engine.is_authenticated() if trading_engine else False,
                          is_running=trading_engine.running if trading_engine else False,
                          mode=trading_engine.mode if trading_engine and trading_engine.running else None)

@app.route('/api/trading/start', methods=['POST'])
def start_trading():
    """
    Start trading with a strategy.
    """
    strategy_name = request.form.get('strategy')
    mode = request.form.get('mode', 'paper')
    
    if strategy_name not in strategies:
        return jsonify({'success': False, 'message': f'Strategy {strategy_name} not found'})
    
    if mode == 'live' and not trading_engine.is_authenticated():
        return jsonify({'success': False, 'message': 'Cannot start live trading without authentication'})
    
    strategy = strategies[strategy_name]
    
    # Add strategy to trading engine
    trading_engine.add_strategy(strategy)
    
    # Add symbol to watchlist
    trading_engine.add_to_watchlist(strategy.symbol)
    
    # Start trading engine
    trading_engine.start(mode=mode)
    
    return jsonify({'success': True, 'message': f'Started {mode} trading with strategy {strategy_name}'})

@app.route('/api/trading/stop', methods=['POST'])
def stop_trading():
    """
    Stop trading with a strategy.
    """
    strategy_name = request.form.get('strategy')
    
    if strategy_name not in strategies:
        return jsonify({'success': False, 'message': f'Strategy {strategy_name} not found'})
    
    strategy = strategies[strategy_name]
    
    # Remove strategy from trading engine
    trading_engine.remove_strategy(strategy)
    
    # If no strategies left, stop trading engine
    if not trading_engine.strategies:
        trading_engine.stop()
    
    return jsonify({'success': True, 'message': f'Stopped trading with strategy {strategy_name}'})

@app.route('/api/trading/positions', methods=['GET'])
def get_positions():
    """
    Get current positions.
    """
    if not trading_engine:
        return jsonify({'success': False, 'message': 'Trading engine not initialized'})
    
    positions = trading_engine.get_positions()
    
    return jsonify({'success': True, 'positions': positions})

@app.route('/api/trading/orders', methods=['GET'])
def get_orders():
    """
    Get current orders.
    """
    if not trading_engine:
        return jsonify({'success': False, 'message': 'Trading engine not initialized'})
    
    orders = trading_engine.get_orders()
    
    return jsonify({'success': True, 'orders': orders})

@app.route('/zerodha')
def zerodha():
    """
    Render the Zerodha integration page.
    """
    return render_template('zerodha.html', 
                          is_authenticated=trading_engine.is_authenticated() if trading_engine else False)

@app.route('/api/zerodha/login', methods=['GET'])
def zerodha_login():
    """
    Get Zerodha login URL.
    """
    if not trading_engine:
        return jsonify({'success': False, 'message': 'Trading engine not initialized'})
    
    login_url = trading_engine.login(open_browser=False)
    
    return jsonify({'success': True, 'login_url': login_url})

@app.route('/api/zerodha/complete', methods=['POST'])
def zerodha_complete_login():
    """
    Complete Zerodha login.
    """
    if not trading_engine:
        return jsonify({'success': False, 'message': 'Trading engine not initialized'})
    
    redirect_url = request.form.get('redirect_url')
    
    if not redirect_url:
        return jsonify({'success': False, 'message': 'No redirect URL provided'})
    
    success = trading_engine.complete_login(redirect_url)
    
    if success:
        return jsonify({'success': True, 'message': 'Login completed successfully'})
    else:
        return jsonify({'success': False, 'message': 'Error completing login'})

@app.route('/api/zerodha/logout', methods=['POST'])
def zerodha_logout():
    """
    Logout from Zerodha.
    """
    if not trading_engine:
        return jsonify({'success': False, 'message': 'Trading engine not initialized'})
    
    success = trading_engine.auth.logout()
    
    if success:
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    else:
        return jsonify({'success': False, 'message': 'Error logging out'})

def main():
    """
    Main entry point for the dashboard.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Algorithmic Trading System Dashboard')
    parser.add_argument('--config', '-c', help='Path to config file')
    parser.add_argument('--host', d<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>
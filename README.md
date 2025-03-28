# Algorithmic Trading System Documentation

## Overview

This document provides an overview of the algorithmic trading system developed for Zerodha integration. The system allows you to develop, backtest, and deploy trading algorithms using Python, with seamless integration to the Zerodha trading platform.

## System Architecture

The system consists of the following main components:

1. **Data Fetching Module**: Retrieves historical and real-time market data from various sources including Yahoo Finance and Zerodha.
2. **Backtesting Framework**: Simulates trading strategies on historical data to evaluate performance.
3. **Trading Algorithms**: Implements various technical analysis-based trading strategies.
4. **Zerodha Integration**: Connects to Zerodha's Kite Connect API for live trading.
5. **User Interface**: Provides both command-line and web-based interfaces for system interaction.

## Installation and Setup

### Prerequisites

- Python 3.10 or higher
- Zerodha trading account (for live trading)
- Kite Connect API credentials

### Installation

1. Clone the repository:
```
git clone <repository-url>
cd algorithmic_trading
```

2. Create and activate a virtual environment:
```
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Configure your Zerodha API credentials:
```
python -m ui.cli config set zerodha.api_key YOUR_API_KEY
python -m ui.cli config set zerodha.api_secret YOUR_API_SECRET
python -m ui.cli config save
```

## Using the Command-Line Interface

The system provides a comprehensive command-line interface for all operations.

### Starting the CLI

```
python -m ui.cli
```

### Basic Commands

- `config`: Manage configuration settings
- `zerodha`: Manage Zerodha integration
- `data`: Fetch and manage market data
- `strategy`: Manage trading strategies
- `backtest`: Run backtests on strategies
- `trade`: Manage live trading
- `help`: Show help information

### Examples

#### Fetching Data
```
algo-trading> data fetch RELIANCE.NS 365 1d
```

#### Creating a Strategy
```
algo-trading> strategy create MyTrendStrategy trend RELIANCE.NS ema_short=20 ema_long=50
```

#### Running a Backtest
```
algo-trading> backtest run MyTrendStrategy 100000 0.1
```

#### Starting Paper Trading
```
algo-trading> trade start MyTrendStrategy paper
```

## Using the Web Dashboard

The system also provides a web-based dashboard for visual interaction.

### Starting the Dashboard

```
python -m ui.dashboard
```

Then open your browser and navigate to `http://localhost:5000`.

### Dashboard Features

- Configuration management
- Data visualization
- Strategy creation and management
- Backtesting with performance metrics
- Trading control and monitoring
- Zerodha integration management

## Data Fetching

The system can fetch data from multiple sources:

### Yahoo Finance

```python
from data_fetcher.factory import DataFetcherFactory

factory = DataFetcherFactory()
fetcher = factory.get_yahoo_fetcher()

# Fetch historical data
data = fetcher.fetch_historical_data(
    symbol="RELIANCE.NS",
    start_date="2023-01-01",
    end_date="2023-12-31",
    interval="1d"
)
```

### Zerodha

```python
from zerodha_integration.trading_engine import TradingEngine

engine = TradingEngine(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")
engine.login()  # Follow the login process

# Fetch historical data
data = engine.get_historical_data(
    symbol="NSE:RELIANCE",
    from_date=datetime(2023, 1, 1),
    to_date=datetime(2023, 12, 31),
    interval="day"
)
```

## Backtesting Strategies

The system provides a robust backtesting framework:

```python
from backtesting.base import Backtester
from strategies.advanced import TrendFollowingStrategy

# Create a strategy
strategy = TrendFollowingStrategy(
    symbol="RELIANCE.NS",
    ema_short=20,
    ema_long=50,
    adx_period=14,
    adx_threshold=25
)

# Create a backtester
backtester = Backtester(
    strategy=strategy,
    data={"RELIANCE.NS": data},
    initial_capital=100000.0,
    commission=0.001
)

# Run the backtest
results = backtester.run()

# Plot results
backtester.plot_results()
```

## Trading Strategies

The system includes several pre-built strategies:

### Trend Following Strategy

Uses EMA crossovers, ADX for trend strength, and MACD for signal confirmation with trailing stops.

```python
from strategies.advanced import TrendFollowingStrategy

strategy = TrendFollowingStrategy(
    symbol="RELIANCE.NS",
    ema_short=20,
    ema_long=50,
    adx_period=14,
    adx_threshold=25,
    risk_per_trade=0.02,
    trailing_stop_pct=0.05
)
```

### Mean Reversion Strategy

Identifies overbought/oversold conditions using Bollinger Bands and RSI with ATR-based stop losses and take profits.

```python
from strategies.advanced import MeanReversionStrategy

strategy = MeanReversionStrategy(
    symbol="RELIANCE.NS",
    bb_period=20,
    bb_std=2.0,
    rsi_period=14,
    rsi_oversold=30,
    rsi_overbought=70,
    risk_per_trade=0.02,
    take_profit_atr_multiple=2.0,
    stop_loss_atr_multiple=1.0
)
```

### Breakout Strategy

Detects price consolidation patterns and enters on breakouts with volume confirmation.

```python
from strategies.advanced import BreakoutStrategy

strategy = BreakoutStrategy(
    symbol="RELIANCE.NS",
    channel_period=20,
    volume_factor=1.5,
    consolidation_factor=0.5,
    risk_per_trade=0.02,
    stop_loss_atr_multiple=1.5,
    take_profit_atr_multiple=3.0
)
```

## Zerodha Integration

The system provides seamless integration with Zerodha's Kite Connect API:

```python
from zerodha_integration.trading_engine import TradingEngine
from zerodha_integration.orders import OrderType, ProductType, TransactionType

# Create trading engine
engine = TradingEngine(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")

# Login to Zerodha
login_url = engine.login(open_browser=True)
# Complete the login process in your browser

# Place an order
order_id = engine.place_order(
    symbol="RELIANCE",
    exchange="NSE",
    transaction_type=TransactionType.BUY,
    quantity=10,
    order_type=OrderType.MARKET,
    product_type=ProductType.INTRADAY
)

# Get positions
positions = engine.get_positions()

# Get orders
orders = engine.get_orders()
```

## Running Tests

The system includes comprehensive tests to ensure all components work correctly:

```
python -m tests.run_tests
```

## Extending the System

### Creating Custom Strategies

You can create custom strategies by extending the `Strategy` base class:

```python
from backtesting.base import Strategy

class MyCustomStrategy(Strategy):
    def __init__(self, symbol, param1=10, param2=20):
        super().__init__(symbol)
        self.name = "My Custom Strategy"
        self.param1 = param1
        self.param2 = param2
    
    def generate_signals(self, data):
        # Calculate indicators
        data['indicator1'] = ...
        data['indicator2'] = ...
        
        # Generate signals
        data['signal'] = 0
        
        # Buy condition
        buy_condition = ...
        data.loc[buy_condition, 'signal'] = 1
        
        # Sell condition
        sell_condition = ...
        data.loc[sell_condition, 'signal'] = -1
        
        return data
```

### Adding New Data Sources

You can add new data sources by creating a new fetcher class:

```python
from data_fetcher.base import DataFetcher

class MyCustomFetcher(DataFetcher):
    def __init__(self, api_key=None):
        super().__init__()
        self.api_key = api_key
    
    def fetch_historical_data(self, symbol, start_date, end_date, interval):
        # Implement data fetching logic
        ...
        
        # Return pandas DataFrame with OHLCV data
        return data
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure your Zerodha API credentials are correct and that you've completed the login process.

2. **Data Fetching Issues**: Check your internet connection and verify that the symbol exists on the specified exchange.

3. **Backtesting Performance**: For large datasets, consider using a smaller date range or a larger timeframe.

4. **Live Trading Issues**: Ensure you have sufficient funds in your Zerodha account and that the symbols are tradable.

### Getting Help

If you encounter any issues, please:

1. Check the logs in the `logs` directory
2. Run the tests to ensure all components are working correctly
3. Consult the Zerodha API documentation for API-specific issues

## Conclusion

This algorithmic trading system provides a comprehensive framework for developing, testing, and deploying trading strategies with Zerodha integration. By following the documentation and examples, you can create sophisticated trading algorithms and automate your trading process.

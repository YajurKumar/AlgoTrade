"""
Data normalization utilities for algorithmic trading system.
This module provides functions to normalize and preprocess market data.
"""

import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('data_normalizer')

def normalize_column_names(df):
    """
    Normalize column names to a standard format.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with market data.
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with normalized column names.
    """
    column_map = {
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Adj Close': 'adj_close',
        'Volume': 'volume',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume',
        'last_price': 'close',
        'ohlc.open': 'open',
        'ohlc.high': 'high',
        'ohlc.low': 'low',
        'ohlc.close': 'close',
        'oi': 'open_interest'
    }
    
    # Create a mapping for the columns that exist in the DataFrame
    mapping = {col: column_map.get(col, col) for col in df.columns if col in column_map}
    
    # Rename columns
    if mapping:
        df = df.rename(columns=mapping)
    
    return df

def ensure_ohlcv_columns(df):
    """
    Ensure that the DataFrame has the standard OHLCV columns.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with market data.
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with standard OHLCV columns.
    """
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    
    # Check if all required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.warning(f"Missing columns: {missing_columns}")
        
        # If close exists but other price columns are missing, fill them with close
        if 'close' in df.columns:
            for col in ['open', 'high', 'low']:
                if col in missing_columns:
                    df[col] = df['close']
                    logger.info(f"Created {col} column from close")
        
        # If volume is missing, create it with zeros
        if 'volume' in missing_columns:
            df['volume'] = 0
            logger.info("Created volume column with zeros")
    
    return df

def resample_data(df, timeframe):
    """
    Resample data to a different timeframe.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with market data. Index must be datetime.
    timeframe : str
        Target timeframe in pandas resample format (e.g., '1H', '1D', '1W').
        
    Returns:
    --------
    pandas.DataFrame
        Resampled DataFrame.
    """
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        logger.error("DataFrame index must be DatetimeIndex for resampling")
        return df
    
    # Define how to resample each column
    resampler = df.resample(timeframe)
    
    # Create a new DataFrame with resampled data
    resampled = pd.DataFrame()
    
    # Handle OHLCV columns if they exist
    if 'open' in df.columns:
        resampled['open'] = resampler['open'].first()
    if 'high' in df.columns:
        resampled['high'] = resampler['high'].max()
    if 'low' in df.columns:
        resampled['low'] = resampler['low'].min()
    if 'close' in df.columns:
        resampled['close'] = resampler['close'].last()
    if 'volume' in df.columns:
        resampled['volume'] = resampler['volume'].sum()
    if 'adj_close' in df.columns:
        resampled['adj_close'] = resampler['adj_close'].last()
    if 'open_interest' in df.columns:
        resampled['open_interest'] = resampler['open_interest'].last()
    
    # Handle other columns by taking the last value
    other_columns = [col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume', 'adj_close', 'open_interest']]
    for col in other_columns:
        resampled[col] = resampler[col].last()
    
    return resampled

def calculate_returns(df, column='close', periods=1):
    """
    Calculate returns for a specified column.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with market data.
    column : str, optional
        Column to calculate returns for. Default is 'close'.
    periods : int, optional
        Number of periods to calculate returns over. Default is 1.
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with an additional column for returns.
    """
    if column not in df.columns:
        logger.error(f"Column {column} not found in DataFrame")
        return df
    
    # Calculate simple returns
    return_column = f'{column}_return_{periods}'
    df[return_column] = df[column].pct_change(periods=periods)
    
    return df

def calculate_log_returns(df, column='close', periods=1):
    """
    Calculate logarithmic returns for a specified column.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with market data.
    column : str, optional
        Column to calculate returns for. Default is 'close'.
    periods : int, optional
        Number of periods to calculate returns over. Default is 1.
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with an additional column for log returns.
    """
    if column not in df.columns:
        logger.error(f"Column {column} not found in DataFrame")
        return df
    
    # Calculate log returns
    log_return_column = f'{column}_log_return_{periods}'
    df[log_return_column] = np.log(df[column] / df[column].shift(periods))
    
    return df

def add_technical_indicators(df, indicators=None):
    """
    Add technical indicators to the DataFrame.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with market data.
    indicators : list, optional
        List of indicators to add. If None, a default set is used.
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with additional columns for technical indicators.
    """
    # Ensure we have OHLCV columns
    df = ensure_ohlcv_columns(df)
    
    if indicators is None:
        indicators = ['sma', 'ema', 'rsi', 'macd', 'bollinger']
    
    # Simple Moving Average
    if 'sma' in indicators:
        for period in [5, 10, 20, 50, 200]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
    
    # Exponential Moving Average
    if 'ema' in indicators:
        for period in [5, 10, 20, 50, 200]:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
    
    # Relative Strength Index
    if 'rsi' in indicators:
        for period in [14]:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
    
    # Moving Average Convergence Divergence
    if 'macd' in indicators:
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd_line'] = ema_12 - ema_26
        df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd_line'] - df['macd_signal']
    
    # Bollinger Bands
    if 'bollinger' in indicators:
        for period in [20]:
            df[f'bollinger_mid_{period}'] = df['close'].rolling(window=period).mean()
            df[f'bollinger_std_{period}'] = df['close'].rolling(window=period).std()
            df[f'bollinger_upper_{period}'] = df[f'bollinger_mid_{period}'] + 2 * df[f'bollinger_std_{period}']
            df[f'bollinger_lower_{period}'] = df[f'bollinger_mid_{period}'] - 2 * df[f'bollinger_std_{period}']
    
    return df

def prepare_data_for_backtesting(df, dropna=True, add_indicators=True):
    """
    Prepare data for backtesting by normalizing columns and adding indicators.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with market data.
    dropna : bool, optional
        Whether to drop rows with NaN values. Default is True.
    add_indicators : bool, optional
        Whether to add technical indicators. Default is True.
        
    Returns:
    --------
    pandas.DataFrame
        Prepared DataFrame.
    """
    # Normalize column names
    df = normalize_column_names(df)
    
    # Ensure OHLCV columns
    df = ensure_ohlcv_columns(df)
    
    # Add technical indicators
    if add_indicators:
        df = add_technical_indicators(df)
    
    # Calculate returns
    df = calculate_returns(df)
    df = calculate_log_returns(df)
    
    # Drop NaN values
    if dropna:
        df = df.dropna()
    
    return df

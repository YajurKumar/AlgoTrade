"""
Authentication module for Zerodha Kite Connect API.
This module provides functionality to authenticate with Zerodha and manage API sessions.
"""

import os
import json
import logging
import webbrowser
import hashlib
import time
from kiteconnect import KiteConnect
from urllib.parse import parse_qs, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('zerodha_auth')

class ZerodhaAuth:
    """
    Class to handle authentication with Zerodha's Kite Connect API.
    """
    
    def __init__(self, api_key=None, api_secret=None, redirect_url=None, config_file=None):
        """
        Initialize the Zerodha authentication handler.
        
        Parameters:
        -----------
        api_key : str, optional
            Zerodha API key.
        api_secret : str, optional
            Zerodha API secret.
        redirect_url : str, optional
            Redirect URL registered with Zerodha.
        config_file : str, optional
            Path to a config file containing API credentials.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_url = redirect_url
        self.access_token = None
        self.kite = None
        self.config_file = config_file
        
        # Load credentials from config file if provided
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
        
        # Initialize Kite Connect if API key is available
        if self.api_key:
            self.kite = KiteConnect(api_key=self.api_key)
            logger.info(f"Initialized Kite Connect with API key: {self.api_key}")
    
    def load_config(self, config_file):
        """
        Load API credentials from a config file.
        
        Parameters:
        -----------
        config_file : str
            Path to the config file containing API credentials.
            
        Returns:
        --------
        bool
            True if credentials were loaded successfully, False otherwise.
        """
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            self.api_key = config.get('api_key')
            self.api_secret = config.get('api_secret')
            self.redirect_url = config.get('redirect_url')
            self.access_token = config.get('access_token')
            
            logger.info(f"Loaded credentials from {config_file}")
            
            # Initialize Kite Connect with loaded API key
            if self.api_key:
                self.kite = KiteConnect(api_key=self.api_key)
                
                # Set access token if available
                if self.access_token:
                    self.kite.set_access_token(self.access_token)
                    logger.info("Set access token from config file")
                
                return True
            else:
                logger.error("API key not found in config file")
                return False
        
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return False
    
    def save_config(self, config_file=None):
        """
        Save API credentials to a config file.
        
        Parameters:
        -----------
        config_file : str, optional
            Path to the config file. If None, uses the instance's config_file.
            
        Returns:
        --------
        bool
            True if credentials were saved successfully, False otherwise.
        """
        if config_file is None:
            config_file = self.config_file
        
        if config_file is None:
            logger.error("No config file specified")
            return False
        
        try:
            config = {
                'api_key': self.api_key,
                'api_secret': self.api_secret,
                'redirect_url': self.redirect_url,
                'access_token': self.access_token
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(config_file)), exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            
            logger.info(f"Saved credentials to {config_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
            return False
    
    def get_login_url(self):
        """
        Get the Zerodha login URL.
        
        Returns:
        --------
        str
            The login URL.
        """
        if not self.kite:
            logger.error("Kite Connect not initialized. Set API key first.")
            return None
        
        return self.kite.login_url()
    
    def generate_session(self, request_token):
        """
        Generate a session by exchanging the request token for an access token.
        
        Parameters:
        -----------
        request_token : str
            The request token obtained after login.
            
        Returns:
        --------
        bool
            True if session was generated successfully, False otherwise.
        """
        if not self.kite:
            logger.error("Kite Connect not initialized. Set API key first.")
            return False
        
        if not self.api_secret:
            logger.error("API secret not set. Cannot generate session.")
            return False
        
        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)
            
            logger.info("Generated session successfully")
            
            # Save to config file if available
            if self.config_file:
                self.save_config()
            
            return True
        
        except Exception as e:
            logger.error(f"Error generating session: {str(e)}")
            return False
    
    def extract_request_token(self, redirect_url):
        """
        Extract the request token from the redirect URL.
        
        Parameters:
        -----------
        redirect_url : str
            The URL to which the user was redirected after login.
            
        Returns:
        --------
        str
            The request token.
        """
        try:
            parsed = urlparse(redirect_url)
            query_params = parse_qs(parsed.query)
            
            if 'request_token' in query_params:
                request_token = query_params['request_token'][0]
                logger.info(f"Extracted request token: {request_token}")
                return request_token
            else:
                logger.error("No request token found in redirect URL")
                return None
        
        except Exception as e:
            logger.error(f"Error extracting request token: {str(e)}")
            return None
    
    def login(self, open_browser=True):
        """
        Start the login flow.
        
        Parameters:
        -----------
        open_browser : bool, optional
            Whether to open the login URL in a browser.
            
        Returns:
        --------
        str
            The login URL.
        """
        if not self.kite:
            logger.error("Kite Connect not initialized. Set API key first.")
            return None
        
        login_url = self.get_login_url()
        
        if open_browser:
            webbrowser.open(login_url)
            logger.info(f"Opened login URL in browser: {login_url}")
        
        return login_url
    
    def complete_login(self, redirect_url):
        """
        Complete the login flow by extracting the request token and generating a session.
        
        Parameters:
        -----------
        redirect_url : str
            The URL to which the user was redirected after login.
            
        Returns:
        --------
        bool
            True if login was completed successfully, False otherwise.
        """
        request_token = self.extract_request_token(redirect_url)
        
        if request_token:
            return self.generate_session(request_token)
        else:
            return False
    
    def is_authenticated(self):
        """
        Check if the user is authenticated.
        
        Returns:
        --------
        bool
            True if authenticated, False otherwise.
        """
        if not self.kite or not self.access_token:
            return False
        
        try:
            # Try to get user profile to check if access token is valid
            self.kite.profile()
            return True
        except Exception:
            return False
    
    def logout(self):
        """
        Logout and invalidate the access token.
        
        Returns:
        --------
        bool
            True if logout was successful, False otherwise.
        """
        if not self.kite or not self.access_token:
            logger.warning("Not logged in")
            return True
        
        try:
            self.kite.invalidate_access_token()
            self.access_token = None
            
            # Update config file if available
            if self.config_file:
                self.save_config()
            
            logger.info("Logged out successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error logging out: {str(e)}")
            return False
    
    def get_kite(self):
        """
        Get the KiteConnect instance.
        
        Returns:
        --------
        KiteConnect
            The KiteConnect instance.
        """
        return self.kite

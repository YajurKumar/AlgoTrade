"""
Main test runner for the algorithmic trading system.
This script runs all the tests and generates a report.
"""

import os
import sys
import unittest
import time
import datetime

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from tests.test_data_fetcher import TestDataFetcher
from tests.test_backtesting import TestBacktesting
from tests.test_strategies import TestStrategies
from tests.test_integration import TestIntegration

def run_tests():
    """Run all tests and generate a report."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add tests
    test_suite.addTest(unittest.makeSuite(TestDataFetcher))
    test_suite.addTest(unittest.makeSuite(TestBacktesting))
    test_suite.addTest(unittest.makeSuite(TestStrategies))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Create test runner
    test_runner = unittest.TextTestRunner(verbosity=2)
    
    # Run tests
    print("\n" + "="*80)
    print(f"Running tests at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    start_time = time.time()
    test_result = test_runner.run(test_suite)
    end_time = time.time()
    
    # Generate report
    print("\n" + "="*80)
    print("Test Report")
    print("="*80)
    print(f"Tests run: {test_result.testsRun}")
    print(f"Errors: {len(test_result.errors)}")
    print(f"Failures: {len(test_result.failures)}")
    print(f"Skipped: {len(test_result.skipped)}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    print("="*80 + "\n")
    
    # Return success status
    return len(test_result.errors) == 0 and len(test_result.failures) == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

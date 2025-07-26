"""
Simple test script for Stock Tracker application
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import streamlit as st
        print("OK: Streamlit imported successfully")
    except ImportError as e:
        print(f"ERROR: Streamlit import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("OK: Pandas imported successfully")
    except ImportError as e:
        print(f"ERROR: Pandas import failed: {e}")
        return False
    
    try:
        import plotly.express as px
        print("OK: Plotly imported successfully")
    except ImportError as e:
        print(f"ERROR: Plotly import failed: {e}")
        return False
    
    return True

def test_app_syntax():
    """Test if app.py has valid syntax"""
    print("Testing app.py syntax...")
    
    try:
        import ast
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print("OK: app.py syntax is valid")
        return True
    except Exception as e:
        print(f"ERROR: app.py syntax error: {e}")
        return False

def run_tests():
    """Run basic tests"""
    print("Stock Tracker - Basic Tests")
    print("=" * 40)
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    tests = [
        ("Import Tests", test_imports),
        ("Syntax Tests", test_app_syntax)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        result = test_func()
        results.append((test_name, result))
        
        if result:
            print(f"PASS: {test_name}")
        else:
            print(f"FAIL: {test_name}")
    
    print("\n" + "=" * 40)
    print("Test Summary")
    print("=" * 40)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nSUCCESS: All tests passed!")
        print("To start the application:")
        print("  Windows: Double-click 'start_app.bat'")
        print("  Manual: streamlit run app.py")
    else:
        print("\nWARNING: Some tests failed.")
        print("Common solutions:")
        print("  - Install missing packages: pip install -r requirements.txt")
        print("  - Check file locations and permissions")
    
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    input("\nPress Enter to continue...")
    sys.exit(0 if success else 1)

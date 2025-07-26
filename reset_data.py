"""
Quick reset script to clear all data and start fresh
"""

import os
import json

def reset_data():
    """Clear all stored data"""
    data_file = "stock_data.json"
    
    if os.path.exists(data_file):
        print("Removing existing data file...")
        os.remove(data_file)
        print("Data file removed successfully!")
    else:
        print("No data file found - starting fresh!")
    
    print("\nRestart your application to load clean sample data.")
    print("The sample data will now include all ASINs for all parent products.")

if __name__ == "__main__":
    reset_data()

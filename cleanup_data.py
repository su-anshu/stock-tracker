"""
Data cleanup script to fix products with 'nan' descriptions
"""

import json
import os

def cleanup_data():
    """Clean up products with invalid descriptions"""
    data_file = "stock_data.json"
    
    if not os.path.exists(data_file):
        print("No data file found - nothing to clean up")
        return
    
    print("Loading data file...")
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    # Clean up packet variations
    fixed_count = 0
    if 'packet_variations' in data:
        for parent_id, variations in data['packet_variations'].items():
            for asin, details in variations.items():
                # Fix invalid descriptions
                if not details.get('description') or details.get('description') == 'nan' or str(details.get('description')).lower() == 'nan':
                    # Create a proper description
                    weight = details.get('weight', 'Unknown')
                    parent_name = data.get('parent_items', {}).get(parent_id, {}).get('name', parent_id)
                    new_description = f"{weight}kg {parent_name} Pack"
                    details['description'] = new_description
                    fixed_count += 1
                    print(f"Fixed ASIN {asin}: '{details.get('description')}' -> '{new_description}'")
                
                # Ensure all required fields exist
                if 'weight' not in details:
                    details['weight'] = 1.0
                if 'mrp' not in details:
                    details['mrp'] = 0
    
    if fixed_count > 0:
        # Save the cleaned data
        print(f"\nFixed {fixed_count} invalid descriptions")
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
        print("Data file updated successfully!")
        print("\nRestart your application to see the cleaned data.")
    else:
        print("No issues found - data is already clean!")

if __name__ == "__main__":
    cleanup_data()

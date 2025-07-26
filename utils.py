"""
Utility functions for the Stock Tracker application
"""

import pandas as pd
import datetime
import json
import os
from config import EXCEL_COLUMN_MAPPINGS, TRANSACTION_TYPES

def find_column(df, possible_names):
    """Find a column in DataFrame using possible column names"""
    for col in df.columns:
        if col in possible_names:
            return col
    return None

def validate_asin_format(asin):
    """Validate ASIN format (basic validation)"""
    if not asin:
        return False
    # Basic ASIN validation - should be 10 characters alphanumeric
    if len(asin) == 10 and asin.isalnum():
        return True
    return False

def validate_weight(weight):
    """Validate weight value"""
    try:
        weight_val = float(weight)
        return weight_val > 0
    except (ValueError, TypeError):
        return False

def calculate_stock_value(stock_data, parent_items, packet_variations):
    """Calculate total stock value based on MRP"""
    total_value = 0
    
    for parent_id, stock in stock_data.items():
        if parent_id in parent_items:
            # Calculate packed stock value
            packed_stock = stock.get("packed_stock", {})
            for asin, units in packed_stock.items():
                if (parent_id in packet_variations and 
                    asin in packet_variations[parent_id] and
                    units > 0):
                    mrp = packet_variations[parent_id][asin].get("mrp", 0)
                    total_value += units * mrp
    
    return total_value

def get_low_stock_items(stock_data, parent_items, packet_variations, threshold=5):
    """Get items with low stock (below threshold)"""
    low_stock_items = []
    
    for parent_id, stock in stock_data.items():
        if parent_id in parent_items:
            # Check loose stock
            loose_stock = stock.get("loose_stock", 0)
            if loose_stock < threshold:
                low_stock_items.append({
                    "type": "loose",
                    "parent_id": parent_id,
                    "product_name": parent_items[parent_id]["name"],
                    "current_stock": loose_stock,
                    "threshold": threshold
                })
            
            # Check packed stock
            packed_stock = stock.get("packed_stock", {})
            for asin, units in packed_stock.items():
                if (parent_id in packet_variations and 
                    asin in packet_variations[parent_id] and
                    units < threshold):
                    low_stock_items.append({
                        "type": "packed",
                        "parent_id": parent_id,
                        "product_name": parent_items[parent_id]["name"],
                        "asin": asin,
                        "description": packet_variations[parent_id][asin]["description"],
                        "current_stock": units,
                        "threshold": threshold
                    })
    
    return low_stock_items

def generate_stock_report(stock_data, parent_items, packet_variations, include_zero_stock=False):
    """Generate comprehensive stock report"""
    report_data = []
    
    for parent_id, stock in stock_data.items():
        if parent_id in parent_items:
            loose_stock = stock.get("loose_stock", 0)
            
            # Add loose stock entry
            if loose_stock > 0 or include_zero_stock:
                report_data.append({
                    "Product_ID": parent_id,
                    "Product_Name": parent_items[parent_id]["name"],
                    "Category": parent_items[parent_id].get("category", ""),
                    "Type": "Loose Stock",
                    "ASIN": "",
                    "Description": "Loose stock in kg",
                    "Quantity": loose_stock,
                    "Unit": "kg",
                    "Weight_per_Unit": 1,
                    "Total_Weight": loose_stock,
                    "MRP_per_Unit": 0,
                    "Total_Value": 0,
                    "Last_Updated": stock.get("last_updated", "")
                })
            
            # Add packed stock entries
            packed_stock = stock.get("packed_stock", {})
            for asin, units in packed_stock.items():
                if (parent_id in packet_variations and 
                    asin in packet_variations[parent_id] and
                    (units > 0 or include_zero_stock)):
                    
                    variation = packet_variations[parent_id][asin]
                    total_weight = units * variation["weight"]
                    mrp = variation.get("mrp", 0)
                    total_value = units * mrp
                    
                    report_data.append({
                        "Product_ID": parent_id,
                        "Product_Name": parent_items[parent_id]["name"],
                        "Category": parent_items[parent_id].get("category", ""),
                        "Type": "Packed Stock",
                        "ASIN": asin,
                        "Description": variation["description"],
                        "Quantity": units,
                        "Unit": "packets",
                        "Weight_per_Unit": variation["weight"],
                        "Total_Weight": total_weight,
                        "MRP_per_Unit": mrp,
                        "Total_Value": total_value,
                        "Last_Updated": stock.get("last_updated", "")
                    })
    
    return pd.DataFrame(report_data)

def process_sales_file(df, sales_type="fba"):
    """Process uploaded sales file and extract data"""
    processed_data = []
    errors = []
    
    # Get column mappings for the sales type
    if sales_type not in EXCEL_COLUMN_MAPPINGS:
        return [], ["Invalid sales type"]
    
    mappings = EXCEL_COLUMN_MAPPINGS[sales_type]
    
    # Find required columns
    asin_col = find_column(df, mappings["asin"])
    quantity_col = find_column(df, mappings["quantity"])
    date_col = find_column(df, mappings.get("date", []))
    order_id_col = find_column(df, mappings.get("order_id", []))
    
    if not asin_col or not quantity_col:
        return [], ["Required columns (ASIN, Quantity) not found in the file"]
    
    for index, row in df.iterrows():
        try:
            asin = str(row[asin_col]).strip()
            quantity = int(row[quantity_col])
            
            # Validate data
            if not validate_asin_format(asin):
                errors.append(f"Row {index+1}: Invalid ASIN format - {asin}")
                continue
            
            if quantity <= 0:
                errors.append(f"Row {index+1}: Invalid quantity - {quantity}")
                continue
            
            # Extract optional fields
            sale_date = None
            if date_col and pd.notna(row[date_col]):
                try:
                    sale_date = pd.to_datetime(row[date_col]).date()
                except:
                    sale_date = datetime.date.today()
            else:
                sale_date = datetime.date.today()
            
            order_id = ""
            if order_id_col and pd.notna(row[order_id_col]):
                order_id = str(row[order_id_col]).strip()
            
            processed_data.append({
                "asin": asin,
                "quantity": quantity,
                "date": sale_date,
                "order_id": order_id,
                "row_number": index + 1
            })
            
        except Exception as e:
            errors.append(f"Row {index+1}: Error processing - {str(e)}")
    
    return processed_data, errors

def backup_data(stock_data, transactions, parent_items, packet_variations, backup_folder="backups"):
    """Create a backup of all data"""
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"stock_backup_{timestamp}.json"
    backup_path = os.path.join(backup_folder, backup_filename)
    
    backup_data = {
        "backup_info": {
            "timestamp": datetime.datetime.now().isoformat(),
            "version": "1.0.0",
            "description": "Stock Tracker Data Backup"
        },
        "stock_data": stock_data,
        "transactions": transactions,
        "parent_items": parent_items,
        "packet_variations": packet_variations
    }
    
    try:
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        return backup_path
    except Exception as e:
        return None

def restore_data(backup_file_path):
    """Restore data from backup file"""
    try:
        with open(backup_file_path, 'r') as f:
            backup_data = json.load(f)
        
        return (
            backup_data.get("stock_data", {}),
            backup_data.get("transactions", []),
            backup_data.get("parent_items", {}),
            backup_data.get("packet_variations", {})
        )
    except Exception as e:
        return None, None, None, None

def calculate_daily_summary(transactions, target_date=None):
    """Calculate daily summary of transactions"""
    if target_date is None:
        target_date = datetime.date.today()
    
    target_date_str = target_date.isoformat()
    daily_transactions = [t for t in transactions if t.get("date") == target_date_str]
    
    summary = {
        "date": target_date_str,
        "total_transactions": len(daily_transactions),
        "stock_inward": {"count": 0, "total_weight": 0},
        "packing": {"count": 0, "total_packets": 0},
        "fba_sales": {"count": 0, "total_units": 0},
        "easy_ship_sales": {"count": 0, "total_units": 0}
    }
    
    for transaction in daily_transactions:
        transaction_type = transaction.get("type", "")
        
        if transaction_type == "Stock Inward":
            summary["stock_inward"]["count"] += 1
            summary["stock_inward"]["total_weight"] += transaction.get("weight", 0)
        elif transaction_type == "Packing":
            summary["packing"]["count"] += 1
            summary["packing"]["total_packets"] += transaction.get("quantity", 0)
        elif "FBA" in transaction_type:
            summary["fba_sales"]["count"] += 1
            summary["fba_sales"]["total_units"] += transaction.get("quantity", 0)
        elif "Easy Ship" in transaction_type:
            summary["easy_ship_sales"]["count"] += 1
            summary["easy_ship_sales"]["total_units"] += transaction.get("quantity", 0)
    
    return summary

def get_top_selling_products(transactions, parent_items, packet_variations, days=30):
    """Get top selling products in the last N days"""
    cutoff_date = datetime.date.today() - datetime.timedelta(days=days)
    cutoff_date_str = cutoff_date.isoformat()
    
    # Filter sales transactions
    sales_transactions = [
        t for t in transactions 
        if ("Sale" in t.get("type", "") and 
            t.get("date", "") >= cutoff_date_str)
    ]
    
    # Aggregate by parent product
    product_sales = {}
    
    for transaction in sales_transactions:
        parent_id = transaction.get("parent_id")
        asin = transaction.get("asin")
        quantity = transaction.get("quantity", 0)
        
        if parent_id and parent_id in parent_items:
            if parent_id not in product_sales:
                product_sales[parent_id] = {
                    "parent_id": parent_id,
                    "product_name": parent_items[parent_id]["name"],
                    "total_units": 0,
                    "total_weight": 0,
                    "total_value": 0,
                    "asin_breakdown": {}
                }
            
            product_sales[parent_id]["total_units"] += quantity
            
            if (asin and parent_id in packet_variations and 
                asin in packet_variations[parent_id]):
                weight_per_unit = packet_variations[parent_id][asin]["weight"]
                mrp = packet_variations[parent_id][asin].get("mrp", 0)
                
                product_sales[parent_id]["total_weight"] += quantity * weight_per_unit
                product_sales[parent_id]["total_value"] += quantity * mrp
                
                if asin not in product_sales[parent_id]["asin_breakdown"]:
                    product_sales[parent_id]["asin_breakdown"][asin] = 0
                product_sales[parent_id]["asin_breakdown"][asin] += quantity
    
    # Convert to list and sort by total units
    top_products = list(product_sales.values())
    top_products.sort(key=lambda x: x["total_units"], reverse=True)
    
    return top_products

def format_currency(amount, currency="₹"):
    """Format amount as currency"""
    return f"{currency}{amount:,.2f}"

def format_weight(weight_kg):
    """Format weight with appropriate units"""
    if weight_kg >= 1000:
        return f"{weight_kg/1000:.2f} tonnes"
    elif weight_kg >= 1:
        return f"{weight_kg:.2f} kg"
    else:
        return f"{weight_kg*1000:.0f} gm"

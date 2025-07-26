import streamlit as st
import pandas as pd
import datetime
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# Configure page
st.set_page_config(
    page_title="Stock Tracker - Mithila Foods",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Data persistence
DATA_FILE = "stock_data.json"

def initialize_sample_data():
    """Initialize with sample data"""
    st.session_state.parent_items = {
        "RICE_BASMATI": {"name": "Basmati Rice Premium", "unit": "kg", "category": "Rice", "reorder_level": 10.0},
        "RICE_JASMINE": {"name": "Jasmine Rice Fragrant", "unit": "kg", "category": "Rice", "reorder_level": 5.0},
        "WHEAT_FLOUR": {"name": "Wheat Flour Organic", "unit": "kg", "category": "Flour", "reorder_level": 8.0},
        "PULSES_TOOR": {"name": "Toor Dal Premium", "unit": "kg", "category": "Pulses", "reorder_level": 3.0}
    }
    
    st.session_state.packet_variations = {
        "RICE_BASMATI": {
            "B07BASMATI1KG": {"weight": 1, "asin": "B07BASMATI1KG", "description": "1kg Basmati Rice Pack", "mrp": 120},
            "B07BASMATI5KG": {"weight": 5, "asin": "B07BASMATI5KG", "description": "5kg Basmati Rice Pack", "mrp": 580}
        },
        "RICE_JASMINE": {
            "B07JASMINE1KG": {"weight": 1, "asin": "B07JASMINE1KG", "description": "1kg Jasmine Rice Pack", "mrp": 110}
        },
        "WHEAT_FLOUR": {
            "B07WHEAT1KG": {"weight": 1, "asin": "B07WHEAT1KG", "description": "1kg Wheat Flour Pack", "mrp": 45},
            "B07WHEAT5KG": {"weight": 5, "asin": "B07WHEAT5KG", "description": "5kg Wheat Flour Pack", "mrp": 220}
        },
        "PULSES_TOOR": {
            "B07TOOR1KG": {"weight": 1, "asin": "B07TOOR1KG", "description": "1kg Toor Dal Pack", "mrp": 85},
            "B07TOOR2KG": {"weight": 2, "asin": "B07TOOR2KG", "description": "2kg Toor Dal Pack", "mrp": 165}
        }
    }
    
    # Initialize stock data
    st.session_state.stock_data = {}
    for parent_id in st.session_state.parent_items:
        st.session_state.stock_data[parent_id] = {
            "loose_stock": 0,
            "packed_stock": {},
            "opening_stock": 0,
            "last_updated": datetime.datetime.now().isoformat()
        }
        for asin in st.session_state.packet_variations.get(parent_id, {}):
            st.session_state.stock_data[parent_id]["packed_stock"][asin] = 0
    
    st.session_state.transactions = []
    
    # Initialize return data
    st.session_state.return_data = {}
    for parent_id in st.session_state.parent_items:
        st.session_state.return_data[parent_id] = {
            "loose_return": {"good": 0, "bad": 0},
            "packed_return": {}
        }
        for asin in st.session_state.packet_variations.get(parent_id, {}):
            st.session_state.return_data[parent_id]["packed_return"][asin] = {"good": 0, "bad": 0}
    
    st.session_state.return_transactions = []

def save_data():
    """Save data to JSON file"""
    data = {
        "stock_data": st.session_state.stock_data,
        "transactions": st.session_state.transactions,
        "parent_items": st.session_state.parent_items,
        "packet_variations": st.session_state.packet_variations,
        "daily_opening_stock": getattr(st.session_state, 'daily_opening_stock', {}),
        "return_data": getattr(st.session_state, 'return_data', {}),
        "return_transactions": getattr(st.session_state, 'return_transactions', []),
        "last_updated": datetime.datetime.now().isoformat()
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_data():
    """Load data from JSON file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                st.session_state.stock_data = data.get("stock_data", {})
                st.session_state.transactions = data.get("transactions", [])
                st.session_state.parent_items = data.get("parent_items", {})
                st.session_state.packet_variations = data.get("packet_variations", {})
                st.session_state.daily_opening_stock = data.get("daily_opening_stock", {})
                st.session_state.return_data = data.get("return_data", {})
                st.session_state.return_transactions = data.get("return_transactions", [])
        except Exception as e:
            st.error(f"Error loading data: {e}")
            initialize_sample_data()
    else:
        initialize_sample_data()

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

if not st.session_state.initialized:
    load_data()
    # Ensure return data is initialized for existing users
    if not hasattr(st.session_state, 'return_data') or not st.session_state.return_data:
        st.session_state.return_data = {}
        for parent_id in st.session_state.parent_items:
            st.session_state.return_data[parent_id] = {
                "loose_return": {"good": 0, "bad": 0},
                "packed_return": {}
            }
            for asin in st.session_state.packet_variations.get(parent_id, {}):
                st.session_state.return_data[parent_id]["packed_return"][asin] = {"good": 0, "bad": 0}
    
    if not hasattr(st.session_state, 'return_transactions') or not st.session_state.return_transactions:
        st.session_state.return_transactions = []
    
    # Add reorder level to existing parent items (backward compatibility)
    for parent_id, parent_info in st.session_state.parent_items.items():
        if "reorder_level" not in parent_info:
            parent_info["reorder_level"] = 5.0  # Default reorder level of 5kg
    
    st.session_state.initialized = True

def record_transaction(transaction_type, parent_id, asin=None, quantity=0, weight=0, notes="", batch_id=None, transaction_date=None):
    """Record a transaction and return transaction ID"""
    transaction_id = len(st.session_state.transactions) + 1
    
    # Use provided date or default to today
    if transaction_date is None:
        transaction_date = datetime.date.today()
    
    transaction = {
        "id": transaction_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "date": transaction_date.isoformat(),
        "type": transaction_type,
        "parent_id": parent_id,
        "parent_name": st.session_state.parent_items[parent_id]["name"],
        "asin": asin,
        "quantity": quantity,
        "weight": weight,
        "notes": notes
    }
    
    # Add batch information if provided
    if batch_id:
        transaction["batch_id"] = batch_id
    
    st.session_state.transactions.append(transaction)
    save_data()
    return transaction_id

def get_clean_product_description(parent_id, asin):
    """Get a clean product description, handling NaN and empty values"""
    if (parent_id not in st.session_state.packet_variations or 
        asin not in st.session_state.packet_variations[parent_id]):
        return f"Unknown Product ({asin})"
    
    details = st.session_state.packet_variations[parent_id][asin]
    weight = details.get('weight', 1.0)
    description = details.get('description', '')
    
    # Clean up description - handle NaN and empty values
    if not description or str(description).lower() in ['nan', 'null', 'none', '']:
        parent_name = st.session_state.parent_items.get(parent_id, {}).get('name', 'Unknown Product')
        description = f"{weight}kg {parent_name}"
    
    return f"{description} ({weight}kg)"

def can_undo_transaction(transaction_id):
    """Check if a transaction can be undone (based on recording time, not transaction date)"""
    from config import DEFAULT_SETTINGS
    
    if not st.session_state.transactions:
        return False, "No transactions found"
    
    # Find transaction
    transaction = None
    for t in st.session_state.transactions:
        if t["id"] == transaction_id:
            transaction = t
            break
    
    if not transaction:
        return False, "Transaction not found"
    
    # Get configuration
    undo_window_hours = DEFAULT_SETTINGS.get("undo_window_hours", 24)
    max_recent_transactions = DEFAULT_SETTINGS.get("max_recent_transactions", 50)
    
    # Check if transaction was recorded recently (within configured window)
    # Use timestamp (when recorded) not date (transaction date)
    try:
        recorded_time = datetime.datetime.fromisoformat(transaction["timestamp"])
        current_time = datetime.datetime.now()
        time_diff = current_time - recorded_time
        
        # Allow undo if recorded within configured window
        if time_diff.total_seconds() > undo_window_hours * 60 * 60:  # Convert hours to seconds
            return False, f"Can only undo transactions recorded within last {undo_window_hours} hours"
    except:
        # Fallback to old logic if timestamp parsing fails
        today = datetime.date.today().isoformat()
        if transaction.get("date") != today:
            return False, "Can only undo transactions from today"
    
    # Check if it's one of the recent transactions (safety limit)
    recent_transactions = st.session_state.transactions[-max_recent_transactions:]
    if transaction not in recent_transactions:
        return False, f"Can only undo recent transactions (last {max_recent_transactions})"
    
    return True, "OK"

def undo_transaction(transaction_id):
    """Undo a specific transaction and reverse its effects"""
    try:
        # Find the transaction
        transaction = None
        transaction_index = None
        for i, t in enumerate(st.session_state.transactions):
            if t["id"] == transaction_id:
                transaction = t
                transaction_index = i
                break
        
        if not transaction:
            st.error("Transaction not found!")
            return False
        
        # Check if can undo
        can_undo, reason = can_undo_transaction(transaction_id)
        if not can_undo:
            st.error(f"Cannot undo: {reason}")
            return False
        
        # Reverse the transaction effects
        parent_id = transaction["parent_id"]
        trans_type = transaction["type"]
        quantity = transaction.get("quantity", 0)
        weight = transaction.get("weight", 0)
        asin = transaction.get("asin")
        
        if parent_id not in st.session_state.stock_data:
            st.error("Parent product not found!")
            return False
        
        # Reverse based on transaction type
        if trans_type == "Stock Inward":
            # Check if we can safely remove the inward stock
            current_loose = st.session_state.stock_data[parent_id]["loose_stock"]
            if current_loose < weight:
                st.error(f"Cannot undo: Would result in negative stock (Current: {current_loose} kg, Trying to remove: {weight} kg)")
                return False
            # Remove the inward stock
            st.session_state.stock_data[parent_id]["loose_stock"] -= weight
            
        elif trans_type == "Packing":
            # Check if we can safely reverse packing
            if asin and asin in st.session_state.stock_data[parent_id]["packed_stock"]:
                current_packed = st.session_state.stock_data[parent_id]["packed_stock"][asin]
                if current_packed < quantity:
                    st.error(f"Cannot undo: Would result in negative packed stock (Current: {current_packed}, Trying to remove: {quantity})")
                    return False
            # Reverse packing: add back loose stock, remove packed units
            st.session_state.stock_data[parent_id]["loose_stock"] += weight
            if asin and asin in st.session_state.stock_data[parent_id]["packed_stock"]:
                st.session_state.stock_data[parent_id]["packed_stock"][asin] -= quantity
            
        elif "Sale" in trans_type:
            # Reverse sale: add back packed stock
            if asin and asin in st.session_state.stock_data[parent_id]["packed_stock"]:
                st.session_state.stock_data[parent_id]["packed_stock"][asin] += quantity
        
        # Remove the transaction from history
        st.session_state.transactions.pop(transaction_index)
        
        # Update timestamp
        st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
        
        # Save data
        save_data()
        
        # Show success message with details
        if trans_type == "Stock Inward":
            st.success(f"✅ Successfully undone: {trans_type} for {transaction['parent_name']} (-{weight} kg)")
        elif trans_type == "Packing":
            st.success(f"✅ Successfully undone: {trans_type} for {transaction['parent_name']} (+{weight} kg loose, -{quantity} packed)")
        elif "Sale" in trans_type:
            st.success(f"✅ Successfully undone: {trans_type} for {transaction['parent_name']} (+{quantity} units)")
        else:
            st.success(f"✅ Successfully undone: {trans_type} for {transaction['parent_name']}")
        return True
        
    except Exception as e:
        st.error(f"Error undoing transaction: {e}")
        return False

def can_undo_batch(batch_id):
    """Check if an entire batch can be undone (based on recording time)"""
    from config import DEFAULT_SETTINGS
    
    # Find all transactions in the batch
    batch_transactions = [t for t in st.session_state.transactions if t.get("batch_id") == batch_id]
    
    if not batch_transactions:
        return False, "Batch not found"
    
    # Get configuration
    undo_window_hours = DEFAULT_SETTINGS.get("undo_window_hours", 24)
    
    # Check if batch was recorded recently (within configured window)
    try:
        # Get the latest transaction timestamp in the batch
        latest_timestamp = max(t.get("timestamp") for t in batch_transactions)
        recorded_time = datetime.datetime.fromisoformat(latest_timestamp)
        current_time = datetime.datetime.now()
        time_diff = current_time - recorded_time
        
        # Allow undo if recorded within configured window
        if time_diff.total_seconds() > undo_window_hours * 60 * 60:  # Convert hours to seconds
            return False, f"Can only undo batches recorded within last {undo_window_hours} hours"
    except:
        # Fallback to old logic if timestamp parsing fails
        today = datetime.date.today().isoformat()
        for transaction in batch_transactions:
            if transaction.get("date") != today:
                return False, "Can only undo batches from today"
    
    # Check if there are subsequent transactions affecting the same ASINs
    batch_asins = set(t.get("asin") for t in batch_transactions if t.get("asin"))
    latest_batch_time = max(t.get("timestamp") for t in batch_transactions)
    
    # Look for any transactions after the batch that affect the same ASINs
    for transaction in st.session_state.transactions:
        if (transaction.get("timestamp", "") > latest_batch_time and 
            transaction.get("asin") in batch_asins and
            transaction.get("batch_id") != batch_id):
            return False, f"Cannot undo: Activity found after batch on ASIN {transaction.get('asin')}"
    
    return True, "OK"

def undo_batch(batch_id):
    """Undo an entire batch of transactions"""
    try:
        # Check if batch has already been undone
        if 'undone_batches' in st.session_state and batch_id in st.session_state.undone_batches:
            st.error("❌ This batch has already been undone!")
            return False
        
        # Validate batch can be undone
        can_undo, reason = can_undo_batch(batch_id)
        if not can_undo:
            st.error(f"Cannot undo batch: {reason}")
            return False
        
        # Find all transactions in the batch
        batch_transactions = [t for t in st.session_state.transactions if t.get("batch_id") == batch_id]
        
        if not batch_transactions:
            st.error("Batch not found!")
            return False
        
        # Group transactions by parent and ASIN for efficient processing
        stock_adjustments = {}
        
        for transaction in batch_transactions:
            parent_id = transaction["parent_id"]
            asin = transaction.get("asin")
            quantity = transaction.get("quantity", 0)
            weight = transaction.get("weight", 0)
            trans_type = transaction["type"]
            
            if parent_id not in stock_adjustments:
                stock_adjustments[parent_id] = {"loose": 0, "packed": {}}
            
            # Calculate stock adjustment needed based on transaction type
            if "Sale" in trans_type:
                # For all types of sales (FBA Sale, Easy Ship Sale, etc.), add stock back
                if asin:
                    if asin not in stock_adjustments[parent_id]["packed"]:
                        stock_adjustments[parent_id]["packed"][asin] = 0
                    stock_adjustments[parent_id]["packed"][asin] += quantity
            elif trans_type == "Stock Inward":
                # For stock inward, remove the added loose stock
                stock_adjustments[parent_id]["loose"] -= weight
            elif trans_type == "Packing":
                # For packing, add back loose stock and remove packed units
                stock_adjustments[parent_id]["loose"] += weight
                if asin:
                    if asin not in stock_adjustments[parent_id]["packed"]:
                        stock_adjustments[parent_id]["packed"][asin] = 0
                    stock_adjustments[parent_id]["packed"][asin] -= quantity
        
        # Apply stock adjustments
        for parent_id, adjustments in stock_adjustments.items():
            # Ensure parent exists in stock data
            if parent_id not in st.session_state.stock_data:
                st.error(f"Parent product {parent_id} not found in stock data!")
                continue
            
            # Apply loose stock adjustments
            if adjustments["loose"] != 0:
                if "loose_stock" not in st.session_state.stock_data[parent_id]:
                    st.session_state.stock_data[parent_id]["loose_stock"] = 0
                st.session_state.stock_data[parent_id]["loose_stock"] += adjustments["loose"]
            
            # Apply packed stock adjustments
            for asin, quantity_to_add in adjustments["packed"].items():
                # Ensure packed_stock structure exists
                if "packed_stock" not in st.session_state.stock_data[parent_id]:
                    st.session_state.stock_data[parent_id]["packed_stock"] = {}
                
                # Ensure ASIN exists in packed_stock
                if asin not in st.session_state.stock_data[parent_id]["packed_stock"]:
                    st.session_state.stock_data[parent_id]["packed_stock"][asin] = 0
                
                # Apply the adjustment
                st.session_state.stock_data[parent_id]["packed_stock"][asin] += quantity_to_add
            
            st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
        
        # Remove all transactions in the batch
        st.session_state.transactions = [
            t for t in st.session_state.transactions 
            if t.get("batch_id") != batch_id
        ]
        
        save_data()
        
        batch_size = len(batch_transactions)
        batch_type = batch_transactions[0].get("type", "Unknown")
        
        st.success(f"✅ Successfully undone batch: {batch_type} ({batch_size} transactions)")
        return True
        
    except Exception as e:
        st.error(f"Error undoing batch: {e}")
        return False

def get_recent_transactions(limit=8):
    """Get recent transactions from today"""
    today = datetime.date.today().isoformat()
    today_transactions = []
    
    # Get all transactions from today
    for transaction in reversed(st.session_state.transactions):
        if transaction.get("date") == today:
            today_transactions.append(transaction)
            if len(today_transactions) >= limit:
                break
    
    return today_transactions

def show_debug_info():
    """Show debug information about current state"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Debug Info")
    
    if hasattr(st.session_state, 'last_transaction'):
        st.sidebar.write("**Last Transaction:**")
        st.sidebar.write(f"ID: {st.session_state.last_transaction.get('id', 'None')}")
        st.sidebar.write(f"Show Undo: {st.session_state.last_transaction.get('show_undo', False)}")
    
    st.sidebar.write("**Recent Transactions:**")
    if st.session_state.transactions:
        recent = st.session_state.transactions[-3:]
        for t in recent:
            st.sidebar.write(f"• {t['id']}: {t['type']} - {t.get('weight', 0)}kg")
    
    st.sidebar.write("**Stock Data Sample:**")
    if st.session_state.stock_data:
        for pid, stock in list(st.session_state.stock_data.items())[:2]:
            product_name = st.session_state.parent_items.get(pid, {}).get('name', pid)
            st.sidebar.write(f"• {product_name}: {stock.get('loose_stock', 0)} kg")

def show_immediate_undo(transaction_id, transaction_summary):
    """Show immediate undo option after recording a transaction"""
    st.success(f"✅ Transaction recorded successfully!")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**Added:** {transaction_summary}")
    with col2:
        if st.button("🔄 Undo", key=f"immediate_undo_{transaction_id}", help="Undo this transaction"):
            if undo_transaction(transaction_id):
                st.rerun()
            else:
                st.error("❌ Undo failed")

def show_batch_undo_option(batch_id, batch_description, batch_size):
    """Show immediate undo option for a batch"""
    st.success(f"✅ Batch uploaded successfully!")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**Batch:** {batch_description}")
        st.write(f"**Transactions:** {batch_size}")
    with col2:
        if st.button("🔄 Undo Batch", key=f"batch_undo_{batch_id}", help="Undo entire batch"):
            if undo_batch(batch_id):
                st.rerun()

def get_today_transactions():
    """Get all transactions from today"""
    today = datetime.date.today().isoformat()
    today_transactions = []
    
    for transaction in st.session_state.transactions:
        if transaction.get("date") == today:
            today_transactions.append(transaction)
    
    return today_transactions

def calculate_opening_stock():
    """Calculate or retrieve opening stock for today"""
    today = datetime.date.today().isoformat()
    
    # Check if we have opening stock data for today
    if "daily_opening_stock" not in st.session_state:
        st.session_state.daily_opening_stock = {}
    
    if today not in st.session_state.daily_opening_stock:
        # If no opening stock for today, use current stock as opening
        # (This happens on first run or new day)
        opening_stock = {}
        for parent_id, stock_data in st.session_state.stock_data.items():
            opening_stock[parent_id] = {
                "loose_stock": stock_data.get("loose_stock", 0),
                "packed_stock": stock_data.get("packed_stock", {}).copy()
            }
        st.session_state.daily_opening_stock[today] = opening_stock
        save_data()
    
    return st.session_state.daily_opening_stock[today]

def calculate_activity_summary(parent_id, today_transactions):
    """Calculate activity summary for a parent product today"""
    activity = {
        "stock_inward": 0,
        "packing_out": 0,  # loose stock used in packing
        "packing_in": {},  # units created by packing per ASIN
        "fba_sales": {},   # FBA sales per ASIN
        "easy_ship_sales": {},  # Easy Ship sales per ASIN
        "other_changes": 0,
        "activity_details": []
    }
    
    for transaction in today_transactions:
        if transaction.get("parent_id") == parent_id:
            trans_type = transaction.get("type", "")
            weight = transaction.get("weight", 0)
            quantity = transaction.get("quantity", 0)
            asin = transaction.get("asin", "")
            timestamp = transaction.get("timestamp", "")
            
            # Parse time for display
            try:
                time_obj = datetime.datetime.fromisoformat(timestamp)
                time_str = time_obj.strftime("%H:%M")
            except:
                time_str = "00:00"
            
            if trans_type == "Stock Inward":
                activity["stock_inward"] += weight
                activity["activity_details"].append({
                    "time": time_str,
                    "type": "Stock Inward",
                    "amount": weight,
                    "unit": "kg",
                    "notes": transaction.get("notes", "")
                })
                
            elif trans_type == "Packing":
                activity["packing_out"] += weight  # loose stock used
                if asin not in activity["packing_in"]:
                    activity["packing_in"][asin] = 0
                activity["packing_in"][asin] += quantity
                activity["activity_details"].append({
                    "time": time_str,
                    "type": "Packing",
                    "amount": f"-{weight}kg → +{quantity} units",
                    "asin": asin,
                    "notes": transaction.get("notes", "")
                })
                
            elif "FBA Sale" in trans_type:
                if asin not in activity["fba_sales"]:
                    activity["fba_sales"][asin] = 0
                activity["fba_sales"][asin] += quantity
                activity["activity_details"].append({
                    "time": time_str,
                    "type": "FBA Sale",
                    "amount": quantity,
                    "asin": asin,
                    "notes": transaction.get("notes", "")
                })
                
            elif "Easy Ship Sale" in trans_type:
                if asin not in activity["easy_ship_sales"]:
                    activity["easy_ship_sales"][asin] = 0
                activity["easy_ship_sales"][asin] += quantity
                activity["activity_details"].append({
                    "time": time_str,
                    "type": "Easy Ship Sale",
                    "amount": quantity,
                    "asin": asin,
                    "notes": transaction.get("notes", "")
                })
                
            else:
                # Other changes (adjustments, etc.)
                if "weight" in transaction:
                    activity["other_changes"] += weight
                activity["activity_details"].append({
                    "time": time_str,
                    "type": trans_type,
                    "amount": weight if weight else quantity,
                    "asin": asin,
                    "notes": transaction.get("notes", "")
                })
    
    return activity

def show_live_stock_view():
    """Display the Live Stock View dashboard in tabular format"""
    st.header("📦 Live Stock View")
    
    # Date display and controls
    today = datetime.date.today()
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.subheader(f"📅 Today: {today.strftime('%B %d, %Y')}")
    
    with col2:
        if st.button("🔄 Refresh View", help="Refresh live data"):
            st.rerun()
    
    with col3:
        if st.button("📊 Export Report", help="Export today's stock report"):
            export_daily_report()
    
    # Get today's data
    today_transactions = get_today_transactions()
    opening_stock = calculate_opening_stock()
    
    # Filter options
    st.subheader("🎛️ View Options")
    col1, col2 = st.columns(2)
    
    with col1:
        show_zero_stock = st.checkbox("Show Zero Stock Items", value=True)
    with col2:
        show_activity_only = st.checkbox("Show Only Items with Today's Activity", value=False)
    
    # Always show parent headers (no option needed)
    show_parent_headers = True
    
    # Build table data
    table_data = []
    
    for parent_id, parent_info in st.session_state.parent_items.items():
        # Get current and opening stock
        current_stock = st.session_state.stock_data.get(parent_id, {})
        opening_data = opening_stock.get(parent_id, {})
        
        # Calculate activity
        activity = calculate_activity_summary(parent_id, today_transactions)
        
        # Check if item has activity or stock
        has_activity = (activity["stock_inward"] != 0 or 
                       activity["packing_out"] != 0 or 
                       len(activity["fba_sales"]) > 0 or 
                       len(activity["easy_ship_sales"]) > 0 or
                       activity["other_changes"] != 0)
        
        current_loose = current_stock.get("loose_stock", 0)
        has_stock = current_loose > 0 or any(v > 0 for v in current_stock.get("packed_stock", {}).values())
        
        # Apply activity filter
        if show_activity_only and not has_activity:
            continue
            
        # Apply zero stock filter
        if not show_zero_stock and not has_stock and not has_activity:
            continue
        
        # Add parent header row (if enabled)
        if show_parent_headers:
            table_data.append({
                "Product/Variation": f"📦 **{parent_info['name'].upper()}**",
                "Type/Weight": "",
                "Opening Stock": "",
                "Stock Inward": "",
                "Packing Activity": "",
                "FBA Sales": "",
                "Easy Ship Sales": "",
                "Other Changes": "",
                "Closing Stock": "",
                "Row Type": "parent_header"
            })
        
        # Add loose stock row with reorder level highlighting
        opening_loose = opening_data.get("loose_stock", 0)
        loose_change = current_loose - opening_loose
        reorder_level = st.session_state.parent_items.get(parent_id, {}).get("reorder_level", 5.0)
        
        # Format values with colors
        def format_change(value, unit=""):
            if value > 0:
                return f"🟢 +{value}{unit}"
            elif value < 0:
                return f"🔴 {value}{unit}"
            else:
                return f"0{unit}"
        
        # Check if stock is at or below reorder level for highlighting
        is_low_stock = current_loose <= reorder_level
        stock_display = f"**{current_loose:.1f}kg**"
        if is_low_stock:
            stock_display = f"🚨 **{current_loose:.1f}kg** ⚠️ REORDER (≤{reorder_level:.1f}kg)"
        
        table_data.append({
            "Product/Variation": f"├ **Loose Stock**",
            "Type/Weight": "kg",
            "Opening Stock": f"{opening_loose:.1f}",
            "Stock Inward": format_change(activity["stock_inward"], "kg") if activity["stock_inward"] != 0 else "-",
            "Packing Activity": format_change(-activity["packing_out"], "kg") if activity["packing_out"] != 0 else "-",
            "FBA Sales": "-",
            "Easy Ship Sales": "-",
            "Other Changes": format_change(activity["other_changes"], "kg") if activity["other_changes"] != 0 else "-",
            "Closing Stock": stock_display,
            "Row Type": "loose_stock_reorder" if is_low_stock else "loose_stock"
        })
        
        # Add packed stock variations
        if parent_id in st.session_state.packet_variations:
            variations = st.session_state.packet_variations[parent_id]
            packed_stock = current_stock.get("packed_stock", {})
            opening_packed = opening_data.get("packed_stock", {})
            
            variation_list = list(variations.items())
            for i, (asin, variation_info) in enumerate(variation_list):
                current_units = packed_stock.get(asin, 0)
                opening_units = opening_packed.get(asin, 0)
                
                # Skip if no stock and no activity and not showing zero stock
                asin_has_activity = (asin in activity["packing_in"] or 
                                   asin in activity["fba_sales"] or 
                                   asin in activity["easy_ship_sales"])
                
                if not show_zero_stock and current_units == 0 and opening_units == 0 and not asin_has_activity:
                    continue
                
                weight = variation_info.get("weight", 0)
                description = variation_info.get("description", "")
                
                # Clean up description - remove 'nan' and create proper description
                if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                    parent_name = st.session_state.parent_items[parent_id]["name"]
                    description = f"{weight}kg {parent_name}"
                
                # Determine prefix (├ or └)
                is_last = (i == len(variation_list) - 1)
                prefix = "└" if is_last else "├"
                
                table_data.append({
                    "Product/Variation": f"{prefix} {description}",
                    "Type/Weight": f"{weight}kg",
                    "Opening Stock": f"{opening_units}",
                    "Stock Inward": "-",
                    "Packing Activity": format_change(activity["packing_in"].get(asin, 0)) if activity["packing_in"].get(asin, 0) != 0 else "-",
                    "FBA Sales": format_change(-activity["fba_sales"].get(asin, 0)) if activity["fba_sales"].get(asin, 0) != 0 else "-",
                    "Easy Ship Sales": format_change(-activity["easy_ship_sales"].get(asin, 0)) if activity["easy_ship_sales"].get(asin, 0) != 0 else "-",
                    "Other Changes": "-",
                    "Closing Stock": f"**{current_units} units**",
                    "Row Type": "packed_stock",
                    "ASIN": asin  # Keep ASIN in background for data processing
                })
    
    # Display the table
    if table_data:
        st.subheader("📋 Daily Stock Movement Table")
        
        # Create DataFrame
        df = pd.DataFrame(table_data)
        
        # Custom styling function
        def style_table(df):
            def highlight_rows(row):
                if row['Row Type'] == 'parent_header':
                    return ['background-color: #f0f2f6; font-weight: bold'] * len(row)
                elif row['Row Type'] == 'loose_stock':
                    return ['background-color: #f8f9fa'] * len(row)
                elif row['Row Type'] == 'loose_stock_reorder':
                    return ['background-color: #ffe6e6; border-left: 4px solid #ff4444; font-weight: bold'] * len(row)
                else:
                    return [''] * len(row)
            return df.style.apply(highlight_rows, axis=1)
        
        # Display the styled table
        display_df = df.drop(columns=['Row Type', 'ASIN'], errors='ignore')
        
        # Use HTML table for better formatting
        html_table = display_df.to_html(escape=False, index=False, table_id="stock_table")
        
        # Custom CSS for better table appearance
        st.markdown("""
        <style>
        #stock_table {
            border-collapse: collapse;
            width: 100%;
            font-size: 13px;
            margin-top: 10px;
        }
        #stock_table th, #stock_table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            vertical-align: top;
        }
        #stock_table th {
            background-color: #f2f2f2;
            font-weight: bold;
            font-size: 12px;
        }
        #stock_table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        #stock_table tr:hover {
            background-color: #f5f5f5;
        }
        .parent-header {
            background-color: #e6f3ff !important;
            font-weight: bold;
        }
        .loose-stock {
            background-color: #f0f8f0 !important;
        }
        .loose-stock-reorder {
            background-color: #ffe6e6 !important;
            border-left: 4px solid #ff4444 !important;
            animation: blink 1.5s infinite;
        }
        @keyframes blink {
            0%, 50% { background-color: #ffe6e6; }
            51%, 100% { background-color: #ffcccc; }
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(html_table, unsafe_allow_html=True)
        
        # Activity summary
        if today_transactions:
            st.subheader("📊 Today's Activity Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_inward = sum(t.get("weight", 0) for t in today_transactions if t.get("type") == "Stock Inward")
                st.metric("Stock Inward", f"{total_inward:.1f} kg")
            
            with col2:
                total_packed = len([t for t in today_transactions if t.get("type") == "Packing"])
                st.metric("Packing Operations", total_packed)
            
            with col3:
                total_fba = sum(t.get("quantity", 0) for t in today_transactions if "FBA Sale" in t.get("type", ""))
                st.metric("FBA Sales", f"{total_fba} units")
            
            with col4:
                total_easy_ship = sum(t.get("quantity", 0) for t in today_transactions if "Easy Ship Sale" in t.get("type", ""))
                st.metric("Easy Ship Sales", f"{total_easy_ship} units")
        
        # Reorder Level Alerts Summary
        st.subheader("🚨 Reorder Level Alerts")
        reorder_alerts = []
        for parent_id, parent_info in st.session_state.parent_items.items():
            current_loose = st.session_state.stock_data.get(parent_id, {}).get("loose_stock", 0)
            reorder_level = parent_info.get("reorder_level", 5.0)
            if current_loose <= reorder_level:
                reorder_alerts.append({
                    "Product": parent_info["name"],
                    "Current Stock": f"{current_loose:.1f} kg",
                    "Reorder Level": f"{reorder_level:.1f} kg",
                    "Deficit": f"{max(0, reorder_level - current_loose):.1f} kg"
                })
        
        if reorder_alerts:
            st.error(f"⚠️ **{len(reorder_alerts)} product(s) at or below reorder level!**")
            reorder_df = pd.DataFrame(reorder_alerts)
            st.dataframe(reorder_df, use_container_width=True, hide_index=True)
        else:
            st.success("✅ All products above reorder level")
        
    else:
        st.info("📭 No stock data to display with current filters. Try adjusting your filter settings.")
        
        # Show helpful suggestions
        st.write("**💡 Suggestions:**")
        st.write("• Enable 'Show Zero Stock Items' to see all products")
        st.write("• Disable 'Show Only Items with Today's Activity' to see all stock")
        st.write("• Check if you have products in the selected category")
        st.write("• Add some stock or record transactions to see data")

def export_daily_report():
    """Export today's stock report in clean format without emojis"""
    today = datetime.date.today()
    today_transactions = get_today_transactions()
    opening_stock = calculate_opening_stock()
    
    report_data = []
    
    for parent_id, parent_info in st.session_state.parent_items.items():
        current_stock = st.session_state.stock_data.get(parent_id, {})
        opening_data = opening_stock.get(parent_id, {})
        activity = calculate_activity_summary(parent_id, today_transactions)
        
        # Calculate total loose change
        opening_loose = opening_data.get("loose_stock", 0)
        current_loose = current_stock.get("loose_stock", 0)
        
        # Format function for changes (clean, no emojis)
        def format_export_change(value, unit=""):
            if value > 0:
                return f"+{value}{unit}"
            elif value < 0:
                return f"{value}{unit}"
            else:
                return "-"
        
        # Add parent header row (clean, no emojis)
        report_data.append({
            "Product/Variation": f"{parent_info['name'].upper()}",
            "Type/Weight": "",
            "ASIN": "",
            "Opening Stock": "",
            "Stock Inward": "",
            "Packing Activity": "",
            "FBA Sales": "",
            "Easy Ship Sales": "",
            "Other Changes": "",
            "Closing Stock": ""
        })
        
        # Add loose stock row (clean format)
        report_data.append({
            "Product/Variation": "|- Loose Stock",
            "Type/Weight": "kg",
            "ASIN": "",
            "Opening Stock": f"{opening_loose:.1f}",
            "Stock Inward": format_export_change(activity["stock_inward"], "kg") if activity["stock_inward"] != 0 else "-",
            "Packing Activity": format_export_change(-activity["packing_out"], "kg") if activity["packing_out"] != 0 else "-",
            "FBA Sales": "-",
            "Easy Ship Sales": "-", 
            "Other Changes": format_export_change(activity["other_changes"], "kg") if activity["other_changes"] != 0 else "-",
            "Closing Stock": f"{current_loose:.1f}kg"
        })
        
        # Add ALL packed stock variations (clean format)
        if parent_id in st.session_state.packet_variations:
            variations = st.session_state.packet_variations[parent_id]
            packed_stock = current_stock.get("packed_stock", {})
            opening_packed = opening_data.get("packed_stock", {})
            
            variation_list = list(variations.items())
            for i, (asin, variation_info) in enumerate(variation_list):
                current_units = packed_stock.get(asin, 0)
                opening_units = opening_packed.get(asin, 0)
                
                weight = variation_info.get("weight", 0)
                description = variation_info.get("description", "")
                
                # Clean up description (same logic as Live Stock View)
                if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                    parent_name = st.session_state.parent_items[parent_id]["name"]
                    clean_description = f"{weight}kg {parent_name}"
                else:
                    clean_description = description
                
                # Determine prefix (clean ASCII characters)
                is_last = (i == len(variation_list) - 1)
                prefix = "\\-" if is_last else "|-"
                
                report_data.append({
                    "Product/Variation": f"{prefix} {clean_description}",
                    "Type/Weight": f"{weight}kg",
                    "ASIN": asin,
                    "Opening Stock": f"{opening_units}",
                    "Stock Inward": "-",
                    "Packing Activity": format_export_change(activity["packing_in"].get(asin, 0)) if activity["packing_in"].get(asin, 0) != 0 else "-",
                    "FBA Sales": format_export_change(-activity["fba_sales"].get(asin, 0)) if activity["fba_sales"].get(asin, 0) != 0 else "-",
                    "Easy Ship Sales": format_export_change(-activity["easy_ship_sales"].get(asin, 0)) if activity["easy_ship_sales"].get(asin, 0) != 0 else "-",
                    "Other Changes": "-",
                    "Closing Stock": f"{current_units} units"
                })
    
    # Create DataFrame
    df_report = pd.DataFrame(report_data)
    
    # Convert to CSV with proper encoding
    csv_content = df_report.to_csv(index=False, encoding='utf-8-sig')
    
    st.download_button(
        label="📥 Download Daily Stock Report",
        data=csv_content,
        file_name=f"daily_stock_report_{today.isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
        help="Download daily stock report in clean Excel-compatible format"
    )

def main():
    st.title("Stock Tracker - Mithila Foods")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Live Stock View", "Stock Inward", "Packing Operations", "FBA Sales", "Easy Ship Sales", "Returns", "Products Management"]
    )
    
    if page == "Live Stock View":
        show_live_stock_view()
    elif page == "Stock Inward":
        show_stock_inward()
    elif page == "Packing Operations":
        show_packing_operations()
    elif page == "FBA Sales":
        show_fba_sales()
    elif page == "Easy Ship Sales":
        show_easy_ship_sales()
    elif page == "Returns":
        show_returns()
    elif page == "Products Management":
        show_products_management_protected()

def show_dashboard():
    """Display main dashboard"""
    st.header("Stock Dashboard")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    total_loose = sum(stock.get("loose_stock", 0) for stock in st.session_state.stock_data.values())
    total_packed_items = sum(sum(stock.get("packed_stock", {}).values()) for stock in st.session_state.stock_data.values())
    total_products = len(st.session_state.parent_items)
    total_asins = sum(len(variations) for variations in st.session_state.packet_variations.values())
    
    with col1:
        st.metric("Total Loose Stock", f"{total_loose:.2f} kg")
    with col2:
        st.metric("Total Packed Items", total_packed_items)
    with col3:
        st.metric("Product Categories", total_products)
    with col4:
        st.metric("Total ASINs", total_asins)
    
    # Current Stock Overview
    st.subheader("Current Stock Overview")
    
    if st.session_state.stock_data:
        stock_overview = []
        for parent_id, stock in st.session_state.stock_data.items():
            total_packed_weight = 0
            total_packed_units = 0
            
            for asin, units in stock.get("packed_stock", {}).items():
                if asin in st.session_state.packet_variations.get(parent_id, {}):
                    weight_per_unit = st.session_state.packet_variations[parent_id][asin]["weight"]
                    total_packed_weight += units * weight_per_unit
                    total_packed_units += units
            
            stock_overview.append({
                "Product": st.session_state.parent_items[parent_id]["name"],
                "Category": st.session_state.parent_items[parent_id].get("category", "General"),
                "Loose Stock (kg)": stock.get("loose_stock", 0),
                "Packed Units": total_packed_units,
                "Packed Weight (kg)": total_packed_weight,
                "Total Stock (kg)": stock.get("loose_stock", 0) + total_packed_weight
            })
        
        df_stock = pd.DataFrame(stock_overview)
        st.dataframe(df_stock, use_container_width=True)
    
    # Add Recent Transactions Panel with Undo functionality
    st.markdown("---")  # Separator line
    show_recent_transactions_panel()

def show_recent_transactions_panel():
    """Show recent transactions with batch grouping and undo options"""
    st.subheader("📋 Recent Transactions (Today)")
    
    recent_transactions = get_recent_transactions(limit=10)
    
    if not recent_transactions:
        st.info("No transactions recorded today")
        return
    
    # Group transactions by batch_id
    batches = {}
    individual_transactions = []
    
    for transaction in recent_transactions:
        batch_id = transaction.get("batch_id")
        if batch_id:
            if batch_id not in batches:
                batches[batch_id] = []
            batches[batch_id].append(transaction)
        else:
            individual_transactions.append(transaction)
    
    # Display batches first
    for batch_id, batch_transactions in batches.items():
        batch_type = batch_transactions[0].get("type", "Unknown")
        batch_size = len(batch_transactions)
        batch_time = datetime.datetime.fromisoformat(batch_transactions[0]["timestamp"]).strftime("%H:%M")
        
        # Create batch summary
        product_summary = {}
        for t in batch_transactions:
            parent_name = t["parent_name"]
            quantity = t.get("quantity", 0)
            if parent_name not in product_summary:
                product_summary[parent_name] = 0
            product_summary[parent_name] += quantity
        
        summary_text = ", ".join([f"{qty} x {name}" for name, qty in product_summary.items()])
        
        with st.expander(f"📦 {batch_time} - {batch_type} ({batch_size} transactions)", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Batch ID:** `{batch_id}`")
                st.write(f"**Products:** {summary_text}")
                st.write(f"**Total Transactions:** {batch_size}")
            
            with col2:
                can_undo, reason = can_undo_batch(batch_id)
                if can_undo:
                    if st.button("🔄 Undo Batch", key=f"undo_batch_{batch_id}"):
                        if undo_batch(batch_id):
                            st.rerun()
                else:
                    st.button("🔄 Undo Batch", key=f"undo_batch_disabled_{batch_id}", 
                             disabled=True, help=reason)
    
    # Display individual transactions
    for transaction in individual_transactions:
        trans_time = datetime.datetime.fromisoformat(transaction["timestamp"]).strftime("%H:%M")
        trans_summary = f"{trans_time} - {transaction['type']} - {transaction['parent_name']}"
        
        if transaction.get("asin"):
            trans_summary += f" ({transaction['asin']})"
        
        if transaction.get("weight", 0) > 0:
            trans_summary += f" - {transaction['weight']}kg"
        if transaction.get("quantity", 0) > 0:
            trans_summary += f" - {transaction['quantity']} units"
        
        with st.expander(trans_summary, expanded=False):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**Type:** {transaction['type']}")
                st.write(f"**Product:** {transaction['parent_name']}")
                if transaction.get("asin"):
                    st.write(f"**ASIN:** {transaction['asin']}")
                if transaction.get("notes"):
                    st.write(f"**Notes:** {transaction['notes']}")
            
            with col2:
                if transaction.get("weight", 0) > 0:
                    st.metric("Weight", f"{transaction['weight']} kg")
                if transaction.get("quantity", 0) > 0:
                    st.metric("Quantity", f"{transaction['quantity']} units")
            
            with col3:
                can_undo, reason = can_undo_transaction(transaction["id"])
                if can_undo:
                    if st.button("🔄 Undo", key=f"panel_undo_{transaction['id']}", 
                               help="Undo this transaction"):
                        if undo_transaction(transaction["id"]):
                            st.rerun()
                else:
                    st.button("🔄 Undo", key=f"panel_undo_disabled_{transaction['id']}", 
                            disabled=True, help=reason)

def show_stock_inward():
    """Stock inward entry"""
    st.header("Stock Inward")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Add New Stock")
        
        with st.form("stock_inward_form"):
            parent_id = st.selectbox(
                "Select Product",
                options=list(st.session_state.parent_items.keys()),
                format_func=lambda x: st.session_state.parent_items[x]["name"]
            )
            
            weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1, format="%.2f")
            notes = st.text_area("Notes (optional)")
            
            submitted = st.form_submit_button("Add Stock")
            
            if submitted and weight > 0:
                if parent_id not in st.session_state.stock_data:
                    st.session_state.stock_data[parent_id] = {"loose_stock": 0, "packed_stock": {}}
                
                # Store original stock before adding
                original_stock = st.session_state.stock_data[parent_id]["loose_stock"]
                
                st.session_state.stock_data[parent_id]["loose_stock"] += weight
                st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
                
                transaction_id = record_transaction("Stock Inward", parent_id, weight=weight, notes=notes)
                
                # Store transaction details for undo outside form
                st.session_state.last_transaction = {
                    "id": transaction_id,
                    "summary": f"{weight} kg of {st.session_state.parent_items[parent_id]['name']} to loose stock",
                    "show_undo": True,
                    "original_stock": original_stock,
                    "new_stock": st.session_state.stock_data[parent_id]["loose_stock"]
                }
                # Don't call st.rerun() immediately - let the undo show first
    
    # Show immediate undo outside the form - SIMPLIFIED VERSION
    if hasattr(st.session_state, 'last_transaction') and st.session_state.last_transaction.get('show_undo'):
        st.markdown("---")
        transaction_info = st.session_state.last_transaction
        
        st.success(f"✅ Stock added successfully!")
        st.write(f"**Added:** {transaction_info['summary']}")
        
        # Show current stock levels for verification
        parent_id = list(st.session_state.parent_items.keys())[0]  # Get first product for testing
        current_stock = st.session_state.stock_data.get(parent_id, {}).get('loose_stock', 0)
        st.write(f"**Current loose stock:** {current_stock} kg")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Undo Last Entry", key="undo_last_stock"):
                success = undo_transaction(transaction_info['id'])
                if success:
                    st.session_state.last_transaction['show_undo'] = False
                    st.rerun()
                else:
                    st.error("❌ Undo failed!")
        
        with col2:
            if st.button("✅ Keep Entry", key="keep_entry"):
                st.session_state.last_transaction['show_undo'] = False
                st.rerun()
    
    with col2:
        st.subheader("Current Loose Stock")
        if st.session_state.stock_data:
            loose_stock_data = []
            for parent_id, stock in st.session_state.stock_data.items():
                loose_stock_data.append({
                    "Product": st.session_state.parent_items[parent_id]["name"],
                    "Stock (kg)": stock.get("loose_stock", 0)
                })
            
            df_loose = pd.DataFrame(loose_stock_data)
            st.dataframe(df_loose, use_container_width=True)

def show_packing_operations():
    """Packing operations"""
    st.header("Packing Operations")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Pack Products")
        
        # Product selection outside form for dynamic updates
        parent_id = st.selectbox(
            "Select Product to Pack",
            options=list(st.session_state.parent_items.keys()),
            format_func=lambda x: st.session_state.parent_items[x]["name"],
            key="pack_parent_select"
        )
        
        if parent_id and parent_id in st.session_state.packet_variations:
            def format_packet_option(asin_key):
                details = st.session_state.packet_variations[parent_id][asin_key]
                weight = details.get('weight', 1.0)
                description = details.get('description', '')
                
                # Clean up description - remove 'nan' and empty values
                if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                    parent_name = st.session_state.parent_items[parent_id]["name"]
                    description = f"{weight}kg {parent_name}"
                
                return f"{description} ({weight}kg)"
            
            # ASIN selection outside form for dynamic updates
            asin = st.selectbox(
                "Select Packet Size",
                options=list(st.session_state.packet_variations[parent_id].keys()),
                format_func=format_packet_option,
                key="pack_asin_select"
            )
            
            if asin:
                packet_weight = st.session_state.packet_variations[parent_id][asin]["weight"]
                available_loose = st.session_state.stock_data.get(parent_id, {}).get("loose_stock", 0)
                max_packets = int(available_loose / packet_weight) if packet_weight > 0 else 0
                
                # Dynamic info that updates with selection changes
                st.info(f"Available loose stock: {available_loose} kg")
                st.info(f"Each packet: {packet_weight} kg")
                st.info(f"Maximum packets possible: {max_packets}")
                
                # Only the packing action inside the form
                with st.form("packing_form"):
                    packets_to_pack = st.number_input(
                        "Number of packets to pack",
                        min_value=0,
                        max_value=max_packets,
                        step=1
                    )
                    
                    notes = st.text_area("Notes (optional)")
                    
                    submitted = st.form_submit_button("Pack Products")
                    
                    if submitted and packets_to_pack > 0:
                        total_weight_used = packets_to_pack * packet_weight
                        
                        st.session_state.stock_data[parent_id]["loose_stock"] -= total_weight_used
                        
                        if asin not in st.session_state.stock_data[parent_id]["packed_stock"]:
                            st.session_state.stock_data[parent_id]["packed_stock"][asin] = 0
                        st.session_state.stock_data[parent_id]["packed_stock"][asin] += packets_to_pack
                        
                        st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
                        
                        transaction_id = record_transaction("Packing", parent_id, asin, packets_to_pack, total_weight_used, notes)
                        
                        # Store transaction details for undo outside form
                        description = get_clean_product_description(parent_id, asin)
                        
                        st.session_state.last_transaction = {
                            "id": transaction_id,
                            "summary": f"Packed {packets_to_pack} packets of {description} using {total_weight_used} kg",
                            "show_undo": True
                        }
                        # Don't call st.rerun() immediately - let the undo show first
            
            # Show immediate undo outside the form - SIMPLIFIED VERSION
            if hasattr(st.session_state, 'last_transaction') and st.session_state.last_transaction.get('show_undo'):
                st.markdown("---")
                transaction_info = st.session_state.last_transaction
                
                st.success(f"✅ Packing completed successfully!")
                st.write(f"**Operation:** {transaction_info['summary']}")
                
                # Show current stock levels for verification
                current_loose = st.session_state.stock_data.get(parent_id, {}).get('loose_stock', 0)
                current_packed = st.session_state.stock_data.get(parent_id, {}).get('packed_stock', {}).get(asin, 0)
                st.write(f"**Current loose stock:** {current_loose} kg")
                st.write(f"**Current packed units:** {current_packed}")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🔄 Undo Packing", key="undo_last_packing"):
                        success = undo_transaction(transaction_info['id'])
                        if success:
                            st.session_state.last_transaction['show_undo'] = False
                            st.rerun()
                        else:
                            st.error("❌ Undo failed!")
                
                with col2:
                    if st.button("✅ Keep Packing", key="keep_packing"):
                        st.session_state.last_transaction['show_undo'] = False
                        st.rerun()
            else:
                st.info("Please select a packet size to see packing options")
        else:
            st.warning("No packet variations defined for this product.")
    
    with col2:
        st.subheader("Packed Stock Summary")
        if st.session_state.stock_data:
            packed_summary = []
            for parent_id, stock in st.session_state.stock_data.items():
                for asin, units in stock.get("packed_stock", {}).items():
                    if units > 0 and asin in st.session_state.packet_variations.get(parent_id, {}):
                        packed_summary.append({
                            "Product": st.session_state.parent_items[parent_id]["name"],
                            "ASIN": asin,
                            "Description": st.session_state.packet_variations[parent_id][asin]["description"],
                            "Units": units,
                            "Weight per Unit": st.session_state.packet_variations[parent_id][asin]["weight"],
                            "Total Weight": units * st.session_state.packet_variations[parent_id][asin]["weight"]
                        })
            
            if packed_summary:
                df_packed = pd.DataFrame(packed_summary)
                st.dataframe(df_packed, use_container_width=True)
            else:
                st.info("No packed stock available.")

def show_fba_sales():
    """FBA Sales entry with improved user experience"""
    st.header("FBA Sales")
    
    tab1, tab2 = st.tabs(["📝 Manual Entry", "📁 Bulk Upload"])
    
    with tab1:
        st.subheader("Record FBA Sale")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Product selection outside form for dynamic updates
            parent_id = st.selectbox(
                "Select Product",
                options=list(st.session_state.parent_items.keys()),
                format_func=lambda x: st.session_state.parent_items[x]["name"],
                key="fba_parent_select"
            )
            
            if parent_id and parent_id in st.session_state.packet_variations:
                def format_product_option(asin_key):
                    details = st.session_state.packet_variations[parent_id][asin_key]
                    weight = details.get('weight', 1.0)
                    description = details.get('description', '')
                    
                    # Clean up description
                    if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                        parent_name = st.session_state.parent_items[parent_id]["name"]
                        description = f"{weight}kg {parent_name}"
                    
                    return f"{description} ({weight}kg)"
                
                # Weight variation selection
                asin = st.selectbox(
                    "Select Weight Variation",
                    options=list(st.session_state.packet_variations[parent_id].keys()),
                    format_func=format_product_option,
                    key="fba_asin_select"
                )
                
                if asin:
                    # Get current stock and product details
                    available_units = st.session_state.stock_data.get(parent_id, {}).get("packed_stock", {}).get(asin, 0)
                    product_details = st.session_state.packet_variations[parent_id][asin]
                    weight = product_details.get('weight', 1.0)
                    mrp = product_details.get('mrp', 0)
                    
                    # Dynamic info display
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.info(f"📦 Available Units: **{available_units}**")
                        st.info(f"⚖️ Weight per Unit: **{weight} kg**")
                    with col_info2:
                        st.info(f"💰 MRP per Unit: **₹{mrp}**")
                        if available_units > 0:
                            st.info(f"💎 Total Stock Value: **₹{available_units * mrp:,.0f}**")
                    
                    # Sales form
                    with st.form("fba_sale_form"):
                        col_sale1, col_sale2 = st.columns(2)
                        
                        with col_sale1:
                            quantity_sold = st.number_input(
                                "Units Sold",
                                min_value=1,
                                max_value=available_units if available_units > 0 else 1,
                                step=1,
                                help=f"Maximum available: {available_units} units"
                            )
                            
                            sale_date = st.date_input(
                                "Sale Date", 
                                value=datetime.date.today(),
                                help="Date when the sale occurred"
                            )
                        
                        with col_sale2:
                            order_id = st.text_input(
                                "Order ID (Optional)",
                                placeholder="AMZ-123456789",
                                help="Amazon order reference"
                            )
                            
                            selling_price = st.number_input(
                                "Selling Price per Unit (Optional)",
                                min_value=0.0,
                                value=float(mrp) if mrp > 0 else 0.0,
                                step=1.0,
                                format="%.2f",
                                help="Actual selling price (defaults to MRP)"
                            )
                        
                        notes = st.text_area(
                            "Notes (Optional)",
                            placeholder="Any additional information about this sale..."
                        )
                        
                        # Sale summary
                        if quantity_sold > 0:
                            total_weight = quantity_sold * weight
                            total_value = quantity_sold * selling_price
                            
                            st.write("**📋 Sale Summary:**")
                            summary_col1, summary_col2, summary_col3 = st.columns(3)
                            with summary_col1:
                                st.metric("Units", quantity_sold)
                            with summary_col2:
                                st.metric("Total Weight", f"{total_weight} kg")
                            with summary_col3:
                                st.metric("Total Value", f"₹{total_value:,.0f}")
                        
                        # Submit button
                        submitted = st.form_submit_button("🚚 Record FBA Sale", type="primary", use_container_width=True)
                        
                        if submitted:
                            if available_units >= quantity_sold:
                                # Update stock
                                st.session_state.stock_data[parent_id]["packed_stock"][asin] -= quantity_sold
                                st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
                                
                                # Prepare transaction notes
                                transaction_notes = f"FBA Sale"
                                if order_id:
                                    transaction_notes += f" | Order: {order_id}"
                                if selling_price != mrp:
                                    transaction_notes += f" | Price: ₹{selling_price}/unit"
                                if notes:
                                    transaction_notes += f" | {notes}"
                                
                                # Record transaction
                                weight_sold = quantity_sold * weight
                                transaction_id = record_transaction(
                                    transaction_type="FBA Sale", 
                                    parent_id=parent_id, 
                                    asin=asin, 
                                    quantity=quantity_sold, 
                                    weight=weight_sold, 
                                    notes=transaction_notes, 
                                    batch_id=None, 
                                    transaction_date=sale_date
                                )
                                
                                # Store transaction details for undo outside form
                                st.session_state.last_transaction = {
                                    "id": transaction_id,
                                    "summary": f"FBA sale: {quantity_sold} units of {format_product_option(asin)}",
                                    "show_undo": True
                                }
                                st.balloons()
                                # Don't call st.rerun() immediately - let the undo show first
                            else:
                                st.error(f"❌ Insufficient stock! Available: {available_units}, Requested: {quantity_sold}")
                else:
                    st.info("Please select a weight variation to continue")
            else:
                st.warning("No weight variations available for this product. Please add product variations first.")
        
        # Show immediate undo outside the form - SIMPLIFIED VERSION
        if hasattr(st.session_state, 'last_transaction') and st.session_state.last_transaction.get('show_undo'):
            st.markdown("---")
            transaction_info = st.session_state.last_transaction
            
            st.success(f"✅ FBA sale recorded successfully!")
            st.write(f"**Sale:** {transaction_info['summary']}")
            
            # Show current stock for verification (get the product info from recent transaction)
            if st.session_state.transactions:
                last_trans = st.session_state.transactions[-1]
                parent_id = last_trans.get('parent_id')
                asin = last_trans.get('asin')
                if parent_id and asin:
                    current_packed = st.session_state.stock_data.get(parent_id, {}).get('packed_stock', {}).get(asin, 0)
                    st.write(f"**Current stock for {asin}:** {current_packed} units")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔄 Undo Sale", key="undo_last_fba_sale_app"):
                    success = undo_transaction(transaction_info['id'])
                    if success:
                        st.session_state.last_transaction['show_undo'] = False
                        st.rerun()
                    else:
                        st.error("❌ Undo failed!")
            
            with col2:
                if st.button("✅ Keep Sale", key="keep_fba_sale_app"):
                    st.session_state.last_transaction['show_undo'] = False
                    st.rerun()
        
        with col2:
            st.subheader("📈 Recent FBA Sales")
            fba_transactions = [t for t in st.session_state.transactions if "FBA Sale" in t.get("type", "")]
            if fba_transactions:
                recent_fba = pd.DataFrame(fba_transactions[-5:])
                recent_fba = recent_fba.sort_values('timestamp', ascending=False)
                
                for _, sale in recent_fba.iterrows():
                    with st.container():
                        st.write(f"**{sale['parent_name']}**")
                        st.write(f"🗓️ {sale['date']} | 📦 {sale['quantity']} units | ⚖️ {sale['weight']} kg")
                        if sale.get('notes'):
                            st.caption(sale['notes'])
                        st.divider()
            else:
                st.info("No recent FBA sales")
    
    with tab2:
        st.subheader("📁 Bulk Upload FBA Sales")
        st.info("📋 Upload your FBA sales Excel file. Review the data carefully before confirming.")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose your FBA Sales Excel file", 
            type=['xlsx', 'xls'],
            help="Excel file should contain 'ASIN' and 'Shipped' columns",
            key="fba_file_uploader"
        )
        
        if uploaded_file is not None:
            try:
                # Read the Excel file
                df = pd.read_excel(uploaded_file)
                
                # Check required columns
                required_cols = ['ASIN', 'Shipped']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"❌ Missing required columns: {missing_cols}")
                    st.write("**Available columns:** ", list(df.columns))
                else:
                    # Filter and prepare data for review
                    sales_data = df[df['Shipped'] > 0].copy()
                    
                    if len(sales_data) == 0:
                        st.warning("⚠️ No sales data found (no rows with Shipped > 0)")
                        return
                    
                    # Enrich data with product information for better review
                    enriched_data = []
                    
                    for _, row in sales_data.iterrows():
                        asin = str(row['ASIN']).strip()
                        shipped_qty = int(row['Shipped'])
                        
                        # Get product info
                        parent_id = None
                        product_name = "Unknown Product"
                        weight = "Unknown"
                        current_stock = "Unknown"
                        
                        # Find parent_id for this ASIN
                        for pid, variations in st.session_state.packet_variations.items():
                            if asin in variations:
                                parent_id = pid
                                variation_info = variations[asin]
                                weight = f"{variation_info.get('weight', 0)}kg"
                                
                                # Get product name
                                description = variation_info.get('description', '')
                                if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                                    parent_name = st.session_state.parent_items.get(pid, {}).get('name', 'Unknown')
                                    product_name = f"{weight} {parent_name}"
                                else:
                                    product_name = description
                                
                                # Get current stock
                                current_stock = st.session_state.stock_data.get(pid, {}).get("packed_stock", {}).get(asin, 0)
                                break
                        
                        # Additional columns from Excel
                        merchant_sku = str(row.get('Merchant SKU', '')).strip() if 'Merchant SKU' in row else ''
                        fnsku = str(row.get('FNSKU', '')).strip() if 'FNSKU' in row else ''
                        
                        enriched_data.append({
                            'ASIN': asin,
                            'Product Name': product_name,
                            'Weight': weight,
                            'Current Stock': current_stock,
                            'Merchant SKU': merchant_sku,
                            'FNSKU': fnsku,
                            'Shipped Qty': shipped_qty,
                            'Status': 'Ready' if parent_id else 'Not Found',
                            'parent_id': parent_id  # Hidden field for processing
                        })
                    
                    # Create review dataframe
                    review_df = pd.DataFrame(enriched_data)
                    
                    # Show summary
                    st.subheader("📊 Upload Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Rows", len(sales_data))
                    with col2:
                        st.metric("Total Units", review_df['Shipped Qty'].sum())
                    with col3:
                        ready_count = len(review_df[review_df['Status'] == 'Ready'])
                        st.metric("Ready to Process", ready_count)
                    with col4:
                        not_found_count = len(review_df[review_df['Status'] == 'Not Found'])
                        st.metric("Products Not Found", not_found_count)
                    
                    # Show detailed review table
                    st.subheader("📋 Review Data Before Processing")
                    st.warning("⚠️ **Please review this data carefully before confirming. Once processed, you'll need to use manual corrections for any errors.**")
                    
                    # Display table without the hidden parent_id column
                    display_df = review_df.drop(columns=['parent_id'])
                    
                    # Apply styling to highlight issues
                    def highlight_issues(row):
                        if row['Status'] == 'Not Found':
                            return ['background-color: #ffebee'] * len(row)
                        elif row['Current Stock'] != 'Unknown' and isinstance(row['Current Stock'], (int, float)) and row['Current Stock'] < row['Shipped Qty']:
                            return ['background-color: #fff3e0'] * len(row)
                        else:
                            return [''] * len(row)
                    
                    # Show styled dataframe
                    styled_df = display_df.style.apply(highlight_issues, axis=1)
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    
                    # Legend for colors
                    st.write("**Legend:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("🔴 **Red Background**: Product not found in catalog")
                    with col2:
                        st.markdown("🟠 **Orange Background**: Insufficient stock")
                    
                    # Show issues summary
                    if not_found_count > 0:
                        st.error(f"❌ **{not_found_count} products not found** in your catalog. These will be skipped.")
                        not_found_asins = review_df[review_df['Status'] == 'Not Found']['ASIN'].tolist()
                        with st.expander("View products not found"):
                            for asin in not_found_asins:
                                st.write(f"• {asin}")
                    
                    # Check for insufficient stock
                    stock_issues = []
                    for _, row in review_df.iterrows():
                        if (row['Status'] == 'Ready' and 
                            isinstance(row['Current Stock'], (int, float)) and 
                            row['Current Stock'] < row['Shipped Qty']):
                            stock_issues.append({
                                'ASIN': row['ASIN'],
                                'Product': row['Product Name'],
                                'Available': row['Current Stock'],
                                'Requested': row['Shipped Qty']
                            })
                    
                    if stock_issues:
                        st.warning(f"⚠️ **{len(stock_issues)} products have insufficient stock**. These will result in errors.")
                        with st.expander("View stock issues"):
                            for issue in stock_issues:
                                st.write(f"• {issue['ASIN']} ({issue['Product']}): Available {issue['Available']}, Requested {issue['Requested']}")
                    
                    # Confirmation section
                    st.markdown("---")
                    st.subheader("🔍 Final Confirmation")
                    
                    # Show what will be processed
                    processable_count = len(review_df[review_df['Status'] == 'Ready'])
                    total_units = review_df[review_df['Status'] == 'Ready']['Shipped Qty'].sum()
                    
                    if processable_count > 0:
                        st.success(f"✅ Ready to process **{processable_count}** products with **{total_units}** total units")
                        
                        # Final confirmation checkbox
                        confirm_processing = st.checkbox(
                            "✅ I have reviewed the data above and confirm it is correct", 
                            key="confirm_fba_processing"
                        )
                        
                        if confirm_processing:
                            # Check if processing is in progress
                            processing_key = "fba_processing_in_progress"
                            is_processing = st.session_state.get(processing_key, False)
                            
                            if not is_processing:
                                # Show buttons only when not processing
                                col1, col2 = st.columns([1, 1])
                                
                                with col1:
                                    if st.button("🚀 Confirm & Process FBA Sales", type="primary", use_container_width=True):
                                        # Set processing flag and trigger rerun
                                        st.session_state[processing_key] = True
                                        st.rerun()
                                
                                with col2:
                                    if st.button("❌ Cancel", type="secondary", use_container_width=True):
                                        st.info("Processing cancelled. You can upload a different file or make corrections.")
                            else:
                                # Processing is in progress - process data directly without extra message
                                # Process the data
                                ready_rows = review_df[review_df['Status'] == 'Ready']
                                process_confirmed_fba_sales(ready_rows)
                                
                                # Clear processing flag and confirmation checkbox after completion
                                st.session_state[processing_key] = False
                                if "confirm_fba_processing" in st.session_state:
                                    del st.session_state["confirm_fba_processing"]
                        else:
                            st.info("👆 Please review the data and check the confirmation box to proceed.")
                    else:
                        st.error("❌ No products are ready to process. Please check your data and product catalog.")
                        
            except Exception as e:
                st.error(f"❌ Error reading Excel file: {str(e)}")
                st.write("Please ensure your file is a valid Excel format (.xlsx or .xls)")

def process_confirmed_fba_sales(ready_rows):
    """Process confirmed FBA sales data (simple version without undo complexity)"""
    import datetime
    
    st.write("🔄 **Processing confirmed FBA sales...**")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Generate batch ID for this upload
    batch_id = f"FBA_CONFIRMED_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    
    success_count = 0
    error_count = 0
    success_details = []
    error_details = []
    
    total_rows = len(ready_rows)
    
    for index, row in ready_rows.iterrows():
        try:
            # Update progress
            progress = (index + 1) / total_rows
            progress_bar.progress(progress)
            status_text.text(f"Processing: {row['Product Name']}")
            
            asin = row['ASIN']
            parent_id = row['parent_id']
            quantity = row['Shipped Qty']
            
            # Check stock availability (final check)
            available_stock = st.session_state.stock_data.get(parent_id, {}).get("packed_stock", {}).get(asin, 0)
            
            if available_stock >= quantity:
                # Update stock
                st.session_state.stock_data[parent_id]["packed_stock"][asin] -= quantity
                st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
                
                # Record transaction
                weight_sold = quantity * st.session_state.packet_variations[parent_id][asin]["weight"]
                notes = f"FBA Sale - Bulk Upload"
                if row['Merchant SKU']:
                    notes += f" | SKU: {row['Merchant SKU']}"
                
                transaction_id = record_transaction(
                    transaction_type="FBA Sale", 
                    parent_id=parent_id, 
                    asin=asin, 
                    quantity=quantity, 
                    weight=weight_sold, 
                    notes=notes
                )
                
                success_count += 1
                success_details.append({
                    "ASIN": asin,
                    "Product": row['Product Name'],
                    "Quantity": quantity,
                    "Stock Before": available_stock,
                    "Stock After": available_stock - quantity
                })
                
            else:
                error_count += 1
                error_details.append({
                    "ASIN": asin,
                    "Product": row['Product Name'],
                    "Issue": "Insufficient Stock",
                    "Available": available_stock,
                    "Requested": quantity
                })
                
        except Exception as e:
            error_count += 1
            error_details.append({
                "ASIN": row.get('ASIN', 'Unknown'),
                "Product": row.get('Product Name', 'Unknown'),
                "Issue": f"Processing Error: {str(e)}",
                "Available": "N/A",
                "Requested": row.get('Shipped Qty', 0)
            })
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Show results
    st.success(f"✅ **FBA Processing Complete!**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅ Successful", success_count)
    with col2:
        st.metric("❌ Errors", error_count)
    
    # Show successful transactions
    if success_details:
        st.subheader("✅ Successfully Processed")
        success_df = pd.DataFrame(success_details)
        st.dataframe(success_df, use_container_width=True, hide_index=True)
    
    # Show errors
    if error_details:
        st.subheader("❌ Processing Errors")
        error_df = pd.DataFrame(error_details)
        st.dataframe(error_df, use_container_width=True, hide_index=True)
    
    # Success celebration
    if success_count > 0:
        st.balloons()
        st.info("💡 **Stock levels updated successfully!** Check Live Stock View for current inventory.")
    
    # Next steps
    st.markdown("---")
    st.subheader("📋 Next Steps")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📊 View Updated Stock:**")
        st.write("• Go to Live Stock View")
        st.write("• Check Dashboard for overview")
        
    with col2:
        st.write("**🔄 For Any Corrections:**")
        st.write("• Use Manual Entry for individual sales")
        st.write("• Check Products Management if ASINs missing")

def process_fba_sales_excel(df, batch_id_override=None):
    """Process the uploaded FBA sales Excel file with improved status reporting and undo functionality"""
    import datetime
    
    processed_transactions = []
    success_details = []
    errors = []
    warnings = []
    
    # Filter only rows with sales (Shipped > 0)
    sales_data = df[df['Shipped'] > 0].copy()
    
    st.write(f"🔄 Processing {len(sales_data)} rows with sales data...")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Generate batch ID for this upload (use override if provided)
    if batch_id_override:
        batch_id = batch_id_override
    else:
        batch_id = f"BULK_FBA_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    
    def get_product_display_name(asin, parent_id):
        """Get user-friendly product name with weight"""
        if parent_id and parent_id in st.session_state.packet_variations:
            if asin in st.session_state.packet_variations[parent_id]:
                variation = st.session_state.packet_variations[parent_id][asin]
                weight = variation.get('weight', 0)
                description = variation.get('description', '')
                parent_name = st.session_state.parent_items.get(parent_id, {}).get('name', 'Unknown Product')
                
                # Clean up description
                if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                    description = f"{weight}kg {parent_name}"
                
                return f"{description} ({weight}kg)"
        return f"Unknown Product (ASIN: {asin})"
    
    for index, row in sales_data.iterrows():
        try:
            asin = str(row['ASIN']).strip()
            quantity = int(row['Shipped'])
            
            # Additional info from Excel
            merchant_sku = str(row.get('Merchant SKU', '')).strip() if 'Merchant SKU' in row else ''
            title = str(row.get('Title', '')).strip() if 'Title' in row else ''
            
            # Update progress
            progress = (index + 1) / len(sales_data)
            progress_bar.progress(progress)
            status_text.text(f"Processing ASIN: {asin}")
            
            # Find parent_id for this ASIN
            parent_id = None
            for pid, variations in st.session_state.packet_variations.items():
                if asin in variations:
                    parent_id = pid
                    break
            
            # Get user-friendly product name
            product_display = get_product_display_name(asin, parent_id)
            
            if not parent_id:
                warnings.append({
                    "type": "Product Not Found",
                    "asin": asin,
                    "product": product_display,
                    "message": f"ASIN {asin} not found in your product catalog",
                    "details": f"SKU: {merchant_sku}" if merchant_sku else "No SKU provided",
                    "quantity": quantity
                })
                continue
            
            if quantity <= 0:
                warnings.append({
                    "type": "Invalid Quantity",
                    "asin": asin,
                    "product": product_display,
                    "message": f"Invalid quantity: {quantity}",
                    "details": "Quantity must be greater than 0",
                    "quantity": quantity
                })
                continue
            
            # Check stock availability
            available_stock = st.session_state.stock_data.get(parent_id, {}).get("packed_stock", {}).get(asin, 0)
            
            if available_stock >= quantity:
                # Update stock
                st.session_state.stock_data[parent_id]["packed_stock"][asin] -= quantity
                st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
                
                # Record transaction
                weight_sold = quantity * st.session_state.packet_variations[parent_id][asin]["weight"]
                notes = f"FBA Bulk upload"
                if merchant_sku:
                    notes += f" | SKU: {merchant_sku}"
                if title:
                    notes += f" | Title: {title[:50]}"
                
                transaction_id = record_transaction(
                    transaction_type="FBA Sale (Bulk)", 
                    parent_id=parent_id, 
                    asin=asin, 
                    quantity=quantity, 
                    weight=weight_sold, 
                    notes=notes,
                    batch_id=batch_id
                )
                
                # Track successful transaction
                processed_transactions.append(transaction_id)
                success_details.append({
                    "asin": asin,
                    "product": product_display,
                    "quantity": quantity,
                    "weight": weight_sold,
                    "stock_before": available_stock,
                    "stock_after": available_stock - quantity,
                    "sku": merchant_sku
                })
                
            else:
                errors.append({
                    "type": "Insufficient Stock",
                    "asin": asin,
                    "product": product_display,
                    "message": f"Insufficient stock",
                    "details": f"Available: {available_stock}, Requested: {quantity}",
                    "quantity": quantity,
                    "available": available_stock
                })
                
        except Exception as e:
            errors.append({
                "type": "Processing Error",
                "asin": asin if 'asin' in locals() else "Unknown",
                "product": "Unknown Product",
                "message": f"Error processing row {index + 1}",
                "details": str(e),
                "quantity": 0
            })
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Show detailed results
    show_fba_processing_results(
        success_details=success_details,
        errors=errors,
        warnings=warnings,
        batch_id=batch_id,
        processed_count=len(processed_transactions)
    )

def show_fba_processing_results(success_details, errors, warnings, batch_id, processed_count):
    """Display detailed processing results with undo option"""
    
    # Check if this batch has already been undone
    batch_exists = any(t.get("batch_id") == batch_id for t in st.session_state.transactions)
    
    # Summary metrics
    st.success(f"✅ **FBA Bulk Processing Complete!**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Successful", processed_count, delta=None)
    with col2:
        st.metric("⚠️ Warnings", len(warnings), delta=None)
    with col3:
        st.metric("❌ Errors", len(errors), delta=None)
    
    # Undo option for successful transactions (only if batch still exists)
    if processed_count > 0:
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**📦 Batch ID:** `{batch_id}`")
            st.write(f"**🕒 Processed:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"**📊 Total Transactions:** {processed_count}")
            
            if not batch_exists:
                st.warning("⚠️ **This batch has already been undone**")
        
        with col2:
            if batch_exists:
                can_undo, reason = can_undo_batch(batch_id)
                if can_undo:
                    # Create a unique key for this batch undo button
                    undo_key = f"undo_batch_{batch_id}_{processed_count}"
                    
                    if st.button("🔄 Undo Entire Batch", type="secondary", use_container_width=True, 
                               help="Undo all transactions from this upload", key=undo_key):
                        st.write("🔄 **Processing undo request...**")
                        
                        # Prevent multiple undos by setting a flag
                        undo_flag_key = f"undoing_{batch_id}"
                        if undo_flag_key not in st.session_state:
                            st.session_state[undo_flag_key] = True
                            
                            if undo_batch(batch_id):
                                st.success("✅ Batch undone successfully!")
                                # Track that this batch was undone
                                if 'undone_batches' not in st.session_state:
                                    st.session_state.undone_batches = set()
                                st.session_state.undone_batches.add(batch_id)
                                
                                # Remove the processing flag
                                del st.session_state[undo_flag_key]
                                st.rerun()
                            else:
                                st.error("❌ Failed to undo batch")
                                del st.session_state[undo_flag_key]
                        else:
                            st.warning("⚠️ Undo already in progress...")
                else:
                    st.button("🔄 Undo Entire Batch", disabled=True, help=reason, use_container_width=True)
            else:
                st.button("🔄 Undo Entire Batch", disabled=True, help="Batch already undone", use_container_width=True)
    
    # Detailed success results
    if success_details:
        st.subheader("✅ Successfully Processed Sales")
        
        success_df = pd.DataFrame([
            {
                "Product": detail["product"],
                "ASIN": detail["asin"],
                "Quantity Sold": detail["quantity"],
                "Weight (kg)": detail["weight"],
                "Stock Before": detail["stock_before"],
                "Stock After": detail["stock_after"],
                "SKU": detail["sku"] if detail["sku"] else "N/A"
            }
            for detail in success_details
        ])
        
        st.dataframe(success_df, use_container_width=True, hide_index=True)
        
        # Export option
        csv_data = success_df.to_csv(index=False)
        st.download_button(
            label="📥 Export Successful Transactions",
            data=csv_data,
            file_name=f"fba_successful_transactions_{datetime.date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Detailed error results
    if errors:
        st.subheader("❌ Processing Errors")
        
        error_df = pd.DataFrame([
            {
                "Error Type": error["type"],
                "Product": error["product"],
                "ASIN": error["asin"],
                "Issue": error["message"],
                "Details": error["details"],
                "Requested Qty": error["quantity"],
                "Available Stock": error.get("available", "N/A")
            }
            for error in errors
        ])
        
        st.dataframe(error_df, use_container_width=True, hide_index=True)
        
        # Export option
        csv_data = error_df.to_csv(index=False)
        st.download_button(
            label="📥 Export Error Report",
            data=csv_data,
            file_name=f"fba_errors_{datetime.date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Detailed warning results
    if warnings:
        st.subheader("⚠️ Processing Warnings")
        
        warning_df = pd.DataFrame([
            {
                "Warning Type": warning["type"],
                "Product": warning["product"],
                "ASIN": warning["asin"],
                "Issue": warning["message"],
                "Details": warning["details"],
                "Quantity": warning["quantity"]
            }
            for warning in warnings
        ])
        
        st.dataframe(warning_df, use_container_width=True, hide_index=True)
        
        # Export option
        csv_data = warning_df.to_csv(index=False)
        st.download_button(
            label="📥 Export Warning Report",
            data=csv_data,
            file_name=f"fba_warnings_{datetime.date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Celebration for successful processing
    if processed_count > 0:
        st.balloons()
        st.info("💡 **Next Steps:** Check the Live Stock View to see updated inventory levels, or visit the Dashboard for an overview.")
    
    # Helpful tips
    if errors or warnings:
        st.markdown("---")
        st.subheader("💡 Troubleshooting Tips")
        
        if any(error["type"] == "Product Not Found" for error in errors + warnings):
            st.write("🔍 **Product Not Found:** Add missing ASINs in Products Management > ASIN Products")
        
        if any(error["type"] == "Insufficient Stock" for error in errors):
            st.write("📦 **Insufficient Stock:** Record stock inward or check current inventory levels")
        
        if any(error["type"] == "Invalid Quantity" for error in errors + warnings):
            st.write("📊 **Invalid Quantity:** Ensure all quantity values are positive numbers")

def process_confirmed_easy_ship_sales(ready_rows):
    """Process confirmed Easy Ship sales data (matching FBA style)"""
    import datetime
    
    st.write("🔄 **Processing confirmed Easy Ship sales...**")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Generate batch ID for this upload
    batch_id = f"EASY_SHIP_CONFIRMED_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    
    success_count = 0
    error_count = 0
    success_details = []
    error_details = []
    
    total_rows = len(ready_rows)
    
    for index, row in ready_rows.iterrows():
        try:
            # Update progress
            progress = (index + 1) / total_rows
            progress_bar.progress(progress)
            status_text.text(f"Processing: {row['Product Name']}")
            
            asin = row['ASIN']
            parent_id = row['parent_id']
            quantity = row['Quantity Purchased']
            
            # Check stock availability (final check)
            available_stock = st.session_state.stock_data.get(parent_id, {}).get("packed_stock", {}).get(asin, 0)
            
            if available_stock >= quantity:
                # Update stock
                st.session_state.stock_data[parent_id]["packed_stock"][asin] -= quantity
                st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
                
                # Record transaction
                weight_sold = quantity * st.session_state.packet_variations[parent_id][asin]["weight"]
                notes = f"Easy Ship Sale - Bulk Upload"
                if row['Order ID']:
                    notes += f" | Order: {row['Order ID']}"
                if row['SKU']:
                    notes += f" | SKU: {row['SKU']}"
                
                transaction_id = record_transaction(
                    transaction_type="Easy Ship Sale", 
                    parent_id=parent_id, 
                    asin=asin, 
                    quantity=quantity, 
                    weight=weight_sold, 
                    notes=notes,
                    batch_id=batch_id
                )
                
                success_count += 1
                success_details.append({
                    "ASIN": asin,
                    "Product": row['Product Name'],
                    "Quantity": quantity,
                    "Stock Before": available_stock,
                    "Stock After": available_stock - quantity,
                    "Order ID": row['Order ID'] if row['Order ID'] else "N/A",
                    "SKU": row['SKU'] if row['SKU'] else "N/A"
                })
                
            else:
                error_count += 1
                error_details.append({
                    "ASIN": asin,
                    "Product": row['Product Name'],
                    "Issue": "Insufficient Stock",
                    "Available": available_stock,
                    "Requested": quantity
                })
                
        except Exception as e:
            error_count += 1
            error_details.append({
                "ASIN": row.get('ASIN', 'Unknown'),
                "Product": row.get('Product Name', 'Unknown'),
                "Issue": f"Processing Error: {str(e)}",
                "Available": "N/A",
                "Requested": row.get('Quantity Purchased', 0)
            })
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Show results using the enhanced processing results function
    show_easy_ship_processing_results(
        success_details=success_details,
        error_details=error_details,
        batch_id=batch_id,
        processed_count=success_count
    )

def show_easy_ship_processing_results(success_details, error_details, batch_id, processed_count):
    """Display detailed Easy Ship processing results (matching FBA style but without undo)"""
    
    # Summary metrics
    st.success(f"✅ **Easy Ship Bulk Processing Complete!**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅ Successful", processed_count)
    with col2:
        st.metric("❌ Errors", len(error_details))
    
    # Show batch information (without undo option)
    if processed_count > 0:
        st.markdown("---")
        st.write(f"**📦 Batch ID:** `{batch_id}`")
        st.write(f"**🕒 Processed:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"**📊 Total Transactions:** {processed_count}")
    
    # Show successful transactions
    if success_details:
        st.subheader("✅ Successfully Processed Sales")
        success_df = pd.DataFrame(success_details)
        st.dataframe(success_df, use_container_width=True, hide_index=True)
    
    # Show errors
    if error_details:
        st.subheader("❌ Processing Errors")
        error_df = pd.DataFrame(error_details)
        st.dataframe(error_df, use_container_width=True, hide_index=True)
    
    # Success celebration
    if processed_count > 0:
        st.balloons()
        st.info("💡 **Stock levels updated successfully!** Check Live Stock View for current inventory.")
    
    # Next steps
    st.markdown("---")
    st.subheader("📋 Next Steps")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📊 View Updated Stock:**")
        st.write("• Go to Live Stock View")
        st.write("• Check Dashboard for overview")
        
    with col2:
        st.write("**🔄 For Any Corrections:**")
        st.write("• Use Manual Entry for individual sales")
        st.write("• Check Products Management if ASINs missing")


def display_recent_easy_ship_sales():
    """Helper function to display recent Easy Ship sales"""
    st.subheader("📈 Recent Easy Ship Sales")
    easy_ship_transactions = [t for t in st.session_state.transactions if "Easy Ship Sale" in t.get("type", "")]
    if easy_ship_transactions:
        recent_easy_ship = pd.DataFrame(easy_ship_transactions[-5:])
        recent_easy_ship = recent_easy_ship.sort_values('timestamp', ascending=False)
        
        for _, sale in recent_easy_ship.iterrows():
            with st.container():
                st.write(f"**{sale['parent_name']}**")
                st.write(f"🗓️ {sale['date']} | 📦 {sale['quantity']} units | ⚖️ {sale['weight']} kg")
                if sale.get('notes'):
                    st.caption(sale['notes'])
                st.divider()
    else:
        st.info("No recent Easy Ship sales")

def show_easy_ship_sales():
    """Easy Ship Sales entry with improved user experience"""
    st.header("Easy Ship Sales")
    
    tab1, tab2 = st.tabs(["📝 Manual Entry", "📁 Bulk Upload"])
    
    with tab1:
        st.subheader("Record Easy Ship Sale")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Product selection outside form for dynamic updates
            parent_id = st.selectbox(
                "Select Product",
                options=list(st.session_state.parent_items.keys()),
                format_func=lambda x: st.session_state.parent_items[x]["name"],
                key="easy_ship_parent_select"
            )
            
            if parent_id and parent_id in st.session_state.packet_variations:
                def format_product_option(asin_key):
                    details = st.session_state.packet_variations[parent_id][asin_key]
                    weight = details.get('weight', 1.0)
                    description = details.get('description', '')
                    
                    # Clean up description
                    if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                        parent_name = st.session_state.parent_items[parent_id]["name"]
                        description = f"{weight}kg {parent_name}"
                    
                    return f"{description} ({weight}kg)"
                
                # Weight variation selection
                asin = st.selectbox(
                    "Select Weight Variation",
                    options=list(st.session_state.packet_variations[parent_id].keys()),
                    format_func=format_product_option,
                    key="easy_ship_asin_select"
                )
                
                if asin:
                    # Get current stock and product details
                    available_units = st.session_state.stock_data.get(parent_id, {}).get("packed_stock", {}).get(asin, 0)
                    product_details = st.session_state.packet_variations[parent_id][asin]
                    weight = product_details.get('weight', 1.0)
                    mrp = product_details.get('mrp', 0)
                    
                    # Dynamic info display
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.info(f"📦 Available Units: **{available_units}**")
                        st.info(f"⚖️ Weight per Unit: **{weight} kg**")
                    with col_info2:
                        st.info(f"💰 MRP per Unit: **₹{mrp}**")
                        if available_units > 0:
                            st.info(f"💎 Total Stock Value: **₹{available_units * mrp:,.0f}**")
                    
                    # Sales form
                    with st.form("easy_ship_sale_form"):
                        col_sale1, col_sale2 = st.columns(2)
                        
                        with col_sale1:
                            quantity_sold = st.number_input(
                                "Units Sold",
                                min_value=1,
                                max_value=available_units if available_units > 0 else 1,
                                step=1,
                                help=f"Maximum available: {available_units} units"
                            )
                            
                            sale_date = st.date_input(
                                "Sale Date", 
                                value=datetime.date.today(),
                                help="Date when the sale occurred"
                            )
                        
                        with col_sale2:
                            order_id = st.text_input(
                                "Order ID (Optional)",
                                placeholder="ES-123456789",
                                help="Easy Ship order reference"
                            )
                            
                            selling_price = st.number_input(
                                "Selling Price per Unit (Optional)",
                                min_value=0.0,
                                value=float(mrp) if mrp > 0 else 0.0,
                                step=1.0,
                                format="%.2f",
                                help="Actual selling price (defaults to MRP)"
                            )
                        
                        notes = st.text_area(
                            "Notes (Optional)",
                            placeholder="Any additional information about this sale..."
                        )
                        
                        # Sale summary
                        if quantity_sold > 0:
                            total_weight = quantity_sold * weight
                            total_value = quantity_sold * selling_price
                            
                            st.write("**📋 Sale Summary:**")
                            summary_col1, summary_col2, summary_col3 = st.columns(3)
                            with summary_col1:
                                st.metric("Units", quantity_sold)
                            with summary_col2:
                                st.metric("Total Weight", f"{total_weight} kg")
                            with summary_col3:
                                st.metric("Total Value", f"₹{total_value:,.0f}")
                        
                        # Submit button
                        submitted = st.form_submit_button("🚛 Record Easy Ship Sale", type="primary", use_container_width=True)
                        
                        if submitted:
                            if available_units >= quantity_sold:
                                # Update stock
                                st.session_state.stock_data[parent_id]["packed_stock"][asin] -= quantity_sold
                                st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
                                
                                # Prepare transaction notes
                                transaction_notes = f"Easy Ship Sale"
                                if order_id:
                                    transaction_notes += f" | Order: {order_id}"
                                if selling_price != mrp:
                                    transaction_notes += f" | Price: ₹{selling_price}/unit"
                                if notes:
                                    transaction_notes += f" | {notes}"
                                
                                # Record transaction
                                weight_sold = quantity_sold * weight
                                transaction_id = record_transaction(
                                    transaction_type="Easy Ship Sale", 
                                    parent_id=parent_id, 
                                    asin=asin, 
                                    quantity=quantity_sold, 
                                    weight=weight_sold, 
                                    notes=transaction_notes, 
                                    batch_id=None, 
                                    transaction_date=sale_date
                                )
                                
                                # Store transaction details for undo outside form
                                st.session_state.last_transaction = {
                                    "id": transaction_id,
                                    "summary": f"Easy Ship sale: {quantity_sold} units of {format_product_option(asin)}",
                                    "show_undo": True
                                }
                                st.balloons()
                                # Don't call st.rerun() immediately - let the undo show first
                            else:
                                st.error(f"❌ Insufficient stock! Available: {available_units}, Requested: {quantity_sold}")
                else:
                    st.info("Please select a weight variation to continue")
            else:
                st.warning("No weight variations available for this product. Please add product variations first.")
        
        # Show immediate undo outside the form - SIMPLIFIED VERSION
        if hasattr(st.session_state, 'last_transaction') and st.session_state.last_transaction.get('show_undo'):
            st.markdown("---")
            transaction_info = st.session_state.last_transaction
            
            st.success(f"✅ Easy Ship sale recorded successfully!")
            st.write(f"**Sale:** {transaction_info['summary']}")
            
            # Show current stock for verification (get the product info from recent transaction)
            if st.session_state.transactions:
                last_trans = st.session_state.transactions[-1]
                parent_id = last_trans.get('parent_id')
                asin = last_trans.get('asin')
                if parent_id and asin:
                    current_packed = st.session_state.stock_data.get(parent_id, {}).get('packed_stock', {}).get(asin, 0)
                    st.write(f"**Current stock for {asin}:** {current_packed} units")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔄 Undo Sale", key="undo_last_easy_ship_sale"):
                    success = undo_transaction(transaction_info['id'])
                    if success:
                        st.session_state.last_transaction['show_undo'] = False
                        st.rerun()
                    else:
                        st.error("❌ Undo failed!")
            
            with col2:
                if st.button("✅ Keep Sale", key="keep_easy_ship_sale"):
                    st.session_state.last_transaction['show_undo'] = False
                    st.rerun()
        
        with col2:
            display_recent_easy_ship_sales()
    
    with tab2:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📁 Bulk Upload Easy Ship Sales")
            st.info("📋 Upload your Easy Ship sales Excel file. Review the data carefully before confirming.")
            
            # File upload
            uploaded_file = st.file_uploader(
                "Choose your Easy Ship Sales Excel file", 
                type=['xlsx', 'xls'],
                help="Excel file should contain 'asin' and 'quantity-purchased' columns",
                key="easy_ship_file_uploader"
            )
        
        if uploaded_file is not None:
            try:
                # Read the Excel file
                df = pd.read_excel(uploaded_file)
                
                # Check required columns (case-insensitive)
                df_columns_lower = [col.lower() for col in df.columns]
                required_cols = ['asin', 'quantity-purchased']
                missing_cols = []
                
                # Map columns (case-insensitive)
                column_mapping = {}
                for req_col in required_cols:
                    found = False
                    for actual_col in df.columns:
                        if actual_col.lower() == req_col or actual_col.lower().replace('-', '_') == req_col.replace('-', '_'):
                            column_mapping[req_col] = actual_col
                            found = True
                            break
                    if not found:
                        missing_cols.append(req_col)
                
                if missing_cols:
                    st.error(f"❌ Missing required columns: {missing_cols}")
                    st.write("**Available columns:** ", list(df.columns))
                    st.info("💡 **Expected columns:** 'asin' and 'quantity-purchased' (case-insensitive)")
                else:
                    # Rename columns for processing
                    df_processed = df.rename(columns={
                        column_mapping['asin']: 'asin',
                        column_mapping['quantity-purchased']: 'quantity_purchased'
                    })
                    
                    # Filter and prepare data for review
                    sales_data = df_processed[df_processed['quantity_purchased'] > 0].copy()
                    
                    if len(sales_data) == 0:
                        st.warning("⚠️ No sales data found (no rows with quantity-purchased > 0)")
                        return
                    
                    # Enrich data with product information for better review
                    enriched_data = []
                    
                    for _, row in sales_data.iterrows():
                        asin = str(row['asin']).strip()
                        quantity_purchased = int(row['quantity_purchased'])
                        
                        # Get product info
                        parent_id = None
                        product_name = "Unknown Product"
                        weight = "Unknown"
                        current_stock = "Unknown"
                        
                        # Find parent_id for this ASIN
                        for pid, variations in st.session_state.packet_variations.items():
                            if asin in variations:
                                parent_id = pid
                                variation_info = variations[asin]
                                weight = f"{variation_info.get('weight', 0)}kg"
                                
                                # Get product name
                                description = variation_info.get('description', '')
                                if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                                    parent_name = st.session_state.parent_items.get(pid, {}).get('name', 'Unknown')
                                    product_name = f"{weight} {parent_name}"
                                else:
                                    product_name = description
                                
                                # Get current stock
                                current_stock = st.session_state.stock_data.get(pid, {}).get("packed_stock", {}).get(asin, 0)
                                break
                        
                        # Additional columns from Excel
                        order_id = str(row.get('order-id', '')).strip() if 'order-id' in row else ''
                        sku = str(row.get('sku', '')).strip() if 'sku' in row else ''
                        
                        enriched_data.append({
                            'ASIN': asin,
                            'Product Name': product_name,
                            'Weight': weight,
                            'Current Stock': current_stock,
                            'Order ID': order_id,
                            'SKU': sku,
                            'Quantity Purchased': quantity_purchased,
                            'Status': 'Ready' if parent_id else 'Not Found',
                            'parent_id': parent_id  # Hidden field for processing
                        })
                    
                    # Create review dataframe
                    review_df = pd.DataFrame(enriched_data)
                    
                    # Show summary
                    st.subheader("📊 Upload Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Rows", len(sales_data))
                    with col2:
                        st.metric("Total Units", review_df['Quantity Purchased'].sum())
                    with col3:
                        ready_count = len(review_df[review_df['Status'] == 'Ready'])
                        st.metric("Ready to Process", ready_count)
                    with col4:
                        not_found_count = len(review_df[review_df['Status'] == 'Not Found'])
                        st.metric("Products Not Found", not_found_count)
                    
                    # Show detailed review table
                    st.subheader("📋 Review Data Before Processing")
                    st.warning("⚠️ **Please review this data carefully before confirming. Once processed, you'll need to use manual corrections for any errors.**")
                    
                    # Display table without the hidden parent_id column
                    display_df = review_df.drop(columns=['parent_id'])
                    
                    # Apply styling to highlight issues
                    def highlight_issues(row):
                        if row['Status'] == 'Not Found':
                            return ['background-color: #ffebee'] * len(row)
                        elif row['Current Stock'] != 'Unknown' and isinstance(row['Current Stock'], (int, float)) and row['Current Stock'] < row['Quantity Purchased']:
                            return ['background-color: #fff3e0'] * len(row)
                        else:
                            return [''] * len(row)
                    
                    # Show styled dataframe
                    styled_df = display_df.style.apply(highlight_issues, axis=1)
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    
                    # Legend for colors
                    st.write("**Legend:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("🔴 **Red Background**: Product not found in catalog")
                    with col2:
                        st.markdown("🟠 **Orange Background**: Insufficient stock")
                    
                    # Show issues summary
                    if not_found_count > 0:
                        st.error(f"❌ **{not_found_count} products not found** in your catalog. These will be skipped.")
                        not_found_asins = review_df[review_df['Status'] == 'Not Found']['ASIN'].tolist()
                        with st.expander("View products not found"):
                            for asin in not_found_asins:
                                st.write(f"• {asin}")
                    
                    # Check for insufficient stock
                    stock_issues = []
                    for _, row in review_df.iterrows():
                        if (row['Status'] == 'Ready' and 
                            isinstance(row['Current Stock'], (int, float)) and 
                            row['Current Stock'] < row['Quantity Purchased']):
                            stock_issues.append({
                                'ASIN': row['ASIN'],
                                'Product': row['Product Name'],
                                'Available': row['Current Stock'],
                                'Requested': row['Quantity Purchased']
                            })
                    
                    if stock_issues:
                        st.warning(f"⚠️ **{len(stock_issues)} products have insufficient stock**. These will result in errors.")
                        with st.expander("View stock issues"):
                            for issue in stock_issues:
                                st.write(f"• {issue['ASIN']} ({issue['Product']}): Available {issue['Available']}, Requested {issue['Requested']}")
                    
                    # Confirmation section
                    st.markdown("---")
                    st.subheader("🔍 Final Confirmation")
                    
                    # Show what will be processed
                    processable_count = len(review_df[review_df['Status'] == 'Ready'])
                    total_units = review_df[review_df['Status'] == 'Ready']['Quantity Purchased'].sum()
                    
                    if processable_count > 0:
                        st.success(f"✅ Ready to process **{processable_count}** products with **{total_units}** total units")
                        
                        # Final confirmation checkbox
                        confirm_processing = st.checkbox(
                            "✅ I have reviewed the data above and confirm it is correct", 
                            key="confirm_easy_ship_processing"
                        )
                        
                        if confirm_processing:
                            # Check if processing is in progress
                            processing_key = "easy_ship_processing_in_progress"
                            is_processing = st.session_state.get(processing_key, False)
                            
                            if not is_processing:
                                # Show buttons only when not processing
                                col1, col2 = st.columns([1, 1])
                                
                                with col1:
                                    if st.button("🚀 Confirm & Process Easy Ship Sales", type="primary", use_container_width=True):
                                        # Set processing flag and trigger rerun
                                        st.session_state[processing_key] = True
                                        st.rerun()
                                
                                with col2:
                                    if st.button("❌ Cancel", type="secondary", use_container_width=True):
                                        st.info("Processing cancelled. You can upload a different file or make corrections.")
                            else:
                                # Processing is in progress - process data directly without extra message
                                # Process the data
                                ready_rows = review_df[review_df['Status'] == 'Ready']
                                process_confirmed_easy_ship_sales(ready_rows)
                                
                                # Clear processing flag and confirmation checkbox after completion
                                st.session_state[processing_key] = False
                                if "confirm_easy_ship_processing" in st.session_state:
                                    del st.session_state["confirm_easy_ship_processing"]
                        else:
                            st.info("👆 Please review the data and check the confirmation box to proceed.")
                    else:
                        st.error("❌ No products are ready to process. Please check your data and product catalog.")
                        
            except Exception as e:
                st.error(f"❌ Error reading Excel file: {str(e)}")
                st.write("Please ensure your file is a valid Excel format (.xlsx or .xls)")

def show_products_management_protected():
    """Password-protected wrapper for Products Management"""
    
    # Check if user is already authenticated for this session
    if 'products_management_authenticated' not in st.session_state:
        st.session_state.products_management_authenticated = False
    
    if not st.session_state.products_management_authenticated:
        st.header("🔒 Products Management - Access Restricted")
        st.warning("This section requires authentication.")
        
        # Password input
        password_input = st.text_input(
            "Enter Password:", 
            type="password", 
            placeholder="Enter the access password",
            help="Contact administrator if you need access"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔓 Access", type="primary"):
                if password_input == "AVIRALTHEBOSS":
                    st.session_state.products_management_authenticated = True
                    st.success("✅ Access granted! Redirecting...")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Access denied.")
                    st.warning("Please contact the administrator for the correct password.")
        
        with col2:
            if st.button("← Back to Dashboard"):
                # Redirect to Live Stock View
                st.session_state.products_management_authenticated = False
                st.info("Redirected to Live Stock View")
        
        # Show some info about what this section contains
        st.markdown("---")
        st.subheader("📋 Products Management Features")
        st.write("""
        This restricted section allows you to:
        
        **🏷️ ASIN Products:**
        - Add new parent products
        - Create ASIN variations with weights and descriptions
        - Set MRP and product details
        
        **📁 Bulk Upload:**
        - Import products from Excel/CSV files
        - Download template files
        - Bulk add multiple products and variations
        
        **📊 Current Products & Management:**
        - View all existing products and ASINs
        - Edit product information
        - Manage product categories and details
        - Delete or modify existing entries
        
        **⚠️ Why is this protected?**
        - Product data affects all stock calculations
        - Changes here impact the entire inventory system
        - Prevents accidental modifications to critical product data
        """)
        
        return  # Exit early if not authenticated
    
    # If authenticated, show logout option and proceed to main function
    col1, col2, col3 = st.columns([3, 1, 1])
    with col2:
        if st.button("🔓 Logout", help="Logout from Products Management"):
            st.session_state.products_management_authenticated = False
            st.info("Logged out from Products Management")
            st.rerun()
    
    with col3:
        st.write(f"👤 **Authenticated**")
    
    # Call the actual products management function
    show_products_management()

def show_products_management():
    """Manage products and ASIN variations"""
    st.header("Products Management")
    
    tab1, tab2, tab3 = st.tabs(["ASIN Products", "Bulk Upload", "Current Products & Management"])
    
    with tab1:
        st.subheader("Add ASIN-Based Product")
        st.info("💡 All products are ASIN-based. Each ASIN represents a specific product with weight variation.")
        
        with st.form("add_asin_product"):
            col1, col2 = st.columns(2)
            
            with col1:
                asin = st.text_input("🏷️ ASIN *", placeholder="e.g., B07EXAMPLE123", help="Amazon Standard Identification Number")
                parent_item_name = st.text_input("📦 Parent Item Name *", placeholder="e.g., Premium Basmati Rice", help="Main product category")
                weight_variation = st.number_input("⚖️ Weight Variation (kg) *", min_value=0.1, step=0.1, format="%.2f", help="Weight of this specific pack")
                reorder_level = st.number_input("📊 Reorder Level (kg) *", min_value=0.0, value=5.0, step=0.5, format="%.1f", help="Alert when loose stock falls below this level")
            
            with col2:
                category = st.selectbox("📂 Category", 
                    options=["Rice", "Flour", "Pulses", "Spices", "Oil", "Cereals", "Dry Fruits", "Ready to Cook", "Organic", "Other"])
                
                description = st.text_input("📝 Product Description", placeholder="e.g., 1kg Premium Pack", help="Brief description of the product")
                mrp = st.number_input("💰 MRP (₹)", min_value=0.0, step=1.0, format="%.2f", help="Maximum Retail Price")
            
            notes = st.text_area("📋 Additional Notes", placeholder="Any special instructions or details...")
            
            submitted = st.form_submit_button("✅ Add ASIN Product", use_container_width=True)
            
            if submitted:
                # Validation
                if not asin or not parent_item_name or not weight_variation:
                    st.error("🚨 Please fill all required fields (ASIN, Parent Item Name, Weight)")
                elif len(asin) != 10 or not asin.isalnum():
                    st.error("🚨 ASIN must be exactly 10 alphanumeric characters")
                else:
                    # Create parent ID from parent item name
                    parent_id = parent_item_name.upper().replace(" ", "_").replace("-", "_")
                    
                    # Add parent item if not exists
                    if parent_id not in st.session_state.parent_items:
                        st.session_state.parent_items[parent_id] = {
                            "name": parent_item_name,
                            "unit": "kg",
                            "category": category,
                            "reorder_level": reorder_level
                        }
                        # Initialize stock data for parent
                        st.session_state.stock_data[parent_id] = {
                            "loose_stock": 0,
                            "packed_stock": {},
                            "opening_stock": 0,
                            "last_updated": datetime.datetime.now().isoformat()
                        }
                    else:
                        # Update reorder level if parent already exists
                        st.session_state.parent_items[parent_id]["reorder_level"] = reorder_level
                    
                    # Check if ASIN already exists
                    asin_exists = False
                    for pid, variations in st.session_state.packet_variations.items():
                        if asin in variations:
                            asin_exists = True
                            break
                    
                    if asin_exists:
                        st.error(f"🚨 ASIN {asin} already exists!")
                    else:
                        # Add ASIN variation
                        if parent_id not in st.session_state.packet_variations:
                            st.session_state.packet_variations[parent_id] = {}
                        
                        st.session_state.packet_variations[parent_id][asin] = {
                            "weight": weight_variation,
                            "asin": asin,
                            "description": description or f"{weight_variation}kg {parent_item_name}",
                            "mrp": mrp,
                            "category": category,
                            "notes": notes
                        }
                        
                        # Initialize packed stock for this ASIN
                        st.session_state.stock_data[parent_id]["packed_stock"][asin] = 0
                        
                        save_data()
                        st.success(f"✅ Successfully added ASIN: {asin} for {parent_item_name} ({weight_variation}kg)")
                        st.rerun()
    
    with tab2:
        st.subheader("📁 Bulk Upload Products")
        
        # Template download
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📥 Download Template")
            template_data = {
                "ASIN": ["B07BASMATI1K", "B07BASMATI5K", "B07JASMINE1K", "B07WHEAT001K"],
                "Parent_Item_Name": ["Premium Basmati Rice", "Premium Basmati Rice", "Jasmine Rice", "Wheat Flour"],
                "Weight_kg": [1.0, 5.0, 1.0, 1.0],
                "Category": ["Rice", "Rice", "Rice", "Flour"],
                "Description": ["1kg Premium Basmati Pack", "5kg Family Pack", "1kg Jasmine Pack", "1kg Wheat Flour"],
                "MRP": [120, 580, 110, 45],
                "Reorder_Level_kg": [10.0, 10.0, 5.0, 8.0],
                "Notes": ["Premium quality", "Family size", "Fragrant rice", "Organic flour"]
            }
            template_df = pd.DataFrame(template_data)
            
            st.download_button(
                label="📥 Download Excel Template",
                data=template_df.to_csv(index=False),
                file_name="mithila_foods_products_template.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            st.info("📋 **Template Format:**\n- ASIN: 10-character alphanumeric\n- Parent_Item_Name: Product category\n- Weight_kg: Weight in kilograms\n- Category: Product category\n- Description: Product description\n- MRP: Price in rupees\n- Reorder_Level_kg: Minimum stock alert level\n- Notes: Additional info")
        
        with col2:
            st.subheader("📤 Upload Your File")
            uploaded_file = st.file_uploader(
                "Choose Excel or CSV file", 
                type=['xlsx', 'xls', 'csv'],
                help="Upload your product data file matching the template format"
            )
            
            if uploaded_file is not None:
                try:
                    # Read the file
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.write("📊 **Preview of uploaded data:**")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    # Validate required columns
                    required_columns = ['ASIN', 'Parent_Item_Name', 'Weight_kg']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        st.error(f"🚨 Missing required columns: {', '.join(missing_columns)}")
                    else:
                        if st.button("🚀 Process Upload", type="primary", use_container_width=True):
                            process_products_upload(df)
                            
                except Exception as e:
                    st.error(f"🚨 Error reading file: {e}")
                    st.info("💡 Please ensure your file matches the template format")
    
    with tab3:
        st.subheader("📋 Current Products Overview & Management")
        
        # Display current ASINs with delete functionality
        if st.session_state.packet_variations:
            all_products = []
            for parent_id, variations in st.session_state.packet_variations.items():
                parent_name = st.session_state.parent_items.get(parent_id, {}).get("name", parent_id)
                category = st.session_state.parent_items.get(parent_id, {}).get("category", "Unknown")
                
                for asin, details in variations.items():
                    # Get current stock
                    current_stock = st.session_state.stock_data.get(parent_id, {}).get("packed_stock", {}).get(asin, 0)
                    
                    all_products.append({
                        "ASIN": asin,
                        "Parent Item": parent_name,
                        "Category": category,
                        "Weight (kg)": details["weight"],
                        "Description": details["description"],
                        "MRP (₹)": details.get("mrp", 0),
                        "Current Stock": current_stock,
                        "Stock Value (₹)": current_stock * details.get("mrp", 0),
                        "parent_id": parent_id  # Hidden field for operations
                    })
            
            if all_products:
                df_products = pd.DataFrame(all_products)
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total ASINs", len(df_products))
                with col2:
                    st.metric("Total Categories", df_products["Category"].nunique())
                with col3:
                    st.metric("Total Stock Units", df_products["Current Stock"].sum())
                with col4:
                    st.metric("Total Stock Value", f"₹{df_products['Stock Value (₹)'].sum():,.0f}")
                
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    category_filter = st.selectbox("Filter by Category", ["All"] + sorted(df_products["Category"].unique()))
                with col2:
                    stock_filter = st.selectbox("Filter by Stock", ["All", "In Stock", "Out of Stock"])
                
                # Apply filters
                filtered_df = df_products.copy()
                if category_filter != "All":
                    filtered_df = filtered_df[filtered_df["Category"] == category_filter]
                if stock_filter == "In Stock":
                    filtered_df = filtered_df[filtered_df["Current Stock"] > 0]
                elif stock_filter == "Out of Stock":
                    filtered_df = filtered_df[filtered_df["Current Stock"] == 0]
                
                # Display table (without parent_id column)
                display_df = filtered_df.drop(columns=['parent_id'])
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Product Management Section
                st.subheader("🛠️ Product Management")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("🗑️ Delete Weight Variation")
                    
                    # Step 1: Select Parent Product
                    parent_options = []
                    for parent_id, parent_info in st.session_state.parent_items.items():
                        if parent_id in st.session_state.packet_variations:
                            variation_count = len(st.session_state.packet_variations[parent_id])
                            parent_options.append({
                                "parent_id": parent_id,
                                "name": parent_info["name"],
                                "display": f"{parent_info['name']} ({variation_count} variations)"
                            })
                    
                    if parent_options:
                        selected_parent = st.selectbox(
                            "Step 1: Select Parent Product",
                            options=parent_options,
                            format_func=lambda x: x["display"],
                            key="delete_parent_select"
                        )
                        
                        if selected_parent:
                            parent_id = selected_parent["parent_id"]
                            
                            # Step 2: Select Weight Variation
                            if parent_id in st.session_state.packet_variations:
                                variation_options = []
                                for asin, variation_info in st.session_state.packet_variations[parent_id].items():
                                    weight = variation_info.get("weight", 0)
                                    description = variation_info.get("description", "")
                                    
                                    # Clean up description
                                    if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                                        clean_description = f"{weight}kg {st.session_state.parent_items[parent_id]['name']}"
                                    else:
                                        clean_description = description
                                    
                                    current_stock = st.session_state.stock_data.get(parent_id, {}).get("packed_stock", {}).get(asin, 0)
                                    
                                    variation_options.append({
                                        "asin": asin,
                                        "parent_id": parent_id,
                                        "display": f"{clean_description} (ASIN: {asin})",
                                        "description": clean_description,
                                        "weight": weight,
                                        "stock": current_stock
                                    })
                                
                                if variation_options:
                                    selected_variation = st.selectbox(
                                        "Step 2: Select Weight Variation to Delete",
                                        options=variation_options,
                                        format_func=lambda x: x["display"],
                                        key="delete_variation_select"
                                    )
                                    
                                    if selected_variation:
                                        # Show deletion info
                                        st.warning("**⚠️ This will permanently delete:**")
                                        st.write(f"• **Product:** {selected_parent['name']}")
                                        st.write(f"• **Variation:** {selected_variation['description']}")
                                        st.write(f"• **ASIN:** {selected_variation['asin']}")
                                        st.write(f"• **Weight:** {selected_variation['weight']}kg")
                                        st.write(f"• **Current Stock:** {selected_variation['stock']} units")
                                        
                                        # Count related transactions
                                        related_transactions = len([t for t in st.session_state.transactions if t.get("asin") == selected_variation['asin']])
                                        st.write(f"• **Related Transactions:** {related_transactions}")
                                        
                                        # Deletion form
                                        with st.form("delete_weight_variation"):
                                            confirm_delete = st.checkbox("⚠️ I understand this action cannot be undone")
                                            
                                            if st.form_submit_button("🗑️ Delete Weight Variation", type="secondary", use_container_width=True):
                                                if confirm_delete:
                                                    asin = selected_variation["asin"]
                                                    parent_id = selected_variation["parent_id"]
                                                    description = selected_variation["description"]
                                                    
                                                    # Remove ASIN variation
                                                    if parent_id in st.session_state.packet_variations and asin in st.session_state.packet_variations[parent_id]:
                                                        del st.session_state.packet_variations[parent_id][asin]
                                                    
                                                    # Remove packed stock for this ASIN
                                                    if parent_id in st.session_state.stock_data and asin in st.session_state.stock_data[parent_id].get("packed_stock", {}):
                                                        del st.session_state.stock_data[parent_id]["packed_stock"][asin]
                                                    
                                                    # Remove related transactions
                                                    st.session_state.transactions = [
                                                        t for t in st.session_state.transactions 
                                                        if t.get("asin") != asin
                                                    ]
                                                    
                                                    save_data()
                                                    st.success(f"✅ Successfully deleted: {description}")
                                                    st.rerun()
                                                else:
                                                    st.error("❌ Please confirm deletion by checking the checkbox")
                                else:
                                    st.info("No weight variations found for this product.")
                            else:
                                st.info("No variations found for this product.")
                    else:
                        st.info("No products with variations available for deletion.")
                
                with col2:
                    st.subheader("🗑️ Delete Parent Product")
                    
                    # Get unique parent products
                    parent_products = df_products[['Parent Item', 'parent_id']].drop_duplicates()
                    
                    if not parent_products.empty:
                        parent_options = []
                        for _, parent in parent_products.iterrows():
                            # Count ASINs and stock for this parent
                            parent_data = df_products[df_products['parent_id'] == parent['parent_id']]
                            asin_count = len(parent_data)
                            total_stock = parent_data['Current Stock'].sum()
                            
                            parent_options.append({
                                "parent_id": parent['parent_id'],
                                "name": parent['Parent Item'],
                                "display": f"{parent['Parent Item']} ({asin_count} ASINs, {total_stock} units)",
                                "asin_count": asin_count,
                                "total_stock": total_stock
                            })
                        
                        selected_parent = st.selectbox(
                            "Select Parent Product to Delete",
                            options=parent_options,
                            format_func=lambda x: x["display"]
                        )
                        
                        if selected_parent:
                            # Show deletion info
                            st.warning("**⚠️ This will permanently delete:**")
                            st.write(f"• Parent: **{selected_parent['name']}**")
                            st.write(f"• ASINs: **{selected_parent['asin_count']}**")
                            st.write(f"• Total Stock: **{selected_parent['total_stock']} units**")
                            
                            # Count loose stock
                            loose_stock = st.session_state.stock_data.get(selected_parent['parent_id'], {}).get("loose_stock", 0)
                            st.write(f"• Loose Stock: **{loose_stock} kg**")
                            
                            # Count related transactions
                            related_transactions = len([t for t in st.session_state.transactions if t.get("parent_id") == selected_parent['parent_id']])
                            st.write(f"• Related Transactions: **{related_transactions}**")
                            
                            # Deletion form
                            with st.form("delete_parent_product"):
                                confirm_delete_parent = st.checkbox("⚠️ I understand this will delete ALL products under this parent")
                                
                                if st.form_submit_button("🗑️ Delete Parent & All ASINs", type="secondary", use_container_width=True):
                                    if confirm_delete_parent:
                                        parent_id = selected_parent["parent_id"]
                                        parent_name = selected_parent["name"]
                                        
                                        # Remove parent item
                                        if parent_id in st.session_state.parent_items:
                                            del st.session_state.parent_items[parent_id]
                                        
                                        # Remove stock data
                                        if parent_id in st.session_state.stock_data:
                                            del st.session_state.stock_data[parent_id]
                                        
                                        # Remove packet variations
                                        if parent_id in st.session_state.packet_variations:
                                            del st.session_state.packet_variations[parent_id]
                                        
                                        # Remove related transactions
                                        st.session_state.transactions = [
                                            t for t in st.session_state.transactions 
                                            if t.get("parent_id") != parent_id
                                        ]
                                        
                                        save_data()
                                        st.success(f"✅ Successfully deleted parent product: {parent_name}")
                                        st.rerun()
                                    else:
                                        st.error("❌ Please confirm deletion by checking the checkbox")
                
                # Export current products
                st.subheader("📥 Export Data")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📥 Export Current Products", use_container_width=True):
                        st.download_button(
                            label="📥 Download Products Data",
                            data=display_df.to_csv(index=False),
                            file_name=f"mithila_foods_products_{datetime.date.today()}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                with col2:
                    if st.button("📥 Export Filtered Products", use_container_width=True):
                        st.download_button(
                            label="📥 Download Filtered Data",
                            data=display_df.to_csv(index=False),
                            file_name=f"mithila_foods_filtered_products_{datetime.date.today()}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                
                # Reset Stock Data Section
                st.markdown("---")
                st.subheader("🔄 Reset Stock Data")
                st.warning("⚠️ **Dangerous Operation**: This will reset ALL stock levels to zero while keeping products intact.")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write("**This action will:**")
                    st.write("• Reset all loose stock to 0 kg")
                    st.write("• Reset all packed stock to 0 units")
                    st.write("• **DELETE ALL TRANSACTIONS**")
                    st.write("• **CLEAR ALL RETURN DATA**")
                    st.write("• Clear all daily opening stock data")
                    st.write("• Keep all product definitions unchanged")
                    st.write("• **COMPLETE DATA WIPE (except products)**")
                
                with col2:
                    # Count current stock for confirmation
                    total_loose = sum(stock.get("loose_stock", 0) for stock in st.session_state.stock_data.values())
                    total_packed = sum(sum(stock.get("packed_stock", {}).values()) for stock in st.session_state.stock_data.values())
                    
                    st.metric("Current Loose Stock", f"{total_loose:.1f} kg")
                    st.metric("Current Packed Stock", f"{total_packed} units")
                
                with st.form("reset_stock_form"):
                    st.error("⚠️ **CONFIRMATION REQUIRED**")
                    st.write("Type **RESET ALL STOCK** in the box below to confirm:")
                    
                    confirmation_text = st.text_input(
                        "Confirmation Text:",
                        placeholder="Type: RESET ALL STOCK",
                        key="reset_confirmation_input"
                    )
                    
                    reset_reason = st.text_area(
                        "Reason for Reset (Required):",
                        placeholder="e.g., New inventory count, Year-end reset, System migration, etc.",
                        key="reset_reason_input"
                    )
                    
                    submitted = st.form_submit_button("🗑️ RESET ALL STOCK TO ZERO", type="primary")
                    
                    if submitted:
                        if confirmation_text == "RESET ALL STOCK" and reset_reason.strip():
                            # Perform the complete reset
                            reset_count = 0
                            transactions_deleted = len(st.session_state.transactions)
                            return_transactions_deleted = len(st.session_state.return_transactions)
                            
                            # Reset all stock data while keeping structure
                            for parent_id, stock_data in st.session_state.stock_data.items():
                                # Reset loose stock
                                if stock_data.get("loose_stock", 0) != 0:
                                    reset_count += 1
                                stock_data["loose_stock"] = 0
                                stock_data["opening_stock"] = 0
                                stock_data["last_updated"] = datetime.datetime.now().isoformat()
                                
                                # Reset all packed stock
                                for asin in stock_data.get("packed_stock", {}):
                                    if stock_data["packed_stock"][asin] != 0:
                                        reset_count += 1
                                    stock_data["packed_stock"][asin] = 0
                            
                            # COMPLETE DATA WIPE
                            # Clear all transactions
                            st.session_state.transactions = []
                            
                            # Clear all return transactions
                            st.session_state.return_transactions = []
                            
                            # Reset all return data to zero
                            for parent_id in st.session_state.parent_items:
                                if parent_id not in st.session_state.return_data:
                                    st.session_state.return_data[parent_id] = {
                                        "loose_return": {"good": 0, "bad": 0},
                                        "packed_return": {}
                                    }
                                else:
                                    st.session_state.return_data[parent_id]["loose_return"] = {"good": 0, "bad": 0}
                                    st.session_state.return_data[parent_id]["packed_return"] = {}
                                
                                # Reset packed return data for all ASINs
                                if parent_id in st.session_state.packet_variations:
                                    for asin in st.session_state.packet_variations[parent_id]:
                                        st.session_state.return_data[parent_id]["packed_return"][asin] = {"good": 0, "bad": 0}
                            
                            # Clear daily opening stock completely
                            st.session_state.daily_opening_stock = {}
                            
                            # Record ONE final reset transaction for audit (after clearing all others)
                            reset_transaction = {
                                "id": 1,  # Start fresh with ID 1
                                "timestamp": datetime.datetime.now().isoformat(),
                                "date": datetime.date.today().isoformat(),
                                "type": "COMPLETE_SYSTEM_RESET",
                                "parent_id": "SYSTEM",
                                "parent_name": "System Operation",
                                "asin": None,
                                "quantity": 0,
                                "weight": 0,
                                "notes": f"Complete system reset | Reason: {reset_reason} | Stock items reset: {reset_count} | Transactions deleted: {transactions_deleted} | Return transactions deleted: {return_transactions_deleted} | Loose stock reset: {total_loose:.1f} kg | Packed stock reset: {total_packed} units"
                            }
                            st.session_state.transactions = [reset_transaction]  # Only keep this one transaction
                            
                            # Save the changes
                            save_data()
                            
                            # Show success message
                            st.success("✅ **COMPLETE SYSTEM RESET SUCCESSFUL!**")
                            st.balloons()
                            
                            # Show detailed reset summary
                            st.info("🔄 **Reset Summary:**")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**📊 Stock Data Reset:**")
                                st.write(f"• Loose stock cleared: {total_loose:.1f} kg")
                                st.write(f"• Packed stock cleared: {total_packed} units")
                                st.write(f"• Stock items reset: {reset_count}")
                                
                            with col2:
                                st.write("**🗑️ Data Cleared:**")
                                st.write(f"• Transactions deleted: {transactions_deleted}")
                                st.write(f"• Return transactions deleted: {return_transactions_deleted}")
                                st.write(f"• All return data cleared")
                            
                            st.success("**✨ System is now completely fresh! All data wiped except product definitions.**")
                            st.info("**Next Steps:** Start fresh with new stock inward entries. No history will show in Live Stock View.")
                            
                            # Auto-refresh after 2 seconds to show the clean state
                            import time
                            time.sleep(2)
                            st.rerun()
                            
                        elif confirmation_text != "RESET ALL STOCK":
                            st.error("❌ Incorrect confirmation text. Please type exactly: **RESET ALL STOCK**")
                        elif not reset_reason.strip():
                            st.error("❌ Please provide a reason for the stock reset.")
                
                # Reorder Level Management Section
                st.markdown("---")
                st.subheader("📊 Reorder Level Management")
                st.info("💡 Set minimum stock levels for automatic alerts when stock runs low.")
                
                if st.session_state.parent_items:
                    # Show current reorder levels
                    reorder_data = []
                    for parent_id, parent_info in st.session_state.parent_items.items():
                        current_loose = st.session_state.stock_data.get(parent_id, {}).get("loose_stock", 0)
                        reorder_level = parent_info.get("reorder_level", 5.0)
                        status = "🔴 REORDER" if current_loose <= reorder_level else "✅ OK"
                        
                        reorder_data.append({
                            "Product": parent_info["name"],
                            "Category": parent_info.get("category", "Unknown"),
                            "Current Stock": f"{current_loose:.1f} kg",
                            "Reorder Level": f"{reorder_level:.1f} kg",
                            "Status": status,
                            "parent_id": parent_id  # Hidden for operations
                        })
                    
                    # Display current reorder levels
                    reorder_df = pd.DataFrame(reorder_data)
                    display_reorder_df = reorder_df.drop(columns=['parent_id'])
                    
                    st.write("**📋 Current Reorder Levels:**")
                    st.dataframe(display_reorder_df, use_container_width=True, hide_index=True)
                    
                    # Quick edit interface
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.subheader("✏️ Update Reorder Level")
                        
                        # Select parent product
                        selected_parent_for_reorder = st.selectbox(
                            "Select Product:",
                            options=list(st.session_state.parent_items.keys()),
                            format_func=lambda x: f"{st.session_state.parent_items[x]['name']} ({st.session_state.parent_items[x].get('category', 'Unknown')})",
                            key="reorder_parent_select"
                        )
                        
                        if selected_parent_for_reorder:
                            current_reorder = st.session_state.parent_items[selected_parent_for_reorder].get("reorder_level", 5.0)
                            current_stock_for_display = st.session_state.stock_data.get(selected_parent_for_reorder, {}).get("loose_stock", 0)
                            
                            col_info1, col_info2 = st.columns(2)
                            with col_info1:
                                st.metric("Current Stock", f"{current_stock_for_display:.1f} kg")
                            with col_info2:
                                st.metric("Current Reorder Level", f"{current_reorder:.1f} kg")
                            
                            new_reorder_level = st.number_input(
                                "New Reorder Level (kg):",
                                min_value=0.0,
                                value=current_reorder,
                                step=0.5,
                                format="%.1f",
                                help="Stock level at which to trigger reorder alerts",
                                key="new_reorder_level_input"
                            )
                            
                            if st.button("💾 Update Reorder Level", type="primary", use_container_width=True):
                                # Update the reorder level
                                st.session_state.parent_items[selected_parent_for_reorder]["reorder_level"] = new_reorder_level
                                save_data()
                                
                                st.success(f"✅ Updated reorder level for {st.session_state.parent_items[selected_parent_for_reorder]['name']} to {new_reorder_level:.1f} kg")
                                st.rerun()
                    
                    with col2:
                        st.subheader("📈 Quick Stats")
                        
                        # Calculate reorder stats
                        total_products = len(st.session_state.parent_items)
                        products_below_reorder = 0
                        
                        for parent_id, parent_info in st.session_state.parent_items.items():
                            current_loose = st.session_state.stock_data.get(parent_id, {}).get("loose_stock", 0)
                            reorder_level = parent_info.get("reorder_level", 5.0)
                            if current_loose <= reorder_level:
                                products_below_reorder += 1
                        
                        st.metric("Total Products", total_products)
                        st.metric("Below Reorder Level", products_below_reorder, delta=f"{products_below_reorder - (total_products - products_below_reorder)}")
                        
                        if products_below_reorder > 0:
                            st.error(f"🚨 {products_below_reorder} product(s) need reordering!")
                        else:
                            st.success("✅ All stock levels OK")
                
                else:
                    st.info("No products found. Add products first to set reorder levels.")
                        
                # New Section: Stock Management
                st.markdown("---")
                st.subheader("📦 Stock Management")
                
                # Sub-tabs for stock management
                stock_tab1, stock_tab2 = st.columns([1, 1])
                
                with stock_tab1:
                    st.subheader("✏️ Manual Stock Update")
                    
                    # Step 1: Select Parent Product (like packing operations)
                    parent_id = st.selectbox(
                        "Select Product Category",
                        options=list(st.session_state.parent_items.keys()),
                        format_func=lambda x: st.session_state.parent_items[x]["name"],
                        key="manual_update_parent_select"
                    )
                    
                    if parent_id:
                        # Step 2: Select what to update - loose stock or specific weight variation
                        stock_options = []
                        
                        # Add loose stock option
                        current_loose = st.session_state.stock_data.get(parent_id, {}).get("loose_stock", 0)
                        parent_name = st.session_state.parent_items[parent_id]["name"]
                        parent_unit = st.session_state.parent_items[parent_id].get("unit", "kg")
                        
                        stock_options.append({
                            "type": "loose",
                            "display": f"🌾 Loose Stock ({parent_name})",
                            "current": current_loose,
                            "unit": parent_unit,
                            "parent_id": parent_id
                        })
                        
                        # Add weight variations
                        if parent_id in st.session_state.packet_variations:
                            for asin, details in st.session_state.packet_variations[parent_id].items():
                                current_packed = st.session_state.stock_data.get(parent_id, {}).get("packed_stock", {}).get(asin, 0)
                                weight = details.get('weight', 1.0)
                                description = details.get('description', f"{weight}kg {parent_name}")
                                
                                # Clean up description
                                if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                                    description = f"{weight}kg {parent_name}"
                                
                                stock_options.append({
                                    "type": "packed",
                                    "display": f"📦 {description} ({weight}kg)",
                                    "current": current_packed,
                                    "unit": "units",
                                    "asin": asin,
                                    "parent_id": parent_id,
                                    "weight": weight
                                })
                        
                        # Display options
                        selected_option = st.selectbox(
                            "Select what to update:",
                            options=stock_options,
                            format_func=lambda x: f"{x['display']} - Current: {x['current']} {x['unit']}",
                            key="manual_stock_option_select"
                        )
                        
                        if selected_option:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.info(f"**Current Stock:** {selected_option['current']} {selected_option['unit']}")
                                
                            with col2:
                                update_type = st.radio(
                                    "Update Type:",
                                    ["Set New Value", "Add to Current", "Subtract from Current"],
                                    key="stock_update_type"
                                )
                            
                            # Stock input based on update type
                            if update_type == "Set New Value":
                                if selected_option['type'] == 'loose':
                                    new_stock = st.number_input(
                                        f"New Stock Value ({selected_option['unit']}):",
                                        min_value=0.0,
                                        value=float(selected_option['current']),
                                        step=0.1,
                                        key="new_stock_value"
                                    )
                                else:
                                    new_stock = st.number_input(
                                        f"New Stock Value ({selected_option['unit']}):",
                                        min_value=0,
                                        value=selected_option['current'],
                                        step=1,
                                        key="new_stock_value"
                                    )
                                final_stock = new_stock
                                
                            elif update_type == "Add to Current":
                                if selected_option['type'] == 'loose':
                                    add_amount = st.number_input(
                                        f"Amount to Add ({selected_option['unit']}):",
                                        min_value=0.0,
                                        value=0.0,
                                        step=0.1,
                                        key="add_stock_amount"
                                    )
                                else:
                                    add_amount = st.number_input(
                                        f"Amount to Add ({selected_option['unit']}):",
                                        min_value=0,
                                        value=0,
                                        step=1,
                                        key="add_stock_amount"
                                    )
                                final_stock = selected_option['current'] + add_amount
                                st.info(f"Final Stock: {final_stock} {selected_option['unit']}")
                                
                            else:  # Subtract from Current
                                if selected_option['type'] == 'loose':
                                    subtract_amount = st.number_input(
                                        f"Amount to Subtract ({selected_option['unit']}):",
                                        min_value=0.0,
                                        max_value=float(selected_option['current']),
                                        value=0.0,
                                        step=0.1,
                                        key="subtract_stock_amount"
                                    )
                                else:
                                    subtract_amount = st.number_input(
                                        f"Amount to Subtract ({selected_option['unit']}):",
                                        min_value=0,
                                        max_value=selected_option['current'],
                                        value=0,
                                        step=1,
                                        key="subtract_stock_amount"
                                    )
                                final_stock = selected_option['current'] - subtract_amount
                                st.info(f"Final Stock: {final_stock} {selected_option['unit']}")
                            
                            # Reason for update
                            update_reason = st.text_input(
                                "Reason for Update:",
                                placeholder="e.g., Physical count correction, Damage adjustment, etc.",
                                key="stock_update_reason"
                            )
                            
                            # Update button
                            if st.button("💾 Update Stock", type="primary", use_container_width=True):
                                if update_reason.strip():
                                    # Ensure stock data structure exists
                                    if parent_id not in st.session_state.stock_data:
                                        st.session_state.stock_data[parent_id] = {"loose_stock": 0, "packed_stock": {}}
                                    
                                    if selected_option['type'] == 'loose':
                                        # Update loose stock
                                        old_stock = selected_option['current']
                                        st.session_state.stock_data[parent_id]["loose_stock"] = final_stock
                                        st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
                                        
                                        # Record transaction
                                        stock_change = final_stock - old_stock
                                        record_transaction(
                                            transaction_type="LOOSE_STOCK_ADJUSTMENT",
                                            parent_id=parent_id,
                                            weight=stock_change,
                                            notes=f"Manual loose stock update: {update_reason}. Stock changed from {old_stock} to {final_stock} {selected_option['unit']}",
                                            transaction_date=datetime.datetime.now()
                                        )
                                        
                                        save_data()
                                        st.success(f"✅ Loose stock updated successfully! {parent_name} loose stock set to {final_stock} {selected_option['unit']}")
                                        st.rerun()
                                        
                                    else:
                                        # Update packed stock
                                        old_stock = selected_option['current']
                                        asin = selected_option['asin']
                                        
                                        if "packed_stock" not in st.session_state.stock_data[parent_id]:
                                            st.session_state.stock_data[parent_id]["packed_stock"] = {}
                                        
                                        st.session_state.stock_data[parent_id]["packed_stock"][asin] = int(final_stock)
                                        st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
                                        
                                        # Record transaction
                                        stock_change = int(final_stock) - old_stock
                                        record_transaction(
                                            transaction_type="STOCK_ADJUSTMENT",
                                            parent_id=parent_id,
                                            asin=asin,
                                            quantity=stock_change,
                                            notes=f"Manual packed stock update: {update_reason}. Stock changed from {old_stock} to {int(final_stock)} {selected_option['unit']}",
                                            transaction_date=datetime.datetime.now()
                                        )
                                        
                                        save_data()
                                        st.success(f"✅ Packed stock updated successfully! {selected_option['display']} set to {int(final_stock)} {selected_option['unit']}")
                                        st.rerun()
                                else:
                                    st.error("Please provide a reason for the stock update.")
                    else:
                        st.info("Please select a product category to update stock.")
                
                with stock_tab2:
                    st.subheader("📁 Bulk Stock Update")
                    
                    # Download current stock template
                    st.subheader("📥 Download Current Stock Data")
                    if st.button("📥 Download Stock Template", use_container_width=True):
                        stock_template_data = []
                        
                        # Add parent items for loose stock updates
                        for parent_id, parent_info in st.session_state.parent_items.items():
                            current_loose_stock = st.session_state.stock_data.get(parent_id, {}).get("loose_stock", 0)
                            
                            stock_template_data.append({
                                "Type": "PARENT_LOOSE",
                                "Parent_ID": parent_id,
                                "Parent_Name": parent_info.get("name", parent_id),
                                "ASIN": "",  # Empty for parent items
                                "Product_Name": f"[LOOSE] {parent_info.get('name', parent_id)}",
                                "Current_Stock": current_loose_stock,
                                "New_Stock": current_loose_stock,
                                "Unit": parent_info.get("unit", "kg"),
                                "Update_Reason": ""
                            })
                        
                        # Add ASIN-based products for packed stock updates
                        for parent_id, variations in st.session_state.packet_variations.items():
                            parent_name = st.session_state.parent_items.get(parent_id, {}).get("name", parent_id)
                            for asin, details in variations.items():
                                current_stock = st.session_state.stock_data.get(parent_id, {}).get("packed_stock", {}).get(asin, 0)
                                weight = details.get('weight', 1.0)
                                
                                # Create enhanced product name with weight
                                clean_description = details.get("description", f"{weight}kg {parent_name}")
                                
                                # Clean up description and ensure weight is clearly visible
                                if not clean_description or str(clean_description).lower() in ['nan', 'null', 'none', '']:
                                    clean_description = f"{weight}kg {parent_name}"
                                elif f"{weight}kg" not in clean_description:
                                    clean_description = f"{weight}kg {clean_description}"
                                
                                stock_template_data.append({
                                    "Type": "ASIN_PACKED",
                                    "Parent_ID": parent_id,
                                    "Parent_Name": parent_name,
                                    "Weight": f"{weight}kg",
                                    "ASIN": asin,
                                    "Product_Name": clean_description,
                                    "Current_Stock": current_stock,
                                    "New_Stock": current_stock,
                                    "Unit": "units",
                                    "Update_Reason": ""
                                })
                        
                        if stock_template_data:
                            stock_template_df = pd.DataFrame(stock_template_data)
                            
                            st.download_button(
                                label="📥 Download Stock Update Template",
                                data=stock_template_df.to_csv(index=False),
                                file_name=f"stock_update_template_{datetime.date.today()}.csv",
                                mime="text/csv",
                                use_container_width=True,
                                key="download_stock_template"
                            )
                            
                            st.info("📋 **Instructions:**\n1. Download the template above\n2. Edit the 'New_Stock' column with desired stock levels\n3. Fill 'Update_Reason' for each change\n4. **Type**: 'PARENT_LOOSE' for loose stock, 'ASIN_PACKED' for packed stock\n5. Upload the file below")
                        else:
                            st.warning("No products found to create template")
                    
                    # Upload stock update file
                    st.subheader("📤 Upload Stock Updates")
                    stock_upload_file = st.file_uploader(
                        "Choose Stock Update File",
                        type=['xlsx', 'xls', 'csv'],
                        help="Upload your modified stock template file",
                        key="stock_upload_file"
                    )
                    
                    if stock_upload_file is not None:
                        try:
                            # Read the file
                            if stock_upload_file.name.endswith('.csv'):
                                stock_df = pd.read_csv(stock_upload_file)
                            else:
                                stock_df = pd.read_excel(stock_upload_file)
                            
                            st.write("📊 **Preview of stock update file:**")
                            st.dataframe(stock_df.head(10), use_container_width=True)
                            
                            # Validate required columns
                            required_stock_columns = ['Type', 'New_Stock']
                            missing_stock_columns = [col for col in required_stock_columns if col not in stock_df.columns]
                            
                            if missing_stock_columns:
                                st.error(f"🚨 Missing required columns: {', '.join(missing_stock_columns)}")
                            else:
                                # Filter rows with changes
                                if 'Current_Stock' in stock_df.columns:
                                    # Only process rows where New_Stock differs from Current_Stock
                                    changes_df = stock_df[stock_df['New_Stock'] != stock_df['Current_Stock']].copy()
                                else:
                                    changes_df = stock_df.copy()
                                
                                if len(changes_df) > 0:
                                    st.write(f"📝 **Found {len(changes_df)} stock changes to process:**")
                                    display_columns = ['Type', 'Parent_Name', 'Weight', 'ASIN', 'Product_Name', 'Current_Stock', 'New_Stock', 'Update_Reason']
                                    available_columns = [col for col in display_columns if col in changes_df.columns]
                                    st.dataframe(changes_df[available_columns].head(10), use_container_width=True)
                                    
                                    if st.button("🚀 Process Stock Updates", type="primary", use_container_width=True):
                                        process_enhanced_stock_updates(changes_df)
                                else:
                                    st.info("ℹ️ No stock changes detected in the uploaded file")
                        
                        except Exception as e:
                            st.error(f"🚨 Error reading stock file: {e}")
                            st.info("💡 Please ensure your file matches the template format")
                            
            else:
                st.info("🔍 No products found. Add some products using the ASIN form or bulk upload.")
        else:
            st.info("🚀 Start by adding your first ASIN-based product!")

def process_products_upload(df):
    """Process bulk product upload"""
    imported_count = 0
    updated_count = 0
    errors = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index, row in df.iterrows():
        try:
            # Update progress
            progress = (index + 1) / len(df)
            progress_bar.progress(progress)
            status_text.text(f"Processing row {index + 1} of {len(df)}")
            
            # Extract required fields
            asin = str(row.get('ASIN', '')).strip().upper()
            parent_item_name = str(row.get('Parent_Item_Name', '')).strip()
            weight_kg = float(row.get('Weight_kg', 0))
            
            # Extract optional fields
            category = str(row.get('Category', 'Other')).strip()
            description = str(row.get('Description', '')).strip()
            mrp = float(row.get('MRP', 0))
            reorder_level = float(row.get('Reorder_Level_kg', 5.0))  # Default to 5kg if not provided
            notes = str(row.get('Notes', '')).strip()
            
            # Validation
            if not asin or not parent_item_name or weight_kg <= 0:
                errors.append(f"Row {index+1}: Missing required fields (ASIN: {asin}, Parent: {parent_item_name}, Weight: {weight_kg})")
                continue
            
            if len(asin) != 10 or not asin.replace('_', '').isalnum():
                errors.append(f"Row {index+1}: Invalid ASIN format - {asin}")
                continue
            
            # Create parent ID
            parent_id = parent_item_name.upper().replace(" ", "_").replace("-", "_")
            
            # Add parent item if not exists
            if parent_id not in st.session_state.parent_items:
                st.session_state.parent_items[parent_id] = {
                    "name": parent_item_name,
                    "unit": "kg",
                    "category": category,
                    "reorder_level": reorder_level
                }
                # Initialize stock data
                st.session_state.stock_data[parent_id] = {
                    "loose_stock": 0,
                    "packed_stock": {},
                    "opening_stock": 0,
                    "last_updated": datetime.datetime.now().isoformat()
                }
            else:
                # Update reorder level for existing parent
                st.session_state.parent_items[parent_id]["reorder_level"] = reorder_level
            
            # Check if ASIN already exists
            asin_exists = False
            existing_parent = None
            for pid, variations in st.session_state.packet_variations.items():
                if asin in variations:
                    asin_exists = True
                    existing_parent = pid
                    break
            
            if asin_exists:
                # Update existing ASIN
                st.session_state.packet_variations[existing_parent][asin].update({
                    "weight": weight_kg,
                    "description": description or f"{weight_kg}kg {parent_item_name}",
                    "mrp": mrp,
                    "category": category,
                    "notes": notes
                })
                updated_count += 1
            else:
                # Add new ASIN
                if parent_id not in st.session_state.packet_variations:
                    st.session_state.packet_variations[parent_id] = {}
                
                st.session_state.packet_variations[parent_id][asin] = {
                    "weight": weight_kg,
                    "asin": asin,
                    "description": description or f"{weight_kg}kg {parent_item_name}",
                    "mrp": mrp,
                    "category": category,
                    "notes": notes
                }
                
                # Initialize packed stock
                st.session_state.stock_data[parent_id]["packed_stock"][asin] = 0
                imported_count += 1
            
        except Exception as e:
            errors.append(f"Row {index+1}: Error processing - {str(e)}")
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Save data
    save_data()
    
    # Show results
    st.success(f"🎉 **Upload Complete!**\n- ✅ New products imported: {imported_count}\n- 🔄 Products updated: {updated_count}")
    
    if errors:
        st.error(f"⚠️ **{len(errors)} errors encountered:**")
        with st.expander("View Errors"):
            for error in errors[:10]:  # Show first 10 errors
                st.error(error)
            if len(errors) > 10:
                st.warning(f"... and {len(errors) - 10} more errors")
    
    # Show import summary
    if imported_count > 0 or updated_count > 0:
        st.info(f"💾 Data has been saved automatically. You can now use these products in stock operations.")
        st.rerun()

def process_stock_updates(changes_df):
    """Process bulk stock updates from uploaded file"""
    updated_count = 0
    errors = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index, row in changes_df.iterrows():
        try:
            # Update progress
            progress = (index + 1) / len(changes_df)
            progress_bar.progress(progress)
            status_text.text(f"Processing stock update {index + 1} of {len(changes_df)}")
            
            # Extract fields
            asin = str(row.get('ASIN', '')).strip()
            new_stock = int(row.get('New_Stock', 0))
            update_reason = str(row.get('Update_Reason', 'Bulk stock update')).strip()
            current_stock = int(row.get('Current_Stock', 0)) if 'Current_Stock' in row else None
            
            # Validation
            if not asin:
                errors.append(f"Row {index+1}: Missing ASIN")
                continue
                
            if new_stock < 0:
                errors.append(f"Row {index+1}: Invalid stock value - {new_stock}")
                continue
            
            # Find the product
            found_product = False
            for parent_id, variations in st.session_state.packet_variations.items():
                if asin in variations:
                    found_product = True
                    
                    # Get current stock from system
                    actual_current_stock = st.session_state.stock_data.get(parent_id, {}).get("packed_stock", {}).get(asin, 0)
                    
                    # Update stock
                    if parent_id not in st.session_state.stock_data:
                        st.session_state.stock_data[parent_id] = {"loose_stock": 0, "packed_stock": {}}
                    if "packed_stock" not in st.session_state.stock_data[parent_id]:
                        st.session_state.stock_data[parent_id]["packed_stock"] = {}
                    
                    st.session_state.stock_data[parent_id]["packed_stock"][asin] = new_stock
                    st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
                    
                    # Record transaction
                    difference = new_stock - actual_current_stock
                    transaction_type = "Stock Adjustment (Bulk)"
                    notes = f"Bulk stock update | Reason: {update_reason} | Changed from {actual_current_stock} to {new_stock} units"
                    
                    record_transaction(
                        transaction_type=transaction_type,
                        parent_id=parent_id,
                        asin=asin,
                        quantity=difference,
                        weight=0,
                        notes=notes
                    )
                    
                    updated_count += 1
                    break
            
            if not found_product:
                errors.append(f"Row {index+1}: ASIN {asin} not found in product catalog")
                
        except Exception as e:
            errors.append(f"Row {index+1}: Error processing - {str(e)}")
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Save data
    save_data()
    
    # Show results
    st.success(f"🎉 **Stock Update Complete!**\n- ✅ Stock updated for {updated_count} products")
    
    if errors:
        st.error(f"⚠️ **{len(errors)} errors encountered:**")
        with st.expander("View Errors"):
            for error in errors[:10]:  # Show first 10 errors
                st.error(error)
            if len(errors) > 10:
                st.warning(f"... and {len(errors) - 10} more errors")
    
    # Show update summary
    if updated_count > 0:
        st.info(f"💾 Stock data has been saved automatically. Check Live Stock View to see updated inventory.")
        st.rerun()

def process_enhanced_stock_updates(changes_df):
    """Process enhanced bulk stock updates with parent loose and ASIN packed stock support"""
    updated_count = 0
    errors = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index, row in changes_df.iterrows():
        try:
            # Update progress
            progress = (index + 1) / len(changes_df)
            progress_bar.progress(progress)
            status_text.text(f"Processing stock update {index + 1} of {len(changes_df)}")
            
            # Extract fields
            update_type = str(row.get('Type', 'ASIN_PACKED')).strip()
            parent_id = str(row.get('Parent_ID', '')).strip()
            asin = str(row.get('ASIN', '')).strip()
            new_stock = float(row.get('New_Stock', 0))
            update_reason = str(row.get('Update_Reason', 'Bulk stock update')).strip()
            current_stock = float(row.get('Current_Stock', 0)) if 'Current_Stock' in row else None
            
            # Validation
            if not parent_id:
                errors.append(f"Row {index+1}: Missing Parent_ID")
                continue
                
            if new_stock < 0:
                errors.append(f"Row {index+1}: Invalid stock value - {new_stock}")
                continue
            
            # Process based on type
            if update_type == "PARENT_LOOSE":
                # Handle loose stock update
                if parent_id not in st.session_state.parent_items:
                    errors.append(f"Row {index+1}: Parent product {parent_id} not found")
                    continue
                
                # Get current loose stock
                actual_current_loose = st.session_state.stock_data.get(parent_id, {}).get("loose_stock", 0)
                
                # Update loose stock
                if parent_id not in st.session_state.stock_data:
                    st.session_state.stock_data[parent_id] = {"loose_stock": 0, "packed_stock": {}}
                
                st.session_state.stock_data[parent_id]["loose_stock"] = new_stock
                st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
                
                # Record transaction
                difference = new_stock - actual_current_loose
                transaction_type = "Loose Stock Adjustment (Bulk)"
                notes = f"Bulk loose stock update | Reason: {update_reason} | Changed from {actual_current_loose} to {new_stock} kg"
                
                record_transaction(
                    transaction_type=transaction_type,
                    parent_id=parent_id,
                    weight=difference,
                    notes=notes
                )
                
                updated_count += 1
                
            elif update_type == "ASIN_PACKED":
                # Handle ASIN-based packed stock update
                if not asin:
                    errors.append(f"Row {index+1}: Missing ASIN for packed stock update")
                    continue
                
                # Find the product
                found_product = False
                for pid, variations in st.session_state.packet_variations.items():
                    if asin in variations:
                        found_product = True
                        
                        # Get current stock from system
                        actual_current_stock = st.session_state.stock_data.get(pid, {}).get("packed_stock", {}).get(asin, 0)
                        
                        # Update stock
                        if pid not in st.session_state.stock_data:
                            st.session_state.stock_data[pid] = {"loose_stock": 0, "packed_stock": {}}
                        if "packed_stock" not in st.session_state.stock_data[pid]:
                            st.session_state.stock_data[pid]["packed_stock"] = {}
                        
                        st.session_state.stock_data[pid]["packed_stock"][asin] = int(new_stock)
                        st.session_state.stock_data[pid]["last_updated"] = datetime.datetime.now().isoformat()
                        
                        # Record transaction
                        difference = int(new_stock) - actual_current_stock
                        transaction_type = "Packed Stock Adjustment (Bulk)"
                        notes = f"Bulk packed stock update | Reason: {update_reason} | Changed from {actual_current_stock} to {int(new_stock)} units"
                        
                        record_transaction(
                            transaction_type=transaction_type,
                            parent_id=pid,
                            asin=asin,
                            quantity=difference,
                            notes=notes
                        )
                        
                        updated_count += 1
                        break
                
                if not found_product:
                    errors.append(f"Row {index+1}: ASIN {asin} not found in product catalog")
            
            else:
                errors.append(f"Row {index+1}: Unknown update type - {update_type}")
                
        except Exception as e:
            errors.append(f"Row {index+1}: Error processing - {str(e)}")
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Save data
    save_data()
    
    # Show results
    st.success(f"🎉 **Enhanced Stock Update Complete!**\n- ✅ Stock updated for {updated_count} items")
    
    if errors:
        st.error(f"⚠️ **{len(errors)} errors encountered:**")
        with st.expander("View Errors"):
            for error in errors[:10]:  # Show first 10 errors
                st.error(error)
            if len(errors) > 10:
                st.warning(f"... and {len(errors) - 10} more errors")
    
    # Show update summary
    if updated_count > 0:
        st.info(f"💾 Stock data has been saved automatically. Check Live Stock View to see updated inventory.")
        st.rerun()

def show_settings():
    """Settings and data management"""
    st.header("Settings")
    
    tab1, tab2, tab3 = st.tabs(["Data Management", "Export Data", "Undo Settings"])
    
    with tab1:
        st.subheader("Data Backup & Restore")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Export Data")
            if st.button("Create Backup"):
                backup_data = {
                    "stock_data": st.session_state.stock_data,
                    "transactions": st.session_state.transactions,
                    "parent_items": st.session_state.parent_items,
                    "packet_variations": st.session_state.packet_variations,
                    "backup_date": datetime.datetime.now().isoformat()
                }
                
                st.download_button(
                    label="Download Backup File",
                    data=json.dumps(backup_data, indent=2),
                    file_name=f"stock_tracker_backup_{datetime.date.today()}.json",
                    mime="application/json"
                )
        
        with col2:
            st.subheader("Import Data")
            uploaded_file = st.file_uploader("Upload Backup File", type=['json'])
            
            if uploaded_file is not None:
                try:
                    backup_data = json.load(uploaded_file)
                    
                    if st.button("Restore from Backup"):
                        st.session_state.stock_data = backup_data.get("stock_data", {})
                        st.session_state.transactions = backup_data.get("transactions", [])
                        st.session_state.parent_items = backup_data.get("parent_items", {})
                        st.session_state.packet_variations = backup_data.get("packet_variations", {})
                        save_data()
                        st.success("Data restored successfully!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error reading backup file: {e}")
    
    with tab2:
        st.subheader("Export Reports")
        
        if st.button("Export Current Stock"):
            stock_report = []
            for parent_id, stock in st.session_state.stock_data.items():
                stock_report.append({
                    "Product_ID": parent_id,
                    "Product_Name": st.session_state.parent_items[parent_id]["name"],
                    "Category": st.session_state.parent_items[parent_id].get("category", ""),
                    "Loose_Stock_kg": stock.get("loose_stock", 0),
                    "Last_Updated": stock.get("last_updated", "")
                })
                
                for asin, units in stock.get("packed_stock", {}).items():
                    if units > 0:
                        stock_report.append({
                            "Product_ID": parent_id,
                            "Product_Name": st.session_state.parent_items[parent_id]["name"],
                            "ASIN": asin,
                            "Description": st.session_state.packet_variations[parent_id][asin]["description"],
                            "Units_in_Stock": units,
                            "Weight_per_Unit": st.session_state.packet_variations[parent_id][asin]["weight"],
                            "Total_Weight_kg": units * st.session_state.packet_variations[parent_id][asin]["weight"]
                        })
            
            df_stock_report = pd.DataFrame(stock_report)
            st.download_button(
                label="Download Stock Report",
                data=df_stock_report.to_csv(index=False),
                file_name=f"stock_report_{datetime.date.today()}.csv",
                mime="text/csv"
            )
    
    with tab3:
        st.subheader("⚙️ Undo Settings")
        st.info("Configure how long transactions can be undone after recording")
        
        from config import DEFAULT_SETTINGS
        
        # Initialize settings in session state if not exists
        if "settings" not in st.session_state:
            st.session_state.settings = DEFAULT_SETTINGS.copy()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🕒 Undo Time Window")
            undo_hours = st.number_input(
                "Undo Window (Hours)",
                min_value=1,
                max_value=168,  # 1 week
                value=st.session_state.settings.get("undo_window_hours", 24),
                help="Number of hours after recording during which transactions can be undone"
            )
            
            st.info(f"Current setting: Transactions can be undone up to {undo_hours} hours after recording")
        
        with col2:
            st.subheader("📊 Recent Transactions Limit")
            max_recent = st.number_input(
                "Max Recent Transactions",
                min_value=10,
                max_value=200,
                value=st.session_state.settings.get("max_recent_transactions", 50),
                help="Maximum number of recent transactions that can be undone"
            )
            
            st.info(f"Current setting: Only the last {max_recent} transactions can be undone")
        
        # Save settings
        if st.button("💾 Save Undo Settings", type="primary"):
            st.session_state.settings["undo_window_hours"] = undo_hours
            st.session_state.settings["max_recent_transactions"] = max_recent
            
            # Update config file
            try:
                import os
                config_path = "config.py"
                if os.path.exists(config_path):
                    # Read current config
                    with open(config_path, 'r') as f:
                        config_content = f.read()
                    
                    # Update the DEFAULT_SETTINGS section
                    updated_config = config_content.replace(
                        f'"undo_window_hours": {DEFAULT_SETTINGS.get("undo_window_hours", 24)}',
                        f'"undo_window_hours": {undo_hours}'
                    ).replace(
                        f'"max_recent_transactions": {DEFAULT_SETTINGS.get("max_recent_transactions", 50)}',
                        f'"max_recent_transactions": {max_recent}'
                    )
                    
                    # Write updated config
                    with open(config_path, 'w') as f:
                        f.write(updated_config)
                    
                    st.success("✅ Settings saved successfully!")
                    st.info("💡 Settings will take effect for new transactions")
                else:
                    st.warning("Config file not found. Settings saved in session only.")
            except Exception as e:
                st.error(f"Error saving settings: {e}")
        
        # Current settings display
        st.subheader("📋 Current Settings Summary")
        st.write(f"**Undo Window:** {st.session_state.settings.get('undo_window_hours', 24)} hours")
        st.write(f"**Max Recent Transactions:** {st.session_state.settings.get('max_recent_transactions', 50)}")
        
        # Test current transactions
        if st.button("🧪 Test Current Transactions"):
            if st.session_state.transactions:
                recent_count = len(st.session_state.transactions[-max_recent:])
                st.write(f"**Recent transactions available for undo:** {recent_count}")
                
                # Show how many are within time window
                within_window = 0
                current_time = datetime.datetime.now()
                
                for t in st.session_state.transactions[-max_recent:]:
                    try:
                        recorded_time = datetime.datetime.fromisoformat(t["timestamp"])
                        time_diff = current_time - recorded_time
                        if time_diff.total_seconds() <= undo_hours * 60 * 60:
                            within_window += 1
                    except:
                        pass
                
                st.write(f"**Transactions within time window:** {within_window}")
                
                if within_window > 0:
                    st.success(f"✅ {within_window} transactions can be undone with current settings")
                else:
                    st.warning("⚠️ No recent transactions can be undone with current settings")
            else:
                st.info("No transactions found to test")

def show_returns():
    """Returns management"""
    st.header("Returns Management")
    
    # Create tabs for different return functionalities
    tab1, tab2, tab3 = st.tabs(["📥 Return Entry", "🔄 Transfer Good Returns", "📊 Returns Live View"])
    
    with tab1:
        st.subheader("📥 Return Entry")
        
        # Step 1: Select Parent Product (like packing operations)
        parent_id = st.selectbox(
            "Select Product Category",
            options=list(st.session_state.parent_items.keys()),
            format_func=lambda x: st.session_state.parent_items[x]["name"],
            key="return_parent_select"
        )
        
        if parent_id:
            # Step 2: Select what to return - loose stock or specific weight variation
            return_options = []
            
            # Add loose return option
            parent_name = st.session_state.parent_items[parent_id]["name"]
            parent_unit = st.session_state.parent_items[parent_id].get("unit", "kg")
            
            return_options.append({
                "type": "loose",
                "display": f"🌾 Loose Return ({parent_name})",
                "unit": parent_unit,
                "parent_id": parent_id
            })
            
            # Add weight variations
            if parent_id in st.session_state.packet_variations:
                for asin, details in st.session_state.packet_variations[parent_id].items():
                    weight = details.get('weight', 1.0)
                    description = details.get('description', f"{weight}kg {parent_name}")
                    
                    # Clean up description
                    if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                        description = f"{weight}kg {parent_name}"
                    
                    return_options.append({
                        "type": "packed",
                        "display": f"📦 {description} ({weight}kg)",
                        "unit": "units",
                        "asin": asin,
                        "parent_id": parent_id,
                        "weight": weight
                    })
            
            # Display options
            selected_option = st.selectbox(
                "Select what to return:",
                options=return_options,
                format_func=lambda x: x['display'],
                key="return_option_select"
            )
            
            if selected_option:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Return source
                    return_source = st.selectbox(
                        "Return Source:",
                        ["Easy Ship", "FBA Sales"],
                        key="return_source_select"
                    )
                    
                    # Return condition
                    return_condition = st.selectbox(
                        "Return Condition:",
                        ["Good", "Bad"],
                        key="return_condition_select"
                    )
                
                with col2:
                    # Return quantity
                    if selected_option['type'] == 'loose':
                        return_quantity = st.number_input(
                            f"Return Quantity ({selected_option['unit']}):",
                            min_value=0.0,
                            value=0.0,
                            step=0.1,
                            key="return_quantity_input"
                        )
                    else:
                        return_quantity = st.number_input(
                            f"Return Quantity ({selected_option['unit']}):",
                            min_value=0,
                            value=0,
                            step=1,
                            key="return_quantity_input"
                        )
                
                # Return reason
                return_reason = st.text_area(
                    "Return Reason:",
                    placeholder="e.g., Customer return, Damaged in transit, Quality issue, etc.",
                    key="return_reason_input"
                )
                
                # Process return button
                if st.button("📥 Process Return", type="primary", use_container_width=True):
                    if return_quantity > 0 and return_reason.strip():
                        # Ensure return data structure exists
                        if parent_id not in st.session_state.return_data:
                            st.session_state.return_data[parent_id] = {
                                "loose_return": {"good": 0, "bad": 0},
                                "packed_return": {}
                            }
                        
                        if selected_option['type'] == 'loose':
                            # Process loose return
                            condition_key = return_condition.lower()
                            st.session_state.return_data[parent_id]["loose_return"][condition_key] += return_quantity
                            
                            # Record return transaction
                            return_transaction = {
                                "id": f"RET-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                "timestamp": datetime.datetime.now().isoformat(),
                                "type": "RETURN_LOOSE",
                                "parent_id": parent_id,
                                "quantity": return_quantity,
                                "unit": selected_option['unit'],
                                "source": return_source,
                                "condition": return_condition,
                                "reason": return_reason,
                                "product_name": parent_name
                            }
                            
                        else:
                            # Process packed return
                            asin = selected_option['asin']
                            if asin not in st.session_state.return_data[parent_id]["packed_return"]:
                                st.session_state.return_data[parent_id]["packed_return"][asin] = {"good": 0, "bad": 0}
                            
                            condition_key = return_condition.lower()
                            st.session_state.return_data[parent_id]["packed_return"][asin][condition_key] += return_quantity
                            
                            # Record return transaction
                            return_transaction = {
                                "id": f"RET-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                "timestamp": datetime.datetime.now().isoformat(),
                                "type": "RETURN_PACKED",
                                "parent_id": parent_id,
                                "asin": asin,
                                "quantity": return_quantity,
                                "unit": selected_option['unit'],
                                "source": return_source,
                                "condition": return_condition,
                                "reason": return_reason,
                                "product_name": selected_option['display']
                            }
                        
                        # Add to return transactions
                        st.session_state.return_transactions.append(return_transaction)
                        
                        save_data()
                        st.success(f"✅ Return processed successfully! {return_quantity} {selected_option['unit']} of {selected_option['display']} returned as {return_condition.lower()} from {return_source}")
                        st.rerun()
                    else:
                        if return_quantity <= 0:
                            st.error("Please enter a valid return quantity.")
                        if not return_reason.strip():
                            st.error("Please provide a reason for the return.")
        else:
            st.info("Please select a product category to process returns.")
    
    with tab2:
        st.subheader("🔄 Transfer Good Returns to Main Stock")
        
        # Show available good returns
        good_returns = []
        for parent_id, return_data in st.session_state.return_data.items():
            parent_name = st.session_state.parent_items.get(parent_id, {}).get("name", parent_id)
            parent_unit = st.session_state.parent_items.get(parent_id, {}).get("unit", "kg")
            
            # Loose good returns
            loose_good = return_data.get("loose_return", {}).get("good", 0)
            if loose_good > 0:
                good_returns.append({
                    "type": "loose",
                    "parent_id": parent_id,
                    "display": f"🌾 {parent_name} (Loose)",
                    "quantity": loose_good,
                    "unit": parent_unit
                })
            
            # Packed good returns
            for asin, return_stock in return_data.get("packed_return", {}).items():
                packed_good = return_stock.get("good", 0)
                if packed_good > 0:
                    asin_details = st.session_state.packet_variations.get(parent_id, {}).get(asin, {})
                    weight = asin_details.get('weight', 1.0)
                    description = asin_details.get('description', f"{weight}kg {parent_name}")
                    
                    if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                        description = f"{weight}kg {parent_name}"
                    
                    good_returns.append({
                        "type": "packed",
                        "parent_id": parent_id,
                        "asin": asin,
                        "display": f"📦 {description}",
                        "quantity": packed_good,
                        "unit": "units"
                    })
        
        if good_returns:
            st.write(f"**Available Good Returns:** {len(good_returns)} items")
            
            # Show good returns summary
            for item in good_returns:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{item['display']}**")
                with col2:
                    st.write(f"{item['quantity']} {item['unit']}")
                with col3:
                    transfer_key = f"transfer_{item['parent_id']}_{item.get('asin', 'loose')}"
                    if st.button("🔄 Transfer", key=transfer_key):
                        # Transfer good return to main stock
                        if item['type'] == 'loose':
                            # Transfer loose return to main loose stock
                            st.session_state.stock_data[item['parent_id']]["loose_stock"] += item['quantity']
                            st.session_state.return_data[item['parent_id']]["loose_return"]["good"] = 0
                            
                            # Record transfer transaction
                            record_transaction(
                                transaction_type="RETURN_TRANSFER_LOOSE",
                                parent_id=item['parent_id'],
                                weight=item['quantity'],
                                notes=f"Transferred good return to main stock: {item['quantity']} {item['unit']} of {item['display']}",
                                transaction_date=datetime.datetime.now()
                            )
                            
                        else:
                            # Transfer packed return to main packed stock
                            if "packed_stock" not in st.session_state.stock_data[item['parent_id']]:
                                st.session_state.stock_data[item['parent_id']]["packed_stock"] = {}
                            if item['asin'] not in st.session_state.stock_data[item['parent_id']]["packed_stock"]:
                                st.session_state.stock_data[item['parent_id']]["packed_stock"][item['asin']] = 0
                            
                            st.session_state.stock_data[item['parent_id']]["packed_stock"][item['asin']] += item['quantity']
                            st.session_state.return_data[item['parent_id']]["packed_return"][item['asin']]["good"] = 0
                            
                            # Record transfer transaction
                            record_transaction(
                                transaction_type="RETURN_TRANSFER_PACKED",
                                parent_id=item['parent_id'],
                                asin=item['asin'],
                                quantity=item['quantity'],
                                notes=f"Transferred good return to main stock: {item['quantity']} {item['unit']} of {item['display']}",
                                transaction_date=datetime.datetime.now()
                            )
                        
                        save_data()
                        st.success(f"✅ Transferred {item['quantity']} {item['unit']} of {item['display']} to main stock!")
                        st.rerun()
        else:
            st.info("No good returns available for transfer.")
    
    with tab3:
        st.subheader("📊 Returns Live View")
        
        # Calculate return metrics
        total_good_returns = 0
        total_bad_returns = 0
        return_summary = []
        
        for parent_id, return_data in st.session_state.return_data.items():
            parent_name = st.session_state.parent_items.get(parent_id, {}).get("name", parent_id)
            parent_unit = st.session_state.parent_items.get(parent_id, {}).get("unit", "kg")
            
            # Process loose returns
            loose_good = return_data.get("loose_return", {}).get("good", 0)
            loose_bad = return_data.get("loose_return", {}).get("bad", 0)
            
            if loose_good > 0 or loose_bad > 0:
                return_summary.append({
                    "Product": f"{parent_name} (Loose)",
                    "Good Returns": f"{loose_good} {parent_unit}",
                    "Bad Returns": f"{loose_bad} {parent_unit}",
                    "Total Returns": f"{loose_good + loose_bad} {parent_unit}"
                })
            
            # Process packed returns
            for asin, return_stock in return_data.get("packed_return", {}).items():
                packed_good = return_stock.get("good", 0)
                packed_bad = return_stock.get("bad", 0)
                
                if packed_good > 0 or packed_bad > 0:
                    asin_details = st.session_state.packet_variations.get(parent_id, {}).get(asin, {})
                    weight = asin_details.get('weight', 1.0)
                    description = asin_details.get('description', f"{weight}kg {parent_name}")
                    
                    if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                        description = f"{weight}kg {parent_name}"
                    
                    return_summary.append({
                        "Product": description,
                        "Good Returns": f"{packed_good} units",
                        "Bad Returns": f"{packed_bad} units",
                        "Total Returns": f"{packed_good + packed_bad} units"
                    })
                    
                    total_good_returns += packed_good
                    total_bad_returns += packed_bad
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Good Returns", total_good_returns)
        with col2:
            st.metric("Total Bad Returns", total_bad_returns)
        with col3:
            st.metric("Total Returns", total_good_returns + total_bad_returns)
        
        # Display return summary table
        if return_summary:
            st.subheader("📋 Return Stock Summary")
            return_df = pd.DataFrame(return_summary)
            st.dataframe(return_df, use_container_width=True)
        else:
            st.info("No return stock available.")
        
        # Show recent return transactions
        st.subheader("📝 Recent Return Transactions")
        if st.session_state.return_transactions:
            recent_returns = st.session_state.return_transactions[-10:]  # Last 10 transactions
            
            transaction_data = []
            for trans in reversed(recent_returns):
                transaction_data.append({
                    "Date": trans.get("timestamp", "").split("T")[0],
                    "Time": trans.get("timestamp", "").split("T")[1][:8] if "T" in trans.get("timestamp", "") else "",
                    "Product": trans.get("product_name", ""),
                    "Quantity": f"{trans.get('quantity', 0)} {trans.get('unit', '')}",
                    "Source": trans.get("source", ""),
                    "Condition": trans.get("condition", ""),
                    "Reason": trans.get("reason", "")[:50] + "..." if len(trans.get("reason", "")) > 50 else trans.get("reason", "")
                })
            
            if transaction_data:
                trans_df = pd.DataFrame(transaction_data)
                st.dataframe(trans_df, use_container_width=True)
        else:
            st.info("No return transactions recorded yet.")

if __name__ == "__main__":
    main()

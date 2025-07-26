# Stock Tracker Configuration
APP_CONFIG = {
    "app_name": "Mithila Foods Stock Tracker",
    "version": "1.0.0",
    "author": "Stock Management System",
    "description": "Comprehensive stock tracking system for Mithila Foods"
}

# Default settings
DEFAULT_SETTINGS = {
    "auto_save": True,
    "backup_frequency": "daily",  # daily, weekly, manual
    "data_retention_days": 365,
    "sync_to_sheets": False,
    "default_currency": "INR",
    "date_format": "%Y-%m-%d",
    "time_format": "%H:%M:%S",
    "undo_window_hours": 24,  # Hours within which transactions can be undone
    "max_recent_transactions": 50  # Maximum number of recent transactions to allow undo
}

# Sample product categories
PRODUCT_CATEGORIES = [
    "Rice",
    "Flour", 
    "Pulses",
    "Spices",
    "Oil",
    "Cereals",
    "Dry Fruits",
    "Condiments",
    "Ready to Cook",
    "Organic Products"
]

# Sample units
UNITS = [
    "kg",
    "gm", 
    "ltr",
    "ml",
    "pcs",
    "packets"
]

# Transaction types
TRANSACTION_TYPES = [
    "Stock Inward",
    "Packing",
    "FBA Sale",
    "FBA Sale (Bulk)",
    "Easy Ship Sale",
    "Easy Ship Sale (Bulk)",
    "Stock Adjustment",
    "Damage/Loss",
    "Return"
]

# Excel column mappings for imports
EXCEL_COLUMN_MAPPINGS = {
    "fba_sales": {
        "asin": ["ASIN", "asin", "Asin"],
        "quantity": ["Shipped", "shipped", "Quantity", "quantity", "Qty", "qty"],
        "date": ["Date", "date", "Sale Date", "Order Date"],
        "order_id": ["Order ID", "order_id", "OrderID"]
    },
    "easy_ship_sales": {
        "asin": ["asin", "ASIN", "Asin"],
        "quantity": ["quantity-purchased", "quantity_purchased", "Quantity", "quantity", "Qty", "qty"],
        "date": ["purchase-date", "purchase_date", "Date", "date", "Sale Date", "Order Date"],
        "order_id": ["order-id", "order_id", "Order ID", "OrderID"]
    },
    "products": {
        "product_id": ["Product_ID", "product_id", "ProductID", "ID"],
        "product_name": ["Product_Name", "product_name", "Name", "Product Name"],
        "category": ["Category", "category"],
        "unit": ["Unit", "unit"],
        "asin": ["ASIN", "asin"],
        "weight": ["Weight", "weight", "Weight_per_packet", "Weight per packet"],
        "description": ["Description", "description", "Desc"],
        "mrp": ["MRP", "mrp", "Price"]
    }
}

# Google Sheets configuration
GOOGLE_SHEETS_CONFIG = {
    "scopes": [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ],
    "credentials_file": "credentials.json",
    "default_spreadsheet_name": "Mithila_Foods_Stock_Tracker"
}

# Dashboard colors
DASHBOARD_COLORS = {
    "primary": "#007bff",
    "success": "#28a745", 
    "warning": "#ffc107",
    "danger": "#dc3545",
    "info": "#17a2b8",
    "secondary": "#6c757d"
}

# File paths
FILE_PATHS = {
    "data_file": "stock_data.json",
    "backup_folder": "backups",
    "uploads_folder": "uploads",
    "exports_folder": "exports"
}

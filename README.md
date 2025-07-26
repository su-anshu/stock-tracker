# 📦 Mithila Foods Stock Tracker

A comprehensive stock tracking system built with Streamlit for managing inventory, packing operations, and sales data.

## 🚀 Features

### Core Functionality
- **Stock Inward Management**: Record incoming stock in loose form (kgs)
- **Packing Operations**: Convert loose stock to packaged products with ASIN tracking
- **FBA Sales Tracking**: Record Amazon FBA sales with automatic stock deduction
- **Easy Ship Sales**: Track Easy Ship sales with inventory updates
- **Real-time Dashboard**: Live stock overview with charts and metrics
- **Google Sheets Integration**: Automatic sync with Google Sheets for backup and reporting

### Advanced Features
- **Multi-product Support**: Manage multiple parent products with weight-based packet variations
- **ASIN-based Tracking**: Track each product variation by Amazon ASIN
- **Transaction History**: Complete audit trail of all stock movements
- **Bulk Data Import**: Excel/CSV upload for sales data and product catalogs
- **Data Export**: Export reports and backups in various formats
- **Responsive Dashboard**: Visual charts and real-time stock status

## 📁 Project Structure

```
stock_tracker/
├── app.py                 # Main Streamlit application
├── google_sheets.py       # Google Sheets integration module
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── start_app.bat         # Windows startup script
├── stock_data.json       # Data storage file (auto-created)
├── credentials.json      # Google Sheets credentials (you need to add this)
└── README.md            # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Internet connection for Google Sheets integration

### Quick Start (Windows)
1. **Clone or download** this project to your desired location
2. **Double-click** `start_app.bat` to automatically:
   - Create virtual environment
   - Install dependencies
   - Start the application
3. **Open your browser** to `http://localhost:8501`

### Manual Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## 🔗 Google Sheets Integration Setup

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Sheets API
   - Google Drive API

### Step 2: Create Service Account
1. Go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Fill in the details and create
4. Click on the created service account
5. Go to "Keys" tab
6. Click "Add Key" > "Create New Key"
7. Select "JSON" format and download

### Step 3: Setup Credentials
1. Rename the downloaded file to `credentials.json`
2. Place it in the `stock_tracker` folder
3. The app will automatically detect and use these credentials

### Step 4: Share Spreadsheet (Optional)
If you want to access the spreadsheet from multiple accounts:
1. Open the created spreadsheet in Google Sheets
2. Click "Share" button
3. Add email addresses with appropriate permissions

## 📊 Using the Application

### 1. Dashboard
- **Overview**: Quick metrics of total stock, packed items, and products
- **Charts**: Visual representation of stock by category and top products
- **Recent Transactions**: Latest stock movements

### 2. Stock Inward
- Add new stock in loose form (kgs)
- Select product and enter weight
- Automatic transaction recording

### 3. Packing Operations
- Convert loose stock to packaged products
- Select product and ASIN variation
- System calculates maximum possible packets
- Automatic stock adjustment

### 4. Sales Recording

#### FBA Sales
- **Manual Entry**: Individual sale recording
- **Bulk Upload**: Excel file import for multiple sales
- Automatic stock deduction
- Transaction history tracking

#### Easy Ship Sales
- Similar to FBA sales
- Separate tracking for easy identification
- Bulk upload supported

### 5. Products Management
- **Add Products**: Create new parent products
- **Add ASINs**: Define packet variations with weights and descriptions
- **Import Data**: Bulk import from Excel/CSV
- **Template Download**: Get pre-formatted template

### 6. Settings & Data Management
- **Backup/Restore**: Export and import complete data
- **Reports Export**: Generate stock and transaction reports
- **Google Sheets Sync**: One-click synchronization
- **Data Reset**: Clear transactions or reset everything

## 📋 Data Formats

### Product Import Format
```csv
Product_ID,Product_Name,Category,Unit,ASIN,Weight_per_packet,Description,MRP
RICE_BASMATI,Premium Basmati Rice,Rice,kg,B07EXAMPLE1,1,1kg Premium Pack,120
RICE_BASMATI,Premium Basmati Rice,Rice,kg,B07EXAMPLE2,5,5kg Family Pack,580
```

### Sales Data Format
```csv
ASIN,Quantity,Date,Order_ID
B07EXAMPLE1,5,2024-01-15,AMZ-123456
B07EXAMPLE2,2,2024-01-15,AMZ-123457
```

## 🔧 Configuration

### Customizing Categories
Edit `config.py` to modify product categories:
```python
PRODUCT_CATEGORIES = [
    "Rice", "Flour", "Pulses", "Spices", "Oil"
    # Add your categories here
]
```

### Excel Column Mapping
Update column mappings in `config.py` for your specific Excel formats:
```python
EXCEL_COLUMN_MAPPINGS = {
    "fba_sales": {
        "asin": ["ASIN", "asin", "Product_Code"],
        "quantity": ["Quantity", "Qty", "Units_Sold"]
    }
}
```

## 📊 Google Sheets Output

The system creates the following sheets:
- **Current_Stock**: Real-time stock levels
- **Packed_Stock_Details**: Detailed ASIN-wise inventory
- **Transactions**: Complete transaction history
- **Products_Master**: Product catalog with ASINs
- **Summary_Dashboard**: Key metrics and overview

## 🚨 Troubleshooting

### Common Issues

**1. Google Sheets Connection Failed**
- Verify `credentials.json` is in the correct location
- Ensure Google Sheets and Drive APIs are enabled
- Check service account permissions

**2. Excel Import Errors**
- Verify column names match expected format
- Check for empty rows or invalid data
- Use the provided template for reference

**3. Stock Calculation Issues**
- Verify weight values are numeric
- Check ASIN mappings are correct
- Ensure parent products exist before adding variations

**4. Application Won't Start**
- Check Python installation
- Verify all requirements are installed
- Run `pip install -r requirements.txt`

### Getting Help
1. Check the error messages in the application
2. Verify your data formats match the expected structure
3. Test with small datasets first
4. Check the browser console for additional error details

## 📈 Best Practices

### Data Entry
- Use consistent naming conventions for products
- Keep ASIN formats standardized
- Regular backups before bulk operations
- Verify weights and quantities before confirming

### Stock Management
- Record stock inward immediately upon receipt
- Pack products in regular intervals
- Update sales data daily
- Monitor stock levels regularly

### Backup Strategy
- Daily Google Sheets sync
- Weekly full data exports
- Keep multiple backup versions
- Test restore procedures

## 🔄 Updates and Maintenance

### Adding New Products
1. Go to "Products Management" tab
2. Add parent product first
3. Then add ASIN variations
4. Set appropriate weights and descriptions

### Modifying Existing Data
- Use the dashboard to monitor changes
- Export data before major modifications
- Update Google Sheets after changes
- Verify calculations after updates

## 📞 Support

For technical support or feature requests:
- Check the troubleshooting section above
- Review the configuration options
- Test with sample data first
- Document any errors with screenshots

## 🎯 Future Enhancements

Planned features:
- **Mobile App**: React Native mobile application
- **Barcode Integration**: Barcode scanning for quick data entry
- **Inventory Alerts**: Low stock notifications
- **Advanced Analytics**: Predictive analytics and forecasting
- **Multi-warehouse**: Support for multiple storage locations
- **API Integration**: Direct Amazon Seller Central integration

## 📄 License

This project is created for Mithila Foods internal use. All rights reserved.

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**Compatibility**: Python 3.8+, Windows/macOS/Linux
#   s t o c k - t r a c k e r  
 
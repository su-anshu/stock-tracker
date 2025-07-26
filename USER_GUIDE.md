# 📋 Complete User Guide - Mithila Foods Stock Tracker

## 🎯 Getting Started Walkthrough

### Step 1: First Launch
1. Double-click `start_app.bat`
2. Wait for the browser to open automatically
3. You'll see the Stock Tracker dashboard

### Step 2: Initial Setup
The app comes with sample data. To add your real products:

#### A. Add Parent Products
1. Go to **"Products Management"** in the sidebar
2. Click **"Parent Products"** tab
3. Fill the form:
   - **Product ID**: RICE_BASMATI_PREMIUM (unique identifier)
   - **Product Name**: Premium Basmati Rice
   - **Unit**: kg
   - **Category**: Rice
4. Click **"Add Product"**

#### B. Add ASIN Variations
1. Switch to **"ASIN Variations"** tab
2. Fill the form:
   - **Parent Product**: Select the product you just added
   - **ASIN**: B07ABC123XYZ (your actual Amazon ASIN)
   - **Weight per packet**: 1.0 (kg)
   - **Description**: 1kg Premium Basmati Pack
   - **MRP**: 120 (price)
3. Click **"Add ASIN"**

### Step 3: Daily Operations

#### Morning: Stock Inward
1. Go to **"Stock Inward"**
2. Select product: Premium Basmati Rice
3. Enter weight: 100 kg (example)
4. Add notes: "Received from supplier XYZ"
5. Click **"Add Stock"**

#### Afternoon: Packing
1. Go to **"Packing Operations"**
2. Select product: Premium Basmati Rice
3. Select ASIN: B07ABC123XYZ (1kg pack)
4. System shows: "Available: 100kg, Max packets: 100"
5. Enter packets to pack: 50
6. Click **"Pack Products"**

#### Evening: Sales Recording
1. Go to **"FBA Sales"** or **"Easy Ship Sales"**
2. Select ASIN: B07ABC123XYZ
3. Enter quantity sold: 10
4. Select date: Today
5. Click **"Record Sale"**

#### End of Day: Dashboard Review
1. Go to **"Dashboard"**
2. Check current stock levels
3. Review recent transactions
4. Export reports if needed

## 📊 Dashboard Explained

### Quick Metrics Cards
- **Total Loose Stock**: Raw materials in kg
- **Total Packed Items**: Ready-to-ship packets
- **Product Categories**: Number of product types
- **Total ASINs**: Number of variations

### Stock Overview Table
- **Product**: Product name
- **Category**: Product category
- **Loose Stock**: Raw materials remaining
- **Packed Units**: Number of packets ready
- **Packed Weight**: Weight of packed goods
- **Total Stock**: Combined loose + packed weight

### Recent Transactions
Shows last 10 activities with timestamps, types, and details.

## 🔄 Common Workflows

### Workflow 1: New Product Launch
```
1. Products Management → Add parent product
2. Products Management → Add ASIN variations (1kg, 5kg, 10kg)
3. Stock Inward → Add initial loose stock
4. Packing Operations → Create initial packet inventory
5. Dashboard → Verify setup
```

### Workflow 2: Daily Operations
```
Morning:   Stock Inward → Record new arrivals
Midday:    Packing Operations → Convert loose to packets
Afternoon: FBA/Easy Ship Sales → Record sales
Evening:   Dashboard → Review status
```

### Workflow 3: Weekly Reporting
```
1. Dashboard → Check overall status
2. Settings → Export Data → Generate reports
3. Review low stock items
4. Plan next week's procurement
```

## 🛠️ Advanced Features

### Bulk Sales Import
1. Go to FBA/Easy Ship Sales
2. Click **"Bulk Upload"**
3. Upload Excel file with columns:
   - ASIN
   - Quantity
   - Date
   - Order_ID (optional)
4. Click **"Process Data"**

### Data Backup
1. Go to **"Settings"**
2. Click **"Create Backup"**
3. Download the JSON file
4. Store safely for recovery

### Google Sheets Sync
1. Get Google Cloud credentials (see README.md)
2. Upload credentials.json
3. Settings → Google Sheets → Sync
4. Access live data in Google Sheets

## 🚨 Troubleshooting Guide

### Problem: Stock showing zero after packing
**Solution**: Check if ASIN was properly added to the product

### Problem: Can't add sales - insufficient stock
**Solution**: 
1. Check packed stock for that ASIN
2. Run packing operation if needed
3. Verify ASIN matches exactly

### Problem: Dashboard not updating
**Solution**: Refresh the page (F5) or restart the app

### Problem: Data disappeared
**Solution**: 
1. Check if stock_data.json exists
2. Restore from backup if available
3. Contact support with error details

## 💡 Pro Tips

### Efficiency Tips
- Use bulk upload for daily sales data
- Set up Google Sheets sync for team access
- Create regular backups (weekly recommended)
- Use consistent naming conventions

### Data Entry Best Practices
- Always add parent product before ASINs
- Use clear, descriptive ASIN descriptions
- Include weight units in descriptions
- Add notes for unusual transactions

### Inventory Management
- Monitor dashboard daily
- Set up alerts for low stock (manual for now)
- Regular audit of physical vs system stock
- Plan packing based on sales velocity

## 📈 Scaling Your Operations

### For Growing Business
1. **Add More Categories**: Spices, Oils, Dry Fruits
2. **Multiple Warehouses**: Use notes field for location
3. **Seasonal Products**: Track seasonal items separately
4. **Team Access**: Share Google Sheets for collaboration

### Integration Opportunities
- Connect with accounting software
- Integrate with Amazon Seller Central API
- Add barcode scanning capability
- Implement automated reorder points

## 🎓 Training Your Team

### For Data Entry Staff
1. Show Stock Inward process
2. Demonstrate Packing Operations
3. Practice Sales Recording
4. Explain error handling

### For Management
1. Dashboard interpretation
2. Report generation
3. Data backup procedures
4. Performance monitoring

### For IT Support
1. Application startup/shutdown
2. Backup and restore procedures
3. Basic troubleshooting
4. Google Sheets integration

## 📞 Support Resources

### Built-in Help
- README.md: Technical documentation
- QUICK_START.md: Fast setup guide
- test_simple.py: Diagnostic tool

### Self-Service
- Check SETUP_COMPLETE.md for common issues
- Review transaction history for data verification
- Use export features for external analysis

---

**Remember**: This system grows with your business. Start simple, add complexity as needed!

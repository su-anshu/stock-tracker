import streamlit as st
import pandas as pd
import datetime

def show_fba_sales():
    """FBA Sales entry with Excel upload support"""
    st.header("FBA Sales")
    
    tab1, tab2 = st.tabs(["📁 Bulk Upload", "📝 Manual Entry"])
    
    with tab1:
        st.subheader("Upload FBA Sales Data")
        st.info("📋 Upload your FBA sales Excel file. The system will read ASIN and Shipped columns.")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose your FBA Sales Excel file", 
            type=['xlsx', 'xls'],
            help="Excel file should contain 'ASIN' and 'Shipped' columns"
        )
        
        if uploaded_file is not None:
            try:
                # Read the Excel file
                df = pd.read_excel(uploaded_file)
                
                st.write("📊 **Preview of uploaded data:**")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Check required columns
                required_cols = ['ASIN', 'Shipped']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"❌ Missing required columns: {missing_cols}")
                    st.write("**Available columns:** ", list(df.columns))
                else:
                    st.success("✅ Required columns found: ASIN, Shipped")
                    
                    # Show summary
                    valid_data = df[df['Shipped'] > 0]
                    st.write(f"**📈 Summary:**")
                    st.write(f"- Total rows: {len(df)}")
                    st.write(f"- Rows with sales (Shipped > 0): {len(valid_data)}")
                    st.write(f"- Total units shipped: {valid_data['Shipped'].sum()}")
                    st.write(f"- Unique ASINs: {valid_data['ASIN'].nunique()}")
                    
                    # Process button
                    if st.button("🚀 Process FBA Sales Data", type="primary"):
                        process_fba_sales_excel(df)
                        
            except Exception as e:
                st.error(f"❌ Error reading Excel file: {str(e)}")
                st.write("Please ensure your file is a valid Excel format (.xlsx or .xls)")
    
    with tab2:
        st.subheader("Manual FBA Sale Entry")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.form("fba_sales_form"):
                # Get all ASINs for selection
                all_asins = []
                for parent_id, variations in st.session_state.packet_variations.items():
                    for asin, details in variations.items():
                        # Clean up description - handle NaN values
                        description = details.get('description', '')
                        if not description or str(description).lower() in ['nan', 'null', 'none', '']:
                            weight = details.get('weight', 1.0)
                            parent_name = st.session_state.parent_items[parent_id]['name']
                            description = f"{weight}kg {parent_name}"
                        
                        all_asins.append({
                            "asin": asin,
                            "display": f"{description} - {st.session_state.parent_items[parent_id]['name']}",
                            "parent_id": parent_id
                        })
                
                if all_asins:
                    selected_asin_data = st.selectbox(
                        "Select Product (ASIN)",
                        options=all_asins,
                        format_func=lambda x: x["display"]
                    )
                    
                    quantity_sold = st.number_input("Quantity Sold", min_value=1, step=1)
                    sale_date = st.date_input("Sale Date", value=datetime.date.today())
                    notes = st.text_area("Notes (optional)")
                    
                    submitted = st.form_submit_button("Record FBA Sale")
                    
                    if submitted:
                        asin = selected_asin_data["asin"]
                        parent_id = selected_asin_data["parent_id"]
                        
                        available_stock = st.session_state.stock_data.get(parent_id, {}).get("packed_stock", {}).get(asin, 0)
                        
                        if available_stock >= quantity_sold:
                            st.session_state.stock_data[parent_id]["packed_stock"][asin] -= quantity_sold
                            st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
                            
                            # Debug info
                            st.write(f"🔍 DEBUG: Selected sale date: {sale_date}")
                            st.write(f"🔍 DEBUG: Type of sale_date: {type(sale_date)}")
                            
                            weight_sold = quantity_sold * st.session_state.packet_variations[parent_id][asin]["weight"]
                            transaction_id = record_transaction(
                                transaction_type="FBA Sale", 
                                parent_id=parent_id, 
                                asin=asin, 
                                quantity=quantity_sold, 
                                weight=weight_sold, 
                                notes=notes, 
                                batch_id=None, 
                                transaction_date=sale_date
                            )
                            
                            # Store transaction details for undo outside form
                            st.session_state.last_transaction = {
                                "id": transaction_id,
                                "summary": f"FBA sale: {quantity_sold} units of {selected_asin_data['display']}",
                                "show_undo": True
                            }
                            # Don't call st.rerun() immediately - let the undo show first
                        else:
                            st.error(f"Insufficient stock! Available: {available_stock}, Requested: {quantity_sold}")
                else:
                    st.warning("⚠️ No products/ASINs available. Please add products first in Products Management.")
        
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
                if st.button("🔄 Undo Sale", key="undo_last_fba_sale"):
                    st.write("🔍 Attempting undo...")
                    success = undo_transaction(transaction_info['id'])
                    if success:
                        st.session_state.last_transaction['show_undo'] = False
                        st.write("✅ Undo successful! Refreshing...")
                        st.rerun()
                    else:
                        st.write("❌ Undo failed!")
            
            with col2:
                if st.button("✅ Keep Sale", key="keep_fba_sale"):
                    st.session_state.last_transaction['show_undo'] = False
                    st.rerun()
        
        with col2:
            st.subheader("Recent FBA Sales")
            fba_transactions = [t for t in st.session_state.transactions if "FBA Sale" in t.get("type", "")]
            if fba_transactions:
                recent_fba = pd.DataFrame(fba_transactions[-5:])
                st.dataframe(recent_fba[['date', 'parent_name', 'asin', 'quantity']], use_container_width=True)
            else:
                st.info("No FBA sales recorded yet.")
            
            # Add Recent Transactions Panel for bulk undo
            st.markdown("---")
            st.subheader("📋 Recent Transactions (Today)")
            
            # Get today's transactions
            today = datetime.date.today().isoformat()
            today_transactions = [t for t in st.session_state.transactions if t.get("date") == today and "FBA Sale" in t.get("type", "")]
            
            if today_transactions:
                # Group by batch_id for bulk operations
                batches = {}
                individual_transactions = []
                
                for transaction in today_transactions[-10:]:  # Show last 10
                    batch_id = transaction.get("batch_id")
                    if batch_id:
                        if batch_id not in batches:
                            batches[batch_id] = []
                        batches[batch_id].append(transaction)
                    else:
                        individual_transactions.append(transaction)
                
                # Display batches
                for batch_id, batch_transactions in batches.items():
                    batch_time = datetime.datetime.fromisoformat(batch_transactions[0]["timestamp"]).strftime("%H:%M")
                    with st.expander(f"📦 {batch_time} - FBA Bulk Upload ({len(batch_transactions)} sales)", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Batch ID:** `{batch_id}`")
                            st.write(f"**Total Sales:** {len(batch_transactions)}")
                        with col2:
                            can_undo, reason = can_undo_batch(batch_id)
                            if can_undo:
                                if st.button("🔄 Undo Batch", key=f"undo_fba_batch_{batch_id}"):
                                    if undo_batch(batch_id):
                                        st.rerun()
                            else:
                                st.button("🔄 Undo Batch", key=f"undo_fba_batch_disabled_{batch_id}", 
                                         disabled=True, help=reason)
                
                # Display individual transactions
                for transaction in individual_transactions:
                    trans_time = datetime.datetime.fromisoformat(transaction["timestamp"]).strftime("%H:%M")
                    with st.expander(f"🛒 {trans_time} - {transaction['parent_name']} ({transaction.get('quantity', 0)} units)", expanded=False):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**ASIN:** {transaction.get('asin', 'N/A')}")
                            st.write(f"**Quantity:** {transaction.get('quantity', 0)}")
                        with col2:
                            can_undo, reason = can_undo_transaction(transaction["id"])
                            if can_undo:
                                if st.button("🔄 Undo", key=f"undo_fba_individual_{transaction['id']}"):
                                    if undo_transaction(transaction["id"]):
                                        st.rerun()
                            else:
                                st.button("🔄 Undo", key=f"undo_fba_individual_disabled_{transaction['id']}", 
                                         disabled=True, help=reason)
            else:
                st.info("No FBA sales recorded today")

def process_fba_sales_excel(df):
    """Process the uploaded FBA sales Excel file with batch support"""
    import datetime
    processed = 0
    errors = []
    warnings = []
    batch_data = []  # Collect successful transactions for batch recording
    
    # Filter only rows with sales (Shipped > 0)
    sales_data = df[df['Shipped'] > 0].copy()
    
    st.write(f"🔄 Processing {len(sales_data)} rows with sales data...")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Generate batch ID for this upload
    batch_id = f"BULK_FBA_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    
    for index, row in sales_data.iterrows():
        try:
            asin = str(row['ASIN']).strip()
            quantity = int(row['Shipped'])
            
            # Additional info from Excel
            merchant_sku = str(row.get('Merchant SKU', '')).strip() if 'Merchant SKU' in row else ''
            title = str(row.get('Title', '')).strip() if 'Title' in row else ''
            
            # Extract date from Excel if available
            transaction_date = None
            date_columns = ['Date', 'date', 'Sale Date', 'Order Date', 'ship-date', 'shipped-date']
            for date_col in date_columns:
                if date_col in row and pd.notna(row[date_col]):
                    try:
                        if isinstance(row[date_col], str):
                            transaction_date = pd.to_datetime(row[date_col]).date()
                        else:
                            transaction_date = row[date_col].date() if hasattr(row[date_col], 'date') else row[date_col]
                        break
                    except:
                        continue
            
            # If no date found in Excel, use today
            if transaction_date is None:
                transaction_date = datetime.date.today()
            
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
            
            if not parent_id:
                # Enhanced error message with ASIN info
                warnings.append(f"ASIN {asin} not found in your product catalog (SKU: {merchant_sku})")
                continue
            
            if quantity <= 0:
                # Enhanced error message with product info
                product_name = st.session_state.parent_items[parent_id]["name"]
                warnings.append(f"Invalid quantity {quantity} for ASIN {asin} ({product_name})")
                continue
            
            # Check stock availability
            available_stock = st.session_state.stock_data.get(parent_id, {}).get("packed_stock", {}).get(asin, 0)
            
            if available_stock >= quantity:
                # Update stock immediately
                st.session_state.stock_data[parent_id]["packed_stock"][asin] -= quantity
                st.session_state.stock_data[parent_id]["last_updated"] = datetime.datetime.now().isoformat()
                
                # Prepare transaction data for batch recording
                weight_sold = quantity * st.session_state.packet_variations[parent_id][asin]["weight"]
                notes = f"Bulk upload - SKU: {merchant_sku}"
                if title:
                    notes += f" | Title: {title[:50]}"
                
                # Record individual transaction with batch ID
                record_transaction(
                    transaction_type="FBA Sale (Bulk)", 
                    parent_id=parent_id, 
                    asin=asin, 
                    quantity=quantity, 
                    weight=weight_sold, 
                    notes=notes, 
                    batch_id=batch_id, 
                    transaction_date=transaction_date
                )
                processed += 1
                
            else:
                # Enhanced error message with product details
                product_name = st.session_state.parent_items[parent_id]["name"]
                weight = st.session_state.packet_variations[parent_id][asin]["weight"]
                errors.append(f"Insufficient stock for {product_name} ({weight}kg) - ASIN {asin}: Available {available_stock}, Requested {quantity}")
                
        except Exception as e:
            errors.append(f"Error processing row {index + 1}: {str(e)}")
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Show results
    st.write(f"**📊 Results Summary:**")
    st.write(f"- ✅ Successfully processed: **{processed}** sales")
    st.write(f"- ⚠️ Warnings: **{len(warnings)}**")
    st.write(f"- ❌ Errors: **{len(errors)}**")
    
    if warnings:
        st.warning(f"⚠️ **{len(warnings)} Warnings:**")
        # Show all warnings, not just first 10
        for i, warning in enumerate(warnings, 1):
            st.write(f"{i}. {warning}")
    
    if errors:
        st.error(f"❌ **{len(errors)} Errors:**")
        # Show all errors, not just first 10
        for i, error in enumerate(errors, 1):
            st.write(f"{i}. {error}")
    
    if processed > 0:
        # Show batch undo option
        show_batch_undo_option(batch_id, f"FBA Bulk Upload", processed)
        st.balloons()  # Celebration for successful processing!
        st.info("💡 **Tip:** Check the Live Stock View to see updated stock levels and recent transactions.")
                
            else:
                errors.append(f"Insufficient stock for ASIN {asin}: Available {available_stock}, Requested {quantity}")
                
        except Exception as e:
            errors.append(f"Error processing row {index + 1}: {str(e)}")
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Show results
    st.success(f"✅ **Processing Complete!**")
    st.write(f"**📊 Results Summary:**")
    st.write(f"- ✅ Successfully processed: **{processed}** sales")
    st.write(f"- ⚠️ Warnings: **{len(warnings)}**")
    st.write(f"- ❌ Errors: **{len(errors)}**")
    
    if warnings:
        st.warning(f"⚠️ **{len(warnings)} Warnings:**")
        for warning in warnings[:10]:  # Show first 10 warnings
            st.write(f"• {warning}")
        if len(warnings) > 10:
            st.write(f"... and {len(warnings) - 10} more warnings")
    
    if errors:
        st.error(f"❌ **{len(errors)} Errors:**")
        for error in errors[:10]:  # Show first 10 errors
            st.write(f"• {error}")
        if len(errors) > 10:
            st.write(f"... and {len(errors) - 10} more errors")
    
    if processed > 0:
        st.balloons()  # Celebration for successful processing!
        st.info("💡 **Tip:** Check the Dashboard to see updated stock levels, or go to Settings to export transaction reports.")

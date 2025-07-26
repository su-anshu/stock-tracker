Spreadsheet Name", 
            value="Mithila_Foods_Stock_Tracker",
            help="Enter the name of your Google Spreadsheet"
        )
        
        if st.button("🔄 Sync to Google Sheets"):
            if spreadsheet_name:
                gs_manager = GoogleSheetsManager()
                if gs_manager.setup_connection(credentials_file):
                    if gs_manager.open_or_create_spreadsheet(spreadsheet_name):
                        success = gs_manager.sync_all_data(
                            st.session_state.stock_data,
                            st.session_state.transactions,
                            st.session_state.parent_items,
                            st.session_state.packet_variations
                        )
                        if success:
                            st.success("✅ Data synced successfully!")
                            spreadsheet_url = gs_manager.get_spreadsheet_url()
                            if spreadsheet_url:
                                st.markdown(f"📊 [Open Spreadsheet]({spreadsheet_url})")
                        else:
                            st.error("❌ Failed to sync data")
                    else:
                        st.error("❌ Failed to open/create spreadsheet")
                else:
                    st.error("❌ Failed to connect to Google Sheets")
            else:
                st.error("Please enter a spreadsheet name")

def import_from_google_sheets():
    """Import data from Google Sheets"""
    st.subheader("📥 Import from Google Sheets")
    
    if not os.path.exists("credentials.json"):
        st.warning("Google Sheets credentials required for import")
        return
    
    spreadsheet_name = st.text_input("Source Spreadsheet Name")
    worksheet_name = st.text_input("Worksheet Name", value="Products_Master")
    
    if st.button("Import Data"):
        if spreadsheet_name and worksheet_name:
            try:
                gs_manager = GoogleSheetsManager()
                if gs_manager.setup_connection():
                    if gs_manager.open_or_create_spreadsheet(spreadsheet_name):
                        # Get the worksheet
                        worksheet = gs_manager.spreadsheet.worksheet(worksheet_name)
                        data = worksheet.get_all_records()
                        
                        if data:
                            df = pd.DataFrame(data)
                            st.write("Preview of imported data:")
                            st.dataframe(df.head())
                            
                            if st.button("Confirm Import"):
                                import_product_data(df)
                        else:
                            st.warning("No data found in the worksheet")
            except Exception as e:
                st.error(f"Error importing data: {e}")

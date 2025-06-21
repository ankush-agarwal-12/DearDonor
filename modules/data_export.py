import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta
import os
from modules.supabase_utils import fetch_all_donations, fetch_donors, add_donor
import io
from io import BytesIO

def data_export_view():
    st.title("📊 Data Import/Export")
    
    # Create tabs for different options
    import_tab, donors_tab, donations_tab, custom_tab = st.tabs(["Import Data", "Export Donors", "Export Donations", "Custom Export"])
    
    # Fetch all data
    donations = fetch_all_donations()
    donors = fetch_donors()
    
    # Create donor ID to name mapping
    donor_map = {d["id"]: d["Full Name"] for d in donors}
    
    with import_tab:
        st.subheader("Import Donor Data")
        
        # Download template section
        st.markdown("### 📥 Download Import Template")
        st.markdown("""
        To import donors, please use our template format. The template includes:
        - Required fields marked with *
        - Example data for reference
        - Field descriptions and formats
        """)
        
        # Create template DataFrame
        template_df = pd.DataFrame({
            'Full Name*': ['John Doe', 'Jane Smith Corp'],
            'Email*': ['john@example.com', 'contact@janesmith.com'],
            'Phone': ['+91 1234567890', '+91 9876543210'],
            'Address': ['123 Main St, City', '456 Corp Ave, Business District'],
            'PAN': ['ABCDE1234F', 'FGHIJ5678K'],
            'Donor Type': ['Individual', 'Company']
        })
        
        # Convert template to bytes for download
        template_buffer = io.BytesIO()
        template_df.to_excel(template_buffer, index=False, sheet_name='DonorTemplate')
        template_bytes = template_buffer.getvalue()
        
        st.download_button(
            label="📄 Download Import Template",
            data=template_bytes,
            file_name="donor_import_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Import section
        st.markdown("### 📤 Import Donors")
        uploaded_file = st.file_uploader("Upload your donor data (Excel or CSV)", type=['xlsx', 'csv'])
        
        if uploaded_file is not None:
            try:
                # Read the file
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Validate required columns
                required_columns = ['Full Name*', 'Email*']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"Missing required columns: {', '.join(missing_columns)}")
                    return
                
                # Preview the data
                st.markdown("### Data Preview")
                st.dataframe(df.head(), hide_index=True)
                
                # Import button
                if st.button("Import Donors"):
                    success_count = 0
                    error_count = 0
                    errors = []
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Process each row
                    for index, row in df.iterrows():
                        try:
                            # Add donor using the existing function
                            result = add_donor(
                                full_name=row['Full Name*'],
                                email=row['Email*'],
                                phone=str(row.get('Phone', '')),
                                address=str(row.get('Address', '')),
                                pan=str(row.get('PAN', '')),
                                donor_type=str(row.get('Donor Type', 'Individual'))
                            )
                            
                            if result:
                                success_count += 1
                            else:
                                error_count += 1
                                errors.append(f"Row {index + 2}: Failed to add donor {row['Full Name*']}")
                        
                        except Exception as e:
                            error_count += 1
                            errors.append(f"Row {index + 2}: Error - {str(e)}")
                        
                        # Update progress
                        progress = (index + 1) / len(df)
                        progress_bar.progress(progress)
                        status_text.text(f"Processing... {index + 1}/{len(df)} donors")
                    
                    # Show results
                    if success_count > 0:
                        st.success(f"✅ Successfully imported {success_count} donors")
                    if error_count > 0:
                        st.error(f"❌ Failed to import {error_count} donors")
                        st.markdown("### Error Details")
                        for error in errors:
                            st.markdown(f"- {error}")
            
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                st.markdown("Please make sure you're using the correct template format.")

    with donors_tab:
        st.subheader("Export Donors Data")
        
        if not donors:
            st.warning("No donor records found.")
            return
            
        # Convert donors to DataFrame
        donors_df = pd.DataFrame([{
            'Full Name': d['Full Name'],
            'Email': d['Email'],
            'Phone': d['Phone'],
            'Address': d['Address'],
            'PAN': d.get('pan', ''),
            'Donor Type': d.get('donor_type', 'Individual')
        } for d in donors])
        
        # Print debug information
        print("Donor data sample:", donors[0] if donors else None)
        print("Donor DataFrame columns:", donors_df.columns.tolist())
        
        # Export options
        st.markdown("### Export Options")
        
        col1, col2 = st.columns(2)
        with col1:
            export_format = st.selectbox(
                "Select Format",
                ["Excel (.xlsx)", "CSV (.csv)"],
                key="donors_format"
            )
        
        with col2:
            include_fields = st.multiselect(
                "Select Fields to Include",
                donors_df.columns.tolist(),
                default=donors_df.columns.tolist(),
                key="donors_fields"
            )
        
        # Display preview with selected fields
        st.markdown("### Preview")
        preview_df = donors_df[include_fields] if include_fields else donors_df
        st.dataframe(preview_df.head(), hide_index=True)
        
        if st.button("Export Donors Data"):
            # Create export directory if it doesn't exist
            os.makedirs("exports", exist_ok=True)
            
            # Filter selected fields
            export_df = donors_df[include_fields]
            
            # Create export filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if export_format == "Excel (.xlsx)":
                filename = f"donors_export_{timestamp}.xlsx"
                export_df.to_excel(f"exports/{filename}", index=False)
            else:
                filename = f"donors_export_{timestamp}.csv"
                export_df.to_csv(f"exports/{filename}", index=False)
            
            st.success(f"✅ Data exported successfully as {filename}")
            
            # Provide download link
            with open(f"exports/{filename}", "rb") as file:
                st.download_button(
                    label="📥 Download Exported File",
                    data=file,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" 
                    if export_format == "Excel (.xlsx)" else "text/csv"
                )
    
    with donations_tab:
        st.subheader("Export Donations Data")
        
        if not donations:
            st.warning("No donation records found.")
            return
            
        # Convert donations to DataFrame
        donations_df = pd.DataFrame([{
            'Donation ID': d['id'],
            'Donor Name': donor_map.get(d['Donor'], 'Unknown'),
            'Amount': d['Amount'],
            'Date': d['date'],
            'Payment Method': d['payment_method'],
            'Purpose': d['Purpose'],  # Using uppercase to match the data structure
            'Receipt': d.get('receipt_no', '')
        } for d in donations])
        
        # Convert date to datetime
        donations_df['Date'] = pd.to_datetime(donations_df['Date'])
        
        # Time period selection
        st.markdown("### Select Time Period")
        
        period_type = st.radio(
            "Export Period",
            ["All Time", "Monthly", "Custom Date Range", "Financial Year"],
            horizontal=True
        )
        
        filtered_df = donations_df.copy()
        
        if period_type == "Monthly":
            col1, col2 = st.columns(2)
            with col1:
                selected_year = st.selectbox(
                    "Select Year",
                    range(2020, datetime.now().year + 1),
                    index=len(range(2020, datetime.now().year + 1)) - 1
                )
            with col2:
                selected_month = st.selectbox(
                    "Select Month",
                    range(1, 13),
                    format_func=lambda x: calendar.month_name[x],
                    index=datetime.now().month - 1
                )
            
            # Filter data for selected month
            start_date = pd.Timestamp(datetime(selected_year, selected_month, 1))
            end_date = pd.Timestamp(start_date + relativedelta(months=1, days=-1))
            
            filtered_df = filtered_df[
                (filtered_df['Date'] >= start_date) &
                (filtered_df['Date'] <= end_date)
            ]
            
        elif period_type == "Custom Date Range":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now() - timedelta(days=30)
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now()
                )
            
            # Convert date inputs to pandas Timestamp
            start_date = pd.Timestamp(start_date)
            end_date = pd.Timestamp(end_date)
            
            # Filter data for date range
            filtered_df = filtered_df[
                (filtered_df['Date'] >= start_date) &
                (filtered_df['Date'] <= end_date)
            ]
            
        elif period_type == "Financial Year":
            current_year = datetime.now().year
            fy_years = [f"FY {year}-{str(year+1)[-2:]}" for year in range(2020, current_year + 1)]
            
            selected_fy = st.selectbox(
                "Select Financial Year",
                fy_years,
                index=len(fy_years) - 1
            )
            
            # Parse selected FY
            fy_start_year = int(selected_fy.split("-")[0].split(" ")[1])
            start_date = pd.Timestamp(datetime(fy_start_year, 4, 1))
            end_date = pd.Timestamp(datetime(fy_start_year + 1, 3, 31))
            
            # Filter data for financial year
            filtered_df = filtered_df[
                (filtered_df['Date'] >= start_date) &
                (filtered_df['Date'] <= end_date)
            ]
        
        # Export options
        st.markdown("### Export Options")
        
        col1, col2 = st.columns(2)
        with col1:
            export_format = st.selectbox(
                "Select Format",
                ["Excel (.xlsx)", "CSV (.csv)"],
                key="donations_format"
            )
        
        with col2:
            include_fields = st.multiselect(
                "Select Fields to Include",
                filtered_df.columns.tolist(),
                default=filtered_df.columns.tolist(),
                key="donations_fields"
            )
        
        # Additional options
        include_summary = st.checkbox("Include Summary Statistics", value=True)
        
        # Display preview with selected fields
        st.markdown("### Preview")
        preview_df = filtered_df[include_fields] if include_fields else filtered_df
        st.dataframe(preview_df.head(), hide_index=True)
        
        if st.button("Export Donations Data"):
            # Create export directory if it doesn't exist
            os.makedirs("exports", exist_ok=True)
            
            # Filter selected fields
            export_df = filtered_df[include_fields]
            
            # Create export filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if export_format == "Excel (.xlsx)":
                filename = f"donations_export_{timestamp}.xlsx"
                
                # Create Excel writer object
                with pd.ExcelWriter(f"exports/{filename}") as writer:
                    export_df.to_excel(writer, sheet_name="Donations", index=False)
                    
                    # Add summary sheet if requested
                    if include_summary and 'Amount' in include_fields:
                        summary_data = {
                            "Total Donations": len(export_df),
                            "Total Amount": export_df['Amount'].sum(),
                            "Average Amount": export_df['Amount'].mean(),
                            "Minimum Amount": export_df['Amount'].min(),
                            "Maximum Amount": export_df['Amount'].max(),
                            "Period Start": export_df['Date'].min(),
                            "Period End": export_df['Date'].max()
                        }
                        
                        summary_df = pd.DataFrame(list(summary_data.items()), 
                                               columns=['Metric', 'Value'])
                        summary_df.to_excel(writer, sheet_name="Summary", index=False)
                        
                        # Add monthly trends
                        monthly_donations = export_df.set_index('Date').resample('M')['Amount'].agg(['sum', 'count'])
                        monthly_donations.columns = ['Total Amount', 'Number of Donations']
                        monthly_donations.index = monthly_donations.index.strftime('%B %Y')
                        monthly_donations.to_excel(writer, sheet_name="Monthly Trends")
            else:
                filename = f"donations_export_{timestamp}.csv"
                export_df.to_csv(f"exports/{filename}", index=False)
            
            st.success(f"✅ Data exported successfully as {filename}")
            
            # Provide download link
            with open(f"exports/{filename}", "rb") as file:
                st.download_button(
                    label="📥 Download Exported File",
                    data=file,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" 
                    if export_format == "Excel (.xlsx)" else "text/csv"
                )
    
    with custom_tab:
        st.subheader("Custom Export")
        
        if not donations or not donors:
            st.warning("No data available for custom export.")
            return
            
        # Create merged dataset
        donations_df = pd.DataFrame([{
            'Donation ID': d['id'],
            'Donor ID': d['Donor'],
            'Amount': d['Amount'],
            'Date': pd.to_datetime(d['date']),
            'Payment Method': d['payment_method'],
            'Purpose': d['Purpose'],  # Using uppercase to match the data structure
            'Receipt': d.get('receipt_no', '')
        } for d in donations])
        
        donors_df = pd.DataFrame([{
            'Donor ID': d['id'],
            'Full Name': d['Full Name'],
            'Email': d['Email'],
            'Phone': d['Phone'],
            'Address': d['Address'],
            'PAN': d.get('pan', ''),
            'Donor Type': d.get('donor_type', 'Individual')
        } for d in donors])
        
        # Merge datasets
        merged_df = pd.merge(
            donations_df,
            donors_df,
            on='Donor ID',
            how='left'
        )
        
        # Custom query builder
        st.markdown("### Build Your Query")
        
        # Field selection
        selected_fields = st.multiselect(
            "Select Fields to Include",
            merged_df.columns.tolist(),
            default=['Donation ID', 'Full Name', 'Amount', 'Date', 'Payment Method']
        )
        
        # Filters
        st.markdown("### Add Filters")
        
        # Amount range filter
        col1, col2 = st.columns(2)
        with col1:
            min_amount = st.number_input("Minimum Amount", value=float(merged_df['Amount'].min()))
        with col2:
            max_amount = st.number_input("Maximum Amount", value=float(merged_df['Amount'].max()))
        
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=merged_df['Date'].min()
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=merged_df['Date'].max()
            )
        
        # Payment method filter
        payment_methods = st.multiselect(
            "Payment Methods",
            merged_df['Payment Method'].unique().tolist(),
            default=merged_df['Payment Method'].unique().tolist()
        )
        
        # Donor type filter
        donor_types = st.multiselect(
            "Donor Types",
            merged_df['Donor Type'].unique().tolist(),
            default=merged_df['Donor Type'].unique().tolist()
        )
        
        # Apply filters
        filtered_df = merged_df[
            (merged_df['Amount'] >= min_amount) &
            (merged_df['Amount'] <= max_amount) &
            (merged_df['Date'].dt.date >= start_date) &
            (merged_df['Date'].dt.date <= end_date) &
            (merged_df['Payment Method'].isin(payment_methods)) &
            (merged_df['Donor Type'].isin(donor_types))
        ]
        
        # Display preview with selected fields
        st.markdown("### Preview")
        preview_df = filtered_df[selected_fields] if selected_fields else filtered_df
        st.dataframe(preview_df.head(), hide_index=True)
        
        # Export options
        st.markdown("### Export Options")
        
        export_format = st.selectbox(
            "Select Format",
            ["Excel (.xlsx)", "CSV (.csv)"],
            key="custom_format"
        )
        
        if st.button("Export Custom Data"):
            # Create export directory if it doesn't exist
            os.makedirs("exports", exist_ok=True)
            
            # Create export filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if export_format == "Excel (.xlsx)":
                filename = f"custom_export_{timestamp}.xlsx"
                
                with pd.ExcelWriter(f"exports/{filename}") as writer:
                    filtered_df[selected_fields].to_excel(writer, sheet_name="Custom Export", index=False)
                    
                    # Add summary statistics
                    if 'Amount' in selected_fields:
                        summary_stats = pd.DataFrame({
                            'Metric': ['Total Amount', 'Average Amount', 'Number of Records'],
                            'Value': [
                                f"₹{filtered_df['Amount'].sum():,.2f}",
                                f"₹{filtered_df['Amount'].mean():,.2f}",
                                len(filtered_df)
                            ]
                        })
                        summary_stats.to_excel(writer, sheet_name='Summary', index=False)
            else:
                filename = f"custom_export_{timestamp}.csv"
                filtered_df[selected_fields].to_csv(f"exports/{filename}", index=False)
            
            st.success(f"✅ Data exported successfully as {filename}")
            
            # Provide download link
            with open(f"exports/{filename}", "rb") as file:
                st.download_button(
                    label="📥 Download Exported File",
                    data=file,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" 
                    if export_format == "Excel (.xlsx)" else "text/csv"
                ) 
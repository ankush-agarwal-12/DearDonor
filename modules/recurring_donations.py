import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from modules.supabase_utils import (
    fetch_all_donations, fetch_donors,
    update_recurring_status, bulk_update_recurring_status
)
import calendar

def format_amount(amount):
    return f"₹{amount:,.2f}"

def calculate_next_due_date(start_date, frequency, payment_count=1):
    """
    Calculate the next due date based on the start date, frequency, and number of payments made.
    
    Args:
        start_date: The start date of the recurring donation
        frequency: The frequency of the recurring donation (Monthly, Quarterly, Yearly)
        payment_count: Number of payments made so far (including the current payment)
    
    Returns:
        datetime: The next due date
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    
    # Calculate frequency in months
    frequency_months = {
        "Monthly": 1,
        "Quarterly": 3,
        "Yearly": 12
    }.get(frequency, 1)
    
    # Calculate months to add based on payment count
    months_to_add = payment_count * frequency_months
    
    # Calculate next due date by adding months to start date
    next_due = start_date
    
    # Add months while preserving the day of month from start date
    for _ in range(months_to_add):
        # Get the last day of the current month
        _, last_day = calendar.monthrange(next_due.year, next_due.month)
        
        # If start date is beyond the last day of target month, use the last day
        target_day = min(start_date.day, last_day)
        
        if next_due.month == 12:
            next_due = next_due.replace(year=next_due.year + 1, month=1, day=target_day)
        else:
            next_due = next_due.replace(month=next_due.month + 1, day=target_day)
    
    return next_due

def get_payment_status(scheduled_date, actual_date=None):
    """Calculate payment status based on scheduled and actual dates"""
    if not actual_date or not scheduled_date:
        return "Pending"
    
    try:
        scheduled = pd.to_datetime(scheduled_date)
        actual = pd.to_datetime(actual_date)
        diff = (actual - scheduled).days
        
        if diff < -7:  # More than a week early
            return "Early"
        elif diff > 7:  # More than a week late
            return "Late"
        else:
            return "On Time"
    except (TypeError, ValueError):
        return "Pending"

def recurring_donations_view():
    # Header with icon and title
    st.markdown("# 🔄 Recurring Donations")
    
    # Initialize session state for selections
    if 'selected_donations' not in st.session_state:
        st.session_state.selected_donations = []
    
    # Initialize session state for cancel confirmation
    if 'show_cancel_confirm' not in st.session_state:
        st.session_state.show_cancel_confirm = False
        st.session_state.donations_to_cancel = []
    
    # Get organization_id from session state
    if 'organization' not in st.session_state:
        st.error("❌ Organization not found. Please login again.")
        return
    
    organization_id = st.session_state.organization['id']
    
    # Fetch data
    donations = fetch_all_donations(organization_id=organization_id)
    donors = fetch_donors(organization_id=organization_id)
    
    if not donations:
        st.warning("No donation records found.")
        return
    
    # Create donor map
    donor_map = {d["id"]: d["Full Name"] for d in donors}
    
    # Filter recurring donations
    recurring_donations = [
        d for d in donations 
        if d.get('is_recurring', False) and d.get('recurring_status') != 'Cancelled'  # Filter out cancelled donations
    ]
    
    if not recurring_donations:
        st.info("No active recurring donations found yet. Set up recurring donations through the Record Donation page.")
        return

    # Check for overdue donations
    today = pd.to_datetime(datetime.now().date())
    overdue_donations = [
        d for d in recurring_donations
        if d.get('next_due_date') and pd.to_datetime(d['next_due_date']) < today and d.get('recurring_status') == 'Active'
    ]

    if overdue_donations:
        st.markdown('<p class="section-header">⚠️ Overdue Donations</p>', unsafe_allow_html=True)
        
        # Convert to DataFrame for display
        overdue_df = pd.DataFrame([{
            'Select': False,
            'Donor Name': donor_map.get(d['Donor'], 'Unknown'),
            'Amount': format_amount(d['Amount']),
            'Frequency': d.get('recurring_frequency', 'Monthly'),
            'Due Date': pd.to_datetime(d['next_due_date']).strftime('%Y-%m-%d') if d.get('next_due_date') else 'Unknown',
            'Days Overdue': (today - pd.to_datetime(d['next_due_date'])).days if d.get('next_due_date') else 0,
            'Status': d.get('recurring_status', 'Active'),
            'id': d['id']
        } for d in overdue_donations])

        # Apply styling for overdue section
        def overdue_row_style(row):
            days_overdue = row['Days Overdue']
            if days_overdue > 30:
                return ['background-color: rgba(255, 0, 0, 0.1)'] * len(row)
            elif days_overdue > 14:
                return ['background-color: rgba(255, 165, 0, 0.1)'] * len(row)
            return ['background-color: rgba(255, 255, 0, 0.1)'] * len(row)

        # Apply styling
        styled_overdue_df = overdue_df.style.apply(overdue_row_style, axis=1)

        # Display the overdue donations table
        edited_overdue_df = st.data_editor(
            styled_overdue_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select for actions",
                    default=False,
                    width="small"
                ),
                "Donor Name": st.column_config.TextColumn("Donor Name", width="medium"),
                "Amount": st.column_config.TextColumn("Amount", width="small"),
                "Frequency": st.column_config.TextColumn("Frequency", width="small"),
                "Due Date": st.column_config.TextColumn("Due Date", width="medium"),
                "Days Overdue": st.column_config.NumberColumn("Days Overdue", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
            },
            disabled=["Donor Name", "Amount", "Frequency", "Due Date", "Days Overdue", "Status"],
            key="overdue_donations_table"
        )

        # Get selected overdue donation IDs
        selected_overdue_ids = overdue_df[edited_overdue_df['Select']]['id'].tolist()

        # Action buttons for overdue donations
        if selected_overdue_ids:
            st.markdown("#### Actions for Selected Overdue Donations")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📝 Record Payment", use_container_width=True):
                    # Store selected IDs in session state
                    st.session_state.selected_overdue_donations = selected_overdue_ids
                    # Redirect to Record Donation page
                    st.switch_page("pages/record_donation.py")
            
            with col2:
                if st.button("⏸️ Pause Selected", use_container_width=True):
                    if bulk_update_recurring_status(selected_overdue_ids, "Paused", organization_id=organization_id):
                        st.success(f"Successfully paused {len(selected_overdue_ids)} recurring donation(s)")
                        st.rerun()
                    else:
                        st.error("Failed to pause some donations")

        st.markdown("---")  # Add separator between sections

    # Create DataFrame for recurring donations
    df = pd.DataFrame([{
        'id': d['id'],
        'Donor Name': donor_map.get(d['Donor'], 'Unknown'),
        'Amount': d['Amount'],
        'Frequency': d.get('recurring_frequency', 'Monthly'),
        'Start Date': pd.to_datetime(d.get('start_date')),
        'Next Due Date': pd.to_datetime(d.get('next_due_date')),
        'Status': d.get('recurring_status', 'Active'),
        'Last Paid': pd.to_datetime(d.get('last_paid_date'))
    } for d in recurring_donations])
    
    # Get linked donations
    linked_donations = [
        d for d in donations 
        if d.get('linked_to_recurring', False)
    ]
    
    # Convert linked donations to DataFrame
    linked_df = pd.DataFrame([{
        'Recurring ID': d.get('recurring_id'),
        'Amount': d['Amount'],
        'Date': pd.to_datetime(d['date']) if d.get('date') else None,
        'Status': get_payment_status(
            next(
                (r['next_due_date'] for r in recurring_donations if r['id'] == d.get('recurring_id')),
                None
            ),
            d['date']
        )
    } for d in linked_donations]) if linked_donations else pd.DataFrame()
    
    # Filters section
    st.markdown('<p class="section-header">🔍 Filters</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        frequencies = ['All'] + sorted(df['Frequency'].unique().tolist())
        selected_frequency = st.selectbox('Frequency', frequencies)
    
    with col2:
        statuses = ['All'] + sorted(df['Status'].unique().tolist())
        selected_status = st.selectbox('Status', statuses)
    
    with col3:
        date_filter = st.selectbox(
            'Date Filter',
            ['All', 'Next 7 Days', 'Next 30 Days', 'Overdue']
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_frequency != 'All':
        filtered_df = filtered_df[filtered_df['Frequency'] == selected_frequency]
    
    if selected_status != 'All':
        filtered_df = filtered_df[filtered_df['Status'] == selected_status]
    
    today = pd.to_datetime(datetime.now().date())
    if date_filter == 'Next 7 Days':
        filtered_df = filtered_df[
            (filtered_df['Next Due Date'].notna()) &
            (filtered_df['Next Due Date'] >= today) &
            (filtered_df['Next Due Date'] <= today + timedelta(days=7))
        ]
    elif date_filter == 'Next 30 Days':
        filtered_df = filtered_df[
            (filtered_df['Next Due Date'].notna()) &
            (filtered_df['Next Due Date'] >= today) &
            (filtered_df['Next Due Date'] <= today + timedelta(days=30))
        ]
    elif date_filter == 'Overdue':
        filtered_df = filtered_df[
            (filtered_df['Next Due Date'].notna()) &
            (filtered_df['Next Due Date'] < today)
        ]
    
    # Summary metrics
    st.markdown('<p class="section-header">📊 Summary</p>', unsafe_allow_html=True)
    
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.markdown("""
            <div class="metric-container">
                <div class="metric-label">Total Active</div>
                <div class="metric-value">{}</div>
            </div>
        """.format(len(filtered_df[filtered_df['Status'] == 'Active'])), unsafe_allow_html=True)
    
    with metric_cols[1]:
        st.markdown("""
            <div class="metric-container">
                <div class="metric-label">Monthly Revenue</div>
                <div class="metric-value">{}</div>
            </div>
        """.format(format_amount(
            filtered_df[filtered_df['Status'] == 'Active']['Amount'].sum()
        )), unsafe_allow_html=True)
    
    with metric_cols[2]:
        st.markdown("""
            <div class="metric-container">
                <div class="metric-label">Due This Week</div>
                <div class="metric-value">{}</div>
            </div>
        """.format(len(filtered_df[
            (filtered_df['Next Due Date'].notna()) &
            (filtered_df['Next Due Date'] >= today) &
            (filtered_df['Next Due Date'] <= today + timedelta(days=7))
        ])), unsafe_allow_html=True)
    
    with metric_cols[3]:
        st.markdown("""
            <div class="metric-container">
                <div class="metric-label">Overdue</div>
                <div class="metric-value">{}</div>
            </div>
        """.format(len(filtered_df[
            (filtered_df['Next Due Date'].notna()) &
            (filtered_df['Next Due Date'] < today)
        ])), unsafe_allow_html=True)
    
    # Recurring Plans with Selection
    st.markdown('<p class="section-header">📋 Recurring Plans</p>', unsafe_allow_html=True)
    
    # Add status badges and row styling
    def style_status(series):
        colors = {
            'Active': 'background-color: rgba(0, 255, 0, 0.1)',
            'Paused': 'background-color: rgba(255, 165, 0, 0.1)',
            'Cancelled': 'background-color: rgba(255, 0, 0, 0.1)'
        }
        return [colors.get(val, '') for val in series]

    # Format DataFrame for display
    display_df = filtered_df.copy()
    display_df['Amount'] = display_df['Amount'].apply(format_amount)
    
    # Add selection column if not exists
    if 'Select' not in display_df.columns:
        display_df.insert(0, 'Select', False)
    
    # Safely format dates
    def safe_date_format(date_series):
        return date_series.apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else 'Not Set')
    
    display_df['Start Date'] = safe_date_format(display_df['Start Date'])
    display_df['Last Paid'] = safe_date_format(display_df['Last Paid'])
    display_df['Next Due Date'] = safe_date_format(display_df['Next Due Date'])
    
    # Apply styling
    styled_df = display_df.style.apply(style_status, subset=['Status'])
    
    # Display the recurring plans table with selection
    edited_df = st.data_editor(
        styled_df,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Select",
                help="Select recurring donations",
                default=False
            ),
            "Donor Name": st.column_config.TextColumn(
                "Donor Name",
                help="Name of the donor",
                width="medium"
            ),
            "Amount": st.column_config.NumberColumn(
                "Amount",
                help="Donation amount",
                format="₹%.2f"
            ),
            "Frequency": st.column_config.TextColumn(
                "Frequency",
                help="How often the donation repeats",
                width="small"
            ),
            "Start Date": st.column_config.DateColumn(
                "Start Date",
                help="When the recurring donation started",
                format="YYYY-MM-DD",
                width="medium"
            ),
            "Next Due Date": st.column_config.DateColumn(
                "Next Due Date",
                help="When the next payment is due",
                format="YYYY-MM-DD",
                width="medium"
            ),
            "Status": st.column_config.SelectboxColumn(
                "Status",
                help="Current status of the recurring donation",
                width="medium",
                options=[
                    "Active",
                    "Paused",
                    "Cancelled"
                ],
                required=True,
                disabled=True
            ),
            "Last Paid": st.column_config.DateColumn(
                "Last Paid",
                help="When the last payment was made",
                format="YYYY-MM-DD",
                width="medium"
            )
        },
        use_container_width=True,
        hide_index=True,
        disabled=["Donor Name", "Amount", "Frequency", "Start Date", "Next Due Date", "Status", "Last Paid"],
        key="recurring_plans_table"
    )
    
    # Get selected donation IDs
    selected_ids = display_df[edited_df['Select']]['id'].tolist()
    
    # Action buttons for selected donations
    if not filtered_df.empty:
        st.markdown("### 🛠️ Bulk Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🟡 Pause Selected", use_container_width=True, disabled=len(selected_ids) == 0):
                if selected_ids:
                    # Filter out already paused or cancelled donations
                    active_ids = [
                        id for id in selected_ids 
                        if df[df['id'] == id]['Status'].iloc[0] == 'Active'
                    ]
                    if active_ids:
                        if bulk_update_recurring_status(active_ids, "Paused", organization_id=organization_id):
                            st.success(f"Successfully paused {len(active_ids)} recurring donation(s)")
                            st.rerun()
                        else:
                            st.error("Failed to pause some donations")
                    else:
                        st.warning("No active donations selected")
                else:
                    st.warning("Please select donations to pause")
        
        with col2:
            if st.button("🟢 Unpause Selected", use_container_width=True, disabled=len(selected_ids) == 0):
                if selected_ids:
                    # Filter out non-paused donations
                    paused_ids = [
                        id for id in selected_ids 
                        if df[df['id'] == id]['Status'].iloc[0] == 'Paused'
                    ]
                    if paused_ids:
                        if bulk_update_recurring_status(paused_ids, "Active", organization_id=organization_id):
                            st.success(f"Successfully reactivated {len(paused_ids)} recurring donation(s)")
                            st.rerun()
                        else:
                            st.error("Failed to reactivate some donations")
                    else:
                        st.warning("No paused donations selected")
                else:
                    st.warning("Please select donations to unpause")
        
        with col3:
            if st.button("🔴 Cancel Selected", use_container_width=True, disabled=len(selected_ids) == 0):
                if selected_ids:
                    # Filter out already cancelled donations
                    active_or_paused_ids = [
                        id for id in selected_ids 
                        if df[df['id'] == id]['Status'].iloc[0] in ['Active', 'Paused']
                    ]
                    if active_or_paused_ids:
                        st.session_state.show_cancel_confirm = True
                        st.session_state.donations_to_cancel = active_or_paused_ids
                    else:
                        st.warning("No active or paused donations selected")
                else:
                    st.warning("Please select donations to cancel")

        # Show confirmation dialog if needed
        if st.session_state.show_cancel_confirm:
            st.warning("⚠️ Are you sure you want to cancel the selected recurring donations? This action cannot be undone.")
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                if st.button("✅ Yes, Cancel Donations", type="primary", use_container_width=True):
                    if bulk_update_recurring_status(st.session_state.donations_to_cancel, "Cancelled", organization_id=organization_id):
                        st.success(f"Successfully cancelled {len(st.session_state.donations_to_cancel)} recurring donation(s)")
                        # Reset confirmation state
                        st.session_state.show_cancel_confirm = False
                        st.session_state.donations_to_cancel = []
                        st.rerun()
                    else:
                        st.error("Failed to cancel donations")
            with confirm_col2:
                if st.button("❌ No, Keep Active", use_container_width=True):
                    st.session_state.show_cancel_confirm = False
                    st.session_state.donations_to_cancel = []
                    st.rerun()

    # Show linked donations if any exist
    if not linked_df.empty:
        st.markdown('<p class="section-header">📅 Payment History</p>', unsafe_allow_html=True)
        
        # Add donor and plan information to linked donations
        linked_df = linked_df.merge(
            df[['id', 'Donor Name', 'Frequency']],
            left_on='Recurring ID',
            right_on='id',
            how='left'
        ).drop('id', axis=1)
        
        # Format linked donations for display
        linked_df['Amount'] = linked_df['Amount'].apply(format_amount)
        linked_df['Date'] = safe_date_format(linked_df['Date'])
        
        def format_payment_status(status):
            return status  # Return just the status text without HTML formatting

        linked_df['Status'] = linked_df['Status'].apply(format_payment_status)
        
        # Reorder columns and rename for display
        display_df = linked_df[[
            'Donor Name',
            'Frequency',
            'Date',
            'Amount',
            'Status'
        ]].sort_values(['Date', 'Donor Name'], ascending=[False, True])
        
        # Display all payment history in a single table
        st.dataframe(
            display_df,
            column_config={
                "Donor Name": st.column_config.TextColumn("Donor", width="medium"),
                "Frequency": st.column_config.TextColumn("Plan", width="small"),
                "Date": st.column_config.TextColumn("Payment Date", width="medium"),
                "Amount": st.column_config.TextColumn("Amount", width="small"),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    width="small",
                    options=["On Time", "Early", "Late", "Pending"],
                    required=True
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Add summary statistics
        st.markdown("### 📊 Payment Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_payments = len(display_df)
            st.metric("Total Payments", total_payments)
            
        with col2:
            on_time_payments = len(display_df[display_df['Status'].str.contains('On Time')])
            on_time_percentage = (on_time_payments / total_payments * 100) if total_payments > 0 else 0
            st.metric("On Time Payments", f"{on_time_percentage:.1f}%")
            
        with col3:
            early_payments = len(display_df[display_df['Status'].str.contains('Early')])
            early_percentage = (early_payments / total_payments * 100) if total_payments > 0 else 0
            st.metric("Early Payments", f"{early_percentage:.1f}%")
            
        with col4:
            late_payments = len(display_df[display_df['Status'].str.contains('Late')])
            late_percentage = (late_payments / total_payments * 100) if total_payments > 0 else 0
            st.metric("Late Payments", f"{late_percentage:.1f}%") 
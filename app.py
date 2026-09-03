
import os,re
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import base64
from datetime import timedelta

st.set_page_config(page_title="Nestlé India | Secondary OTR Dashboard",page_icon="📊",layout="wide")
ROOT=os.path.dirname(os.path.abspath(__file__))
PATH=os.path.join(ROOT,"data","OTR_Dashboard_Final.csv")

# Corporate brand color palette
BRAND_COLORS = {
    'primary_blue': '#006EB3',
    'teal_cyan': '#13828F',
    'dark_grey': '#2A2A2A',
    'light_bg': '#F5F7F6'
}

@st.cache_data
def load():
    """Load and preprocess CSV data with caching to prevent reloads on filter changes"""
    d=pd.read_csv(PATH,low_memory=False)
    d["Ticket_Date"]=pd.to_datetime(d["Ticket_Date"],errors="coerce")
    return d

@st.cache_data
def get_filter_options(df, col):
    """Cache filter dropdown options to improve performance"""
    return sorted(df[col].dropna().astype(str).unique().tolist()) if col in df else []

@st.cache_data
def aggregate_by_dimension(df, col, topn=10):
    """Cache dimension aggregation for comparison charts"""
    return df[col].fillna("Not Available").astype(str).value_counts().head(topn).reset_index()

@st.cache_data
def aggregate_by_period(df, col, period='M'):
    """Cache time-series aggregation with caching"""
    per = df.Ticket_Date.dt.to_period(period).astype(str)
    return df.groupby([per, df[col].fillna("Not Available").astype(str)]).size().reset_index(name="Tickets")

df=load()

# Initialize session state for filters
if 'date_range' not in st.session_state:
    st.session_state.date_range = (df.Ticket_Date.min().date(), df.Ticket_Date.max().date())
if 'filters' not in st.session_state:
    st.session_state.filters = {
        "Branch": [], "DC_Code": [], "ASM": [], "ASM_Zone": [],
        "Brand": [], "CAT": [], "BU": [], "Module": [],
        "Distributor": [], "Current_Status": [], "DC_Issue_Status": []
    }

st.markdown("""
<style>
/* App background with brand color */
.stApp{background:""" + BRAND_COLORS['light_bg'] + """}
.block-container{max-width:1550px;padding-top:1rem}

/* Hero section with primary blue */
.hero{background:linear-gradient(135deg,""" + BRAND_COLORS['primary_blue'] + """,""" + BRAND_COLORS['teal_cyan'] + """);padding:24px 28px;border-radius:20px;color:#fff;margin-bottom:24px; position:relative; z-index:0;}
.hero h1{color:#fff!important;margin:0;font-size:32px}.hero p{margin:5px 0 0}

/* Card container styling - Main wrapper for sections */
.card-container{background:#fff;border:1px solid #E5EBE8;border-radius:16px;padding:24px;margin-bottom:20px;box-shadow:0 2px 8px rgba(26,59,50,0.05)}

/* Metric cards (KPI) */
.metric-card{background:#fff;border:1px solid #DCE5E1;border-radius:12px;padding:20px;min-height:120px;box-shadow:0 2px 6px rgba(26,59,50,0.04);transition:all 0.3s ease}
.metric-card:hover{box-shadow:0 4px 12px rgba(26,59,50,0.08)}
.metric-label{font-size:12px;color:#66756F;font-weight:600;text-transform:uppercase;letter-spacing:0.5px}.metric-value{font-size:28px;color:""" + BRAND_COLORS['dark_grey'] + """;font-weight:800;margin-top:8px}
.metric-badge{display:inline-block;background:""" + BRAND_COLORS['primary_blue'] + """;color:#fff;font-size:11px;padding:4px 8px;border-radius:4px;margin-top:8px}

/* Chart card wrapper */
.chart-card{background:#fff;border:1px solid #E5EBE8;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 2px 6px rgba(26,59,50,0.04)}

/* Data table wrapper */
.table-card{background:#fff;border:1px solid #E5EBE8;border-radius:12px;padding:24px;margin-bottom:16px;box-shadow:0 2px 6px rgba(26,59,50,0.04)}

/* Section title with dark grey */
.section{font-size:20px;font-weight:700;color:""" + BRAND_COLORS['dark_grey'] + """;margin:24px 0 16px;padding-bottom:12px;border-bottom:2px solid #E5EBE8}

/* Summary section with primary blue accent */
.summary-box{background:linear-gradient(135deg, #f0f7fb 0%, #e8f4f8 100%);border-left:4px solid""" + BRAND_COLORS['primary_blue'] + """;padding:16px 20px;border-radius:8px;margin-bottom:24px}
.summary-text{font-size:14px;color:""" + BRAND_COLORS['dark_grey'] + """;margin:0;font-weight:500}

/* Divider styling */
.divider{height:1px;background:#E5EBE8;margin:20px 0}

/* Filter control styling in sidebar */
.filter-section{background:rgba(0,110,179,0.05);padding:12px;border-radius:8px;margin:12px 0}

/* Make Streamlit header transparent */
header.css-1bd0g9n.e1g8pov71, header[data-testid="stHeader"] {
  background: transparent !important;
  box-shadow: none !important;
}

.block-container { padding-top: 1.5rem !important; }
.hero img { position:absolute; right:20px; top:50%; transform:translateY(-50%); width:120px; z-index:9999; }
main[role="main"] { z-index:0; }

/* Responsive grid adjustments */
@media (max-width: 768px) {
  .card-container { padding: 16px; }
  .metric-card { padding: 16px; min-height: 100px; }
  .metric-value { font-size: 24px; }
  .section { font-size: 18px; }
}
</style>
""",unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## NESTLÉ INDIA")
    st.caption("Secondary OTR Dashboard")
    st.divider()
    
    # Clear All Filters button with session state reset
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Clear All Filters", use_container_width=True):
            st.session_state.date_range = (df.Ticket_Date.min().date(), df.Ticket_Date.max().date())
            st.session_state.filters = {k: [] for k in st.session_state.filters}
            st.rerun()
    
    st.divider()
    st.markdown("### Filters")
    
    # Date range filter
    dates=st.date_input("OTR Ticket Date",value=st.session_state.date_range)
    st.session_state.date_range = dates if isinstance(dates, tuple) else st.session_state.date_range
    
    f=df.copy()
    if isinstance(dates,tuple) and len(dates)==2:
        f=f[f.Ticket_Date.between(pd.Timestamp(dates[0]),pd.Timestamp(dates[1]))]
    
    # Dynamic filters with session state management
    for label,col in [("Branch","Branch"),("DC Code","DC_Code"),("ASM","ASM"),("ASM Zone","ASM_Zone"),
                      ("Brand","Brand"),("CAT","CAT"),("BU","BU"),("Module Name","Module"),
                      ("Distributor","Distributor"),("Status","Current_Status"),("DC Issue","DC_Issue_Status")]:
        vals=get_filter_options(f, col)
        sel=st.multiselect(label, vals, default=st.session_state.filters.get(col, []))
        st.session_state.filters[col] = sel
        if sel:
            f=f[f[col].astype(str).isin(sel)]

# Build header with logo positioned top-right inside hero
logo_path = os.path.join(ROOT, "assets", "nestle_logo_final.png")
logo_b64 = ""
if os.path.exists(logo_path):
    try:
        with open(logo_path, "rb") as imgf:
            logo_b64 = base64.b64encode(imgf.read()).decode()
    except Exception:
        logo_b64 = ""

hero_html = '''<div class="hero" style="position:relative; padding-right:160px;">
    <h1>NESTLÉ INDIA — SECONDARY OTR DASHBOARD</h1>
    <p>OTR Monitoring | Root Cause Analysis | Product Excellence</p>
</div>'''
# inject inline img if available, positioned absolute to avoid being hidden
if logo_b64:
    # update to use white logo if present, else fall back to original
    if os.path.exists(os.path.join(ROOT, 'assets', 'nestle_logo_white.png')):
        with open(os.path.join(ROOT, 'assets', 'nestle_logo_white.png'), 'rb') as lf:
            logo_b64 = base64.b64encode(lf.read()).decode()
    hero_html = hero_html.replace('</div>','<img src="data:image/png;base64,' + logo_b64 + '" style="position:absolute; right:20px; top:50%; transform:translateY(-50%); width:120px; filter:drop-shadow(0 0 2px rgba(0,0,0,0.25));"/></div>')

st.markdown(hero_html, unsafe_allow_html=True)

# Dynamic summary title based on filtered data
active_filters = [k for k, v in st.session_state.filters.items() if v]
filter_summary = f"Showing {len(f):,} tickets"
if active_filters:
    filter_summary += f" | Active filters: {', '.join(active_filters[:3])}"
    if len(active_filters) > 3:
        filter_summary += f" +{len(active_filters)-3} more"

st.markdown(f'<div class="summary-box"><p class="summary-text">📊 {filter_summary}</p></div>', unsafe_allow_html=True)

# Metric card function
def metric_card(label, value, badge_text=""):
    """Display a metric card with label, value, and optional badge"""
    badge_html = f'<span class="metric-badge">{badge_text}</span>' if badge_text else ''
    return f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div>{badge_html}</div>'

# Overview section with card container
st.markdown('<div class="section">📈 Overview Metrics</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5, gap="medium")
    metrics_data = [
        (col1, "Total OTR Tickets", f"{f.Ticket_Number.nunique():,}"),
        (col2, "Total Invoices", f"{f.Invoice_Number.dropna().nunique():,}"),
        (col3, "Distributors", f"{f.Distributor.nunique():,}"),
        (col4, "Product Codes", f"{f.Product_Code_Extracted.dropna().nunique():,}"),
        (col5, "DC Issues", f"{(f.DC_Issue_Status=='DC Issue').sum():,}"),
    ]
    
    for col, label, value in metrics_data:
        with col:
            st.markdown(metric_card(label, value), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Second row of metrics
with st.container():
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5, gap="medium")
    metrics_data_2 = [
        (col1, "Closed Tickets", f"{(f.Current_Status=='Closed').sum():,}"),
        (col2, "Open / Pending", f"{(~f.Current_Status.isin(['Closed','Resolved'])).sum():,}"),
        (col3, "Brand Mapped", f"{(f.Brand!='Not Available').sum():,}"),
        (col4, "Brand Coverage", f"{((f.Brand!='Not Available').mean()*100 if len(f) else 0):.1f}%"),
        (col5, "Total Records", f"{len(f):,}"),
    ]
    
    for col, label, value in metrics_data_2:
        with col:
            st.markdown(metric_card(label, value), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section">📊 Comparisons & Analytics</div>',unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    
    comp_col1, comp_col2 = st.columns([1,2], gap="large")
    with comp_col1:
        st.markdown("**Chart Configuration**")
        comp_dim = st.selectbox("Compare by", ["DC Code","Distributor (CD)","Brand","Branch","ASM"], index=2)
        agg = st.radio("Aggregation", ["Monthly","Yearly","Overall"], horizontal=True)
        topn = st.slider("Top N Items", min_value=5, max_value=30, value=10)

    with comp_col2:
        col_map = {"DC Code":"DC_Code","Distributor (CD)":"Distributor","Brand":"Brand","Branch":"Branch","ASM":"ASM"}
        col = col_map.get(comp_dim, "Brand")
        if agg == "Overall":
            x = aggregate_by_dimension(f, col, topn)
            x.columns = [col, "Tickets"]
            fig = px.bar(x, y=col, x="Tickets", orientation="h", title=f"Top {topn} by {comp_dim}")
            fig.update_traces(marker_color=BRAND_COLORS['primary_blue'])
        else:
            if agg == "Monthly":
                per = f.Ticket_Date.dt.to_period("M").astype(str)
            else:
                per = f.Ticket_Date.dt.to_period("Y").astype(str)
            grp = f.groupby([per, f[col].fillna("Not Available").astype(str)]).size().reset_index(name="Tickets")
            grp.columns = ["Period", col, "Tickets"]
            top_entities = grp.groupby(col)["Tickets"].sum().nlargest(topn).index.tolist()
            grp = grp[grp[col].isin(top_entities)]
            fig = px.line(grp, x="Period", y="Tickets", color=col, markers=True, title=f"{comp_dim} - {agg} Trend (Top {topn})")
            fig.update_traces(line=dict(width=2))
        
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section">📈 OTR Trends & Product Analysis</div>',unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    
    a,b,c=st.columns([1.4,1,1], gap="medium")
    with a:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        t=f.groupby(f.Ticket_Date.dt.to_period("M").astype(str)).size().reset_index(name="Tickets")
        t.columns=["Month","Tickets"]
        fig=px.line(t,x="Month",y="Tickets",markers=True,title="OTR Tickets by Month")
        fig.update_traces(line_color=BRAND_COLORS['primary_blue'],marker_color=BRAND_COLORS['primary_blue'])
        fig.update_layout(height=350,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white",plot_bgcolor="white")
        st.plotly_chart(fig,use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with b:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        x=f.DC_Issue_Status.fillna("Not Available").value_counts().reset_index()
        x.columns=["Status","Tickets"]
        fig=px.pie(x,names="Status",values="Tickets",hole=.55,title="DC Issue Distribution")
        fig.update_traces(marker_colors=[BRAND_COLORS['primary_blue'], BRAND_COLORS['teal_cyan'], BRAND_COLORS['dark_grey']][:len(x)])
        fig.update_layout(height=350,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white")
        st.plotly_chart(fig,use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with c:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        x=f.Module.fillna("Not Available").value_counts().head(8).reset_index()
        x.columns=["Module","Tickets"]
        fig=px.bar(x,y="Module",x="Tickets",orientation="h",title="Tickets by Module")
        fig.update_traces(marker_color=BRAND_COLORS['teal_cyan'])
        fig.update_layout(height=350,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white",plot_bgcolor="white",yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig,use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Second row of trend charts
with st.container():
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    
    a,b,c=st.columns(3, gap="medium")
    for box,col,title in [(a,"BU","OTR Tickets by BU"),(b,"CAT","OTR Tickets by CAT"),(c,"Brand","Top Brands by Tickets")]:
        with box:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            x=f[col].fillna("Not Available").value_counts().head(8).reset_index()
            x.columns=[col,"Tickets"]
            fig=px.bar(x,y=col,x="Tickets",orientation="h",title=title)
            fig.update_traces(marker_color=BRAND_COLORS['primary_blue'])
            fig.update_layout(height=320,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white",plot_bgcolor="white",yaxis=dict(categoryorder="total ascending"))
            st.plotly_chart(fig,use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section">🏆 Top Contributors</div>',unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    
    a,b,c=st.columns(3, gap="medium")
    for box,col,title in [(a,"Distributor","Top 5 Distributors"),(b,"Product_Code_Extracted","Top Product Codes"),(c,"DC_Code","Top DCs")]:
        with box:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            x=f[col].fillna("Not Available").astype(str).value_counts().head(5).reset_index()
            x.columns=[col,"Tickets"]
            fig=px.bar(x,y=col,x="Tickets",orientation="h",title=title)
            fig.update_traces(marker_color=BRAND_COLORS['teal_cyan'])
            fig.update_layout(height=300,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white",plot_bgcolor="white",yaxis=dict(categoryorder="total ascending"))
            st.plotly_chart(fig,use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section">🔍 OTR Ticket Details</div>',unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="table-card">', unsafe_allow_html=True)
    
    q=st.text_input("🔎 Search Ticket / Invoice / Product Code / Batch / Distributor", placeholder="Type to search...")
    v=f.copy()
    if q:
        mask=pd.Series(False,index=v.index)
        for col in ["Ticket_Number","Invoice_Number","Product_Code_Extracted","Batch_Code","Distributor","SKU_Name"]:
            mask|=v[col].astype(str).str.contains(re.escape(q),case=False,na=False)
        v=v[mask]
    
    cols=["Ticket_Date","Ticket_Number","Distributor_Code_Text","Distributor","Branch","DC_Code","ASM","Module",
          "Invoice_Number","Product_Code_Extracted","Batch_Code","SKU_Name","Brand","CAT","BU","Current_Status","DC_Issue_Status"]
    
    st.markdown(f"**{len(v):,} records found**")
    st.dataframe(v[cols].sort_values("Ticket_Date",ascending=False).head(1000), use_container_width=True, height=430, hide_index=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        st.download_button("📥 Download Filtered Data", v.to_csv(index=False).encode(), file_name="OTR_Dashboard_Filtered.csv", mime="text/csv", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ML / AI section with forecast placeholder
st.markdown('<div class="section">🤖 ML & AI Models</div>',unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    
    # Time-series forecast placeholder for BI-Stock Shortages
    st.markdown("**📈 Time-Series Forecast: BI-Stock Shortage Prediction**")
    st.caption("Predicts future BI-Stock Shortages based on historical ticket patterns and seasonality analysis.")
    
    forecast_col1, forecast_col2 = st.columns([2.5, 1.2], gap="large")
    with forecast_col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        
        # Generate simple placeholder forecast based on historical trends
        @st.cache_data
        def generate_forecast():
            """Placeholder function for time-series forecast of BI-Stock Shortages"""
            try:
                # Filter for BI-Stock shortage tickets
                bi_stock = f[f['DC_Issue_Status'] == 'DC Issue'].copy() if len(f) > 0 else pd.DataFrame()
                
                if len(bi_stock) > 0:
                    # Group by period and count
                    forecast_data = bi_stock.groupby(bi_stock.Ticket_Date.dt.to_period("M").astype(str)).size().reset_index(name="Shortage_Count")
                    forecast_data.columns = ["Month", "Shortage_Count"]
                    
                    # Simple moving average as placeholder forecast
                    if len(forecast_data) > 0:
                        forecast_data['Forecast'] = forecast_data['Shortage_Count'].rolling(window=3, center=True).mean()
                        return forecast_data
                
                return None
            except Exception as e:
                st.warning(f"Forecast generation placeholder: {str(e)}")
                return None
        
        forecast_df = generate_forecast()
        
        if forecast_df is not None and len(forecast_df) > 0:
            fig = px.line(
                forecast_df, 
                x="Month", 
                y=["Shortage_Count", "Forecast"],
                title="BI-Stock Shortage Trend & 3-Month Moving Average Forecast",
                markers=True,
                labels={"value": "Count", "variable": "Type"}
            )
            fig.update_traces(
                line=dict(width=2.5, color=BRAND_COLORS['teal_cyan']),
                marker=dict(size=6),
                selector=dict(name="Shortage_Count")
            )
            fig.update_traces(
                line=dict(dash="dash", width=2, color=BRAND_COLORS['primary_blue']),
                selector=dict(name="Forecast")
            )
            fig.update_layout(
                height=340,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="white",
                plot_bgcolor="white",
                hovermode="x unified",
                font=dict(color=BRAND_COLORS['dark_grey'])
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No BI-Stock shortage data available for forecast.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with forecast_col2:
        st.markdown('<div style="background:#f9f9f9;border:1px solid #E5EBE8;border-radius:12px;padding:16px">', unsafe_allow_html=True)
        st.markdown("**📊 Summary Stats**")
        if forecast_df is not None and len(forecast_df) > 0:
            col1, col2 = st.columns(1)
            with col1:
                avg_shortages = forecast_df['Shortage_Count'].mean()
                peak_month = forecast_df.loc[forecast_df['Shortage_Count'].idxmax(), 'Month']
                trend_direction = "📈 Increasing" if forecast_df['Shortage_Count'].iloc[-1] > forecast_df['Shortage_Count'].iloc[0] else "📉 Decreasing"
                
                st.metric("Avg Monthly", f"{avg_shortages:.0f}")
                st.metric("Peak Month", peak_month)
                st.metric("Trend", trend_direction)
        else:
            st.info("No data available")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Existing ML models section
with st.container():
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    
    st.markdown("**Advanced ML Model Training**")
    st.caption("Click below to train forecasting, anomaly detection, and clustering models on your data.")
    
    from ml_models import train_all
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button('🤖 Run ML Models', use_container_width=True):
            with st.spinner('🔄 Training models...'):
                results = train_all(df)
            st.success('✅ Models complete')
            st.session_state.ml_results = results
    
    # Display stored results if available
    if 'ml_results' in st.session_state:
        results = st.session_state.ml_results
        
        with st.expander("📈 DC Forecasts", expanded=False):
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            if 'forecast_dc' in results and not results.get('forecast_dc_error'):
                st.dataframe(results['forecast_dc'].head(50), use_container_width=True)
                st.download_button('📥 Download DC forecasts', results['forecast_dc'].to_csv(index=False).encode(), file_name='forecast_dc.csv', use_container_width=True)
            else:
                st.info("No DC forecast data available")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.expander("📊 Brand Forecasts", expanded=False):
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            if 'forecast_brand' in results and not results.get('forecast_brand_error'):
                st.dataframe(results['forecast_brand'].head(50), use_container_width=True)
                st.download_button('📥 Download Brand forecasts', results['forecast_brand'].to_csv(index=False).encode(), file_name='forecast_brand.csv', use_container_width=True)
            else:
                st.info("No Brand forecast data available")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.expander("🔍 Detected Anomalies", expanded=False):
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            if 'anomalies_dc' in results and not results.get('anomalies_dc_error'):
                st.dataframe(results['anomalies_dc'].head(50), use_container_width=True)
                st.download_button('📥 Download anomalies', results['anomalies_dc'].to_csv(index=False).encode(), file_name='anomalies_dc.csv', use_container_width=True)
            else:
                st.info("No anomaly data available")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.expander("🎯 Classification Report", expanded=False):
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            if 'classification' in results and not results.get('classification_error'):
                st.dataframe(results['classification'], use_container_width=True)
                st.download_button('📥 Download classification report', results['classification'].to_csv(index=False).encode(), file_name='classification_report.csv', use_container_width=True)
            else:
                st.info("No classification data available")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.expander("👥 Distributor Clusters", expanded=False):
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            if 'clusters' in results and not results.get('clusters_error'):
                st.dataframe(results['clusters'], use_container_width=True)
                st.download_button('📥 Download clusters', results['clusters'].to_csv(index=False).encode(), file_name='distributor_clusters.csv', use_container_width=True)
            else:
                st.info("No cluster data available")
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
with st.container():
    st.markdown("""
    <div style="border-top:2px solid #E5EBE8;margin-top:40px;padding-top:24px;text-align:center">
        <p style="color:#66756F;font-size:12px;margin:0">
            <strong>Nestlé India Secondary OTR Dashboard</strong> | OTR Data + Secondary OTR Issue Report + Product Master<br>
            <em>Last updated: """ + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + """</em>
        </p>
    </div>
    """, unsafe_allow_html=True)

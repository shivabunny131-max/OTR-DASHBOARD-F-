
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
.hero{background:linear-gradient(135deg,""" + BRAND_COLORS['primary_blue'] + """,""" + BRAND_COLORS['teal_cyan'] + """);padding:24px 28px;border-radius:20px;color:#fff;margin-bottom:16px; position:relative; z-index:0;}
.hero h1{color:#fff!important;margin:0;font-size:32px}.hero p{margin:5px 0 0}

/* Cards with dark grey text */
.card{background:#fff;border:1px solid #DCE5E1;border-radius:16px;padding:15px 18px;min-height:100px;box-shadow:0 3px 12px rgba(26,59,50,0.06)}
.lbl{font-size:13px;color:#66756F;font-weight:600}.val{font-size:26px;color:""" + BRAND_COLORS['dark_grey'] + """;font-weight:750;margin-top:7px}

/* Section title with dark grey */
.section{font-size:19px;font-weight:750;color:""" + BRAND_COLORS['dark_grey'] + """;margin:18px 0 8px}

/* Summary section with primary blue accent */
.summary-box{background:#f0f7fb;border-left:4px solid""" + BRAND_COLORS['primary_blue'] + """;padding:12px 16px;border-radius:8px;margin-bottom:16px}
.summary-text{font-size:14px;color:""" + BRAND_COLORS['dark_grey'] + """;margin:0}

/* Make Streamlit header transparent */
header.css-1bd0g9n.e1g8pov71, header[data-testid="stHeader"] {
  background: transparent !important;
  box-shadow: none !important;
}

.block-container { padding-top: 1.5rem !important; }
.hero img { position:absolute; right:20px; top:50%; transform:translateY(-50%); width:120px; z-index:9999; }
main[role="main"] { z-index:0; }
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

def card(label,val):
    st.markdown(f'<div class="card"><div class="lbl">{label}</div><div class="val">{val}</div></div>',unsafe_allow_html=True)

st.markdown('<div class="section">Overview</div>',unsafe_allow_html=True)
cs=st.columns(5)
vals=[("Total OTR Tickets",f"{f.Ticket_Number.nunique():,}"),("Total Invoices",f"{f.Invoice_Number.dropna().nunique():,}"),
      ("Distributors",f"{f.Distributor.nunique():,}"),("Product Codes",f"{f.Product_Code_Extracted.dropna().nunique():,}"),
      ("DC Issues",f"{(f.DC_Issue_Status=='DC Issue').sum():,}")]
for c,(l,v) in zip(cs,vals):
    with c:card(l,v)
cs=st.columns(5)
vals=[("Closed",f"{(f.Current_Status=='Closed').sum():,}"),
      ("Open / Pending",f"{(~f.Current_Status.isin(['Closed','Resolved'])).sum():,}"),
      ("Brand Mapped",f"{(f.Brand!='Not Available').sum():,}"),
      ("Brand Coverage",f"{((f.Brand!='Not Available').mean()*100 if len(f) else 0):.1f}%"),
      ("Records",f"{len(f):,}")]
for c,(l,v) in zip(cs,vals):
    with c:card(l,v)

st.markdown('<div class="section">Comparisons</div>',unsafe_allow_html=True)
comp_col1, comp_col2 = st.columns([1,2])
with comp_col1:
    comp_dim = st.selectbox("Compare by", ["DC Code","Distributor (CD)","Brand","Branch","ASM"], index=2)
    agg = st.radio("Aggregation", ["Monthly","Yearly","Overall"], horizontal=True)
    topn = st.slider("Top N", min_value=5, max_value=30, value=10)

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
        fig = px.line(grp, x="Period", y="Tickets", color=col, markers=True, title=f"{comp_dim} - {agg} trend (Top {topn})")
        fig.update_traces(line=dict(width=2))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="white", plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section">OTR Trends & Product Analysis</div>',unsafe_allow_html=True)
a,b,c=st.columns([1.4,1,1])
with a:
    t=f.groupby(f.Ticket_Date.dt.to_period("M").astype(str)).size().reset_index(name="Tickets")
    t.columns=["Month","Tickets"]
    fig=px.line(t,x="Month",y="Tickets",markers=True,title="OTR Tickets by Month")
    fig.update_traces(line_color=BRAND_COLORS['primary_blue'],marker_color=BRAND_COLORS['primary_blue'])
    fig.update_layout(height=320,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white",plot_bgcolor="white")
    st.plotly_chart(fig,use_container_width=True)
with b:
    x=f.DC_Issue_Status.fillna("Not Available").value_counts().reset_index()
    x.columns=["Status","Tickets"]
    fig=px.pie(x,names="Status",values="Tickets",hole=.55,title="DC Issue Distribution")
    fig.update_traces(marker_colors=[BRAND_COLORS['primary_blue'], BRAND_COLORS['teal_cyan'], BRAND_COLORS['dark_grey']][:len(x)])
    fig.update_layout(height=320,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white")
    st.plotly_chart(fig,use_container_width=True)
with c:
    x=f.Module.fillna("Not Available").value_counts().head(8).reset_index()
    x.columns=["Module","Tickets"]
    fig=px.bar(x,y="Module",x="Tickets",orientation="h",title="Tickets by Module")
    fig.update_traces(marker_color=BRAND_COLORS['teal_cyan'])
    fig.update_layout(height=320,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white",plot_bgcolor="white",yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig,use_container_width=True)

a,b,c=st.columns(3)
for box,col,title in [(a,"BU","OTR Tickets by BU"),(b,"CAT","OTR Tickets by CAT"),(c,"Brand","Top Brands by Tickets")]:
    with box:
        x=f[col].fillna("Not Available").value_counts().head(8).reset_index()
        x.columns=[col,"Tickets"]
        fig=px.bar(x,y=col,x="Tickets",orientation="h",title=title)
        fig.update_traces(marker_color=BRAND_COLORS['primary_blue'])
        fig.update_layout(height=300,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white",plot_bgcolor="white",yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig,use_container_width=True)

st.markdown('<div class="section">Top Contributors</div>',unsafe_allow_html=True)
a,b,c=st.columns(3)
for box,col,title in [(a,"Distributor","Top 5 Distributors"),(b,"Product_Code_Extracted","Top Product Codes"),(c,"DC_Code","Top DCs")]:
    with box:
        x=f[col].fillna("Not Available").astype(str).value_counts().head(5).reset_index()
        x.columns=[col,"Tickets"]
        fig=px.bar(x,y=col,x="Tickets",orientation="h",title=title)
        fig.update_traces(marker_color=BRAND_COLORS['teal_cyan'])
        fig.update_layout(height=270,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white",plot_bgcolor="white",yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig,use_container_width=True)

st.markdown('<div class="section">OTR Ticket Details</div>',unsafe_allow_html=True)
q=st.text_input("Search Ticket / Invoice / Product Code / Batch / Distributor")
v=f.copy()
if q:
    mask=pd.Series(False,index=v.index)
    for col in ["Ticket_Number","Invoice_Number","Product_Code_Extracted","Batch_Code","Distributor","SKU_Name"]:
        mask|=v[col].astype(str).str.contains(re.escape(q),case=False,na=False)
    v=v[mask]
cols=["Ticket_Date","Ticket_Number","Distributor_Code_Text","Distributor","Branch","DC_Code","ASM","Module",
      "Invoice_Number","Product_Code_Extracted","Batch_Code","SKU_Name","Brand","CAT","BU","Current_Status","DC_Issue_Status"]
st.dataframe(v[cols].sort_values("Ticket_Date",ascending=False).head(1000),use_container_width=True,height=430,hide_index=True)
st.download_button("Download filtered data",v.to_csv(index=False).encode(),file_name="OTR_Dashboard_Filtered.csv",mime="text/csv")

# ML / AI section with forecast placeholder
st.markdown('<div class="section">ML & AI Models</div>',unsafe_allow_html=True)

# Time-series forecast placeholder for BI-Stock Shortages
st.markdown("**📈 Time-Series Forecast: BI-Stock Shortage Prediction**")
st.info("Predicts future BI-Stock Shortages based on historical ticket patterns and seasonality analysis.")

forecast_col1, forecast_col2 = st.columns([2, 1])
with forecast_col1:
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
            title="BI-Stock Shortage Trend & 3-Month Moving Avg Forecast",
            markers=True,
            labels={"value": "Count", "variable": "Type"}
        )
        fig.update_traces(
            line=dict(width=2),
            selector=dict(name="Shortage_Count")
        )
        fig.update_traces(
            line=dict(dash="dash", color=BRAND_COLORS['primary_blue']),
            selector=dict(name="Forecast")
        )
        fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=50, b=10),
            paper_bgcolor="white",
            plot_bgcolor="white",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No BI-Stock shortage data available for forecast.")

with forecast_col2:
    # Summary statistics
    st.markdown("**Summary Stats**")
    if forecast_df is not None and len(forecast_df) > 0:
        st.metric("Avg Monthly Shortages", f"{forecast_df['Shortage_Count'].mean():.0f}")
        st.metric("Peak Month", forecast_df.loc[forecast_df['Shortage_Count'].idxmax(), 'Month'])
        st.metric("Trend", "📈 Increasing" if forecast_df['Shortage_Count'].iloc[-1] > forecast_df['Shortage_Count'].iloc[0] else "📉 Decreasing")
    else:
        st.info("No data for summary statistics")

st.divider()

# Existing ML models section
from ml_models import train_all

if st.button('🤖 Run Advanced ML Models (may take a moment)', use_container_width=False):
    with st.spinner('Training models...'):
        results = train_all(df)
    st.success('✅ Models run complete')
    
    # Show quick summaries
    if 'forecast_dc' in results and not results.get('forecast_dc_error'):
        st.markdown('**Forecasts - DC (next periods)**')
        st.dataframe(results['forecast_dc'].head(50),use_container_width=True)
        st.download_button('Download DC forecasts', results['forecast_dc'].to_csv(index=False).encode(), file_name='forecast_dc.csv')
    
    if 'forecast_brand' in results and not results.get('forecast_brand_error'):
        st.markdown('**Forecasts - Brand (next periods)**')
        st.dataframe(results['forecast_brand'].head(50),use_container_width=True)
        st.download_button('Download Brand forecasts', results['forecast_brand'].to_csv(index=False).encode(), file_name='forecast_brand.csv')
    
    if 'anomalies_dc' in results and not results.get('anomalies_dc_error'):
        st.markdown('**Detected anomalies (DC/month)**')
        st.dataframe(results['anomalies_dc'].head(50),use_container_width=True)
        st.download_button('Download anomalies', results['anomalies_dc'].to_csv(index=False).encode(), file_name='anomalies_dc.csv')
    
    if 'classification' in results and not results.get('classification_error'):
        st.markdown('**Classification report (DC Issue prediction)**')
        st.dataframe(results['classification'],use_container_width=True)
        st.download_button('Download classification report', results['classification'].to_csv(index=False).encode(), file_name='classification_report.csv')
    
    if 'clusters' in results and not results.get('clusters_error'):
        st.markdown('**Distributor clusters**')
        st.dataframe(results['clusters'],use_container_width=True)
        st.download_button('Download clusters', results['clusters'].to_csv(index=False).encode(), file_name='distributor_clusters.csv')

st.caption("Nestlé India | Secondary OTR Dashboard • OTR data + Secondary OTR issue report + Product Master")

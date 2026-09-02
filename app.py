
import os,re
import pandas as pd
import streamlit as st
import plotly.express as px
import base64

st.set_page_config(page_title="Nestlé India | Secondary OTR Dashboard",page_icon="📊",layout="wide")
ROOT=os.path.dirname(os.path.abspath(__file__))
PATH=os.path.join(ROOT,"data","OTR_Dashboard_Final.csv")

@st.cache_data
def load():
    d=pd.read_csv(PATH,low_memory=False)
    d["Ticket_Date"]=pd.to_datetime(d["Ticket_Date"],errors="coerce")
    return d
df=load()

st.markdown("""
<style>
/* App background */
.stApp{background:#F5F7F6}.block-container{max-width:1550px;padding-top:1rem}

/* Hero */
.hero{background:linear-gradient(135deg,#006B4F,#008A61);padding:24px 28px;border-radius:20px;color:#fff;margin-bottom:16px; position:relative; z-index:0;}
.hero h1{color:#fff!important;margin:0;font-size:32px}.hero p{margin:5px 0 0}

/* cards */
.card{background:#fff;border:1px solid #DCE5E1;border-radius:16px;padding:15px 18px;min-height:100px;box-shadow:0 3px 12px #173B3210}
.lbl{font-size:13px;color:#66756F;font-weight:600}.val{font-size:26px;color:#173B32;font-weight:750;margin-top:7px}

/* Section title */
.section{font-size:19px;font-weight:750;color:#173B32;margin:18px 0 8px}

/* Make Streamlit header transparent so logo is visible */
header.css-1bd0g9n.e1g8pov71, header[data-testid="stHeader"] {
  background: transparent !important;
  box-shadow: none !important;
}

/* Adjust top padding of block-container to prevent overlap */
.block-container { padding-top: 1.5rem !important; }

/* Logo absolute positioning inside hero */
.hero img { position:absolute; right:20px; top:50%; transform:translateY(-50%); width:120px; z-index:9999; }

/* Ensure content below hero is above header */
main[role="main"] { z-index:0; }
</style>
""",unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## NESTLÉ INDIA")
    st.caption("Secondary OTR Dashboard")
    st.divider()
    st.markdown("### Filters")
    dates=st.date_input("OTR Ticket Date",value=(df.Ticket_Date.min().date(),df.Ticket_Date.max().date()))
    f=df.copy()
    if isinstance(dates,tuple) and len(dates)==2:
        f=f[f.Ticket_Date.between(pd.Timestamp(dates[0]),pd.Timestamp(dates[1]))]
    for label,col in [("Branch","Branch"),("DC Code","DC_Code"),("ASM","ASM"),("ASM Zone","ASM_Zone"),
                      ("Brand","Brand"),("CAT","CAT"),("BU","BU"),("Module Name","Module"),
                      ("Distributor","Distributor"),("Status","Current_Status"),("DC Issue","DC_Issue_Status")]:
        vals=sorted(f[col].dropna().astype(str).unique()) if col in f else []
        sel=st.multiselect(label,vals)
        if sel:f=f[f[col].astype(str).isin(sel)]

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
        x = f[col].fillna("Not Available").astype(str).value_counts().head(topn).reset_index()
        x.columns = [col, "Tickets"]
        fig = px.bar(x, y=col, x="Tickets", orientation="h", title=f"Top {topn} by {comp_dim}")
        fig.update_traces(marker_color="#2F7E5E")
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
    fig.update_traces(line_color="#007A53",marker_color="#007A53")
    fig.update_layout(height=320,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white",plot_bgcolor="white")
    st.plotly_chart(fig,use_container_width=True)
with b:
    x=f.DC_Issue_Status.fillna("Not Available").value_counts().reset_index()
    x.columns=["Status","Tickets"]
    fig=px.pie(x,names="Status",values="Tickets",hole=.55,title="DC Issue Distribution")
    fig.update_layout(height=320,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white")
    st.plotly_chart(fig,use_container_width=True)
with c:
    x=f.Module.fillna("Not Available").value_counts().head(8).reset_index()
    x.columns=["Module","Tickets"]
    fig=px.bar(x,y="Module",x="Tickets",orientation="h",title="Tickets by Module")
    fig.update_traces(marker_color="#00A36C")
    fig.update_layout(height=320,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white",plot_bgcolor="white",yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig,use_container_width=True)

a,b,c=st.columns(3)
for box,col,title in [(a,"BU","OTR Tickets by BU"),(b,"CAT","OTR Tickets by CAT"),(c,"Brand","Top Brands by Tickets")]:
    with box:
        x=f[col].fillna("Not Available").value_counts().head(8).reset_index()
        x.columns=[col,"Tickets"]
        fig=px.bar(x,y=col,x="Tickets",orientation="h",title=title)
        fig.update_traces(marker_color="#007A53")
        fig.update_layout(height=300,margin=dict(l=10,r=10,t=50,b=10),paper_bgcolor="white",plot_bgcolor="white",yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig,use_container_width=True)

st.markdown('<div class="section">Top Contributors</div>',unsafe_allow_html=True)
a,b,c=st.columns(3)
for box,col,title in [(a,"Distributor","Top 5 Distributors"),(b,"Product_Code_Extracted","Top Product Codes"),(c,"DC_Code","Top DCs")]:
    with box:
        x=f[col].fillna("Not Available").astype(str).value_counts().head(5).reset_index()
        x.columns=[col,"Tickets"]
        fig=px.bar(x,y=col,x="Tickets",orientation="h",title=title)
        fig.update_traces(marker_color="#2F7E5E")
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

# ML / AI section
st.markdown('<div class="section">ML & AI Models</div>',unsafe_allow_html=True)
from ml_models import train_all

if st.button('Run ML models (may take a moment)'):
    with st.spinner('Training models...'):
        results = train_all(df)
    st.success('Models run complete')
    # show quick summaries
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

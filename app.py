
import os,re
import pandas as pd
import streamlit as st
import plotly.express as px

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
.stApp{background:#F5F7F6}.block-container{max-width:1550px;padding-top:1rem}
.hero{background:linear-gradient(135deg,#006B4F,#008A61);padding:24px 28px;border-radius:20px;color:#fff;margin-bottom:16px}
.hero h1{color:#fff!important;margin:0;font-size:32px}.hero p{margin:5px 0 0}
.card{background:#fff;border:1px solid #DCE5E1;border-radius:16px;padding:15px 18px;min-height:100px;box-shadow:0 3px 12px #173B3210}
.lbl{font-size:13px;color:#66756F;font-weight:600}.val{font-size:26px;color:#173B32;font-weight:750;margin-top:7px}
.section{font-size:19px;font-weight:750;color:#173B32;margin:18px 0 8px}
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

st.markdown('<div class="hero"><h1>NESTLÉ INDIA — SECONDARY OTR DASHBOARD</h1><p>OTR Monitoring | Root Cause Analysis | Product Excellence</p></div>',unsafe_allow_html=True)

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
st.caption("Nestlé India | Secondary OTR Dashboard • OTR data + Secondary OTR issue report + Product Master")

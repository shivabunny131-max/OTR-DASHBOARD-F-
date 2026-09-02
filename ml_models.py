import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from statsmodels.tsa.holtwinters import ExponentialSmoothing

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(ROOT, "data", "OTR_Dashboard_Final.csv")
RESULTS_DIR = os.path.join(ROOT, "data", "ml_results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def _prepare(df):
    df = df.copy()
    df['Ticket_Date'] = pd.to_datetime(df['Ticket_Date'], errors='coerce')
    df = df.dropna(subset=['Ticket_Date'])
    return df


def forecast_top_entities(df, by_col='DC_Code', period='M', topn=5, periods_forecast=3):
    df = _prepare(df)
    col = by_col
    monthly = df.groupby([pd.Grouper(key='Ticket_Date', freq='M'), df[col].fillna('Not Available').astype(str)]).size().reset_index(name='Tickets')
    monthly.columns = ['Period', col, 'Tickets']
    # pick top entities by total
    top_entities = monthly.groupby(col)['Tickets'].sum().nlargest(topn).index.tolist()
    results = []
    for ent in top_entities:
        ser = monthly.loc[monthly[col]==ent].set_index('Period').reindex(pd.date_range(monthly['Period'].min(), monthly['Period'].max(), freq='M'))
        ser = monthly[monthly[col]==ent].set_index('Period')['Tickets'].asfreq('M').fillna(0)
        try:
            model = ExponentialSmoothing(ser, trend='add', seasonal=None).fit()
            pred = model.forecast(periods_forecast)
        except Exception:
            # fallback to mean
            pred = pd.Series([ser.mean()]*periods_forecast, index=pd.date_range(ser.index[-1]+pd.offsets.MonthEnd(1), periods=periods_forecast, freq='M'))
        dfp = pd.DataFrame({'Period': pred.index.astype(str), col: ent, 'Predicted': pred.values})
        results.append(dfp)
    out = pd.concat(results, ignore_index=True) if results else pd.DataFrame()
    out.to_csv(os.path.join(RESULTS_DIR, f'forecast_{col}.csv'), index=False)
    return out


def detect_anomalies(df, by_col='DC_Code', period='M', topn=10):
    df = _prepare(df)
    col = by_col
    monthly = df.groupby([pd.Grouper(key='Ticket_Date', freq='M'), df[col].fillna('Not Available').astype(str)]).size().reset_index(name='Tickets')
    monthly.columns = ['Period', col, 'Tickets']
    # simple z-score anomalies per entity
    monthly['Period'] = pd.to_datetime(monthly['Period'])
    results = []
    for ent, g in monthly.groupby(col):
        if len(g) < 3:
            continue
        z = (g['Tickets'] - g['Tickets'].mean()) / (g['Tickets'].std(ddof=0) + 1e-9)
        mask = (z.abs() > 3)
        tmp = g.loc[mask, ['Period', col, 'Tickets']].copy()
        tmp['z'] = z[mask]
        results.append(tmp)
    out = pd.concat(results, ignore_index=True) if results else pd.DataFrame()
    out.to_csv(os.path.join(RESULTS_DIR, f'anomalies_{col}.csv'), index=False)
    return out


def classify_dc_issue(df, target_col='DC_Issue_Status'):
    df = _prepare(df)
    # target: whether it's a DC Issue (binary)
    y = (df[target_col] == 'DC Issue').astype(int)
    # select simple features
    X = pd.DataFrame()
    X['month'] = df['Ticket_Date'].dt.month.fillna(0).astype(int)
    for c in ['Brand', 'BU', 'CAT', 'Module']:
        vals = df[c].fillna('NA').astype(str)
        dums = pd.get_dummies(vals, prefix=c).iloc[:, :10]  # limit columns
        X = pd.concat([X, dums], axis=1)
    # align sizes
    X = X.fillna(0).astype(float)
    if X.shape[0] < 20:
        return {'error': 'Not enough rows to train classifier'}
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(Xtr, ytr)
    preds = clf.predict(Xte)
    report = classification_report(yte, preds, output_dict=True)
    rep_df = pd.DataFrame(report).transpose()
    rep_df.to_csv(os.path.join(RESULTS_DIR, 'classification_report.csv'))
    return rep_df


def cluster_distributors(df, n_clusters=4):
    df = _prepare(df)
    distr = df.groupby('Distributor').agg(total_tickets=('Ticket_Number', 'nunique'), months_active=('Ticket_Date', lambda x: x.dt.to_period('M').nunique()))
    distr['avg_per_month'] = (distr['total_tickets'] / (distr['months_active'].replace(0,1))).fillna(0)
    X = distr[['total_tickets', 'avg_per_month']].fillna(0)
    k = min(n_clusters, max(1, len(X)))
    if len(X) < 2:
        distr['cluster'] = 0
    else:
        km = KMeans(n_clusters=k, random_state=42)
        distr['cluster'] = km.fit_predict(X)
    distr.reset_index().to_csv(os.path.join(RESULTS_DIR, 'distributor_clusters.csv'), index=False)
    return distr.reset_index()


def train_all(df):
    results = {}
    try:
        results['forecast_dc'] = forecast_top_entities(df, by_col='DC_Code', topn=5, periods_forecast=3)
    except Exception as e:
        results['forecast_dc_error'] = str(e)
    try:
        results['forecast_brand'] = forecast_top_entities(df, by_col='Brand', topn=5, periods_forecast=3)
    except Exception as e:
        results['forecast_brand_error'] = str(e)
    try:
        results['anomalies_dc'] = detect_anomalies(df, by_col='DC_Code')
    except Exception as e:
        results['anomalies_dc_error'] = str(e)
    try:
        results['classification'] = classify_dc_issue(df)
    except Exception as e:
        results['classification_error'] = str(e)
    try:
        results['clusters'] = cluster_distributors(df)
    except Exception as e:
        results['clusters_error'] = str(e)
    return results


if __name__ == '__main__':
    df = pd.read_csv(DATA_PATH, low_memory=False)
    out = train_all(df)
    print({k:(v.shape[0] if hasattr(v, 'shape') else str(v)) for k,v in out.items()})

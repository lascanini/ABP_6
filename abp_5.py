"""
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

# --- Configuración visual global ---
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    'figure.dpi': 150,
    'font.family': 'DejaVu Sans',
    'axes.titlesize': 13,
    'axes.labelsize': 11,
})
OUTPUT = "C:\\Users\\franc\\PycharmProjects\\GestionContactos\\outputs\\"

# Asegura que la carpeta de salida exista antes de guardar gráficos.
Path(OUTPUT).mkdir(parents=True, exist_ok=True)


def safe_read_csv(csv_path, **kwargs):
    """Usa pandas.read_csv y, si falla por bug de versión, aplica fallback interno."""
    try:
        return pd.read_csv(csv_path, **kwargs)
    except TypeError as exc:
        if "engine_specified" not in str(exc):
            raise
        from pandas.io.parsers.readers import _read
        return _read(csv_path, kwargs)

# =============================================================
# LECCION 1: CARGA Y ANALISIS INICIAL DEL DATASET (IDA / EDA)
# =============================================================
print("\n" + "="*60)
print("LECCION 1 - CARGA Y ANALISIS INICIAL")
print("="*60)

base_dir = Path(__file__).resolve().parent
csv_candidates = [
    base_dir / "data" / "online_retail.csv",
    base_dir / "data" / "Online_Retail.csv",
    base_dir / "data" / "Nueva carpeta" / "Online_Retail.csv",
]

csv_path = next((p for p in csv_candidates if p.exists()), None)
if csv_path is None:
    raise FileNotFoundError(
        "No se encontro el dataset Online Retail en rutas esperadas dentro de data/."
    )

df = safe_read_csv(
    csv_path,
    sep=";",
    encoding="utf-8-sig",
    decimal=","
)

print(f"Dataset cargado desde: {csv_path}")

# Renombramos columnas para facilitar trabajo
df.columns = [c.strip() for c in df.columns]

# Convertir fecha
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], dayfirst=True, errors='coerce')

print("\n Primeras filas:")
print(df.head())
print(f"\n Dimensiones: {df.shape[0]} filas × {df.shape[1]} columnas")

print("\n Tipos de variables:")
for col in df.columns:
    dtype = df[col].dtype
    vtype = "Categórica" if dtype == object else "Numérica"
    print(f"  {col:15s} → {str(dtype):10s} ({vtype})")

print("\n Valores faltantes por columna:")
missing = df.isnull().sum()
print(missing[missing > 0])

# Limpieza básica
df_clean = df.dropna(subset=['CustomerID', 'Description'])
df_clean = df_clean[df_clean['Quantity'] > 0]
df_clean = df_clean[df_clean['UnitPrice'] > 0]

# Columna Revenue (ingreso por línea)
df_clean = df_clean.copy()
df_clean['Revenue'] = df_clean['Quantity'] * df_clean['UnitPrice']

print(f"\n Registros tras limpieza: {len(df_clean)} (de {len(df)} originales)")
print(f" Eliminados: {len(df) - len(df_clean)} registros")

# =============================================================
# LECCIÓN 2: ESTADÍSTICA DESCRIPTIVA
# =============================================================
print("\n" + "="*60)
print("LECCION 2 - ESTADISTICA DESCRIPTIVA")
print("="*60)

num_cols = ['Quantity', 'UnitPrice', 'Revenue']

stats = pd.DataFrame()
for col in num_cols:
    s = df_clean[col]
    stats[col] = {
        'Media':          s.mean(),
        'Mediana':        s.median(),
        'Moda':           s.mode()[0],
        'Varianza':       s.var(),
        'Desv. Estándar': s.std(),
        'Q1 (25%)':       s.quantile(0.25),
        'Q3 (75%)':       s.quantile(0.75),
        'P90':            s.quantile(0.90),
        'Min':            s.min(),
        'Max':            s.max(),
    }

print("\n Medidas de tendencia central y dispersión:")
print(stats.round(2).to_string())

# ---- Detección de outliers con IQR ----
print("\n Detección de valores atípicos (método IQR):")
for col in num_cols:
    Q1 = df_clean[col].quantile(0.25)
    Q3 = df_clean[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = df_clean[(df_clean[col] < lower) | (df_clean[col] > upper)]
    pct = len(outliers) / len(df_clean) * 100
    print(f"  {col}: {len(outliers)} outliers ({pct:.1f}%) | rango válido [{lower:.2f}, {upper:.2f}]")

# ---- Histogramas ----
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
fig.suptitle("Distribución de Variables Numéricas", fontsize=15, fontweight='bold', y=1.02)

colors = ['#4C72B0', '#55A868', '#C44E52']
for ax, col, color in zip(axes, num_cols, colors):
    data = df_clean[col].clip(upper=df_clean[col].quantile(0.99))  # recorte p99 para visibilidad
    ax.hist(data, bins=40, color=color, alpha=0.8, edgecolor='white')
    ax.axvline(data.mean(), color='black', linestyle='--', linewidth=1.5, label=f'Media: {data.mean():.1f}')
    ax.axvline(data.median(), color='red', linestyle=':', linewidth=1.5, label=f'Mediana: {data.median():.1f}')
    ax.set_title(col)
    ax.set_xlabel("Valor")
    ax.set_ylabel("Frecuencia")
    ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig(OUTPUT + "01_histogramas.png", bbox_inches='tight')
plt.close()
print("\n Gráfico guardado: 01_histogramas.png")

# ---- Boxplots ----
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle("Boxplots – Detección de Valores Atípicos", fontsize=15, fontweight='bold')

for ax, col, color in zip(axes, num_cols, colors):
    data = df_clean[col].clip(upper=df_clean[col].quantile(0.99))
    ax.boxplot(data, patch_artist=True,
               boxprops=dict(facecolor=color, alpha=0.6),
               medianprops=dict(color='black', linewidth=2),
               whiskerprops=dict(linewidth=1.5),
               capprops=dict(linewidth=1.5))
    ax.set_title(col)
    ax.set_ylabel("Valor")
    ax.set_xticklabels([col])

plt.tight_layout()
plt.savefig(OUTPUT + "02_boxplots.png", bbox_inches='tight')
plt.close()
print("Gráfico guardado: 02_boxplots.png")

# =============================================================
# LECCIÓN 3: CORRELACIÓN
# =============================================================
print("\n" + "="*60)
print("LECCION 3 - CORRELACION")
print("="*60)

corr_matrix = df_clean[num_cols].corr(method='pearson')
print("\n Matriz de correlación de Pearson:")
print(corr_matrix.round(3).to_string())

# ---- Heatmap de correlación ----
fig, ax = plt.subplots(figsize=(7, 5))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
sns.heatmap(corr_matrix, annot=True, fmt=".3f", cmap='coolwarm',
            center=0, vmin=-1, vmax=1,
            linewidths=0.5, square=True, ax=ax,
            annot_kws={"size": 12})
ax.set_title("Matriz de Correlación de Pearson\n(Quantity, UnitPrice, Revenue)", fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUT + "03_correlacion_heatmap.png", bbox_inches='tight')
plt.close()
print("Gráfico guardado: 03_correlacion_heatmap.png")

# ---- Scatterplots ----
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Scatterplots entre Variables Numéricas", fontsize=14, fontweight='bold')

pairs = [('Quantity', 'Revenue'), ('UnitPrice', 'Revenue'), ('Quantity', 'UnitPrice')]
for ax, (x, y) in zip(axes, pairs):
    sample = df_clean.sample(min(500, len(df_clean)), random_state=42)
    ax.scatter(sample[x], sample[y], alpha=0.4, s=20, color='#4C72B0')
    # línea de tendencia
    m, b = np.polyfit(df_clean[x], df_clean[y], 1)
    xline = np.linspace(df_clean[x].min(), df_clean[x].quantile(0.99), 100)
    ax.plot(xline, m * xline + b, color='red', linewidth=2, label=f'r={df_clean[x].corr(df_clean[y]):.3f}')
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(f"{x} vs {y}")
    ax.legend()
    ax.set_xlim(left=0, right=df_clean[x].quantile(0.99))
    ax.set_ylim(bottom=0, top=df_clean[y].quantile(0.99))

plt.tight_layout()
plt.savefig(OUTPUT + "04_scatterplots.png", bbox_inches='tight')
plt.close()
print("Gráfico guardado: 04_scatterplots.png")

# =============================================================
# LECCIÓN 4: REGRESIÓN LINEAL (con numpy – sin statsmodels)
# =============================================================
print("\n" + "="*60)
print("LECCION 4 - REGRESION LINEAL")
print("="*60)

# --- Regresión simple: Quantity → Revenue ---
X = df_clean['Quantity'].values
y = df_clean['Revenue'].values

# Regresión con numpy polyfit
coeffs = np.polyfit(X, y, 1)
beta1, beta0 = coeffs
y_pred = beta0 + beta1 * X

# Métricas manuales
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - y.mean()) ** 2)
r2 = 1 - ss_res / ss_tot
mse = np.mean((y - y_pred) ** 2)
mae = np.mean(np.abs(y - y_pred))
rmse = np.sqrt(mse)

print("\n Regresión Simple: Quantity → Revenue")
print(f" Ecuación: Revenue = {beta0:.4f} + {beta1:.4f} × Quantity")
print(f" R²:   {r2:.4f}")
print(f" MSE:  {mse:.4f}")
print(f" MAE:  {mae:.4f}")
print(f" RMSE: {rmse:.4f}")

# --- Regresión múltiple: Quantity + UnitPrice → Revenue ---
X_multi = np.column_stack([np.ones(len(df_clean)), df_clean['Quantity'], df_clean['UnitPrice']])
y_multi = df_clean['Revenue'].values
# OLS: beta = (X'X)^{-1} X'y
beta_multi = np.linalg.lstsq(X_multi, y_multi, rcond=None)[0]
y_pred_m = X_multi @ beta_multi

ss_res_m = np.sum((y_multi - y_pred_m) ** 2)
ss_tot_m = np.sum((y_multi - y_multi.mean()) ** 2)
r2_m = 1 - ss_res_m / ss_tot_m
mse_m = np.mean((y_multi - y_pred_m) ** 2)
mae_m = np.mean(np.abs(y_multi - y_pred_m))

print("\n Regresión Múltiple: Quantity + UnitPrice → Revenue")
print(f" Intercepto:  {beta_multi[0]:.4f}")
print(f" β Quantity:  {beta_multi[1]:.4f}")
print(f" β UnitPrice: {beta_multi[2]:.4f}")
print(f" R²:  {r2_m:.4f}")
print(f" MSE: {mse_m:.4f}")
print(f" MAE: {mae_m:.4f}")

# ---- Gráfico regresión simple ----
sample = df_clean.sample(min(500, len(df_clean)), random_state=42)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Modelos de Regresión Lineal", fontsize=14, fontweight='bold')

# Plot 1: Regresión simple
ax = axes[0]
ax.scatter(sample['Quantity'], sample['Revenue'], alpha=0.35, s=18, color='#4C72B0', label='Datos')
xr = np.linspace(0, df_clean['Quantity'].quantile(0.99), 200)
ax.plot(xr, beta0 + beta1 * xr, color='red', linewidth=2.5, label=f'Regresión (R²={r2:.3f})')
ax.set_xlabel("Quantity")
ax.set_ylabel("Revenue")
ax.set_title("Regresión Simple\nQuantity → Revenue")
ax.set_xlim(0, df_clean['Quantity'].quantile(0.99))
ax.set_ylim(0, df_clean['Revenue'].quantile(0.99))
ax.legend()

# Plot 2: Residuos
residuals = y - y_pred
ax2 = axes[1]
ax2.scatter(y_pred, residuals, alpha=0.3, s=15, color='#C44E52')
ax2.axhline(0, color='black', linewidth=1.5, linestyle='--')
ax2.set_xlabel("Valores Predichos")
ax2.set_ylabel("Residuos")
ax2.set_title("Gráfico de Residuos\n(Regresión Simple)")
ax2.set_xlim(0, np.percentile(y_pred, 99))
ax2.set_ylim(np.percentile(residuals, 1), np.percentile(residuals, 99))

plt.tight_layout()
plt.savefig(OUTPUT + "05_regresion_lineal.png", bbox_inches='tight')
plt.close()
print("\n Gráfico guardado: 05_regresion_lineal.png")

# =============================================================
# LECCIÓN 5: ANÁLISIS VISUAL AVANZADO (Seaborn)
# =============================================================
print("\n" + "="*60)
print("LECCION 5 - ANALISIS VISUAL DE DATOS (SEABORN)")
print("="*60)

# ---- Pairplot ----
sample_pair = df_clean[num_cols].sample(min(800, len(df_clean)), random_state=42)
fig = sns.pairplot(sample_pair, diag_kind='kde', plot_kws={'alpha': 0.3, 's': 15})
fig.figure.suptitle("Pairplot – Variables Numéricas", y=1.02, fontsize=14, fontweight='bold')
plt.savefig(OUTPUT + "06_pairplot.png", bbox_inches='tight')
plt.close()
print("Gráfico guardado: 06_pairplot.png")

# ---- Top 10 países por Revenue ----
top_countries = df_clean.groupby('Country')['Revenue'].sum().sort_values(ascending=False).head(10)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle("Análisis por País", fontsize=14, fontweight='bold')

# Barplot top países
sns.barplot(x=top_countries.values, y=top_countries.index,
            palette='Blues_r', ax=axes[0])
axes[0].set_title("Top 10 Países por Revenue Total")
axes[0].set_xlabel("Revenue (£)")
axes[0].set_ylabel("")
for i, (val, name) in enumerate(zip(top_countries.values, top_countries.index)):
    axes[0].text(val * 0.01, i, f'£{val:,.0f}', va='center', fontsize=8)

# Violinplot Quantity por top países (excluyendo UK por escala)
top5 = top_countries.drop('United Kingdom', errors='ignore').head(5).index.tolist()
df_top5 = df_clean[df_clean['Country'].isin(top5)]
df_top5_clip = df_top5.copy()
df_top5_clip['Quantity'] = df_top5_clip['Quantity'].clip(upper=df_top5_clip['Quantity'].quantile(0.95))
sns.violinplot(data=df_top5_clip, x='Country', y='Quantity',
               palette='Set2', ax=axes[1], inner='box')
axes[1].set_title("Distribución de Quantity\n(Top 5 países excl. UK)")
axes[1].set_xlabel("")
axes[1].tick_params(axis='x', rotation=20)

plt.tight_layout()
plt.savefig(OUTPUT + "07_analisis_paises.png", bbox_inches='tight')
plt.close()
print("Gráfico guardado: 07_analisis_paises.png")

# ---- Revenue mensual (tendencia temporal) ----
df_clean['Month'] = df_clean['InvoiceDate'].dt.to_period('M')
monthly = df_clean.groupby('Month')['Revenue'].sum().reset_index()
monthly['Month_str'] = monthly['Month'].astype(str)

fig, ax = plt.subplots(figsize=(12, 5))
ax.fill_between(range(len(monthly)), monthly['Revenue'], alpha=0.3, color='#4C72B0')
ax.plot(range(len(monthly)), monthly['Revenue'], marker='o', color='#4C72B0', linewidth=2.5)
ax.set_xticks(range(len(monthly)))
ax.set_xticklabels(monthly['Month_str'], rotation=45, ha='right')
ax.set_title("Revenue Mensual – ComercioYA", fontsize=14, fontweight='bold')
ax.set_xlabel("Mes")
ax.set_ylabel("Revenue (£)")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'£{x:,.0f}'))

# Anotación pico
peak_idx = monthly['Revenue'].idxmax()
ax.annotate(f"Pico: £{monthly['Revenue'].max():,.0f}",
            xy=(peak_idx, monthly['Revenue'].max()),
            xytext=(peak_idx - 1.5, monthly['Revenue'].max() * 0.97),
            arrowprops=dict(arrowstyle='->', color='red'),
            fontsize=9, color='red')

plt.tight_layout()
plt.savefig(OUTPUT + "08_revenue_mensual.png", bbox_inches='tight')
plt.close()
print("Gráfico guardado: 08_revenue_mensual.png")

# ---- Jointplot: Quantity vs Revenue ----
sample_j = df_clean[['Quantity', 'Revenue']].sample(min(500, len(df_clean)), random_state=42)
sample_j['Quantity'] = sample_j['Quantity'].clip(upper=sample_j['Quantity'].quantile(0.99))
sample_j['Revenue'] = sample_j['Revenue'].clip(upper=sample_j['Revenue'].quantile(0.99))

g = sns.jointplot(data=sample_j, x='Quantity', y='Revenue',
                  kind='reg', height=6,
                  scatter_kws={'alpha': 0.3, 's': 20},
                  line_kws={'color': 'red'})
g.figure.suptitle("Jointplot: Quantity vs Revenue", y=1.02, fontsize=13, fontweight='bold')
plt.savefig(OUTPUT + "09_jointplot.png", bbox_inches='tight')
plt.close()
print("Gráfico guardado: 09_jointplot.png")

# ---- FacetGrid: Revenue por país ----
top3_countries = top_countries.head(4).index.tolist()
df_facet = df_clean[df_clean['Country'].isin(top3_countries)].copy()
df_facet['Revenue_clip'] = df_facet['Revenue'].clip(upper=df_facet['Revenue'].quantile(0.99))

g = sns.FacetGrid(df_facet, col='Country', col_wrap=2, height=4, sharey=False)
g.map(plt.hist, 'Revenue_clip', bins=30, color='#4C72B0', alpha=0.8, edgecolor='white')
g.set_axis_labels("Revenue (£)", "Frecuencia")
g.figure.suptitle("FacetGrid – Distribución de Revenue por País", y=1.02, fontsize=13, fontweight='bold')
plt.savefig(OUTPUT + "10_facetgrid_paises.png", bbox_inches='tight')
plt.close()
print("Gráfico guardado: 10_facetgrid_paises.png")

# =============================================================
# LECCIÓN 6: VISUALIZACIONES FINALES CON MATPLOTLIB
# =============================================================
print("\n" + "="*60)
print("LECCION 6 - MATPLOTLIB: DASHBOARD FINAL")
print("="*60)

fig = plt.figure(figsize=(18, 12))
fig.suptitle("Dashboard EDA – ComercioYA\nAnálisis Exploratorio de Datos",
             fontsize=18, fontweight='bold', y=0.98)

gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

# ── Panel 1: Revenue mensual ─────────────────
ax1 = fig.add_subplot(gs[0, :2])
ax1.fill_between(range(len(monthly)), monthly['Revenue'], alpha=0.25, color='#4C72B0')
ax1.plot(range(len(monthly)), monthly['Revenue'], marker='o', markersize=5,
         color='#4C72B0', linewidth=2)
ax1.set_title("Revenue Mensual", fontweight='bold')
ax1.set_xticks(range(len(monthly)))
ax1.set_xticklabels(monthly['Month_str'], rotation=45, ha='right', fontsize=7)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'£{x/1e3:.0f}K'))
ax1.set_ylabel("Revenue")

# ── Panel 2: Top países ──────────────────────
ax2 = fig.add_subplot(gs[0, 2])
colors_bar = sns.color_palette("Blues_r", len(top_countries.head(7)))
bars = ax2.barh(top_countries.head(7).index[::-1],
                top_countries.head(7).values[::-1], color=colors_bar[::-1])
ax2.set_title("Top Países (Revenue)", fontweight='bold')
ax2.set_xlabel("Revenue (£)")
ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'£{x/1e3:.0f}K'))

# ── Panel 3: Histograma Revenue ──────────────
ax3 = fig.add_subplot(gs[1, 0])
rev_clip = df_clean['Revenue'].clip(upper=df_clean['Revenue'].quantile(0.99))
ax3.hist(rev_clip, bins=50, color='#55A868', alpha=0.8, edgecolor='white')
ax3.axvline(rev_clip.mean(), color='red', linestyle='--', linewidth=1.5, label=f'Media: £{rev_clip.mean():.1f}')
ax3.axvline(rev_clip.median(), color='orange', linestyle=':', linewidth=1.5, label=f'Mediana: £{rev_clip.median():.1f}')
ax3.set_title("Revenue", fontweight='bold')
ax3.set_xlabel("Revenue (£)")
ax3.legend(fontsize=7)

# ── Panel 4: Boxplot Quantity ────────────────
ax4 = fig.add_subplot(gs[1, 1])
qty_clip = df_clean['Quantity'].clip(upper=df_clean['Quantity'].quantile(0.99))
bp = ax4.boxplot(qty_clip, patch_artist=True,
                 boxprops=dict(facecolor='#C44E52', alpha=0.6),
                 medianprops=dict(color='black', linewidth=2))
ax4.set_title("Boxplot – Quantity", fontweight='bold')
ax4.set_ylabel("Unidades")
ax4.set_xticklabels(['Quantity'])

# ── Panel 5: Scatter Qty vs Revenue ──────────
ax5 = fig.add_subplot(gs[1, 2])
s500 = df_clean.sample(400, random_state=1)
ax5.scatter(s500['Quantity'].clip(upper=s500['Quantity'].quantile(0.99)),
            s500['Revenue'].clip(upper=s500['Revenue'].quantile(0.99)),
            alpha=0.35, s=15, color='#4C72B0')
xr = np.linspace(0, df_clean['Quantity'].quantile(0.99), 200)
ax5.plot(xr, beta0 + beta1 * xr, color='red', linewidth=2, label=f'R²={r2:.3f}')
ax5.set_title("Regresión: Qty → Revenue", fontweight='bold')
ax5.set_xlabel("Quantity")
ax5.set_ylabel("Revenue (£)")
ax5.legend(fontsize=8)

# ── Panel 6: Heatmap correlación ─────────────
ax6 = fig.add_subplot(gs[2, 0])
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='coolwarm',
            center=0, vmin=-1, vmax=1, linewidths=0.5,
            ax=ax6, annot_kws={"size": 10}, square=True)
ax6.set_title("Correlación Pearson", fontweight='bold')

# ── Panel 7: Top 10 productos ────────────────
ax7 = fig.add_subplot(gs[2, 1:])
top_prod = df_clean.groupby('Description')['Revenue'].sum().sort_values(ascending=False).head(10)
colors_prod = sns.color_palette("Greens_r", 10)
bars7 = ax7.barh(
    [d[:35] + '…' if len(d) > 35 else d for d in top_prod.index[::-1]],
    top_prod.values[::-1], color=colors_prod[::-1]
)
ax7.set_title("Top 10 Productos por Revenue", fontweight='bold')
ax7.set_xlabel("Revenue (£)")
ax7.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'£{x/1e3:.0f}K'))

plt.savefig(OUTPUT + "11_dashboard_final.png", bbox_inches='tight', dpi=150)
plt.close()
print("Dashboard guardado: 11_dashboard_final.png")

# =============================================================
# RESUMEN ESTADÍSTICO FINAL
# =============================================================
print("\n" + "="*60)
print("RESUMEN DE HALLAZGOS CLAVE")
print("="*60)

total_rev = df_clean['Revenue'].sum()
total_tx  = df_clean['InvoiceNo'].nunique()
total_cli = df_clean['CustomerID'].nunique()
top_prod_name = df_clean.groupby('Description')['Revenue'].sum().idxmax()
top_country   = df_clean.groupby('Country')['Revenue'].sum().idxmax()

print(f"""
  Revenue Total:         £{total_rev:,.2f}
  Transacciones únicas:  {total_tx:,}
  Clientes únicos:       {total_cli:,}
  Producto estrella:     {top_prod_name}
  País líder:            {top_country}
  R² Regresión simple:   {r2:.4f}
  R² Regresión múltiple: {r2_m:.4f}
  Correlación Qty-Rev:   {df_clean['Quantity'].corr(df_clean['Revenue']):.4f}
  Correlación Price-Rev: {df_clean['UnitPrice'].corr(df_clean['Revenue']):.4f}
""")

print("Análisis EDA completo! Todos los gráficos exportados en /outputs/")
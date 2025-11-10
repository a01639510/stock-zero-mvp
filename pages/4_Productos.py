# pages/4_Productos.py
import streamlit as st
import pandas as pd
import plotly.express as px
# === CARGAR DESDE DB ===
conn = st.connection("supabase", type=SupabaseConnection)
data = conn.table("ventas").select("*").eq("user_id", st.session_state.user_id).execute()
st.session_state.df_ventas = pd.DataFrame(data.data)

# === PARA GUARDAR (en botones de edición) ===
if st.button("Guardar cambios"):
    for _, row in df_ventas.iterrows():
        conn.table("ventas").upsert({
            "user_id": st.session_state.user_id,
            "fecha": row['fecha'],
            "producto": row['producto'],
            "cantidad_vendida": row['cantidad_vendida']
        }).execute()
    st.success("Guardado en DB")
st.title("Productos")

if 'df_ventas' not in st.session_state:
    st.warning("Sube ventas en **Archivos**")
    st.stop()

df_ventas = st.session_state.df_ventas.copy()
df_stock = st.session_state.get('df_stock', pd.DataFrame())

df_merge = df_ventas.merge(df_stock, on='producto', how='left')

producto = st.selectbox("Producto", sorted(df_merge['producto'].unique()))
df_prod = df_merge[df_merge['producto'] == producto]

col1, col2, col3 = st.columns(3)
with col1: st.metric("Ventas Totales", df_prod['cantidad_vendida'].sum())
with col2: st.metric("Stock", df_prod['cantidad_recibida'].sum() if 'cantidad_recibida' in df_prod.columns else 0)
with col3: st.metric("Costo Unitario", f"${df_prod.get('costo_unitario', 10).iloc[0]:.2f}" if not df_prod.empty else "$10.00")

fig = px.line(df_prod.groupby('fecha')['cantidad_vendida'].sum().reset_index(), x='fecha', y='cantidad_vendida')
st.plotly_chart(fig, use_container_width=True)

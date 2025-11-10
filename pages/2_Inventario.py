# pages/2_Inventario.py
import streamlit as st
from modules.components import inventario_basico_app
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
st.title("Inventario")

if 'df_stock' not in st.session_state:
    st.warning("Sube stock en **Archivos**")
    st.stop()

df_stock = st.session_state.df_stock.copy()

col1, col2 = st.columns(2)
valor = (df_stock['cantidad_recibida'] * df_stock.get('costo_unitario', 10)).sum()
with col1: st.metric("Valor Total", f"${valor:,.0f}")
with col2: st.metric("Productos", len(df_stock))

bajos = df_stock[df_stock['cantidad_recibida'] < 10]
if not bajos.empty:
    st.error(f"{len(bajos)} productos con stock bajo")
    st.dataframe(bajos[['producto', 'cantidad_recibida']])
else:
    st.success("Todo en orden")

inventario_basico_app()

st.markdown("### Actualizar Inventario")
edited = st.data_editor(df_stock, num_rows="dynamic")
if st.button("Guardar cambios"):
    st.session_state.df_stock = edited
    if 'df_resultados' in st.session_state:
        del st.session_state.df_resultados
    st.success("Actualizado")
    st.rerun()

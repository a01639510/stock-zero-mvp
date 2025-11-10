# pages/3_Analisis.py
import streamlit as st
from modules.analytics import analytics_app
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
st.title("Análisis")

if 'df_ventas' not in st.session_state:
    st.warning("Sube datos en **Archivos**")
    st.stop()

if 'df_resultados' not in st.session_state:
    with st.spinner("Procesando..."):
        from modules.core_analysis import procesar_multiple_productos
        st.session_state.df_resultados = procesar_multiple_productos(
            st.session_state.df_ventas,
            st.session_state.get('df_stock', pd.DataFrame())
        )

analytics_app()

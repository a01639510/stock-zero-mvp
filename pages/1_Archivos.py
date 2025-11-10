# pages/1_Archivos.py
import streamlit as st
from streamlit_supabase_connection import SupabaseConnection

st.title("Archivos")

conn = st.connection("supabase", type=SupabaseConnection)

# === CARGAR DESDE DB ===
data = conn.table("ventas").select("*").eq("user_id", st.session_state.user_id).execute()
st.session_state.df_ventas = pd.DataFrame(data.data)

# === SUBIR CSV Y GUARDAR EN DB ===
uploaded = st.file_uploader("Ventas CSV", type="csv")
if uploaded:
    df = pd.read_csv(uploaded)
    for _, row in df.iterrows():
        conn.table("ventas").upsert({
            "user_id": st.session_state.user_id,
            "fecha": row['fecha'],
            "producto": row['producto'],
            "cantidad_vendida": row['cantidad_vendida']
        }).execute()
    st.success("CSV guardado en DB")
    st.rerun()

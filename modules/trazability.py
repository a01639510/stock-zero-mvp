# modules/recipes.py
import streamlit as st
import pandas as pd

def calcular_costos_margenes(df_recetas, precio_venta, platillo):
    """
    Calcula costo total, margen y margen % de un platillo.
    """
    if df_recetas.empty:
        st.error("El archivo de recetas está vacío.")
        return None

    # Normalizar nombres de columnas (por si vienen con espacios o mayúsculas)
    df_recetas.columns = df_recetas.columns.str.strip().str.lower()

    # Filtrar el platillo
    mask = df_recetas['platillo'].str.lower() == platillo.lower()
    df_platillo = df_recetas[mask].copy()

    if df_platillo.empty:
        st.error(f"⚠️ No se encontró el platillo: **{platillo}**")
        return None

    # --- DEBUG: Mostrar datos (puedes comentar en producción) ---
    with st.expander("🔍 Debug: Datos del platillo", expanded=False):
        st.write(f"Filas encontradas: {len(df_platillo)}")
        st.write("Columnas disponibles:", df_platillo.columns.tolist())
        st.dataframe(df_platillo)

    # --- Definir nombres esperados (ajusta según tu CSV) ---
    col_cantidad = 'cantidad_por_unidad'   # Cambia si en tu CSV es 'cantidad', 'cant', etc.
    col_costo = 'costo_unitario'           # Cambia si es 'costo', 'precio_unitario', etc.

    # Validar columnas críticas
    missing_cols = []
    if col_cantidad not in df_platillo.columns:
        missing_cols.append(col_cantidad)
    if col_costo not in df_platillo.columns:
        missing_cols.append(col_costo)

    if missing_cols:
        st.error(f"❌ Faltan columnas en el platillo: {missing_cols}")
        st.write("Columnas disponibles:", df_platillo.columns.tolist())
        return None

    # Calcular costo total
    try:
        df_platillo['costo_parcial'] = df_platillo[col_cantidad] * df_platillo[col_costo]
        costo_total = df_platillo['costo_parcial'].sum()
    except Exception as e:
        st.error(f"Error al calcular costos: {e}")
        return None

    # Calcular margen
    if precio_venta <= 0:
        st.warning("El precio de venta debe ser mayor a 0.")
        margen = margen_porcentual = 0
    else:
        margen = precio_venta - costo_total
        margen_porcentual = (margen / precio_venta) * 100

    return {
        'costo_total': round(costo_total, 2),
        'margen': round(margen, 2),
        'margen_porcentual': round(margen_porcentual, 2),
        'df_detalle': df_platillo[['ingrediente', col_cantidad, col_costo, 'costo_parcial']]
    }


def recetas_app():
    st.title("🍽️ Recetas y Costos")

    # --- Cargar datos desde GitHub o local ---
    csv_url = "https://raw.githubusercontent.com/tu-usuario/stock-zero-mvp/main/data/recetas.csv"
    try:
        df_recetas = pd.read_csv(csv_url)
        st.success("Datos cargados desde GitHub")
    except Exception as e:
        st.error(f"No se pudo cargar el CSV: {e}")
        st.info("Asegúrate de que el archivo `recetas.csv` esté en `/data/` en GitHub.")
        return

    if df_recetas.empty:
        st.warning("El archivo está vacío.")
        return

    # Normalizar columnas
    df_recetas.columns = df_recetas.columns.str.strip().str.lower()

    # Validar columnas mínimas
    required_cols = ['platillo', 'ingrediente']
    missing = [col for col in required_cols if col not in df_recetas.columns]
    if missing:
        st.error(f"Faltan columnas obligatorias: {missing}")
        return

    # --- Interfaz ---
    col1, col2 = st.columns([2, 1])
    with col1:
        platillo = st.selectbox(
            "Selecciona un platillo",
            options=sorted(df_recetas['platillo'].unique())
        )
    with col2:
        precio_venta = st.number_input("Precio de venta", min_value=0.0, value=150.0, step=5.0)

    if st.button("Calcular Costos y Margen"):
        info = calcular_costos_margenes(df_recetas, precio_venta, platillo)
        if info:
            st.success(f"**{platillo.upper()}**")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Costo Total", f"${info['costo_total']}")
            col_b.metric("Margen", f"${info['margen']}")
            col_c.metric("Margen %", f"{info['margen_porcentual']}%")

            st.subheader("Desglose de Ingredientes")
            st.dataframe(info['df_detalle'].style.format({
                'cantidad_por_unidad': '{:.2f}',
                'costo_unitario': '${:.2f}',
                'costo_parcial': '${:.2f}'
            }))

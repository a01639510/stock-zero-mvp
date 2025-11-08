    # === PRIORIDAD 1: Usar datos de Optimización ===
    if st.session_state.df_ventas is None:
        st.warning("Sube datos en **Optimización de Inventario** o usa Excel abajo.")
    else:
        df_ventas = st.session_state.df_ventas.copy()
        
        # --- LIMPIEZA DE FECHAS (CRÍTICO) ---
        df_ventas['fecha'] = pd.to_datetime(df_ventas['fecha'], errors='coerce')
        if df_ventas['fecha'].isna().all():
            st.error("Todas las fechas son inválidas. Revisa el formato (YYYY-MM-DD).")
            st.stop()
        df_ventas = df_ventas.dropna(subset=['fecha']).copy()
        df_ventas['fecha'] = df_ventas['fecha'].dt.normalize()

        # === 1. Preparar datos agregados ===
        ventas_diarias = df_ventas.groupby('fecha')['cantidad_vendida'].sum().reset_index()
        ventas_diarias = ventas_diarias.rename(columns={'cantidad_vendida': 'ventas'})
        
        # Stock: acumulado de entradas
        if st.session_state.df_stock is not None:
            stock_diario = st.session_state.df_stock.copy()
            stock_diario['fecha'] = pd.to_datetime(stock_diario['fecha'], errors='coerce')
            stock_diario = stock_diario.dropna(subset=['fecha']).copy()
            stock_acum = stock_diario.groupby('fecha')['cantidad_recibida'].sum().cumsum().reset_index()
            stock_acum = stock_acum.rename(columns={'cantidad_recibida': 'stock_entradas'})
        else:
            stock_acum = pd.DataFrame({'fecha': ventas_diarias['fecha'], 'stock_entradas': 500})

        # Unir
        df = ventas_diarias.merge(stock_acum, on='fecha', how='left').fillna(method='ffill').fillna(0)
        df['stock_real'] = df['stock_entradas'].cumsum() - df['ventas'].cumsum()
        df = df[df['stock_real'] >= 0]  # Evitar negativos irreales

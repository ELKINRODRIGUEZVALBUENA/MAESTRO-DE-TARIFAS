import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tarifación de Catálogo - Comfaboy", layout="wide")
st.title("⚙️ Simulador de Tarifación por Catálogo (200+ Servicios)")
st.markdown("Carga tu archivo plano, selecciona un servicio del catálogo y realiza el estudio técnico de costos e inductores de tarifa paso a paso.")

st.sidebar.header("📁 1. Carga de Catálogo")
uploaded_file = st.sidebar.file_uploader("Sube tu archivo plano (Excel o CSV)", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_catalogo = pd.read_csv(uploaded_file)
        else:
            df_catalogo = pd.read_excel(uploaded_file)
        
        st.sidebar.success(f"✅ Archivo cargado con {len(df_catalogo)} registros.")
        
        columnas = df_catalogo.columns.tolist()
        col_nombre = st.sidebar.selectbox("¿Qué columna contiene los nombres de los servicios?", columnas)
        
        lista_productos = df_catalogo[col_nombre].dropna().astype(str).unique()
        producto_seleccionado = st.sidebar.selectbox("🔍 Selecciona el servicio a tarifar:", lista_productos)
        
        st.header(f"🛠️ Tarifación y Costeo: {producto_seleccionado}")
        
        st.markdown("---")
        st.header("2. Capacidad Instalada y Demanda")
        col1, col2 = st.columns(2)
        with col1:
            capacidad_maxima = st.number_input("Capacidad Máxima Instalada", min_value=1, value=1000, step=10)
        with col2:
            ocupacion_proyectada_pct = st.number_input("Ocupación Proyectada (%)", min_value=0.0, max_value=100.0, value=60.0, step=1.0)
            ocupacion_proyectada = ocupacion_proyectada_pct / 100.0

        unidades_proyectadas = int(capacidad_maxima * ocupacion_proyectada)
        st.info(f"📌 **Demanda Proyectada a Costear:** {unidades_proyectadas} unidades.")

        st.markdown("---")
        st.header("3. Estudio Técnico de Costos (Directos e Indirectos)")
        col_cf, col_cv = st.columns(2)

        with col_cf:
            st.subheader("Costos Fijos")
            cf_directos = st.number_input("Costos Fijos DIRECTOS [$]", value=0.0, step=500000.0)
            cf_indirectos = st.number_input("Costos Fijos INDIRECTOS [$]", value=0.0, step=500000.0)
            cf_total = cf_directos + cf_indirectos

        with col_cv:
            st.subheader("Costos Variables Unitarios")
            cv_directos_u = st.number_input("Costo Variable DIRECTO Unitario [$]", value=0.0, step=1000.0)
            cv_indirectos_u = st.number_input("Costo Variable INDIRECTO Unitario [$]", value=0.0, step=1000.0)
            cv_unitario_total = cv_directos_u + cv_indirectos_u

        if unidades_proyectadas > 0:
            costo_fijo_unitario = cf_total / unidades_proyectadas
            costo_tecnico_unitario = costo_fijo_unitario + cv_unitario_total
            costo_total_operacion = cf_total + (cv_unitario_total * unidades_proyectadas)
        else:
            costo_fijo_unitario = 0
            costo_tecnico_unitario = 0
            costo_total_operacion = cf_total

        df_costos = pd.DataFrame({
            "Rubro": ["Costos Fijos Totales", "Costo Variable Total", "COSTO TOTAL DE OPERACIÓN", "Costo Técnico UNITARIO"],
            "Valor": [f"${cf_total:,.2f}", f"${(cv_unitario_total * unidades_proyectadas):,.2f}", f"${costo_total_operacion:,.2f}", f"${costo_tecnico_unitario:,.2f}"]
        }).set_index("Rubro")
        st.table(df_costos)

        st.markdown("---")
        st.header("4. Inductores de Tarifa (Mercado vs Costo)")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Costo Técnico Unitario", f"${costo_tecnico_unitario:,.2f}")
        with col_m2:
            tarifa_mercado = st.number_input("Tarifa de Mercado [$]", value=float(costo_tecnico_unitario * 1.2), step=1000.0)
        with col_m3:
            tarifa_c = st.number_input("TARIFA PLENA (Cat. C) Seleccionada [$]", value=float(costo_tecnico_unitario), step=1000.0)

        st.markdown("---")
        st.header("5. Subsidios, Rentabilidad y P&G Proyectado")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            sub_a_pct = st.number_input("Subsidio Categoría A (%)", min_value=0.0, max_value=100.0, value=80.0, step=1.0) / 100.0
        with col_s2:
            sub_b_pct = st.number_input("Subsidio Categoría B (%)", min_value=0.0, max_value=100.0, value=70.0, step=1.0) / 100.0
        with col_s3:
            margen_d_pct = st.number_input("Margen de Rentabilidad Cat D (%)", min_value=0.0, max_value=200.0, value=15.0, step=1.0) / 100.0

        tarifa_a = tarifa_c * (1 - sub_a_pct)
        tarifa_b = tarifa_c * (1 - sub_b_pct)
        tarifa_d = tarifa_c * (1 + margen_d_pct)
        v_sub_a = tarifa_c * sub_a_pct
        v_sub_b = tarifa_c * sub_b_pct

        st.subheader("Mezcla de Demanda")
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        with col_p1:
            q_a = st.number_input("Unidades Cat A", min_value=0, value=int(unidades_proyectadas * 0.60), step=1)
        with col_p2:
            q_b = st.number_input("Unidades Cat B", min_value=0, value=int(unidades_proyectadas * 0.20), step=1)
        with col_p3:
            q_c = st.number_input("Unidades Cat C", min_value=0, value=int(unidades_proyectadas * 0.15), step=1)
        with col_p4:
            q_d = st.number_input("Unidades Cat D", min_value=0, value=int(unidades_proyectadas * 0.05), step=1)

        total_mezcla = q_a + q_b + q_c + q_d
        
        ct_real_mezcla = cf_total + (cv_unitario_total * total_mezcla)
        ingresos_tarifas = (q_a * tarifa_a) + (q_b * tarifa_b) + (q_c * tarifa_c) + (q_d * tarifa_d)
        subsidios_otorgados = (q_a * v_sub_a) + (q_b * v_sub_b)
        ingresos_totales = ingresos_tarifas + subsidios_otorgados
        resultado_operativo = ingresos_tarifas - ct_real_mezcla
        sub_oferta = -(resultado_operativo + subsidios_otorgados)

        st.markdown("### 📊 P&G Resumido")
        df_pg = pd.DataFrame({
            "Indicador Financiero": [
                "1. Ingresos Recaudados (Tarifas)", 
                "2. Subsidio a la Demanda", 
                "3. Costos Totales de Operación", 
                "4. RESULTADO NETO (Déficit / Superávit)",
                "5. Subsidio a la Oferta"
            ],
            "Valor Proyectado": [
                ingresos_tarifas, 
                subsidios_otorgados, 
                ct_real_mezcla, 
                resultado_operativo, 
                sub_oferta if sub_oferta > 0 else 0.0
            ]
        }).set_index("Indicador Financiero")

        st.dataframe(df_pg.style.format({"Valor Proyectado": "${:,.2f}"}).map(
            lambda x: 'color: red' if isinstance(x, float) and x < 0 else ('color: green' if isinstance(x, float) and x > 0 else ''),
            subset=["Valor Proyectado"]
        ), use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        
else:
    st.info("👈 Carga el archivo plano (CSV o Excel) con el catálogo de productos en el panel izquierdo para comenzar.")

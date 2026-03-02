# 📊 Órdenes por Día del mes (BARRAS)

df["dia_mes"] = df["fecha"].dt.day

ordenes_dia = (
    df.groupby("dia_mes")["orden_trabajo"]
    .nunique()
    .reset_index(name="ordenes")
    .sort_values("dia_mes")
)

fig = px.bar(
    ordenes_dia,
    x="dia_mes",
    y="ordenes",
    title="Órdenes por día del mes - Febrero 2026"
)

fig.update_layout(
    xaxis_title="Día del mes",
    yaxis_title="Cantidad de órdenes",
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

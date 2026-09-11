from flask import Flask, jsonify, request

app = Flask(__name__)

# Base de datos simulada en memoria
inventario = [
    {
        "id": 1,
        "nombre": "Platillo / Menú Rápido",
        "precio": 350.00,
        "stock": 100,
    },
    {"id": 2, "nombre": "Bebida / Refresco", "precio": 75.00, "stock": 150},
    {"id": 3, "nombre": "Acompañamiento", "precio": 120.00, "stock": 80},
]

ventas = []


# ==========================================
# MÓDULO DE RECURSOS HUMANOS Y NÓMINA (TSS / Ley 16-92)
# ==========================================
@app.route("/api/nomina/calcular", methods=["POST"])
def calcular_nomina():
  data = request.json
  salario_bruto = float(data.get("salario_bruto", 0))

  # 1. Deducciones al Empleado (TSS Régimen Contributivo)
  afp_empleado = salario_bruto * 0.0287  # 2.87% Pensiones
  sfs_empleado = salario_bruto * 0.0304  # 3.04% Salud
  total_desc_empleado = afp_empleado + sfs_empleado

  # 2. Aportes Patronales (Empleador)
  afp_patronal = salario_bruto * 0.0710  # 7.10%
  sfs_patronal = salario_bruto * 0.0709  # 7.09%
  srl_patronal = salario_bruto * 0.0110  # 1.10% Riesgo Laboral (aprox. riesgo bajo)
  infotep = salario_bruto * 0.0100  # 1.00% INFOTEP (Ley 116-80)
  total_patronal = afp_patronal + sfs_patronal + srl_patronal + infotep

  # 3. Provisiones Obligatorias (Código de Trabajo RD)
  regalia_pascual = salario_bruto * 0.0833  # 8.33% (1/12 anual)
  vacaciones = salario_bruto * 0.0417  # 4.17%

  # Cálculos finales
  salario_neto = salario_bruto - total_desc_empleado
  costo_total_empleador = (
      salario_bruto + total_patronal + regalia_pascual + vacaciones
  )

  return jsonify({
      "salario_bruto": round(salario_bruto, 2),
      "descuentos_empleado": {
          "AFP_2.87%": round(afp_empleado, 2),
          "SFS_3.04%": round(sfs_empleado, 2),
          "total_descuentos": round(total_desc_empleado, 2),
      },
      "salario_neto_a_pagar": round(salario_neto, 2),
      "aportes_empleador_tss": {
          "AFP_7.10%": round(afp_patronal, 2),
          "SFS_7.09%": round(sfs_patronal, 2),
          "SRL": round(srl_patronal, 2),
          "INFOTEP_1%": round(infotep, 2),
          "total_patronal": round(total_patronal, 2),
      },
      "provisiones_laborales": {
          "regalia_pascual": round(regalia_pascual, 2),
          "vacaciones": round(vacaciones, 2),
      },
      "costo_real_empresa": round(costo_total_empleador, 2),
  })


# ==========================================
# MÓDULO DE VENTAS E INVENTARIO (Con ITBIS DGII)
# ==========================================
@app.route("/api/inventario", methods=["GET"])
def ver_inventario():
  return jsonify(inventario)


@app.route("/api/ventas", methods=["POST"])
def procesar_venta():
  data = request.json
  items_vendidos = data.get("items", [])  # Ejemplo: [{"id": 1, "cantidad": 2}]

  subtotal = 0
  detalle_factura = []

  for item in items_vendidos:
    producto = next(
        (p for p in inventario if p["id"] == item["id"]), None
    )
    if not producto:
      return (
          jsonify(
              {"error": f"El producto con ID {item['id']} no existe."}
          ),
          404,
      )

    if producto["stock"] < item["cantidad"]:
      return (
          jsonify({
              "error": (
                  f"Stock insuficiente para '{producto['nombre']}'. Disponible:"
                  f" {producto['stock']}"
              )
          }),
          400,
      )

    # Descontar stock
    producto["stock"] -= item["cantidad"]
    precio_linea = producto["precio"] * item["cantidad"]
    subtotal += precio_linea

    detalle_factura.append({
        "producto": producto["nombre"],
        "cantidad": item["cantidad"],
        "precio_unitario": producto["precio"],
        "subtotal": precio_linea,
    })

  # Impuestos según DGII (ITBIS general 18%)
  itbis = subtotal * 0.18
  total_general = subtotal + itbis

  nueva_venta = {
      "id_factura": len(ventas) + 1,
      "detalle": detalle_factura,
      "subtotal": round(subtotal, 2),
      "itbis_18": round(itbis, 2),
      "total": round(total_general, 2),
  }
  ventas.append(nueva_venta)

  return jsonify({
      "mensaje": "Venta procesada con éxito y registrada para efectos fiscales.",
      "factura": nueva_venta,
  })


# ==========================================
# MÓDULO DE CONTABILIDAD BÁSICA
# ==========================================
@app.route("/api/contabilidad/resumen", methods=["GET"])
def resumen_contable():
  total_ingresos = sum(v["subtotal"] for v in ventas)
  total_itbis_cobrado = sum(v["itbis_18"] for v in ventas)

  return jsonify({
      "ingresos_brutos": round(total_ingresos, 2),
      "itbis_por_pagar_dgii": round(
          total_itbis_cobrado, 2
      ),  # ITBIS retenido en ventas para declaración mensual (Formulario IT-1)
      "total_facturado": round(total_ingresos + total_itbis_cobrado, 2),
  })


if __name__ == "__main__":
  app.run(debug=True, port=5000)

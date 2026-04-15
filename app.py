from flask import Flask, render_template, request
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import json
import os

app = Flask(__name__)

# -------------------------------
# CONEXIÓN A GOOGLE SHEETS
# -------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credenciales = json.loads(os.environ["GOOGLE_CREDENTIALS"])

creds = Credentials.from_service_account_info(
    credenciales,
    scopes=SCOPES
)

cliente = gspread.authorize(creds)

# -------------------------------
# CONFIGURACIÓN
# -------------------------------
CLUBES = {
    "tenis": {
        "hoja": "TENIS",
        "simbolo": "🥎"
    },
    "basquet": {
        "hoja": "BASQUET BASICO",  # cambia a "BÁSQUET BASICO" si tu pestaña tiene acento
        "simbolo": "🏀"
    }
}

# -------------------------------
# ABRIR HOJA
# -------------------------------
def abrir_hoja(nombre):
    return cliente.open("LISTAS-CLUBES").worksheet(nombre)

# -------------------------------
# OBTENER ALUMNOS (dinámico)
# Busca la fila donde está "NOMBRE"
# y lee hacia abajo hasta la primera celda vacía
# -------------------------------
def obtener_alumnos(hoja):
    col_b = hoja.col_values(2)  # columna B (NOMBRE)
    alumnos = []

    fila_inicio = None
    for i, v in enumerate(col_b):
        if v.strip().upper() == "NOMBRE":
            fila_inicio = i + 1  # siguiente fila = primer alumno
            break

    if fila_inicio is None:
        return alumnos

    for nombre in col_b[fila_inicio:]:
        if nombre.strip() == "":
            break
        alumnos.append(nombre.strip())

    return alumnos

# -------------------------------
# ENCONTRAR BLOQUE DEL MES Y DÍA
# Busca "ASISTENCIA <MES> <AÑO>" y luego el día en la fila de números
# -------------------------------
    def encontrar_columna_dia(hoja, dia):

        datos = hoja.get_all_values()

        zona = pytz.timezone("America/Mexico_City")
        ahora = datetime.now(zona)

        MESES = {
            1: "ENERO",
            2: "FEBRERO",
            3: "MARZO",
            4: "ABRIL",
            5: "MAYO",
            6: "JUNIO",
            7: "JULIO",
            8: "AGOSTO",
            9: "SEPTIEMBRE",
            10: "OCTUBRE",
            11: "NOVIEMBRE",
            12: "DICIEMBRE"
        }

        mes_actual = MESES[ahora.month]
        anio_actual = ahora.year

        titulo_mes = f"ASISTENCIA {mes_actual} {anio_actual}"

        fila_mes = None

        for i, fila in enumerate(datos):
            texto = " ".join(fila).upper()
            if titulo_mes in texto:
                fila_mes = i
                break

        if fila_mes is None:
            return None

        fila_dias = datos[fila_mes + 1]

        for i, v in enumerate(fila_dias):
            if v.strip() == str(dia):
                return i + 1

        return None

    # La fila de números de días suele estar justo debajo del título
    fila_dias = datos[fila_mes + 1]

    for i, v in enumerate(fila_dias):
        if v.strip() == str(dia):
            return i + 1  # columnas de gspread empiezan en 1

    return None

# -------------------------------
# INICIO
# -------------------------------
@app.route("/")
def inicio():
    return render_template("clubes.html")

# -------------------------------
# LISTA DE ASISTENCIA
# -------------------------------
@app.route("/asistencia/<club>")
def asistencia(club):
    hoja = abrir_hoja(CLUBES[club]["hoja"])
    alumnos = obtener_alumnos(hoja)

    fecha = datetime.now().strftime("%Y-%m-%d")

    return render_template(
        "asistencia.html",
        alumnos=alumnos,
        club=club,
        fecha=fecha
    )

# -------------------------------
# GUARDAR ASISTENCIA
# -------------------------------
@app.route("/guardar/<club>", methods=["POST"])
def guardar(club):

    fecha = request.form.get("fecha")
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")

    _, _, dia = fecha.split("-")
    dia = int(dia)

    hoja = abrir_hoja(CLUBES[club]["hoja"])
    simbolo = CLUBES[club]["simbolo"]

    columna_dia = encontrar_columna_dia(hoja, dia)

    # Si no encuentra el día, no escribe nada (para no romper la hoja)
    if columna_dia is None:
        return "No se encontró la columna del día en el mes actual."

    alumnos_presentes = request.form.getlist("alumnos")
    alumnos = obtener_alumnos(hoja)

    col_b = hoja.col_values(2)

    # Encontrar de nuevo la fila de "NOMBRE"
    fila_inicio = None
    for i, v in enumerate(col_b):
        if v.strip().upper() == "NOMBRE":
            fila_inicio = i + 2  # primera fila de alumnos en hoja (1-index)
            break

    if fila_inicio is None:
        return "No se encontró el encabezado NOMBRE."

    for i, nombre in enumerate(alumnos):
        fila = fila_inicio + i

        if nombre in alumnos_presentes:
            hoja.update_cell(fila, columna_dia, simbolo)
        else:
            hoja.update_cell(fila, columna_dia, "/")

    return render_template("confirmacion.html")

# -------------------------------
# ESTADÍSTICAS (básico)
# -------------------------------
@app.route("/estadisticas/<club>")
def estadisticas(club):
    hoja = abrir_hoja(CLUBES[club]["hoja"])
    datos = hoja.get_all_values()

    alumno_mas_faltas = ""
    max_faltas = 0

    alumnos = obtener_alumnos(hoja)

    for fila in datos:
        if len(fila) > 2:
            nombre = fila[1]
            if nombre in alumnos:
                faltas = fila.count("/")
                if faltas > max_faltas:
                    max_faltas = faltas
                    alumno_mas_faltas = nombre

    return render_template(
        "estadisticas.html",
        alumno=alumno_mas_faltas,
        faltas=max_faltas
    )

# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
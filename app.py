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
        "hoja": "BASQUET BASICO",
        "simbolo": "🏀"
    }
}

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

# -------------------------------
# ABRIR HOJA
# -------------------------------

def abrir_hoja(nombre):
    return cliente.open("LISTAS-CLUBES").worksheet(nombre)

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

    columna_nombres = hoja.col_values(2)

    alumnos = []

    for nombre in columna_nombres:

        nombre = nombre.strip()

        if nombre == "":
            continue

        if nombre.upper() == "NOMBRE":
            continue

        if nombre.isdigit():
            continue

        alumnos.append(nombre)

        if len(alumnos) > 50:
            break

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

    hoja = abrir_hoja(CLUBES[club]["hoja"])

    simbolo = CLUBES[club]["simbolo"]

    alumnos_presentes = request.form.getlist("alumnos")

    zona = pytz.timezone("America/Mexico_City")

    año, mes, dia = fecha.split("-")

    dia = int(dia)
    mes_actual = MESES[int(mes)]

    buscar_mes = "ASISTENCIA " + mes_actual

    datos = hoja.get_all_values()

    columna_dia = None

    for i, valor in enumerate(datos[0]):
        if valor == str(dia):
            columna_dia = i + 1

    if columna_dia is None:
        columna_dia = len(datos[0]) + 1
        hoja.update_cell(1, columna_dia, dia)

    for i, fila in enumerate(datos[1:], start=2):

        if len(fila) > 1:

            nombre = fila[1]

            if nombre in alumnos_presentes:
                hoja.update_cell(i, columna_dia, simbolo)

            else:
                hoja.update_cell(i, columna_dia, "/")

    return render_template("confirmacion.html")

# -------------------------------
# ESTADÍSTICAS
# -------------------------------

@app.route("/estadisticas/<club>")
def estadisticas(club):

    hoja = abrir_hoja(CLUBES[club]["hoja"])

    datos = hoja.get_all_values()

    alumno_mas_faltas = ""
    max_faltas = 0

    for fila in datos[1:]:

        if len(fila) > 1:

            nombre = fila[1]

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
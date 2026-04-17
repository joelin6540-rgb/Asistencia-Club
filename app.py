from flask import Flask, render_template, request, redirect
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import json
import os

app = Flask(__name__)

# ----------------------------------
# CONEXIÓN A GOOGLE SHEETS (RENDER)
# ----------------------------------

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credenciales = json.loads(os.environ["GOOGLE_CREDENTIALS"])

creds = Credentials.from_service_account_info(
    credenciales,
    scopes=scope
)

cliente = gspread.authorize(creds)

libro = cliente.open("LISTAS-CLUBES")

# ----------------------------------
# MESES
# ----------------------------------

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

# ----------------------------------
# ENCONTRAR COLUMNA DEL DÍA
# ----------------------------------

def encontrar_columna_dia(hoja, dia):

    datos = hoja.get_all_values()

    zona = pytz.timezone("America/Mexico_City")
    ahora = datetime.now(zona)

    mes_actual = MESES[ahora.month]

    fila_mes = None

    for i, fila in enumerate(datos):

        texto = " ".join(fila).upper()

        if "ASISTENCIA" in texto and mes_actual in texto:
            fila_mes = i
            break

    if fila_mes is None:
        return None

    fila_dias = datos[fila_mes + 1]

    for i, valor in enumerate(fila_dias):

        if valor.strip() == str(dia):
            return i + 1

    return None

# ----------------------------------
# ENCONTRAR FILA DEL ALUMNO
# ----------------------------------

def encontrar_fila_alumno(hoja, nombre):

    datos = hoja.get_all_values()

    for i, fila in enumerate(datos):

        if len(fila) > 1 and fila[1].strip().upper() == nombre.strip().upper():
            return i + 1

    return None

# ----------------------------------
# PÁGINA PRINCIPAL
# ----------------------------------

@app.route("/")
def index():
    return render_template("index.html")

# ----------------------------------
# CLUBES
# ----------------------------------

@app.route("/clubes")
def clubes():
    return render_template("clubes.html")

# ----------------------------------
# ASISTENCIA TENIS
# ----------------------------------

@app.route("/asistencia/tenis")
def asistencia_tenis():

    hoja = libro.worksheet("TENIS")
    datos = hoja.get_all_values()

    alumnos = []

    for fila in datos:
        if len(fila) > 1 and fila[1] != "":
            alumnos.append(fila[1])

    return render_template(
        "asistencia.html",
        alumnos=alumnos,
        club="tenis"
    )

# ----------------------------------
# GUARDAR ASISTENCIA
# ----------------------------------

@app.route("/guardar/<club>", methods=["POST"])
def guardar(club):

    hoja = libro.worksheet(club.upper())

    nombre = request.form["nombre"]
    estado = request.form["estado"]

    zona = pytz.timezone("America/Mexico_City")
    ahora = datetime.now(zona)

    dia = ahora.day

    columna_dia = encontrar_columna_dia(hoja, dia)

    fila_alumno = encontrar_fila_alumno(hoja, nombre)

    if columna_dia and fila_alumno:

        hoja.update_cell(
            fila_alumno,
            columna_dia,
            estado
        )

    return redirect(f"/asistencia/{club}")

# ----------------------------------
# CONFIRMACIÓN
# ----------------------------------

@app.route("/confirmacion")
def confirmacion():
    return render_template("confirmacion.html")

# ----------------------------------

if __name__ == "__main__":
    app.run(debug=True)
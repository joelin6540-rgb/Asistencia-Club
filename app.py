from flask import Flask, render_template, request
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import json
import os

app = Flask(__name__)

# -----------------------
# CONEXIÓN GOOGLE SHEETS
# -----------------------

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

# -----------------------
# CONFIGURACIÓN CLUBES
# -----------------------

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

# -----------------------
# ABRIR HOJA
# -----------------------

def abrir_hoja(nombre):
    return cliente.open("LISTAS-CLUBES").worksheet(nombre)

# -----------------------
# BUSCAR FILA NOMBRE
# -----------------------

def encontrar_fila_nombres(hoja):

    datos = hoja.get_all_values()

    for i, fila in enumerate(datos):
        if len(fila) > 1:
            if fila[1].strip().upper() == "NOMBRE":
                return i + 2

    return None

# -----------------------
# OBTENER ALUMNOS
# -----------------------

def obtener_alumnos(hoja):

    fila_inicio = encontrar_fila_nombres(hoja)

    if fila_inicio is None:
        return []

    col = hoja.col_values(2)

    alumnos = []

    for nombre in col[fila_inicio-1:]:

        if nombre.strip() == "":
            break

        alumnos.append(nombre.strip())

    return alumnos

# -----------------------
# ENCONTRAR MES Y DÍA
# -----------------------

def encontrar_columna_dia(hoja, dia):

    datos = hoja.get_all_values()

    zona = pytz.timezone("America/Mexico_City")
    ahora = datetime.now(zona)

    MESES = {
        1:"ENERO",
        2:"FEBRERO",
        3:"MARZO",
        4:"ABRIL",
        5:"MAYO",
        6:"JUNIO",
        7:"JULIO",
        8:"AGOSTO",
        9:"SEPTIEMBRE",
        10:"OCTUBRE",
        11:"NOVIEMBRE",
        12:"DICIEMBRE"
    }

    mes_actual = MESES[ahora.month]

    titulo_mes = f"ASISTENCIA {mes_actual}"

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

# -----------------------
# INICIO
# -----------------------

@app.route("/")
def inicio():
    return render_template("clubes.html")

# -----------------------
# ASISTENCIA
# -----------------------

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

# -----------------------
# GUARDAR
# -----------------------

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

    if columna_dia is None:
        return "No se encontró el día en la hoja."

    alumnos_presentes = request.form.getlist("alumnos")

    alumnos = obtener_alumnos(hoja)

    fila_inicio = encontrar_fila_nombres(hoja)

    if fila_inicio is None:
        return "No se encontró la columna de nombres."

    for i, nombre in enumerate(alumnos):

        fila = fila_inicio + i

        if nombre in alumnos_presentes:
            hoja.update_cell(fila, columna_dia, simbolo)

        else:
            hoja.update_cell(fila, columna_dia, "/")

    return render_template("confirmacion.html")

# -----------------------
# ESTADÍSTICAS
# -----------------------

@app.route("/estadisticas/<club>")
def estadisticas(club):

    hoja = abrir_hoja(CLUBES[club]["hoja"])

    datos = hoja.get_all_values()

    alumno_peor = ""
    faltas_max = 0

    for fila in datos:

        if len(fila) > 2:

            nombre = fila[1]

            if nombre.strip() == "" or nombre.upper() == "NOMBRE":
                continue

            faltas = fila.count("/")

            if faltas > faltas_max:
                faltas_max = faltas
                alumno_peor = nombre

    return render_template(
        "estadisticas.html",
        alumno=alumno_peor,
        faltas=faltas_max
    )

# -----------------------
# RUN
# -----------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
from flask import Flask, render_template, request, redirect
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import json
import os


app = Flask(__name__)

# --------------------------------
# CONEXION GOOGLE SHEETS
# --------------------------------

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

# --------------------------------
# MESES
# --------------------------------

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

# --------------------------------
# ENCONTRAR BLOQUE DEL MES
# --------------------------------

def encontrar_bloque_mes(hoja):

    datos = hoja.get_all_values()

    zona = pytz.timezone("America/Mexico_City")
    ahora = datetime.now(zona)

    mes_actual = MESES[ahora.month]

    for i, fila in enumerate(datos):

        texto = " ".join(fila).upper()

        if "ASISTENCIA" in texto and mes_actual in texto:
            return i

    return None


# --------------------------------
# ENCONTRAR COLUMNA DEL DIA
# --------------------------------

def encontrar_columna_dia(hoja, dia):

    datos = hoja.get_all_values()

    fila_mes = encontrar_bloque_mes(hoja)

    if fila_mes is None:
        return None

    fila_dias = datos[fila_mes + 1]

    for i, valor in enumerate(fila_dias):

        if valor.strip() == str(dia):
            return i + 1

    return None


# --------------------------------
# OBTENER ALUMNOS DEL MES
# --------------------------------

def obtener_alumnos_mes(hoja):

    datos = hoja.get_all_values()

    fila_mes = encontrar_bloque_mes(hoja)

    if fila_mes is None:
        return []

    alumnos = []

    for i in range(fila_mes + 2, len(datos)):

        fila = datos[i]

        texto = " ".join(fila).upper()

        # detener si aparece otro mes
        if "ASISTENCIA" in texto:
            break

        if len(fila) < 2:
            break

        nombre = fila[1].strip()

        if nombre == "":
            break

        alumnos.append(nombre)

    return alumnos


# --------------------------------
# ENCONTRAR FILA DEL ALUMNO
# --------------------------------

def encontrar_fila_alumno(hoja, nombre):

    datos = hoja.get_all_values()

    fila_mes = encontrar_bloque_mes(hoja)

    if fila_mes is None:
        return None

    for i in range(fila_mes + 2, len(datos)):

        fila = datos[i]

        if len(fila) < 2:
            break

        if fila[1].strip().upper() == nombre.upper():
            return i + 1

    return None


# --------------------------------
# PAGINAS
# --------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/clubes")
def clubes():
    return render_template("clubes.html")


# --------------------------------
# ASISTENCIA TENIS
# --------------------------------

@app.route("/asistencia/tenis")
def asistencia_tenis():

    hoja = libro.worksheet("TENIS")

    alumnos = obtener_alumnos_mes(hoja)

    zona = pytz.timezone("America/Mexico_City")
    ahora = datetime.now(zona)
    fecha = ahora.strftime("%Y-%m-%d")

    return render_template(
        "asistencia.html",
        alumnos=alumnos,
        club="tenis",
        fecha=fecha
    )

# --------------------------------
# ASISTENCIA BASQUET
# --------------------------------

@app.route("/asistencia/basquet")
def asistencia_basquet():

    hoja = libro.worksheet("BASQUET BASICO")

    alumnos = obtener_alumnos_mes(hoja)

    zona = pytz.timezone("America/Mexico_City")
    ahora = datetime.now(zona)
    fecha = ahora.strftime("%Y-%m-%d")

    return render_template(
        "asistencia.html",
        alumnos=alumnos,
        club="basquet",
        fecha=fecha
    )

# --------------------------------
# Estadisticas
# --------------------------------

@app.route("/estadisticas/<club>")
def estadisticas(club):

    if club == "tenis":
        hoja = libro.worksheet("TENIS")
    elif club == "basquet":
        hoja = libro.worksheet("BASQUET BASICO")

    datos = hoja.col_values(1)

    total_alumnos = len([nombre for nombre in datos if nombre.strip() != ""]) - 1

    asistencias = 0
    faltas = 0

    for fila in datos[1:]:
        for celda in fila[1:]:
            if celda in ["🎾", "🏀", "✓"]:
                asistencias += 1
            elif celda == "❌":
                faltas += 1

    return render_template(
        "estadisticas.html",
        club=club,
        total_alumnos=total_alumnos,
        asistencias=asistencias,
        faltas=faltas
    )

# --------------------------------
# GUARDAR ASISTENCIA
# --------------------------------

@app.route("/guardar/<club>", methods=["POST"])
def guardar(club):
    from datetime import datetime  # asegúrate de tener este import arriba del archivo

    # ...

    fecha_str = request.form.get("fecha")
    if not fecha_str:
        return "Falta la fecha", 400

    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    dia = fecha.day
    mes = fecha.month
    if club == "tenis":
        hoja = libro.worksheet("TENIS")
    elif club == "basquet":
        hoja = libro.worksheet("BASQUET BASICO")

    alumnos_presentes = request.form.getlist("alumnos_presentes")

    fecha = request.form.get("fecha")
    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
    dia = fecha_obj.day

    columna_dia = encontrar_columna_dia(hoja, dia)

    alumnos = obtener_alumnos_mes(hoja)

    # elegir emoji según el club
    if club.lower() == "tenis":
        presente = "🥎"
    elif club.lower() == "basquet":
        presente = "🏀"
    else:
        presente = "✔"

    for alumno in alumnos:

        fila = encontrar_fila_alumno(hoja, alumno)

        if fila and columna_dia:

            if alumno in alumnos_presentes:
                hoja.update_cell(fila, columna_dia, presente)
            else:
                hoja.update_cell(fila, columna_dia, "❌")


    return render_template("confirmacion.html", club=club)


# --------------------------------

if __name__ == "__main__":
    app.run(debug=True)
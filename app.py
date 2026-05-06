from flask import Flask, render_template, request
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import json
import os

app = Flask(name)

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
# CLUBES
# --------------------------------

CLUBES = {

    "tenis": {
        "hoja": "TENIS",
        "emoji": "🥎",
        "fondo": "fondo_tenis.png",
        "nombre": "Tenis"
    },

    "basquet_basico": {
        "hoja": "BASQUET BASICO",
        "emoji": "🏀",
        "fondo": "fondo_basquet.png",
        "nombre": "Basquet Básico"
    },

    "basquet_avanzado": {
        "hoja": "BASQUET AVANZADO",
        "emoji": "🏀",
        "fondo": "fondo_basquet.png",
        "nombre": "Basquet Avanzado"
    },

    "futbol": {
        "hoja": "FUTBOL 25/26",
        "emoji": "⚽",
        "fondo": "fondo_futbol.png",
        "nombre": "Fútbol"
    },

    "voleibol": {
        "hoja": "VOLEIBOL",
        "emoji": "🏐",
        "fondo": "fondo_voley.png",
        "nombre": "Voleibol"
    },

    "karate": {
        "hoja": "KARATE",
        "emoji": "🥋",
        "fondo": "fondo_karate.png",
        "nombre": "Karate"
    },

    "danza": {
        "hoja": "DANZA",
        "emoji": "💃",
        "fondo": "fondo_danza.png",
        "nombre": "Danza"
    },

    "robotica": {
        "hoja": "ROBOTICA",
        "emoji": "🤖",
        "fondo": "fondo_robotica.png",
        "nombre": "Robótica"
    },

    "musica": {
        "hoja": "MUSICA",
        "emoji": "🎵",
        "fondo": "fondo_musica.png",
        "nombre": "Música"
    }

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
    return render_template("index.html", clubes=CLUBES)

@app.route("/clubes")
def clubes():
    return render_template("clubes.html", clubes=CLUBES)

# --------------------------------
# ASISTENCIA DINAMICA
# --------------------------------

@app.route("/asistencia/<club>")
def asistencia(club):

    if club not in CLUBES:
        return "Club no encontrado"

    info_club = CLUBES[club]

    hoja = libro.worksheet(info_club["hoja"])

    alumnos = obtener_alumnos_mes(hoja)

    zona = pytz.timezone("America/Mexico_City")
    ahora = datetime.now(zona)

    fecha = ahora.strftime("%Y-%m-%d")

    return render_template(
        "asistencia.html",
        alumnos=alumnos,
        club=club,
        fecha=fecha,
        info_club=info_club
    )

# --------------------------------
# ESTADISTICAS
# --------------------------------

@app.route("/estadisticas/<club>")
def estadisticas(club):

    if club not in CLUBES:
        return "Club no encontrado"

    info_club = CLUBES[club]

    hoja = libro.worksheet(info_club["hoja"])

    datos = hoja.get_all_values()

    nombres = hoja.col_values(1)

    alumnos = [n for n in nombres[1:] if n.strip() != ""]

    total_alumnos = len(alumnos)

    asistencias = 0
    faltas = 0

    conteo_asistencias = {}
    conteo_faltas = {}

    for fila in datos[1:]:

        if len(fila) == 0:
            continue

        nombre = fila[0].strip()

        if nombre == "":
            continue

        asist = 0
        falt = 0

        columnas_mes = fila[1:32]

        for celda in columnas_mes:

            if celda in ["🥎", "🏀", "⚽", "🏐", "🥋", "💃", "🤖", "🎵", "✓"]:
                asist += 1
                asistencias += 1

            elif celda == "❌":
                falt += 1
                faltas += 1

        conteo_asistencias[nombre] = asist
        conteo_faltas[nombre] = falt

    top_asistencias = sorted(
        [(n, a) for n, a in conteo_asistencias.items() if a > 0],
        key=lambda x: x[1],
        reverse=True
    )[:5]

    alumno_mas_faltas = max(
        conteo_faltas.items(),
        key=lambda x: x[1]
    )

    alertas = [
        nombre for nombre, f in conteo_faltas.items()
        if f >= 3
    ]

    return render_template(
        "estadisticas.html",
        club=club,
        info_club=info_club,
        total_alumnos=total_alumnos,
        asistencias=asistencias,
        faltas=faltas,
        top_asistencias=top_asistencias,
        alumno_mas_faltas=alumno_mas_faltas,
        alertas=alertas
    )

# --------------------------------
# GUARDAR ASISTENCIA
# --------------------------------

@app.route("/guardar/<club>", methods=["POST"])
def guardar(club):

    if club not in CLUBES:
        return "Club no encontrado"

    info_club = CLUBES[club]

    hoja = libro.worksheet(info_club["hoja"])

    fecha_str = request.form.get("fecha")

    if not fecha_str:
        return "Falta la fecha", 400

    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")

    dia = fecha.day

    alumnos_presentes = request.form.getlist("alumnos_presentes")

    columna_dia = encontrar_columna_dia(hoja, dia)

    alumnos = obtener_alumnos_mes(hoja)

    presente = info_club["emoji"]

    for alumno in alumnos:

        fila = encontrar_fila_alumno(hoja, alumno)

        if fila and columna_dia:

            if alumno in alumnos_presentes:
                hoja.update_cell(fila, columna_dia, presente)

            else:
                hoja.update_cell(fila, columna_dia, "❌")

    return render_template(
        "confirmacion.html",
        club=club
    )

# --------------------------------

if name == "main":
    app.run(debug=True)
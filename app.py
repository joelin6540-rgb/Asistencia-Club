from flask import Flask, render_template, request
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

app = Flask(__name__)

# -----------------------------
# CONEXIÓN A GOOGLE SHEETS
# -----------------------------

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)

cliente = gspread.authorize(creds)

# -----------------------------
# CONFIGURACIÓN DE CLUBES
# -----------------------------

CLUBES = {
    "tenis": {
        "hoja": "TENIS",
        "simbolo": "🥎"
    },
    "basquet": {
        "hoja": "BASQUET",
        "simbolo": "🏀"
    }
}

# -----------------------------
# MESES
# -----------------------------

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

# -----------------------------
# ABRIR HOJA
# -----------------------------

def abrir_hoja(nombre):
    return cliente.open("Asistencia Club").worksheet(nombre)

# -----------------------------
# PÁGINA PRINCIPAL
# -----------------------------

@app.route("/")
def inicio():
    return render_template("clubes.html")

# -----------------------------
# PÁGINA DE ASISTENCIA
# -----------------------------

@app.route("/asistencia/<club>")
def asistencia(club):

    hoja = abrir_hoja(CLUBES[club]["hoja"])
    datos = hoja.get_all_values()

    alumnos = []

    for fila in datos[1:]:
        if fila[0] != "":
            alumnos.append(fila[0])

    hoy = datetime.now().strftime("%Y-%m-%d")

    return render_template(
        "asistencia.html",
        alumnos=alumnos,
        club=club,
        fecha=hoy
    )

# -----------------------------
# GUARDAR ASISTENCIA
# -----------------------------

@app.route("/guardar/<club>", methods=["POST"])
def guardar(club):

    fecha = request.form.get("fecha")

    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")

    hoja = abrir_hoja(CLUBES[club]["hoja"])
    simbolo = CLUBES[club]["simbolo"]

    alumnos_presentes = request.form.getlist("alumnos")

    año, mes, dia = fecha.split("-")

    dia = int(dia)
    mes_actual = MESES[int(mes)]

    buscar_mes = "ASISTENCIA " + mes_actual

    datos = hoja.get_all_values()

    fila_mes = None
    fila_dias = None
    columna_dia = None

    for i, fila in enumerate(datos):

        if buscar_mes in fila:
            fila_mes = i + 1
            fila_dias = i + 2

            for j, celda in enumerate(datos[i+1]):
                if celda == str(dia):
                    columna_dia = j + 1
                    break

            break

    if not columna_dia:
        return "No se encontró el día en la hoja"

    for i in range(fila_dias, len(datos)+1):

        fila = datos[i-1]

        if len(fila) > 0 and fila[0] != "" and fila[0] != "NOMBRE":

            nombre = fila[0]

            if nombre in alumnos_presentes:
                hoja.update_cell(i, columna_dia, simbolo)
            else:
                hoja.update_cell(i, columna_dia, "/")

        else:
            break

    return render_template("confirmacion.html")

# -----------------------------
# ESTADÍSTICAS
# -----------------------------

@app.route("/estadisticas")
def estadisticas():

    datos_estadisticas = []

    for club in CLUBES:

        hoja = abrir_hoja(CLUBES[club]["hoja"])
        filas = hoja.get_all_values()

        peor_alumno = ""
        max_faltas = -1

        alertas = []

        for fila in filas[1:]:

            if len(fila) == 0:
                continue

            nombre = fila[0]
            celdas = fila[1:]

            faltas = celdas.count("/")

            clases = sum(1 for c in celdas if c != "")

            asistencias = clases - faltas

            porcentaje = 0
            if clases > 0:
                porcentaje = int((asistencias / clases) * 100)

            if faltas > max_faltas:
                max_faltas = faltas
                peor_alumno = f"{nombre} — {faltas} faltas (de {clases} clases)"

            contador = 0

            for c in celdas:
                if c == "/":
                    contador += 1
                    if contador == 3:
                        alertas.append(f"⚠ {nombre} tiene 3 faltas seguidas")
                        break
                else:
                    contador = 0

        datos_estadisticas.append({
            "nombre": club.capitalize(),
            "peor": peor_alumno,
            "alertas": alertas
        })

    return render_template("estadisticas.html", estadisticas=datos_estadisticas)

# -----------------------------
# EJECUTAR APP
# -----------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
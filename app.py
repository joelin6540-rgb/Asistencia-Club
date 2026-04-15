from flask import Flask, render_template, request
from sheets import abrir_hoja
from datetime import datetime
import pytz
from datetime import datetime

app = Flask(__name__)

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

@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/asistencia/<club>")
def asistencia(club):

    hoja = abrir_hoja(CLUBES[club]["hoja"])
    datos = hoja.get_all_values()

    mes_actual = MESES[datetime.now().month]
    buscar_mes = "ASISTENCIA " + mes_actual

    alumnos = []
    leer_tabla = False
    leer_alumnos = False

    for fila in datos:

        if buscar_mes in " ".join(fila):
            leer_tabla = True
            continue

        if leer_tabla and len(fila) > 1 and fila[1] == "NOMBRE":
            leer_alumnos = True
            continue

        if leer_alumnos:

            if len(fila) > 1 and fila[1] != "":
                alumnos.append(fila[1])
            else:
                break

    from datetime import date

    hoy = date.today().isoformat()

    return render_template(
        "asistencia.html",
        alumnos=alumnos,
        club=club,
        fecha=hoy
    )


@app.route("/guardar/<club>", methods=["POST"])
def guardar(club):

    fecha = request.form.get("fecha")
    hoja = abrir_hoja(CLUBES[club]["hoja"])
    simbolo = CLUBES[club]["simbolo"]

    alumnos_presentes = request.form.getlist("alumnos")

    zona = pytz.timezone("America/Mexico_City")
    año, mes, dia = fecha.split("-")
    dia = int(dia)
    mes_actual = MESES[int(mes)]
    buscar_mes = "ASISTENCIA " + mes_actual

    datos = hoja.get_all_values()

    fila_mes = None
    fila_dias = None
    columna_dia = None

    # buscar el bloque del mes
    for i, fila in enumerate(datos):

        if buscar_mes in " ".join(fila):
            fila_mes = i
            break

    # buscar la fila donde están los números de los días
    for i in range(fila_mes, fila_mes + 10):

        fila = datos[i]

        for j, celda in enumerate(fila):

            if celda == str(hoy):
                fila_dias = i
                columna_dia = j + 1
                break

        if columna_dia:
            break

    # escribir asistencia solo en esa tabla
    for i in range(fila_dias + 1, len(datos)):

        fila = datos[i]

        if len(fila) > 1 and fila[1] != "" and fila[1] != "NOMBRE":

            fila_real = i + 1

            if fila[1] in alumnos_presentes:
                hoja.update_cell(fila_real, columna_dia, simbolo)
            else:
                hoja.update_cell(fila_real, columna_dia, "/")

        else:
            break

    return render_template("confirmacion.html", club=club)

@app.route("/estadisticas")
def estadisticas():

    datos = []

    for club in CLUBES:

        hoja = abrir_hoja(CLUBES[club]["hoja"])
        filas = hoja.get_all_values()

        peor_alumno = ""
        max_faltas = -1

        alertas = []

        for fila in filas[1:]:  # saltar encabezados

            nombre = fila[0]
            celdas = fila[1:]

            faltas = celdas.count("/")

            clases = sum(1 for c in celdas if c != "")

            asistencias = clases - faltas

            porcentaje = 0
            if clases > 0:
                porcentaje = int((asistencias / clases) * 100)

            # alumno con más faltas
            if faltas > max_faltas:
                max_faltas = faltas
                peor_alumno = f"{nombre} — {faltas} faltas (de {clases} clases)"

            # detectar 3 faltas seguidas
            contador = 0
            for c in celdas:
                if c == "/":
                    contador += 1
                    if contador == 3:
                        alertas.append(f"⚠ {nombre} tiene 3 faltas seguidas")
                        break
                else:
                    contador = 0

        datos.append({
            "nombre": club.capitalize(),
            "peor": peor_alumno,
            "alertas": alertas
        })

    return render_template("estadisticas.html", estadisticas=datos)

app.run(host="0.0.0.0", port=5000)
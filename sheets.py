import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

credenciales = ServiceAccountCredentials.from_json_keyfile_name(
    "credenciales.json", scope
)

cliente = gspread.authorize(credenciales)

def abrir_hoja(nombre):

    archivo = cliente.open("LISTAS-CLUBES")
    hoja = archivo.worksheet(nombre)

    return hoja
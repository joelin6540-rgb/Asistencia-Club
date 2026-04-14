import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

credenciales_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
credenciales = ServiceAccountCredentials.from_json_keyfile_dict(credenciales_dict, scope)

cliente = gspread.authorize(credenciales)

def abrir_hoja(nombre):
    archivo = cliente.open("LISTAS-CLUBES")
    hoja = archivo.worksheet(nombre)
    return hoja
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Setup Google Sheets access for public sheet
def get_sheet():
    json_url = "https://script.googleusercontent.com/a/macros/uncobariloche.com/echo?user_content_key=CG2i9176EN_fEhfGMa3sRyKykIKWWxmROxWMfLBOJThwcSl6aFR1KvirjKdvXO5hhXX356lz1q4Zso3ce61qBhn99BeIFztHOJmA1Yb3SEsKFZqtv3DaNYcMrmhZHmUMi80zadyHLKAZkrRHxBu1Au0pz7ld6jVXjnFAkueCBXjF8SZtan461aw3aWeqzN0KdY1xmf8BHr6ieKTr_YLnxBHtS3QtL6pwNWuqWZD6m5Lqc-lqjUur8jj2yWXtZyhcuN5D7Unz2Qjb3lj62okUAQ&lib=M59552CsR-N0Xy2P4BleMRakWGUSP2Iht"
    try:
        df = pd.read_json(json_url)
        
        # Convert DNI column to string and clean it
        if 'DNI' in df.columns:
            df['DNI'] = df['DNI'].astype(str).str.strip()
        else:
            raise ValueError("La columna DNI no fue encontrada en los datos")
            
        records = df.to_dict('records')
        if not records:
            raise ValueError("No se encontraron registros en la base de datos")
            
        return records
    except pd.errors.JSONDecodeError:
        print("Error decodificando JSON de Google Sheets")
        return None
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None

# Define the possible status steps in order
ESTADOS = [
    "Solicitud recibida en Sede Central",
    "Ingreso al Centro Regional Universitario Bariloche UNCo",
    "En revisión de la Comisión de Reválida",
    "Elevado a Sede Central UNCo para continuidad del trámite"
]

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.datetime.now().year}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/consulta', methods=['POST'])
def consulta():
    dni = request.form.get('dni', '').strip()
    
    if not dni:
        return render_template('error.html', 
                             error="Por favor, ingrese un DNI válido.")
    
    try:
        # Get data from Google Sheet
        records = get_sheet()
        
        if records is None:
            return render_template('error.html', 
                                error="No pudimos conectar con el servidor en este momento. Por favor, intente nuevamente en unos minutos.")
        
        # Create a list to store any matching records
        matching_records = []
        for record in records:
            record_dni = str(record.get('DNI', '')).strip()
            if record_dni == dni:
                matching_records.append(record)
        
        if not matching_records:
            return render_template('error.html', 
                                error="No se encontró ningún trámite asociado al DNI ingresado. Por favor, verifique el número y vuelva a intentarlo.")
        
        # Use the most recent record if there are multiple
        tramite = matching_records[0]
        
        # Verify all required fields are present
        required_fields = ['Expediente SUDOCU', 'APELLIDOS', 'NOMBRES', 'Universidad de origen', 'titulo UNCO', 'ESTADO', 'CORREO']
        missing_fields = [field for field in required_fields if not tramite.get(field)]
        
        if missing_fields:
            return render_template('error.html', 
                                error="Los datos del trámite están incompletos. Por favor, contacte al administrador.")
        
        # Get current status
        current_estado = tramite.get('ESTADO', '')
        
        # Validate the estado exists in our defined states
        if current_estado not in ESTADOS:
            return render_template('error.html', 
                                error="El estado del trámite no es válido. Por favor, contacte al administrador.")
        
        # Calculate progress
        progress = []
        for estado in ESTADOS:
            if estado == current_estado:
                progress.append({"estado": estado, "status": "current"})
            elif ESTADOS.index(estado) < ESTADOS.index(current_estado):
                progress.append({"estado": estado, "status": "completed"})
            else:
                progress.append({"estado": estado, "status": "pending"})
        
        # Convert tramite to list format as expected by template
        tramite_list = [tramite]
        
        return render_template('tramite.html', tramite=tramite_list, progress=progress)
    
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', 
                             error="Ocurrió un error inesperado. Por favor, intente nuevamente más tarde.")

if __name__ == '__main__':
    app.run(debug=True)
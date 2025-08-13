#!/usr/bin/env python3
"""
Application principale Flask pour la conversion AutoCAD vers Caneco XML
Utilise le générateur intelligent pour traiter les fichiers Excel AutoCAD
"""

import os
import logging
from flask import Flask, render_template, request, flash, redirect, url_for, send_file, jsonify
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import tempfile
import traceback

# Importer le générateur basé sur Template_Caneco.xml
from caneco_template_generator import CanecoTemplateGenerator

# Configuration de l'application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration logging
logging.basicConfig(level=logging.DEBUG)

# Configuration upload
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Extensions autorisées
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'txt', 'xml'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Page d'accueil avec interface de téléchargement"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Traite le fichier AutoCAD uploadé et génère le XML Caneco"""
    
    if 'file' not in request.files:
        flash('Aucun fichier sélectionné', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Aucun fichier sélectionné', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        try:
            # Sauvegarder le fichier uploadé
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Initialiser le générateur Template_Caneco.xml
            generator = CanecoTemplateGenerator()
            
            # Traiter le fichier AutoCAD
            autocad_data = generator.process_autocad_data(file_path)
            
            if autocad_data['total'] == 0:
                flash('Aucun composant trouvé dans le fichier', 'warning')
                return redirect(url_for('index'))
            
            # Générer le XML Caneco selon Template_Caneco.xml
            output_filename = f"caneco_{filename.split('.')[0]}.xml"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            generator.generate_xml_from_template(autocad_data, output_path)
            
            # Préparer les statistiques pour l'affichage
            stats = {
                'total_components': autocad_data['total'],
                'component_types': autocad_data['stats'],
                'output_file': output_filename
            }
            
            flash(f'Conversion réussie! {autocad_data["total"]} composants traités', 'success')
            
            return render_template('result.html', stats=stats, filename=output_filename)
            
        except Exception as e:
            app.logger.error(f"Erreur traitement fichier: {str(e)}")
            app.logger.error(traceback.format_exc())
            flash(f'Erreur lors du traitement: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    else:
        flash('Type de fichier non autorisé. Utilisez .xlsx, .xls, .txt ou .xml', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """Télécharge le fichier XML généré"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            flash('Fichier non trouvé', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Erreur téléchargement: {str(e)}")
        flash('Erreur lors du téléchargement', 'error')
        return redirect(url_for('index'))

@app.route('/api/status')
def api_status():
    """API pour vérifier le statut de l'application"""
    return jsonify({
        'status': 'ok',
        'message': 'Générateur AutoCAD vers Caneco opérationnel',
        'version': '2.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

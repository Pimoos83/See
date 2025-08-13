import os
import logging
from flask import Flask, render_template, request, flash, redirect, url_for, send_file, jsonify
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import tempfile
import shutil
from caneco_complete_generator import CanecoCompleteGenerator

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xml', 'txt', 'xlsx', 'xls'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page for file upload"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads and process transformation"""
    try:
        # Check if both files are present
        if 'caneco_file' not in request.files or 'autocad_file' not in request.files:
            flash('Veuillez sélectionner les deux fichiers requis', 'error')
            return redirect(url_for('index'))
        
        caneco_file = request.files['caneco_file']
        autocad_file = request.files['autocad_file']
        
        # Validate files
        if caneco_file.filename == '' or autocad_file.filename == '':
            flash('Veuillez sélectionner les deux fichiers requis', 'error')
            return redirect(url_for('index'))
        
        if not (allowed_file(caneco_file.filename) and allowed_file(autocad_file.filename)):
            flash('Types de fichiers non autorisés. Utilisez .xml pour Caneco et .txt/.xlsx/.xls pour AutoCAD', 'error')
            return redirect(url_for('index'))
        
        # Validate file extensions specifically
        if not (caneco_file.filename and caneco_file.filename.lower().endswith('.xml')):
            flash('Le fichier Caneco doit être un fichier XML', 'error')
            return redirect(url_for('index'))
        
        # AutoCAD file can be TXT or Excel
        autocad_ext = autocad_file.filename.lower().split('.')[-1] if autocad_file.filename else ''
        if autocad_ext not in ['txt', 'xlsx', 'xls']:
            flash('Le fichier AutoCAD doit être un fichier TXT, XLSX ou XLS', 'error')
            return redirect(url_for('index'))
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded files
            caneco_filename = secure_filename(caneco_file.filename or 'caneco.xml')
            autocad_filename = secure_filename(autocad_file.filename or f'autocad.{autocad_ext}')
            caneco_path = os.path.join(temp_dir, caneco_filename)
            autocad_path = os.path.join(temp_dir, autocad_filename)
            
            caneco_file.save(caneco_path)
            autocad_file.save(autocad_path)
            
            # Process files - Générateur avec template Product personnalisé
            from caneco_template_product_generator import CanecoTemplateProductGenerator
            from autocad_to_caneco_analyzer import AutoCADToCanecoAnalyzer
            
            # Analyser d'abord les données AutoCAD
            analyzer = AutoCADToCanecoAnalyzer()
            analyzer.analyze_autocad_file(autocad_path)
            analyzer.save_mapping_analysis(os.path.join(temp_dir, 'autocad_mapping.json'))
            
            # Créer le générateur template Product personnalisé
            generator = CanecoTemplateProductGenerator()
            generator.load_autocad_data(os.path.join(temp_dir, 'autocad_mapping.json'))
            
            app.logger.info("Générateur template Product personnalisé configuré")
            
            # Generate XML using template Product
            try:
                output_path = os.path.join(temp_dir, 'caneco_generated.xml')
                success = generator.generate_template_product_xml(output_path)
                
                if success:
                    app.logger.info("XML complet généré")
                    
                    # Validate generated XML
                    if os.path.exists(output_path):
                        app.logger.info("XML complet validé")
                        
                        # Copy to uploads folder
                        final_output = os.path.join(UPLOAD_FOLDER, 'caneco_generated.xml')
                        shutil.copy2(output_path, final_output)
                        
                        # Create summary
                        total_elements = len(generator.autocad_data)
                        summary = {
                            'generated_products': total_elements,
                            'total_records': total_elements,
                            'generated_devices': total_elements,
                            'generated_components': total_elements,
                            'generated_functions': total_elements,
                            'generated_connections': max(0, total_elements - 1)
                        }
                        
                        return render_template('result.html', 
                                             success=True, 
                                             filename='caneco_generated.xml',
                                             summary=summary)
                    else:
                        flash('XML non valide', 'error')
                        return redirect(url_for('index'))
                else:
                    flash('Erreur génération XML', 'error')
                    return redirect(url_for('index'))
                    
            except Exception as e:
                app.logger.error(f"Erreur lors de la génération du XML: {str(e)}")
                flash(f'Erreur lors de la génération du XML: {str(e)}', 'error')
                return redirect(url_for('index'))
    
    except Exception as e:
        app.logger.error(f"Erreur générale lors du traitement: {str(e)}")
        flash(f'Erreur lors du traitement des fichiers: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated XML file"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            flash('Fichier non trouvé', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Erreur lors du téléchargement: {str(e)}")
        flash(f'Erreur lors du téléchargement: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/preview/<filename>')
def preview_file(filename):
    """Preview generated XML content"""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'content': content})
        else:
            return jsonify({'error': 'Fichier non trouvé'}), 404
    except Exception as e:
        app.logger.error(f"Erreur lors de la prévisualisation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    flash('Fichier trop volumineux. Taille maximale autorisée: 16MB', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"Erreur serveur: {str(e)}")
    flash('Erreur interne du serveur', 'error')
    return redirect(url_for('index'))

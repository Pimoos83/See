#!/usr/bin/env python3
"""
Correction finale des namespaces dans tous les templates
"""

import os
import re

def fix_template_namespaces():
    """Corrige les namespaces manquants dans tous les templates"""
    
    print("=== CORRECTION NAMESPACES TEMPLATES ===")
    
    # Namespace complet Schneider Electric
    ns_declarations = ' xmlns:ns0="http://www.schneider-electric.com/electrical-distribution/exchange-format" xmlns:ns1="http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy"'
    commercial_ns = ' xmlns:ns2="http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy"'
    
    # Trouver tous les templates
    template_files = [f for f in os.listdir('.') if f.startswith('Template_') and f.endswith('.xml')]
    
    for template_file in template_files:
        print(f"Correction {template_file}...")
        
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Identifier le type d'élément et ajouter les namespaces appropriés
        if 'Device' in content:
            content = re.sub(r'<ns0:Device', f'<ns0:Device{ns_declarations}', content)
        elif 'Function' in content:
            content = re.sub(r'<ns0:Function', f'<ns0:Function{ns_declarations}', content)
        elif 'Component' in content:
            content = re.sub(r'<ns0:Component', f'<ns0:Component{ns_declarations}', content)
        elif 'Terminal' in content:
            content = re.sub(r'<ns0:Terminal', f'<ns0:Terminal{ns_declarations}', content)
        elif 'Equipment' in content:
            content = re.sub(r'<ns0:Equipment', f'<ns0:Equipment{ns_declarations}', content)
        elif 'Pack' in content:
            content = re.sub(r'<ns0:Pack', f'<ns0:Pack{ns_declarations}{commercial_ns}', content)
        elif 'Instance' in content:
            content = re.sub(r'<ns0:Instance', f'<ns0:Instance{ns_declarations}', content)
        elif 'Company' in content:
            content = re.sub(r'<ns0:Company', f'<ns0:Company{ns_declarations}', content)
        elif 'Person' in content:
            content = re.sub(r'<ns0:Person', f'<ns0:Person{ns_declarations}', content)
        
        # Sauvegarder le fichier corrigé
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ {template_file} corrigé")
    
    print(f"Correction terminée pour {len(template_files)} templates")

if __name__ == "__main__":
    fix_template_namespaces()
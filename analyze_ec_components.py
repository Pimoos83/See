#!/usr/bin/env python3
"""
Analyseur des composants ECxxxxx dans Caneco BT.xml
Extrait les variations et crée les templates
"""

import xml.etree.ElementTree as ET
import re
from collections import defaultdict

def analyze_ec_components():
    """Analyse les composants EC et crée les templates"""
    
    # Charger XML
    with open('attached_assets/Caneco BT _1754486408913.xml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    root = ET.fromstring(content)
    
    print("=== ANALYSE DES COMPOSANTS ECxxxxx ===")
    
    # Trouver tous les Component avec id ECxxxxx
    components = []
    for element in root.iter():
        if element.tag.endswith('}Component') and element.get('id', '').startswith('EC'):
            components.append(element)
    
    print(f"Composants EC trouvés: {len(components)}")
    
    # Analyser les variations par type de composant
    variations = defaultdict(list)
    
    for comp in components:
        # Identifier le type de composant par son premier enfant
        component_type = "Unknown"
        type_element = None
        
        for child in comp:
            if child.tag.endswith('}Component'):
                # C'est un sous-composant
                for subchild in child:
                    if 'Component' in subchild.tag:
                        type_element = subchild
                        component_type = subchild.tag.split('}')[-1]
                        break
                break
            elif 'Component' in child.tag:
                type_element = child
                component_type = child.tag.split('}')[-1]
                break
        
        if type_element is None:
            # Pas de sous-composant spécialisé, utiliser le nom fonctionnel
            func_name = comp.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}FunctionalName')
            if func_name is not None:
                component_type = f"Generic_{func_name.text[:10] if func_name.text else 'Unknown'}"
        
        variations[component_type].append({
            'component': comp,
            'id': comp.get('id'),
            'functional_name': comp.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}FunctionalName')
        })
    
    print(f"\nVariations détectées: {len(variations)}")
    
    # Créer templates pour chaque variation
    created_templates = []
    
    for i, (comp_type, comps) in enumerate(variations.items()):
        print(f"\nVARIATION {chr(65+i)} - {comp_type}: {len(comps)} composants")
        
        # Prendre premier composant comme template
        template_comp = comps[0]['component']
        
        # Convertir en string XML
        template_xml = ET.tostring(template_comp, encoding='unicode')
        
        # Remplacer les IDs par des placeholders
        template_xml = re.sub(r'id="EC\d+"', 'id="{COMPONENT_ID}"', template_xml)
        template_xml = re.sub(r'id="ECT\d+"', 'id="{TERMINAL_ID}"', template_xml)
        
        # Formater proprement
        template_xml = template_xml.replace('><', '>\n<')
        
        # Nom du fichier template
        template_filename = f"Template_ECxxxxx_{chr(65+i)}.xml"
        
        # Sauvegarder
        with open(template_filename, 'w', encoding='utf-8') as f:
            f.write(template_xml)
        
        created_templates.append({
            'filename': template_filename,
            'type': comp_type,
            'count': len(comps),
            'examples': [c['id'] for c in comps[:5]]
        })
        
        print(f"  Template créé: {template_filename}")
        print(f"  Exemples IDs: {[c['id'] for c in comps[:5]]}")
        if comps[0]['functional_name'] is not None:
            print(f"  Nom fonctionnel: {comps[0]['functional_name'].text}")
    
    print(f"\n=== RÉSUMÉ ===")
    print(f"Total templates créés: {len(created_templates)}")
    
    for template in created_templates:
        print(f"  {template['filename']}: {template['type']} ({template['count']} composants)")
    
    return created_templates

if __name__ == "__main__":
    analyze_ec_components()
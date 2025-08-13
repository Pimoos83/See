#!/usr/bin/env python3
"""
Générateur de templates pour tous les éléments Caneco
Analyse chaque pattern et crée les templates correspondants
"""

import xml.etree.ElementTree as ET
import re
from collections import defaultdict
import json

def analyze_and_create_templates():
    """Analyse tous les patterns et crée les templates"""
    
    print("=== GÉNÉRATION TEMPLATES POUR TOUS LES PATTERNS ===")
    
    # Charger XML
    with open('attached_assets/Caneco BT _1754486408913.xml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    root = ET.fromstring(content)
    
    # Patterns à analyser (sauf PGxxxxx et ECxxxxx déjà faits)
    patterns_to_analyze = [
        'EDxxxxx',   # Devices
        'EFxxxxx',   # Functions
        'PKxxxxx',   # Packs
        'PIxxxxx',   # Instances
        'EQxxxxx',   # Equipments
        'ECTxxxxx',  # Terminals
        'CCxxxxx',   # Companies
        'CPxxxxx'    # Persons
    ]
    
    templates_created = {}
    
    for pattern in patterns_to_analyze:
        print(f"\n=== ANALYSE PATTERN {pattern} ===")
        
        # Collecter tous les éléments de ce pattern
        elements = collect_elements_by_pattern(root, pattern)
        print(f"Éléments trouvés: {len(elements)}")
        
        if not elements:
            continue
        
        # Analyser variations pour ce pattern
        variations = analyze_pattern_variations(elements, pattern)
        print(f"Variations détectées: {len(variations)}")
        
        # Créer templates pour chaque variation
        pattern_templates = create_pattern_templates(variations, pattern)
        templates_created[pattern] = pattern_templates
        
        for i, template_info in enumerate(pattern_templates):
            print(f"  Template {template_info['filename']}: {template_info['count']} éléments")
    
    # Sauvegarder résumé
    save_templates_summary(templates_created)
    
    return templates_created

def collect_elements_by_pattern(root, pattern):
    """Collecte tous les éléments correspondant à un pattern"""
    elements = []
    
    for element in root.iter():
        elem_id = element.get('id', '')
        if elem_id and matches_pattern(elem_id, pattern):
            elements.append(element)
    
    return elements

def matches_pattern(elem_id, pattern):
    """Vérifie si un ID correspond à un pattern"""
    pattern_regex = {
        'EDxxxxx': r'^ED\d{5}$',
        'EFxxxxx': r'^EF\d{5}$', 
        'PKxxxxx': r'^PK\d{5}$',
        'PIxxxxx': r'^PI\d{5}$',
        'EQxxxxx': r'^EQ\d{5}$',
        'ECTxxxxx': r'^ECT\d{5}$',
        'CCxxxxx': r'^CC\d{5}$',
        'CPxxxxx': r'^CP\d{5}$'
    }
    
    if pattern in pattern_regex:
        return bool(re.match(pattern_regex[pattern], elem_id))
    
    return False

def analyze_pattern_variations(elements, pattern):
    """Analyse les variations dans un pattern"""
    variations = defaultdict(list)
    
    for element in elements:
        # Créer une clé basée sur la structure de l'élément
        variation_key = create_variation_key(element, pattern)
        variations[variation_key].append(element)
    
    return dict(variations)

def create_variation_key(element, pattern):
    """Crée une clé de variation basée sur la structure"""
    
    if pattern == 'EDxxxxx':
        # Pour Device: différencier par attributs principaux
        components = element.get('Components', '')
        product_instance = element.get('ProductInstance', '')
        
        # Analyser type de components
        if 'EC' in components:
            if len(components.split()) == 1:
                comp_type = 'single'
            else:
                comp_type = 'multiple'
        else:
            comp_type = 'none'
        
        return f"Device_{comp_type}"
    
    elif pattern == 'EFxxxxx':
        # Pour Function: différencier par structure des enfants
        children_tags = [child.tag.split('}')[-1] if '}' in child.tag else child.tag for child in element]
        children_key = '_'.join(sorted(set(children_tags)))
        return f"Function_{children_key}"
    
    elif pattern == 'PKxxxxx':
        # Pour Pack: différencier par attribut Descriptor
        descriptor = element.get('Descriptor', 'default')
        return f"Pack_{descriptor}"
    
    elif pattern == 'PIxxxxx':
        # Pour Instance: différencier par structure interne
        has_values = any(child.tag.endswith('}Values') for child in element.iter())
        return f"Instance_{'with_values' if has_values else 'simple'}"
    
    elif pattern == 'EQxxxxx':
        # Pour Equipment: différencier par type (Commercial/Electrical)
        commercial = element.find('.//*[@*="Commercial"]') is not None
        electrical = element.find('.//*[@*="Electrical"]') is not None
        
        if commercial and electrical:
            return "Equipment_Commercial_Electrical"
        elif commercial:
            return "Equipment_Commercial"
        elif electrical:
            return "Equipment_Electrical"
        else:
            return "Equipment_Generic"
    
    elif pattern == 'ECTxxxxx':
        # Pour Terminal: différencier par polarité
        polarity_elem = element.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Polarity')
        polarity = polarity_elem.text if polarity_elem is not None else 'unknown'
        return f"Terminal_{polarity.replace('+', '_')}"
    
    else:
        # Variation par défaut basée sur le tag
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        return f"{pattern}_{tag}"

def create_pattern_templates(variations, pattern):
    """Crée les templates pour un pattern"""
    templates = []
    
    for i, (variation_key, elements) in enumerate(variations.items()):
        if len(elements) == 0:
            continue
        
        # Utiliser premier élément comme template
        template_element = elements[0]
        
        # Convertir en XML string
        template_xml = ET.tostring(template_element, encoding='unicode')
        
        # Remplacer IDs par placeholders
        template_xml = apply_placeholders(template_xml, pattern)
        
        # Nom du fichier template
        template_filename = f"Template_{pattern}_{chr(65+i)}.xml"
        
        # Sauvegarder template
        with open(template_filename, 'w', encoding='utf-8') as f:
            f.write(template_xml)
        
        templates.append({
            'filename': template_filename,
            'variation': variation_key,
            'count': len(elements),
            'examples': [elem.get('id') for elem in elements[:5]]
        })
    
    return templates

def apply_placeholders(template_xml, pattern):
    """Applique les placeholders appropriés selon le pattern"""
    
    placeholder_mapping = {
        'EDxxxxx': [
            (r'id="ED\d+"', 'id="{DEVICE_ID}"'),
            (r'ProductInstance="PI\d+"', 'ProductInstance="{PRODUCT_INSTANCE}"'),
            (r'Components="[^"]*"', 'Components="{COMPONENTS}"')
        ],
        'EFxxxxx': [
            (r'id="EF\d+"', 'id="{FUNCTION_ID}"'),
            (r'Components="[^"]*"', 'Components="{COMPONENTS}"'),
            (r'Devices="[^"]*"', 'Devices="{DEVICES}"')
        ],
        'PKxxxxx': [
            (r'id="PK\d+"', 'id="{PACK_ID}"'),
            (r'Descriptor="[^"]*"', 'Descriptor="{DESCRIPTOR}"')
        ],
        'PIxxxxx': [
            (r'id="PI\d+"', 'id="{INSTANCE_ID}"')
        ],
        'EQxxxxx': [
            (r'id="EQ\d+"', 'id="{EQUIPMENT_ID}"'),
            (r'ProductPacks="[^"]*"', 'ProductPacks="{PRODUCT_PACKS}"'),
            (r'Devices="[^"]*"', 'Devices="{DEVICES}"'),
            (r'Functions="[^"]*"', 'Functions="{FUNCTIONS}"')
        ],
        'ECTxxxxx': [
            (r'id="ECT\d+"', 'id="{TERMINAL_ID}"')
        ],
        'CCxxxxx': [
            (r'id="CC\d+"', 'id="{COMPANY_ID}"')
        ],
        'CPxxxxx': [
            (r'id="CP\d+"', 'id="{PERSON_ID}"'),
            (r'id="CC\d+"', 'id="{COMPANY_ID}"')
        ]
    }
    
    if pattern in placeholder_mapping:
        for old_pattern, new_pattern in placeholder_mapping[pattern]:
            template_xml = re.sub(old_pattern, new_pattern, template_xml)
    
    return template_xml

def save_templates_summary(templates_created):
    """Sauvegarde un résumé de tous les templates créés"""
    
    summary = {
        'creation_date': '2025-08-11',
        'total_patterns': len(templates_created),
        'patterns': templates_created
    }
    
    with open('caneco_templates_disjoncteur.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== RÉSUMÉ TEMPLATES ===")
    total_templates = sum(len(templates) for templates in templates_created.values())
    print(f"Total templates créés: {total_templates}")
    
    for pattern, templates in templates_created.items():
        print(f"\n{pattern}: {len(templates)} template(s)")
        for template in templates:
            print(f"  {template['filename']}: {template['count']} éléments ({template['variation']})")

if __name__ == "__main__":
    analyze_and_create_templates()

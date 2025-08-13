#!/usr/bin/env python3
"""
Recréation complète des templates avec la structure XML exacte du fichier original
SANS prefixes de namespace parasites
"""

import xml.etree.ElementTree as ET
import re

def recreate_all_templates():
    """Recrée tous les templates avec la structure exacte du fichier original"""
    
    print("=== RECRÉATION TEMPLATES PROPRES ===")
    
    # Charger le XML original
    with open('attached_assets/Caneco BT _1754486408913.xml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    root = ET.fromstring(content)
    
    # Patterns à recréer avec leurs éléments de référence
    patterns_config = {
        'EDxxxxx': {'count': 3, 'element_type': 'Device'},
        'EFxxxxx': {'count': 3, 'element_type': 'Function'},
        'PKxxxxx': {'count': 1, 'element_type': 'Pack'},
        'PIxxxxx': {'count': 1, 'element_type': 'Instance'},
        'EQxxxxx': {'count': 1, 'element_type': 'Equipment'},
        'ECTxxxxx': {'count': 3, 'element_type': 'Terminal'},
        'CCxxxxx': {'count': 1, 'element_type': 'Company'},
        'CPxxxxx': {'count': 1, 'element_type': 'Person'}
    }
    
    templates_created = 0
    
    for pattern, config in patterns_config.items():
        print(f"\n=== RECRÉATION {pattern} ({config['element_type']}) ===")
        
        # Trouver tous les éléments de ce pattern
        elements = find_pattern_elements(root, pattern)
        
        if not elements:
            print(f"Aucun élément {pattern} trouvé")
            continue
        
        print(f"Éléments trouvés: {len(elements)}")
        
        # Créer les templates demandés
        for i in range(min(config['count'], len(elements))):
            template_file = f"Template_{pattern}_{chr(65+i)}.xml"
            
            # Extraire l'élément proprement SANS modification des namespaces
            clean_xml = extract_element_as_is(elements[i])
            
            # Appliquer seulement les placeholders d'ID
            clean_xml = apply_id_placeholders_only(clean_xml, pattern)
            
            # Sauvegarder
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(clean_xml)
            
            print(f"✓ {template_file} créé")
            templates_created += 1
    
    print(f"\n=== RECRÉATION TERMINÉE ===")
    print(f"Templates créés: {templates_created}")
    return templates_created

def find_pattern_elements(root, pattern):
    """Trouve les éléments correspondant au pattern"""
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
    
    regex = pattern_regex.get(pattern, r'^.*$')
    elements = []
    
    for element in root.iter():
        elem_id = element.get('id', '')
        if elem_id and re.match(regex, elem_id):
            elements.append(element)
    
    return elements

def extract_element_as_is(element):
    """Extrait l'élément XML tel quel, sans modification des namespaces"""
    
    # Convertir l'élément en string XML
    xml_str = ET.tostring(element, encoding='unicode')
    
    # IMPORTANT: Ne pas modifier les namespaces, garder la structure exacte
    return xml_str

def apply_id_placeholders_only(xml_content, pattern):
    """Applique SEULEMENT les placeholders d'ID, garde tout le reste intact"""
    
    # Mapping simple des IDs seulement
    id_mappings = {
        'EDxxxxx': (r'id="ED\d+"', 'id="{DEVICE_ID}"'),
        'EFxxxxx': (r'id="EF\d+"', 'id="{FUNCTION_ID}"'),
        'PKxxxxx': (r'id="PK\d+"', 'id="{PACK_ID}"'),
        'PIxxxxx': (r'id="PI\d+"', 'id="{INSTANCE_ID}"'),
        'EQxxxxx': (r'id="EQ\d+"', 'id="{EQUIPMENT_ID}"'),
        'ECTxxxxx': (r'id="ECT\d+"', 'id="{TERMINAL_ID}"'),
        'CCxxxxx': (r'id="CC\d+"', 'id="{COMPANY_ID}"'),
        'CPxxxxx': (r'id="CP\d+"', 'id="{PERSON_ID}"')
    }
    
    if pattern in id_mappings:
        old_pattern, new_pattern = id_mappings[pattern]
        xml_content = re.sub(old_pattern, new_pattern, xml_content)
    
    # Placeholder pour références croisées communes
    xml_content = re.sub(r'ProductInstance="PI\d+"', 'ProductInstance="{PRODUCT_INSTANCE}"', xml_content)
    xml_content = re.sub(r'Components="[^"]*"', 'Components="{COMPONENTS}"', xml_content)
    xml_content = re.sub(r'Devices="[^"]*"', 'Devices="{DEVICES}"', xml_content)
    xml_content = re.sub(r'Functions="[^"]*"', 'Functions="{FUNCTIONS}"', xml_content)
    xml_content = re.sub(r'ProductPacks="[^"]*"', 'ProductPacks="{PRODUCT_PACKS}"', xml_content)
    
    return xml_content

if __name__ == "__main__":
    recreate_all_templates()

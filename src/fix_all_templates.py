#!/usr/bin/env python3
"""
Création des templates EXACTS basés sur le fichier original
SANS aucun prefix ns0: parasites, structure exacte du fichier original
"""

import xml.etree.ElementTree as ET
import re

def create_exact_templates():
    """Crée des templates basés sur la structure EXACTE du fichier original"""
    
    print("=== CRÉATION TEMPLATES EXACTS ===")
    
    # Charger le fichier original
    with open('attached_assets/Caneco BT _1754486408913.xml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parser le XML
    root = ET.fromstring(content)
    
    # Extraire les éléments réels et créer les templates
    templates_created = 0
    
    # 1. DEVICES - Extraire les vrais Device du fichier
    devices = root.findall('.//Device')
    if devices:
        print(f"Devices trouvés: {len(devices)}")
        for i, device in enumerate(devices[:3]):  # Prendre 3 exemples
            template_content = ET.tostring(device, encoding='unicode')
            # Appliquer les placeholders
            template_content = apply_placeholders(template_content, 'Device')
            
            template_file = f"Template_EDxxxxx_{chr(65+i)}.xml"
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            print(f"✓ {template_file} créé")
            templates_created += 1
    
    # 2. FUNCTIONS - Extraire les vrais Function du fichier
    functions = root.findall('.//Function')
    if functions:
        print(f"Functions trouvés: {len(functions)}")
        for i, function in enumerate(functions[:3]):  # Prendre 3 exemples
            template_content = ET.tostring(function, encoding='unicode')
            template_content = apply_placeholders(template_content, 'Function')
            
            template_file = f"Template_EFxxxxx_{chr(65+i)}.xml"
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            print(f"✓ {template_file} créé")
            templates_created += 1
    
    # 3. TERMINALS - Extraire les vrais Terminal du fichier
    terminals = root.findall('.//Terminal')
    if terminals:
        print(f"Terminals trouvés: {len(terminals)}")
        for i, terminal in enumerate(terminals[:3]):  # Prendre 3 exemples
            template_content = ET.tostring(terminal, encoding='unicode')
            template_content = apply_placeholders(template_content, 'Terminal')
            
            template_file = f"Template_ECTxxxxx_{chr(65+i)}.xml"
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            print(f"✓ {template_file} créé")
            templates_created += 1
    
    # 4. EQUIPMENTS - Extraire les vrais Equipment du fichier
    equipments = root.findall('.//Equipment')
    if equipments:
        print(f"Equipments trouvés: {len(equipments)}")
        equipment = equipments[0]  # Prendre le premier
        template_content = ET.tostring(equipment, encoding='unicode')
        template_content = apply_placeholders(template_content, 'Equipment')
        
        template_file = "Template_EQxxxxx_A.xml"
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        print(f"✓ {template_file} créé")
        templates_created += 1
    
    # 5. PACKS - Extraire les vrais Pack du fichier
    packs = root.findall('.//Pack')
    if packs:
        print(f"Packs trouvés: {len(packs)}")
        pack = packs[0]  # Prendre le premier
        template_content = ET.tostring(pack, encoding='unicode')
        template_content = apply_placeholders(template_content, 'Pack')
        
        template_file = "Template_PKxxxxx_A.xml"
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        print(f"✓ {template_file} créé")
        templates_created += 1
    
    # 6. INSTANCES - Extraire les vrais Instance du fichier  
    instances = root.findall('.//Instance')
    if instances:
        print(f"Instances trouvés: {len(instances)}")
        instance = instances[0]  # Prendre le premier
        template_content = ET.tostring(instance, encoding='unicode')
        template_content = apply_placeholders(template_content, 'Instance')
        
        template_file = "Template_PIxxxxx_A.xml"
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        print(f"✓ {template_file} créé")
        templates_created += 1
    
    # 7. COMPANIES - Extraire les vrais Company du fichier
    companies = root.findall('.//Company')
    if companies:
        print(f"Companies trouvés: {len(companies)}")
        company = companies[0]  # Prendre le premier
        template_content = ET.tostring(company, encoding='unicode')
        template_content = apply_placeholders(template_content, 'Company')
        
        template_file = "Template_CCxxxxx_A.xml"
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        print(f"✓ {template_file} créé")
        templates_created += 1
    
    # 8. PERSONS - Extraire les vrais Person du fichier
    persons = root.findall('.//Person')
    if persons:
        print(f"Persons trouvés: {len(persons)}")
        person = persons[0]  # Prendre le premier
        template_content = ET.tostring(person, encoding='unicode')
        template_content = apply_placeholders(template_content, 'Person')
        
        template_file = "Template_CPxxxxx_A.xml"
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        print(f"✓ {template_file} créé")
        templates_created += 1
    
    print(f"\n=== TERMINÉ ===")
    print(f"Templates créés: {templates_created}")
    return templates_created

def apply_placeholders(xml_content, element_type):
    """Applique les placeholders aux IDs dans le contenu XML"""
    
    # Mapping des placeholders par type d'élément
    placeholder_mappings = {
        'Device': {
            r'id="ED\d+"': 'id="{DEVICE_ID}"',
            r'ProductInstance="PI\d+"': 'ProductInstance="{PRODUCT_INSTANCE}"',
            r'Components="[^"]*"': 'Components="{COMPONENTS}"'
        },
        'Function': {
            r'id="EF\d+"': 'id="{FUNCTION_ID}"',
            r'Components="[^"]*"': 'Components="{COMPONENTS}"'
        },
        'Terminal': {
            r'id="ECT\d+"': 'id="{TERMINAL_ID}"'
        },
        'Equipment': {
            r'id="EQ\d+"': 'id="{EQUIPMENT_ID}"',
            r'ProductPacks="[^"]*"': 'ProductPacks="{PRODUCT_PACKS}"',
            r'Devices="[^"]*"': 'Devices="{DEVICES}"',
            r'Functions="[^"]*"': 'Functions="{FUNCTIONS}"'
        },
        'Pack': {
            r'id="PK\d+"': 'id="{PACK_ID}"'
        },
        'Instance': {
            r'id="PI\d+"': 'id="{INSTANCE_ID}"'
        },
        'Company': {
            r'id="CC\d+"': 'id="{COMPANY_ID}"'
        },
        'Person': {
            r'id="CP\d+"': 'id="{PERSON_ID}"',
            r'<Company id="CC\d+"': '<Company id="{COMPANY_ID}"'
        }
    }
    
    if element_type in placeholder_mappings:
        for pattern, replacement in placeholder_mappings[element_type].items():
            xml_content = re.sub(pattern, replacement, xml_content)
    
    return xml_content

if __name__ == "__main__":
    create_exact_templates()

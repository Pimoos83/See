#!/usr/bin/env python3
"""
Générateur de templates Caneco - Version corrigée
Crée des templates pratiques pour tous les patterns
"""

import xml.etree.ElementTree as ET
import re
from collections import defaultdict, Counter

def create_all_templates():
    """Crée tous les templates nécessaires"""
    
    print("=== CRÉATION TEMPLATES CANECO COMPLETS ===")
    
    # Charger XML
    with open('attached_assets/Caneco BT _1754486408913.xml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    root = ET.fromstring(content)
    
    templates_created = []
    
    # 1. Templates EDxxxxx (Device)
    templates_created.extend(create_device_templates(root))
    
    # 2. Templates EFxxxxx (Function)  
    templates_created.extend(create_function_templates(root))
    
    # 3. Templates PKxxxxx (Pack)
    templates_created.extend(create_pack_templates(root))
    
    # 4. Templates PIxxxxx (Instance)
    templates_created.extend(create_instance_templates(root))
    
    # 5. Templates EQxxxxx (Equipment)
    templates_created.extend(create_equipment_templates(root))
    
    # 6. Templates ECTxxxxx (Terminal)
    templates_created.extend(create_terminal_templates(root))
    
    # 7. Templates Contacts (Company, Person)
    templates_created.extend(create_contact_templates(root))
    
    print(f"\n=== RÉSUMÉ FINAL ===")
    print(f"Templates créés: {len(templates_created)}")
    for template in templates_created:
        print(f"  {template['filename']}: {template['count']} éléments ({template['type']})")
    
    return templates_created

def create_device_templates(root):
    """Crée templates pour Device (EDxxxxx)"""
    devices = [elem for elem in root.iter() if elem.get('id', '').startswith('ED')]
    
    # Grouper par type de device
    device_groups = defaultdict(list)
    for device in devices:
        # Analyser le type de device par ses enfants
        device_type = 'Generic'
        for child in device:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if 'Transformer' in child_tag:
                device_type = 'Transformer'
                break
            elif 'Switch' in child_tag:
                device_type = 'Switch'
                break
            elif 'Load' in child_tag:
                device_type = 'Load'
                break
        
        device_groups[device_type].append(device)
    
    templates = []
    for i, (device_type, group_devices) in enumerate(device_groups.items()):
        if group_devices:
            template = create_template(group_devices[0], f"Template_EDxxxxx_{chr(65+i)}.xml")
            template['type'] = f"Device_{device_type}"
            template['count'] = len(group_devices)
            templates.append(template)
    
    return templates

def create_function_templates(root):
    """Crée templates pour Function (EFxxxxx)"""
    functions = [elem for elem in root.iter() if elem.get('id', '').startswith('EF')]
    
    # Grouper par type de function
    function_groups = defaultdict(list)
    for func in functions:
        # Analyser le type par les enfants
        func_type = 'Generic'
        for child in func:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if 'Source' in child_tag:
                func_type = 'Source'
                break
            elif 'Switch' in child_tag:
                func_type = 'Switch'
                break
            elif 'Load' in child_tag:
                func_type = 'Load'
                break
            elif 'Transmission' in child_tag:
                func_type = 'Transmission'
                break
            elif 'Distribution' in child_tag:
                func_type = 'Distribution'
                break
        
        function_groups[func_type].append(func)
    
    templates = []
    for i, (func_type, group_functions) in enumerate(function_groups.items()):
        if group_functions:
            template = create_template(group_functions[0], f"Template_EFxxxxx_{chr(65+i)}.xml")
            template['type'] = f"Function_{func_type}"
            template['count'] = len(group_functions)
            templates.append(template)
    
    return templates

def create_pack_templates(root):
    """Crée templates pour Pack (PKxxxxx) - Version simplifiée"""
    packs = [elem for elem in root.iter() if elem.get('id', '').startswith('PK')]
    
    if not packs:
        return []
    
    # Analyser les premiers packs pour identifier patterns principaux
    pack_types = defaultdict(list)
    
    for pack in packs[:50]:  # Limiter l'analyse aux 50 premiers
        # Identifier par le contenu Product
        pack_type = 'Generic'
        product_elem = pack.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Product')
        if product_elem:
            for child in product_elem:
                child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if 'Transformer' in child_tag:
                    pack_type = 'Transformer'
                    break
                elif 'CircuitBreaker' in child_tag:
                    pack_type = 'CircuitBreaker'
                    break
                elif 'Cable' in child_tag:
                    pack_type = 'Cable'
                    break
        
        pack_types[pack_type].append(pack)
    
    # Créer seulement les 3 principaux templates
    templates = []
    main_types = sorted(pack_types.keys(), key=lambda x: len(pack_types[x]), reverse=True)[:3]
    
    for i, pack_type in enumerate(main_types):
        if pack_types[pack_type]:
            template = create_template(pack_types[pack_type][0], f"Template_PKxxxxx_{chr(65+i)}.xml")
            template['type'] = f"Pack_{pack_type}"
            template['count'] = len([p for p in packs if get_pack_type(p) == pack_type])
            templates.append(template)
    
    return templates

def get_pack_type(pack):
    """Détermine le type d'un Pack"""
    product_elem = pack.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Product')
    if product_elem:
        for child in product_elem:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if 'Transformer' in child_tag:
                return 'Transformer'
            elif 'CircuitBreaker' in child_tag:
                return 'CircuitBreaker'
            elif 'Cable' in child_tag:
                return 'Cable'
    return 'Generic'

def create_instance_templates(root):
    """Crée templates pour Instance (PIxxxxx)"""
    instances = [elem for elem in root.iter() if elem.get('id', '').startswith('PI')]
    
    if instances:
        template = create_template(instances[0], "Template_PIxxxxx_A.xml")
        template['type'] = "Instance_Generic"
        template['count'] = len(instances)
        return [template]
    
    return []

def create_equipment_templates(root):
    """Crée templates pour Equipment (EQxxxxx)"""
    equipments = [elem for elem in root.iter() if elem.get('id', '').startswith('EQ')]
    
    if equipments:
        template = create_template(equipments[0], "Template_EQxxxxx_A.xml")
        template['type'] = "Equipment_Main"
        template['count'] = len(equipments)
        return [template]
    
    return []

def create_terminal_templates(root):
    """Crée templates pour Terminal (ECTxxxxx)"""
    terminals = [elem for elem in root.iter() if elem.get('id', '').startswith('ECT')]
    
    # Grouper par polarité
    terminal_groups = defaultdict(list)
    for terminal in terminals:
        polarity_elem = terminal.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Polarity')
        polarity = polarity_elem.text if polarity_elem is not None else 'unknown'
        terminal_groups[polarity].append(terminal)
    
    templates = []
    for i, (polarity, group_terminals) in enumerate(terminal_groups.items()):
        if group_terminals and i < 5:  # Limiter à 5 variations principales
            template = create_template(group_terminals[0], f"Template_ECTxxxxx_{chr(65+i)}.xml")
            template['type'] = f"Terminal_{polarity.replace('+', '_')}"
            template['count'] = len(group_terminals)
            templates.append(template)
    
    return templates

def create_contact_templates(root):
    """Crée templates pour Contacts (Company, Person)"""
    templates = []
    
    # Template Company
    companies = [elem for elem in root.iter() if elem.get('id', '').startswith('CC')]
    if companies:
        template = create_template(companies[0], "Template_CCxxxxx_A.xml")
        template['type'] = "Company"
        template['count'] = len(companies)
        templates.append(template)
    
    # Template Person
    persons = [elem for elem in root.iter() if elem.get('id', '').startswith('CP')]
    if persons:
        template = create_template(persons[0], "Template_CPxxxxx_A.xml")
        template['type'] = "Person"
        template['count'] = len(persons)
        templates.append(template)
    
    return templates

def create_template(element, filename):
    """Crée un template à partir d'un élément"""
    # Convertir en XML string
    template_xml = ET.tostring(element, encoding='unicode')
    
    # Appliquer placeholders
    template_xml = apply_generic_placeholders(template_xml)
    
    # Sauvegarder
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(template_xml)
    
    return {
        'filename': filename,
        'type': 'Generic',
        'count': 1
    }

def apply_generic_placeholders(template_xml):
    """Applique des placeholders génériques"""
    
    # Mapping des placeholders courants
    placeholders = [
        (r'id="ED\d+"', 'id="{DEVICE_ID}"'),
        (r'id="EF\d+"', 'id="{FUNCTION_ID}"'),
        (r'id="PK\d+"', 'id="{PACK_ID}"'),
        (r'id="PI\d+"', 'id="{INSTANCE_ID}"'),
        (r'id="EQ\d+"', 'id="{EQUIPMENT_ID}"'),
        (r'id="ECT\d+"', 'id="{TERMINAL_ID}"'),
        (r'id="EC\d+"', 'id="{COMPONENT_ID}"'),
        (r'id="CC\d+"', 'id="{COMPANY_ID}"'),
        (r'id="CP\d+"', 'id="{PERSON_ID}"'),
        (r'ProductInstance="PI\d+"', 'ProductInstance="{PRODUCT_INSTANCE}"'),
        (r'Components="[^"]*"', 'Components="{COMPONENTS}"'),
        (r'Devices="[^"]*"', 'Devices="{DEVICES}"'),
        (r'Functions="[^"]*"', 'Functions="{FUNCTIONS}"'),
        (r'ProductPacks="[^"]*"', 'ProductPacks="{PRODUCT_PACKS}"'),
        (r'Descriptor="[^"]*"', 'Descriptor="{DESCRIPTOR}"')
    ]
    
    for old_pattern, new_pattern in placeholders:
        template_xml = re.sub(old_pattern, new_pattern, template_xml)
    
    return template_xml

if __name__ == "__main__":
    create_all_templates()
#!/usr/bin/env python3
"""
Analyseur de structure complète Caneco
Génère un rapport détaillé de tous les éléments
"""

import xml.etree.ElementTree as ET
import json

def generate_complete_structure_report():
    """Génère un rapport de structure complète"""
    
    # Charger XML
    with open('attached_assets/Caneco BT _1754486408913.xml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    root = ET.fromstring(content)
    
    structure_report = {
        'xml_stats': {
            'file_size': len(content),
            'total_elements': len(list(root.iter())),
            'elements_with_id': len([elem for elem in root.iter() if elem.get('id')]),
        },
        'sections': {},
        'id_patterns': {},
        'detailed_structure': []
    }
    
    # Analyser chaque section principale
    for section in root:
        section_name = section.tag.split('}')[-1] if '}' in section.tag else section.tag
        
        # Compter éléments dans cette section
        all_elements = list(section.iter())
        elements_with_ids = [elem for elem in all_elements if elem.get('id')]
        
        section_info = {
            'total_elements': len(all_elements),
            'elements_with_ids': len(elements_with_ids),
            'direct_children': len(list(section)),
            'id_patterns': {},
            'element_types': {}
        }
        
        # Analyser patterns d'ID dans cette section
        for elem in elements_with_ids:
            elem_id = elem.get('id')
            pattern = identify_pattern(elem_id)
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            
            if pattern not in section_info['id_patterns']:
                section_info['id_patterns'][pattern] = []
            section_info['id_patterns'][pattern].append(elem_id)
            
            if tag not in section_info['element_types']:
                section_info['element_types'][tag] = 0
            section_info['element_types'][tag] += 1
        
        structure_report['sections'][section_name] = section_info
    
    # Analyser tous les patterns globalement
    all_elements_with_ids = [elem for elem in root.iter() if elem.get('id')]
    
    for elem in all_elements_with_ids:
        elem_id = elem.get('id')
        pattern = identify_pattern(elem_id)
        
        if pattern not in structure_report['id_patterns']:
            structure_report['id_patterns'][pattern] = {
                'count': 0,
                'examples': [],
                'element_types': set(),
                'sections': set()
            }
        
        structure_report['id_patterns'][pattern]['count'] += 1
        if len(structure_report['id_patterns'][pattern]['examples']) < 10:
            structure_report['id_patterns'][pattern]['examples'].append(elem_id)
        
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        structure_report['id_patterns'][pattern]['element_types'].add(tag)
        
        # Trouver section parent
        parent_section = find_parent_section(elem, root)
        if parent_section:
            structure_report['id_patterns'][pattern]['sections'].add(parent_section)
    
    # Convertir sets en listes pour JSON
    for pattern_info in structure_report['id_patterns'].values():
        pattern_info['element_types'] = list(pattern_info['element_types'])
        pattern_info['sections'] = list(pattern_info['sections'])
    
    # Sauvegarder
    with open('caneco_complete_structure.json', 'w', encoding='utf-8') as f:
        json.dump(structure_report, f, indent=2, ensure_ascii=False)
    
    # Générer rapport texte
    generate_text_report(structure_report)
    
    return structure_report

def identify_pattern(element_id):
    """Identifie le pattern d'un ID"""
    import re
    
    patterns = [
        (r'^PG\d{5}$', 'PGxxxxx'),
        (r'^PI\d{5}$', 'PIxxxxx'), 
        (r'^PK\d{5}$', 'PKxxxxx'),
        (r'^EC\d{5}$', 'ECxxxxx'),
        (r'^ECT\d{5}$', 'ECTxxxxx'),
        (r'^ED\d{5}$', 'EDxxxxx'),
        (r'^EF\d{5}$', 'EFxxxxx'),
        (r'^CC\d{5}$', 'CCxxxxx'),
        (r'^CP\d{5}$', 'CPxxxxx'),
        (r'^EQ\d{5}$', 'EQxxxxx')
    ]
    
    for regex, pattern in patterns:
        if re.match(regex, element_id):
            return pattern
    
    return f'OTHER_{element_id[:2]}'

def find_parent_section(element, root):
    """Trouve la section parent d'un élément"""
    for section in root:
        if element in section.iter():
            return section.tag.split('}')[-1] if '}' in section.tag else section.tag
    return None

def generate_text_report(structure_report):
    """Génère un rapport texte lisible"""
    
    report_lines = []
    report_lines.append("RAPPORT DE STRUCTURE CANECO BT.XML")
    report_lines.append("=" * 50)
    
    # Statistiques globales
    stats = structure_report['xml_stats']
    report_lines.append(f"\\nSTATISTIQUES GLOBALES:")
    report_lines.append(f"  Taille fichier: {stats['file_size']:,} caractères")
    report_lines.append(f"  Total éléments: {stats['total_elements']:,}")
    report_lines.append(f"  Éléments avec ID: {stats['elements_with_id']:,}")
    
    # Patterns d'ID
    report_lines.append(f"\\nPATTERNS D'ID:")
    for pattern, info in sorted(structure_report['id_patterns'].items(), key=lambda x: x[1]['count'], reverse=True):
        report_lines.append(f"\\n  {pattern}: {info['count']} éléments")
        report_lines.append(f"    Types: {', '.join(info['element_types'])}")
        report_lines.append(f"    Sections: {', '.join(info['sections'])}")
        report_lines.append(f"    Exemples: {', '.join(info['examples'][:5])}")
    
    # Sections
    report_lines.append(f"\\nSECTIONS:")
    for section, info in structure_report['sections'].items():
        report_lines.append(f"\\n  {section}:")
        report_lines.append(f"    Total éléments: {info['total_elements']}")
        report_lines.append(f"    Éléments avec ID: {info['elements_with_ids']}")
        report_lines.append(f"    Enfants directs: {info['direct_children']}")
        
        if info['id_patterns']:
            report_lines.append(f"    Patterns ID:")
            for pattern, ids in info['id_patterns'].items():
                report_lines.append(f"      {pattern}: {len(ids)}")
    
    # Sauvegarder rapport
    with open('caneco_structure_report.txt', 'w', encoding='utf-8') as f:
        f.write('\\n'.join(report_lines))

if __name__ == "__main__":
    structure = generate_complete_structure_report()
    print("✓ Analyse complète terminée")
    print("✓ Fichiers générés:")
    print("  - caneco_complete_structure.json")  
    print("  - caneco_structure_report.txt")
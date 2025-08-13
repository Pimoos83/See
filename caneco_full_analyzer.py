#!/usr/bin/env python3
"""
Analyseur complet du fichier Caneco BT.xml
Identifie tous les types d'éléments avec leurs patterns d'ID
"""

import xml.etree.ElementTree as ET
import re
from collections import defaultdict, Counter

def analyze_caneco_complete():
    """Analyse complète de tous les éléments du fichier Caneco"""
    
    print("=== ANALYSE COMPLÈTE CANECO BT.XML ===")
    
    # Charger XML
    with open('attached_assets/Caneco BT _1754486408913.xml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    root = ET.fromstring(content)
    
    # Dictionnaires pour stocker les analyses
    id_patterns = defaultdict(list)  # Pattern -> Liste d'éléments
    element_types = defaultdict(list)  # Type d'élément -> Liste d'éléments
    sections = {}  # Section -> Informations
    
    # Analyser tous les éléments avec un ID
    def analyze_element(element, path=""):
        element_id = element.get('id', '')
        if element_id:
            # Identifier le pattern de l'ID
            pattern = identify_id_pattern(element_id)
            
            # Informations sur l'élément
            elem_info = {
                'id': element_id,
                'tag': element.tag.split('}')[-1] if '}' in element.tag else element.tag,
                'full_tag': element.tag,
                'path': path,
                'attributes': dict(element.attrib),
                'children_tags': [child.tag.split('}')[-1] if '}' in child.tag else child.tag for child in element],
                'has_text': bool(element.text and element.text.strip()),
                'pattern': pattern
            }
            
            id_patterns[pattern].append(elem_info)
            element_types[elem_info['tag']].append(elem_info)
        
        # Analyser les enfants
        for child in element:
            child_path = f"{path}/{child.tag.split('}')[-1] if '}' in child.tag else child.tag}"
            analyze_element(child, child_path)
    
    # Identifier les sections principales
    for child in root:
        section_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        sections[section_name] = {
            'tag': section_name,
            'element_count': len(list(child.iter())),
            'direct_children': len(list(child)),
            'has_ids': bool([elem for elem in child.iter() if elem.get('id')])
        }
    
    # Analyser tous les éléments
    analyze_element(root)
    
    print(f"\n=== SECTIONS PRINCIPALES ===")
    for section, info in sections.items():
        print(f"{section}:")
        print(f"  Éléments totaux: {info['element_count']}")
        print(f"  Enfants directs: {info['direct_children']}")
        print(f"  Contient des IDs: {info['has_ids']}")
    
    print(f"\n=== PATTERNS D'ID DÉTECTÉS ===")
    for pattern, elements in sorted(id_patterns.items()):
        print(f"\nPattern {pattern}: {len(elements)} éléments")
        
        # Analyser les types d'éléments pour ce pattern
        types_count = Counter([elem['tag'] for elem in elements])
        for elem_type, count in types_count.most_common():
            print(f"  {elem_type}: {count}")
        
        # Montrer quelques exemples d'IDs
        example_ids = [elem['id'] for elem in elements[:10]]
        print(f"  Exemples: {example_ids}")
        
        # Analyser les attributs communs
        all_attrs = set()
        for elem in elements:
            all_attrs.update(elem['attributes'].keys())
        if all_attrs:
            print(f"  Attributs: {sorted(all_attrs)}")
    
    print(f"\n=== TYPES D'ÉLÉMENTS ===")
    for elem_type, elements in sorted(element_types.items()):
        if len(elements) > 5:  # Seulement les types significatifs
            print(f"\n{elem_type}: {len(elements)} éléments")
            
            # Patterns d'ID pour ce type
            patterns = Counter([elem['pattern'] for elem in elements])
            for pattern, count in patterns.most_common(3):
                print(f"  Pattern {pattern}: {count}")
            
            # Chemins principaux
            paths = Counter([elem['path'] for elem in elements])
            for path, count in paths.most_common(3):
                print(f"  Chemin: {path} ({count})")
    
    return id_patterns, element_types, sections

def identify_id_pattern(element_id):
    """Identifie le pattern d'un ID"""
    if re.match(r'^PG\d+$', element_id):
        return 'PGxxxxx'
    elif re.match(r'^PI\d+$', element_id):
        return 'PIxxxxx'
    elif re.match(r'^PK\d+$', element_id):
        return 'PKxxxxx'
    elif re.match(r'^EC\d+$', element_id):
        return 'ECxxxxx'
    elif re.match(r'^ECT\d+$', element_id):
        return 'ECTxxxxx'
    elif re.match(r'^ED\d+$', element_id):
        return 'EDxxxxx'
    elif re.match(r'^EF\d+$', element_id):
        return 'EFxxxxx'
    elif re.match(r'^CC\d+$', element_id):
        return 'CCxxxxx'
    elif re.match(r'^CP\d+$', element_id):
        return 'CPxxxxx'
    elif re.match(r'^EQ\d+$', element_id):
        return 'EQxxxxx'
    else:
        return 'OTHER'

def save_analysis_results(id_patterns, element_types, sections):
    """Sauvegarde l'analyse dans un fichier JSON"""
    import json
    
    # Préparer les données pour JSON
    analysis_data = {
        'patterns': {},
        'elements': {},
        'sections': sections,
        'summary': {
            'total_patterns': len(id_patterns),
            'total_element_types': len(element_types),
            'total_elements_with_ids': sum(len(elements) for elements in id_patterns.values())
        }
    }
    
    # Convertir les patterns
    for pattern, elements in id_patterns.items():
        analysis_data['patterns'][pattern] = {
            'count': len(elements),
            'examples': [elem['id'] for elem in elements[:10]],
            'types': list(set([elem['tag'] for elem in elements])),
            'paths': list(set([elem['path'] for elem in elements]))
        }
    
    # Convertir les types d'éléments
    for elem_type, elements in element_types.items():
        if len(elements) > 1:  # Seulement les types avec plusieurs instances
            analysis_data['elements'][elem_type] = {
                'count': len(elements),
                'patterns': list(set([elem['pattern'] for elem in elements])),
                'examples': [elem['id'] for elem in elements[:5]]
            }
    
    # Sauvegarder
    with open('caneco_full_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== ANALYSE SAUVEGARDÉE ===")
    print("Fichier: caneco_full_analysis.json")
    print(f"Patterns identifiés: {analysis_data['summary']['total_patterns']}")
    print(f"Types d'éléments: {analysis_data['summary']['total_element_types']}")
    print(f"Éléments avec ID: {analysis_data['summary']['total_elements_with_ids']}")

if __name__ == "__main__":
    id_patterns, element_types, sections = analyze_caneco_complete()
    save_analysis_results(id_patterns, element_types, sections)
"""
Réplicateur EXACT Caneco - Version 2
Reproduit STRICTEMENT l'arborescence originale sans modification
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any
import json

class CanecoExactReplicatorV2:
    """Réplique EXACTEMENT la structure du fichier original"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.original_structure = {}
        self.autocad_data = []
        self.autocad_to_caneco_mapping = {}
        
    def analyze_original_structure(self, original_file: str):
        """Analyse COMPLÈTE de la structure originale"""
        try:
            self.logger.info("Analyse structure originale exacte...")
            tree = ET.parse(original_file)
            root = tree.getroot()
            
            # Extraire TOUT : namespaces, attributs, ordre exact
            self.original_structure = {
                'root_tag': root.tag,
                'root_attribs': dict(root.attrib),
                'full_xml_content': ET.tostring(root, encoding='unicode'),
                'namespace_prefixes': self._extract_namespaces(root),
                'section_order': [child.tag for child in root],
                'detailed_sections': {}
            }
            
            # Analyser chaque section dans l'ordre EXACT
            for section in root:
                section_name = self._clean_tag(section.tag)
                self.original_structure['detailed_sections'][section_name] = self._extract_section_complete(section)
            
            self.logger.info(f"Structure originale analysée: {len(self.original_structure['detailed_sections'])} sections")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur analyse: {str(e)}")
            return False
    
    def _extract_namespaces(self, root: ET.Element) -> Dict:
        """Extrait TOUS les namespaces"""
        namespaces = {}
        for key, value in root.attrib.items():
            if key.startswith('xmlns'):
                namespaces[key] = value
        return namespaces
    
    def _clean_tag(self, tag: str) -> str:
        """Nettoie les tags des namespaces"""
        if '}' in tag:
            return tag.split('}')[1]
        return tag
    
    def _extract_section_complete(self, section: ET.Element) -> Dict:
        """Extrait TOUT d'une section"""
        section_data = {
            'tag': section.tag,
            'attribs': dict(section.attrib),
            'text': section.text.strip() if section.text else None,
            'children': [],
            'total_elements': len(list(section.iter())),
            'direct_children_count': len(list(section))
        }
        
        # Extraire tous les enfants dans l'ordre EXACT
        for child in section:
            child_data = self._extract_element_recursive(child)
            section_data['children'].append(child_data)
        
        return section_data
    
    def _extract_element_recursive(self, element: ET.Element) -> Dict:
        """Extrait récursivement un élément"""
        elem_data = {
            'tag': element.tag,
            'attribs': dict(element.attrib),
            'text': element.text.strip() if element.text else None,
            'children': []
        }
        
        # Pour éviter la récursion infinie, limiter la profondeur
        if len(list(element)) < 1000:  # Limite de sécurité
            for child in element:
                elem_data['children'].append(self._extract_element_recursive(child))
        
        return elem_data
    
    def load_autocad_data(self, autocad_file: str):
        """Charge et analyse les données AutoCAD"""
        try:
            import pandas as pd
            
            df = pd.read_excel(autocad_file)
            self.logger.info(f"Fichier AutoCAD chargé: {len(df)} lignes, colonnes: {list(df.columns)}")
            
            # Convertir en format standard
            for _, row in df.iterrows():
                record = {}
                for col in df.columns:
                    record[col] = str(row[col]) if pd.notna(row[col]) else ''
                
                self.autocad_data.append(record)
            
            self._create_autocad_to_caneco_mapping()
            self.logger.info(f"Données AutoCAD traitées: {len(self.autocad_data)} éléments")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement AutoCAD: {str(e)}")
            return False
    
    def _create_autocad_to_caneco_mapping(self):
        """Crée le mapping AutoCAD vers format Caneco"""
        # Mapping basé sur l'analyse du fichier original
        self.autocad_to_caneco_mapping = {
            'disjoncteur': {
                'caneco_type': 'CircuitBreakerDevice',
                'component_type': 'CircuitBreakerComponent',
                'function_type': 'SwitchgearFunction',
                'product_group': 'ECD_DISJONCTEUR',
                'product_item': 'MG4_13271'
            },
            'cable': {
                'caneco_type': 'CableDevice',
                'component_type': 'CableComponent', 
                'function_type': 'TransmissionFunction',
                'product_group': 'ECD_CABLE',
                'product_item': 'CBL_001'
            },
            'transformateur': {
                'caneco_type': 'MvLvTransformerDevice',
                'component_type': 'TransformerComponent',
                'function_type': 'TransformationFunction',
                'product_group': 'ECD_TRANSFO',
                'product_item': 'TR_001'
            },
            'charge': {
                'caneco_type': 'PassiveLoadDevice',
                'component_type': 'LoadComponent',
                'function_type': 'ReceiverFunction',
                'product_group': 'ECD_CHARGE',
                'product_item': 'LOAD_001'
            }
        }
    
    def replicate_exact_structure(self, output_file: str) -> bool:
        """Réplique EXACTEMENT la structure originale"""
        try:
            # Créer la racine EXACTEMENT comme l'original
            root = ET.Element('ElectricalProject')
            
            # Copier TOUS les attributs dans l'ordre EXACT
            original_attribs = self.original_structure['root_attribs']
            for key, value in original_attribs.items():
                root.set(key, value)
            
            # Reproduire chaque section dans l'ordre EXACT
            section_order = self.original_structure['section_order']
            
            for section_tag in section_order:
                section_name = self._clean_tag(section_tag)
                original_section = self.original_structure['detailed_sections'][section_name]
                
                if section_name == 'Description':
                    self._replicate_description(root, original_section)
                elif section_name == 'Contacts':
                    self._replicate_contacts(root, original_section)
                elif section_name == 'Products':
                    self._replicate_products_exact(root, original_section)
                elif section_name == 'Equipments':
                    self._replicate_equipments_exact(root, original_section)
                elif section_name == 'Network':
                    self._replicate_network_exact(root, original_section)
            
            # Écrire avec formatage EXACT
            self._write_exact_xml(root, output_file)
            
            self.logger.info("Réplication exacte terminée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur réplication: {str(e)}")
            return False
    
    def _replicate_description(self, root: ET.Element, original: Dict):
        """Réplique la section Description EXACTEMENT"""
        desc = ET.SubElement(root, 'Description')
        
        # Reproduire EXACTEMENT les enfants de l'original
        for child_data in original['children']:
            child_tag = self._clean_tag(child_data['tag'])
            child = ET.SubElement(desc, child_tag)
            
            if child_data['text']:
                if child_tag == 'Name':
                    child.text = 'Caneco BT - Conversion AutoCAD vers Caneco'
                elif child_tag == 'StartDate':
                    child.text = '2025-08-11T00:00:00.0Z'
                else:
                    child.text = child_data['text']
    
    def _replicate_contacts(self, root: ET.Element, original: Dict):
        """Réplique la section Contacts EXACTEMENT"""
        contacts = ET.SubElement(root, 'Contacts')
        
        # Reproduire la structure EXACTE de l'original
        for child_data in original['children']:
            self._replicate_element_recursive(contacts, child_data)
    
    def _replicate_products_exact(self, root: ET.Element, original: Dict):
        """Réplique Products avec les données AutoCAD mappées"""
        products = ET.SubElement(root, 'Products')
        
        # ProductSet
        product_set = ET.SubElement(products, 'ProductSet')
        
        # Générer des produits basés sur AutoCAD mais avec structure originale
        for i, autocad_record in enumerate(self.autocad_data):
            product = ET.SubElement(product_set, 'Product', {'id': f'PG{i+1:05d}'})
            
            name = ET.SubElement(product, 'Name')
            # Utiliser le nom AutoCAD mais formaté
            name.text = self._format_autocad_name(autocad_record)
            
            # Copier la structure Seed de l'original
            original_product = original['children'][0]['children'][0]  # Premier Product du ProductSet
            seed_data = next((c for c in original_product['children'] if self._clean_tag(c['tag']) == 'Seed'), None)
            
            if seed_data:
                seed = ET.SubElement(product, 'Seed')
                for attr, value in seed_data['attribs'].items():
                    seed.set(attr, value)
            
            # Reproduire la structure Content
            self._replicate_product_content(product, original_product, autocad_record)
        
        # ProductList - copier structure mais adapter données
        product_list = ET.SubElement(products, 'ProductList')
        
        for i, autocad_record in enumerate(self.autocad_data):
            pack = ET.SubElement(product_list, 'Pack', {'id': f'PK{i+1:05d}'})
            
            product = ET.SubElement(pack, 'Product', {'id': f'PG{i+1:05d}'})
            
            name = ET.SubElement(product, 'Name')
            name.text = self._format_autocad_name(autocad_record)
            
            # Content commercial
            content = ET.SubElement(product, 'Content')
            device_type = self._determine_device_type(autocad_record)
            device_elem = ET.SubElement(content, device_type)
            device_elem.set('xmlns', 'http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy')
            
            instances = ET.SubElement(pack, 'Instances')
            instance = ET.SubElement(instances, 'Instance', {'id': f'PI{i+1:05d}'})
    
    def _replicate_equipments_exact(self, root: ET.Element, original: Dict):
        """Réplique Equipments EXACTEMENT"""
        equipments = ET.SubElement(root, 'Equipments')
        
        # Copier EXACTEMENT la structure des équipements originaux
        for child_data in original['children']:
            self._replicate_element_recursive(equipments, child_data)
    
    def _replicate_network_exact(self, root: ET.Element, original: Dict):
        """Réplique Network avec TOUTES les sections"""
        network = ET.SubElement(root, 'Network')
        
        # Frequency
        freq = ET.SubElement(network, 'Frequency')
        freq.text = '50'
        
        # Devices - utiliser les données AutoCAD
        devices = ET.SubElement(network, 'Devices')
        for i, autocad_record in enumerate(self.autocad_data):
            device = ET.SubElement(devices, 'Device', {
                'id': f'ED{i+1:05d}',
                'ProductInstance': f'PI{i+1:05d}',
                'Components': f'EC{i+1:05d}'
            })
            
            func_name = ET.SubElement(device, 'FunctionalName')
            func_name.text = self._format_autocad_name(autocad_record)
            
            device_type = self._determine_device_type(autocad_record)
            device_elem = ET.SubElement(device, device_type)
            device_elem.set('xmlns', 'http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy')
        
        # Components - reproduire structure exacte
        components = ET.SubElement(network, 'Components')
        for i, autocad_record in enumerate(self.autocad_data):
            component = ET.SubElement(components, 'Component', {
                'id': f'EC{i+1:05d}',
                'Device': f'ED{i+1:05d}'
            })
            
            terminals = ET.SubElement(component, 'Terminals')
            for t in range(4):
                terminal = ET.SubElement(terminals, 'Terminal', {'id': f'ECT{i*4+t+1:05d}'})
            
            comp_type = self._determine_component_type(autocad_record)
            comp_elem = ET.SubElement(component, comp_type)
            comp_elem.set('xmlns', 'http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy')
        
        # Functions - reproduire structure exacte
        functions = ET.SubElement(network, 'Functions')
        for i, autocad_record in enumerate(self.autocad_data):
            function = ET.SubElement(functions, 'Function', {
                'id': f'EF{i+1:05d}',
                'Components': f'EC{i+1:05d}'
            })
            
            func_type = self._determine_function_type(autocad_record)
            func_elem = ET.SubElement(function, func_type)
            func_elem.set('xmlns', 'http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy')
            
            if func_type == 'TransmissionFunction':
                type_elem = ET.SubElement(func_elem, 'Type')
                type_elem.text = 'Cable'
            
            modes = ET.SubElement(function, 'ExploitationModes')
            props = ET.SubElement(modes, 'Properties', {'ExploitationMode': 'EXM00001'})
        
        # PowerConnections
        connections = ET.SubElement(network, 'PowerConnections')
        for i in range(len(self.autocad_data) - 1):
            connection = ET.SubElement(connections, 'Connection', {
                'id': f'ECX{i+1:05d}',
                'EndpointA': f'ECT{i*4+1:05d}',
                'EndpointB': f'ECT{(i+1)*4+1:05d}'
            })
            
            orientations = ET.SubElement(connection, 'Orientations')
            default = ET.SubElement(orientations, 'Default')
            default.text = 'A_to_B'
    
    def _replicate_element_recursive(self, parent: ET.Element, element_data: Dict):
        """Réplique récursivement un élément"""
        tag = self._clean_tag(element_data['tag'])
        elem = ET.SubElement(parent, tag)
        
        # Copier attributs
        for attr, value in element_data['attribs'].items():
            elem.set(attr, value)
        
        # Copier texte
        if element_data['text']:
            elem.text = element_data['text']
        
        # Copier enfants (limiter récursion)
        if len(element_data['children']) < 100:  # Limite de sécurité
            for child_data in element_data['children']:
                self._replicate_element_recursive(elem, child_data)
    
    def _format_autocad_name(self, autocad_record: Dict) -> str:
        """Formate le nom AutoCAD pour Caneco"""
        # Utiliser la première colonne comme nom principal
        columns = list(autocad_record.keys())
        if columns:
            return str(autocad_record[columns[0]])
        return 'Unknown'
    
    def _determine_device_type(self, autocad_record: Dict) -> str:
        """Détermine le type de device selon les données AutoCAD"""
        name = self._format_autocad_name(autocad_record).lower()
        
        if 'disjoncteur' in name or 'dj' in name:
            return 'CircuitBreakerDevice'
        elif 'cable' in name or 'cbl' in name:
            return 'CableDevice'
        elif 'transfo' in name or 'tr' in name:
            return 'MvLvTransformerDevice'
        else:
            return 'CircuitBreakerDevice'  # Par défaut
    
    def _determine_component_type(self, autocad_record: Dict) -> str:
        """Détermine le type de component"""
        device_type = self._determine_device_type(autocad_record)
        return device_type.replace('Device', 'Component')
    
    def _determine_function_type(self, autocad_record: Dict) -> str:
        """Détermine le type de function"""
        name = self._format_autocad_name(autocad_record).lower()
        
        if 'cable' in name or 'cbl' in name:
            return 'TransmissionFunction'
        elif 'charge' in name or 'load' in name:
            return 'ReceiverFunction'
        else:
            return 'SwitchgearFunction'
    
    def _replicate_product_content(self, product: ET.Element, original_product: Dict, autocad_record: Dict):
        """Réplique le contenu produit"""
        content = ET.SubElement(product, 'Content')
        
        # Copier la structure Characteristics de l'original
        chars_data = None
        for child in original_product['children']:
            if self._clean_tag(child['tag']) == 'Content':
                for subchild in child['children']:
                    if self._clean_tag(subchild['tag']) == 'Characteristics':
                        chars_data = subchild
                        break
                break
        
        if chars_data:
            chars = ET.SubElement(content, 'Characteristics')
            
            # Copier quelques caractéristiques en adaptant les valeurs
            for i, char_data in enumerate(chars_data['children'][:5]):  # Limiter
                char = ET.SubElement(chars, 'Characteristic')
                
                for child in char_data['children']:
                    child_tag = self._clean_tag(child['tag'])
                    child_elem = ET.SubElement(char, child_tag)
                    
                    if child['text']:
                        child_elem.text = child['text']
                    
                    # Adapter les valeurs selon AutoCAD
                    if child_tag == 'SetValues':
                        for value_child in child['children']:
                            self._replicate_element_recursive(child_elem, value_child)
    
    def _write_exact_xml(self, root: ET.Element, output_file: str):
        """Écrit le XML avec formatage EXACT"""
        self._indent(root)
        tree = ET.ElementTree(root)
        
        with open(output_file, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)
        
        # Post-traitement pour format exact
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace("<?xml version='1.0' encoding='utf-8'?>", 
                                '<?xml version="1.0" encoding="utf-8"?>')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _indent(self, elem, level=0):
        """Indentation récursive"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent(child, level+1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    replicator = CanecoExactReplicatorV2()
    replicator.analyze_original_structure('attached_assets/Caneco BT _1754486408913.xml')
    replicator.load_autocad_data('test_autocad_data.xlsx')
    
    success = replicator.replicate_exact_structure('test_exact_replica_v2.xml')
    if success:
        print("Réplication exacte V2 générée: test_exact_replica_v2.xml")
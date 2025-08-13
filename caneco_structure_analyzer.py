#!/usr/bin/env python3
"""
Analyseur de structure Caneco - Extrait templates et patterns
"""

import xml.etree.ElementTree as ET
import json
import logging
from typing import Dict, List, Any
import re

class CanecoStructureAnalyzer:
    """Analyse la structure exacte du XML Caneco original"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.original_tree = None
        self.structure = {}
        self.templates = {}
        self.patterns = {}
    
    def analyze_original_xml(self, xml_path: str) -> bool:
        """Analyse complète du XML original"""
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.original_tree = ET.fromstring(content)
            
            # Analyser chaque section
            self._analyze_header()
            self._analyze_products()
            self._analyze_equipments()
            self._analyze_network()
            self._analyze_patterns()
            
            self.logger.info("Analyse structure complète terminée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur analyse: {str(e)}")
            return False
    
    def _analyze_header(self):
        """Analyse header et namespaces"""
        self.structure['header'] = {
            'namespaces': dict(self.original_tree.attrib),
            'sections': [child.tag for child in self.original_tree]
        }
        
        # Extraire Description et Contacts
        desc = self.original_tree.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Description')
        if desc is not None:
            self.templates['description'] = ET.tostring(desc, encoding='unicode')
        
        contacts = self.original_tree.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Contacts')
        if contacts is not None:
            self.templates['contacts'] = ET.tostring(contacts, encoding='unicode')
    
    def _analyze_products(self):
        """Analyse section Products complète"""
        products = self.original_tree.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Products')
        if products is None:
            return
        
        # Analyser ProductSet
        product_set = products.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}ProductSet')
        if product_set is not None:
            product_elements = product_set.findall('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Product')
            self.structure['products'] = {
                'total_products': len(product_elements),
                'product_ids': [p.get('id') for p in product_elements]
            }
            
            # Extraire template de Product
            if product_elements:
                self.templates['product'] = ET.tostring(product_elements[0], encoding='unicode')
        
        # Analyser ProductList
        product_list = products.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}ProductList')
        if product_list is not None:
            packs = product_list.findall('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Pack')
            self.structure['product_list'] = {
                'total_packs': len(packs),
                'pack_ids': [p.get('id') for p in packs]
            }
            
            # Extraire template de Pack
            if packs:
                self.templates['pack'] = ET.tostring(packs[0], encoding='unicode')
    
    def _analyze_equipments(self):
        """Analyse section Equipments"""
        equipments = self.original_tree.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Equipments')
        if equipments is None:
            return
        
        # Equipment elements (structure principale)
        equipment_elements = equipments.findall('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Equipment')
        
        # Device elements (recherche directe dans Equipments)
        device_elements = []
        for child in equipments:
            if 'Device' in child.tag:
                device_elements.append(child)
        
        self.structure['equipments'] = {
            'total_equipments': len(equipment_elements),
            'total_devices': len(device_elements),
            'equipment_ids': [e.get('id') for e in equipment_elements if e.get('id')],
            'device_ids': [d.get('id') for d in device_elements if d.get('id')]
        }
        
        # Templates
        if equipment_elements:
            self.templates['equipment'] = ET.tostring(equipment_elements[0], encoding='unicode')
        if device_elements:
            self.templates['device'] = ET.tostring(device_elements[0], encoding='unicode')
        
        # Analyser contenu détaillé des Equipment
        self._analyze_equipment_details(equipment_elements)
    
    def _analyze_network(self):
        """Analyse section Network"""
        network = self.original_tree.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Network')
        if network is None:
            return
        
        function_elements = network.findall('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Function')
        
        self.structure['network'] = {
            'total_functions': len(function_elements),
            'function_ids': [f.get('id') for f in function_elements]
        }
        
        # Template Function
        if function_elements:
            self.templates['function'] = ET.tostring(function_elements[0], encoding='unicode')
    
    def _analyze_equipment_details(self, equipment_elements):
        """Analyse détaillée du contenu des Equipment"""
        equipment_details = []
        for eq in equipment_elements:
            eq_id = eq.get('id')
            
            # Analyser Commercial section
            commercial = eq.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Commercial')
            commercial_info = {}
            if commercial is not None:
                product_packs = commercial.get('ProductPacks', '')
                commercial_info = {
                    'product_packs': product_packs.split() if product_packs else [],
                    'product_pack_count': len(product_packs.split()) if product_packs else 0
                }
            
            # Analyser Electrical section
            electrical = eq.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Electrical')
            electrical_info = {}
            if electrical is not None:
                devices = electrical.get('Devices', '')
                functions = electrical.get('Functions', '')
                electrical_info = {
                    'devices': devices.split() if devices else [],
                    'functions': functions.split() if functions else [],
                    'device_count': len(devices.split()) if devices else 0,
                    'function_count': len(functions.split()) if functions else 0
                }
            
            equipment_details.append({
                'id': eq_id,
                'commercial': commercial_info,
                'electrical': electrical_info
            })
        
        self.structure['equipment_details'] = equipment_details
        
    def _analyze_patterns(self):
        """Analyse patterns dans Products et Equipment links"""
        # Analyser structure Product -> ProductPack -> Equipment -> Device
        patterns = {
            'product_to_pack_links': 0,
            'pack_to_equipment_links': 0,
            'equipment_to_device_links': 0,
            'device_sequence_analysis': []
        }
        
        # Analyser liens dans Equipment details
        if 'equipment_details' in self.structure:
            for eq in self.structure['equipment_details']:
                device_count = eq.get('electrical', {}).get('device_count', 0)
                pack_count = eq.get('commercial', {}).get('product_pack_count', 0)
                patterns['device_sequence_analysis'].append({
                    'equipment_id': eq['id'],
                    'devices': device_count,
                    'packs': pack_count
                })
        
        # Analyser les vrais Device types dans le XML
        self._analyze_device_types(patterns)
        
        self.patterns = patterns
        
    def _analyze_device_types(self, patterns):
        """Analyse les vrais types de devices dans le XML complet"""
        xml_content = ET.tostring(self.original_tree, encoding='unicode')
        
        # Compter occurrences
        circuit_breaker_count = xml_content.count('CircuitBreaker')
        cable_count = xml_content.count('Cable')  
        transformer_count = xml_content.count('Transformer')
        
        patterns.update({
            'circuit_breaker_occurrences': circuit_breaker_count,
            'cable_occurrences': cable_count,
            'transformer_occurrences': transformer_count
        })
        
        # Analyser séquences dans Products
        products_section = self.original_tree.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Products')
        if products_section is not None:
            products_xml = ET.tostring(products_section, encoding='unicode')
            patterns['products_analysis'] = {
                'contains_circuit_breakers': 'CircuitBreaker' in products_xml,
                'contains_cables': 'Cable' in products_xml,
                'contains_transformers': 'Transformer' in products_xml
            }
    
    def save_templates(self, output_dir: str = "."):
        """Sauvegarde tous les templates dans des fichiers séparés"""
        try:
            # Template principal
            main_template = f"""<?xml version="1.0" encoding="utf-8"?>
<ElectricalProject {' '.join([f'{k}="{v}"' for k, v in self.structure['header']['namespaces'].items()])}>
{{description}}
{{contacts}}
{{products}}
{{equipments}}
{{network}}
</ElectricalProject>"""
            
            with open(f'{output_dir}/template_main.xml', 'w', encoding='utf-8') as f:
                f.write(main_template)
            
            # Templates individuels
            for name, template in self.templates.items():
                with open(f'{output_dir}/template_{name}.xml', 'w', encoding='utf-8') as f:
                    f.write(template)
            
            # Structure et patterns
            with open(f'{output_dir}/caneco_structure.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'structure': self.structure,
                    'patterns': self.patterns
                }, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Templates sauvegardés dans {output_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde: {str(e)}")
            return False

def main():
    """Test de l'analyseur"""
    logging.basicConfig(level=logging.INFO)
    
    analyzer = CanecoStructureAnalyzer()
    
    if analyzer.analyze_original_xml('attached_assets/Caneco BT _1754486408913.xml'):
        analyzer.save_templates()
        
        print("=== STRUCTURE ANALYSÉE ===")
        print(f"Products: {analyzer.structure.get('products', {}).get('total_products', 0)}")
        print(f"ProductPacks: {analyzer.structure.get('product_list', {}).get('total_packs', 0)}")
        print(f"Equipments: {analyzer.structure.get('equipments', {}).get('total_equipments', 0)}")
        print(f"Devices: {analyzer.structure.get('equipments', {}).get('total_devices', 0)}")
        print(f"Functions: {analyzer.structure.get('network', {}).get('total_functions', 0)}")
        
        print("\n=== PATTERNS DÉTECTÉS ===")
        print(f"Disjoncteurs: {analyzer.patterns.get('disjoncteur_count', 0)}")
        print(f"Câbles: {analyzer.patterns.get('cable_count', 0)}")
        print(f"Transformateurs: {analyzer.patterns.get('transformer_count', 0)}")
        print(f"Séquences disjoncteur->câble: {analyzer.patterns.get('disjoncteur_cable_sequences', 0)}")
        
        print(f"\nPremières séquences: {' -> '.join(analyzer.patterns.get('sequences', [])[:10])}")
        
    else:
        print("Erreur analyse")

if __name__ == "__main__":
    main()
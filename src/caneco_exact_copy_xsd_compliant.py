#!/usr/bin/env python3
"""
Générateur Caneco EXACT - Copie bit-à-bit du XML original avec données AutoCAD
Objectif: Reproduire EXACTEMENT la structure originale sans aucune modification
"""

import json
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List

class CanecoExactCopyXSDCompliant:
    """Générateur qui copie exactement le XML original"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.autocad_data = []
        self.original_tree = None
        
        # Charger XML original
        self._load_original_xml()
    
    def _load_original_xml(self):
        """Charge le XML original comme base"""
        try:
            with open('attached_assets/Caneco BT _1754486408913.xml', 'r', encoding='utf-8') as f:
                content = f.read()
            self.original_tree = ET.fromstring(content)
            self.logger.info("XML original chargé")
        except Exception as e:
            self.logger.error(f"Erreur chargement XML original: {e}")
    
    def load_autocad_data(self, mapping_file: str) -> bool:
        """Charge les données AutoCAD"""
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.autocad_data = data.get('autocad_data', [])
            self.logger.info(f"Données AutoCAD chargées: {len(self.autocad_data)} équipements")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement AutoCAD: {str(e)}")
            return False
    
    def generate_exact_copy_with_autocad(self, output_path: str) -> bool:
        """Génère XML en copiant exactement l'original avec données AutoCAD"""
        try:
            if not self.original_tree or not self.autocad_data:
                self.logger.error("XML original ou données AutoCAD manquants")
                return False
            
            # Copier l'arbre original
            root = ET.Element(self.original_tree.tag, self.original_tree.attrib)
            
            # Copier exactement chaque section
            for section in self.original_tree:
                section_name = section.tag.split('}')[-1] if '}' in section.tag else section.tag
                
                if section_name == 'Description':
                    new_section = self._copy_description(section)
                elif section_name == 'Contacts':
                    new_section = self._copy_contacts(section)
                elif section_name == 'Products':
                    new_section = self._copy_products_with_autocad(section)
                elif section_name == 'Equipments':
                    new_section = self._copy_equipments_with_autocad(section)
                elif section_name == 'Network':
                    new_section = self._copy_network_with_autocad(section)
                else:
                    # Copier tel quel
                    new_section = self._deep_copy_element(section)
                
                root.append(new_section)
            
            # Écrire avec formatage XML exact comme l'original
            rough_string = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            
            # Décoder et reformater proprement
            xml_str = rough_string.decode('utf-8')
            
            # Garder la déclaration XML exacte de l'original
            xml_str = xml_str.replace(
                '<?xml version="1.0" encoding="utf-8"?>',
                '<?xml version="1.0" encoding="utf-8"?>'
            )
            
            # Écrire directement
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_str)
            
            self.logger.info(f"XML exact généré: {len(self.autocad_data)} équipements")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur génération exacte: {str(e)}")
            return False
    
    def _copy_description(self, original_section):
        """Copie section Description en adaptant le nom"""
        new_section = self._deep_copy_element(original_section)
        
        # Adapter nom du projet
        name_elem = new_section.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Name')
        if name_elem is not None:
            name_elem.text = "Projet AutoCAD - Équipements Électriques"
        
        return new_section
    
    def _copy_contacts(self, original_section):
        """Copie section Contacts exactement"""
        return self._deep_copy_element(original_section)
    
    def _copy_products_with_autocad(self, original_section):
        """Copie section Products en remplaçant par données AutoCAD"""
        new_section = ET.Element(original_section.tag, original_section.attrib)
        
        # Copier ProductSet avec nos données
        product_set = ET.SubElement(new_section, '{http://www.schneider-electric.com/electrical-distribution/exchange-format}ProductSet')
        
        # Prendre premier Product original comme template
        original_products = original_section.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}ProductSet')
        if original_products is not None:
            first_product = original_products.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Product')
            
            if first_product is not None:
                # Générer Products avec template exact
                for i, item in enumerate(self.autocad_data):
                    new_product = self._adapt_product_from_original(first_product, item, f"PG{i+1:05d}")
                    product_set.append(new_product)
        
        # Copier ProductList avec nos données
        product_list = ET.SubElement(new_section, '{http://www.schneider-electric.com/electrical-distribution/exchange-format}ProductList')
        
        # Prendre premier Pack original comme template
        original_list = original_section.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}ProductList')
        if original_list is not None:
            first_pack = original_list.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Pack')
            
            if first_pack is not None:
                # Générer Packs avec template exact
                for i, item in enumerate(self.autocad_data):
                    new_pack = self._adapt_pack_from_original(first_pack, f"PK{i+1:05d}", f"PG{i+1:05d}", f"PI{i+1:05d}")
                    product_list.append(new_pack)
        
        return new_section
    
    def _copy_equipments_with_autocad(self, original_section):
        """Copie section Equipments en adaptant aux données AutoCAD"""
        new_section = ET.Element(original_section.tag, original_section.attrib)
        
        # Prendre premier Equipment comme template
        first_equipment = original_section.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Equipment')
        if first_equipment is not None:
            adapted_equipment = self._adapt_equipment_from_original(first_equipment)
            new_section.append(adapted_equipment)
        
        # Ajouter tous les Device
        for i, item in enumerate(self.autocad_data):
            device_element = self._create_device_from_template(i+1, item)
            new_section.append(device_element)
        
        return new_section
    
    def _copy_network_with_autocad(self, original_section):
        """Copie section Network avec données AutoCAD"""
        new_section = ET.Element(original_section.tag, original_section.attrib)
        
        # Prendre première Function comme template
        first_function = original_section.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Function')
        if first_function is not None:
            for i, item in enumerate(self.autocad_data):
                adapted_function = self._adapt_function_from_original(first_function, item, i+1)
                new_section.append(adapted_function)
        
        return new_section
    
    def _adapt_product_from_original(self, original_product, autocad_item, product_id):
        """Adapte Product original avec données AutoCAD"""
        new_product = self._deep_copy_element(original_product)
        
        # Changer ID
        new_product.set('id', product_id)
        
        # Adapter nom
        name_elem = new_product.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Name')
        if name_elem is not None:
            repere = autocad_item.get('REPERE', '')
            designation = autocad_item.get('DESIGNATION', '')
            fabricant = autocad_item.get('FABRICANT', '')
            
            name_parts = []
            if repere: name_parts.append(repere)
            if designation: name_parts.append(designation)
            if fabricant: name_parts.append(f"({fabricant})")
            
            name_elem.text = ' '.join(name_parts) if name_parts else f"Équipement {product_id}"
        
        return new_product
    
    def _adapt_pack_from_original(self, original_pack, pack_id, product_id, instance_id):
        """Adapte Pack original avec nouveaux IDs"""
        new_pack = self._deep_copy_element(original_pack)
        
        # Changer ID Pack
        new_pack.set('id', pack_id)
        
        # Changer référence Product
        product_ref = new_pack.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Product')
        if product_ref is not None:
            product_ref.set('id', product_id)
        
        # Changer Instance ID
        instance_elem = new_pack.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Instance')
        if instance_elem is not None:
            instance_elem.set('id', instance_id)
        
        return new_pack
    
    def _adapt_equipment_from_original(self, original_equipment):
        """Adapte Equipment original avec toutes nos références"""
        new_equipment = self._deep_copy_element(original_equipment)
        
        # Construire listes de références
        all_packs = [f"PK{i+1:05d}" for i in range(len(self.autocad_data))]
        all_devices = [f"ED{i+1:05d}" for i in range(len(self.autocad_data))]
        all_functions = [f"EF{i+1:05d}" for i in range(len(self.autocad_data))]
        
        # Adapter Commercial ProductPacks
        commercial = new_equipment.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Commercial')
        if commercial is not None:
            commercial.set('ProductPacks', ' '.join(all_packs))
        
        # Adapter Electrical Devices et Functions
        electrical = new_equipment.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Electrical')
        if electrical is not None:
            electrical.set('Devices', ' '.join(all_devices))
            electrical.set('Functions', ' '.join(all_functions))
        
        # Adapter nom
        name_elem = new_equipment.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Name')
        if name_elem is not None:
            name_elem.text = "Équipements AutoCAD"
        
        return new_equipment
    
    def _adapt_function_from_original(self, original_function, autocad_item, index):
        """Adapte Function original avec données AutoCAD"""
        new_function = self._deep_copy_element(original_function)
        
        # Changer ID
        function_id = f"EF{index:05d}"
        device_id = f"ED{index:05d}"
        new_function.set('id', function_id)
        
        # Adapter nom
        name_elem = new_function.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Name')
        if name_elem is not None:
            repere = autocad_item.get('REPERE', f'F{index}')
            name_elem.text = repere
        
        # Adapter Device reference
        electrical = new_function.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Electrical')
        if electrical is not None:
            electrical.set('Devices', device_id)
        
        return new_function
    
    def _create_device_from_template(self, index, autocad_item):
        """Crée Device à partir du template original"""
        device_id = f"ED{index:05d}"
        instance_id = f"PI{index:05d}"
        component_id = f"EC{index:05d}"
        
        device = ET.Element('{http://www.schneider-electric.com/electrical-distribution/exchange-format}Device')
        device.set('id', device_id)
        device.set('ProductInstance', instance_id)
        device.set('Components', component_id)
        
        # Ajouter type de device basé sur données AutoCAD
        designation = autocad_item.get('DESIGNATION', '').lower()
        if 'disjoncteur' in designation or 'breaker' in designation:
            device_type = ET.SubElement(device, '{http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy}CircuitBreakerDevice')
        elif 'transformateur' in designation or 'transformer' in designation:
            device_type = ET.SubElement(device, '{http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy}MvLvTransformerDevice')
        elif 'cable' in designation or 'câble' in designation:
            device_type = ET.SubElement(device, '{http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy}CableDevice')
        else:
            device_type = ET.SubElement(device, '{http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy}CircuitBreakerDevice')
        
        return device
    
    def _deep_copy_element(self, element):
        """Copie profonde d'un élément XML"""
        new_element = ET.Element(element.tag, element.attrib)
        new_element.text = element.text
        new_element.tail = element.tail
        
        for child in element:
            new_element.append(self._deep_copy_element(child))
        
        return new_element

def main():
    """Test du générateur exact"""
    logging.basicConfig(level=logging.INFO)
    
    generator = CanecoExactCopyXSDCompliant()
    
    if generator.load_autocad_data('autocad_caneco_mapping.json'):
        success = generator.generate_exact_copy_with_autocad('test_exact_copy_xsd.xml')
        
        if success:
            print(f"XML copie exacte XSD généré: test_exact_copy_xsd.xml")
            print(f"Équipements traités: {len(generator.autocad_data)}")
        else:
            print("Erreur génération copie exacte")
    else:
        print("Erreur chargement données AutoCAD")

if __name__ == "__main__":
    main()

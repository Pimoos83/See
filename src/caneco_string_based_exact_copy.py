#!/usr/bin/env python3
"""
Générateur Caneco utilisant manipulation de STRING directe
Copie l'original exactement et remplace juste les données nécessaires
"""

import json
import logging
import re
from typing import Dict, List

class CanecoStringBasedExactCopy:
    """Générateur utilisant manipulation directe des strings XML"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.autocad_data = []
        self.original_xml = ""
        
        # Charger XML original
        self._load_original_xml()
    
    def _load_original_xml(self):
        """Charge le XML original comme string"""
        try:
            with open('attached_assets/Caneco BT _1754486408913.xml', 'r', encoding='utf-8') as f:
                self.original_xml = f.read()
            self.logger.info("XML original chargé comme string")
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
    
    def generate_string_based_xml(self, output_path: str) -> bool:
        """Génère XML en remplaçant directement dans le string original"""
        try:
            if not self.original_xml or not self.autocad_data:
                self.logger.error("XML original ou données AutoCAD manquants")
                return False
            
            # Partir de l'original exact
            modified_xml = self.original_xml
            
            # 1. Remplacer le nom du projet
            modified_xml = modified_xml.replace(
                '<Name>Caneco BT - Etap Roadshow 2023</Name>',
                '<Name>Projet AutoCAD - Équipements Électriques</Name>'
            )
            
            # 2. Extraire et remplacer section Products complète
            modified_xml = self._replace_products_section(modified_xml)
            
            # 3. Extraire et remplacer section Equipments complète
            modified_xml = self._replace_equipments_section(modified_xml)
            
            # 4. Extraire et remplacer section Network complète
            modified_xml = self._replace_network_section(modified_xml)
            
            # Écrire le résultat
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(modified_xml)
            
            self.logger.info(f"XML string-based généré: {len(self.autocad_data)} équipements")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur génération string-based: {str(e)}")
            return False
    
    def _replace_products_section(self, xml_content: str) -> str:
        """Remplace section Products complète avec données AutoCAD"""
        # Trouver début et fin de la section Products
        products_start = xml_content.find('<Products>')
        products_end = xml_content.find('</Products>') + len('</Products>')
        
        if products_start == -1 or products_end == -1:
            self.logger.error("Section Products non trouvée")
            return xml_content
        
        # Extraire un Product et un Pack comme templates
        original_products_section = xml_content[products_start:products_end]
        
        # Extraire premier Product comme template
        product_match = re.search(r'<Product id="PG\d+">(.*?)</Product>', original_products_section, re.DOTALL)
        pack_match = re.search(r'<Pack id="PK\d+">(.*?)</Pack>', original_products_section, re.DOTALL)
        
        if not product_match or not pack_match:
            self.logger.error("Templates Product/Pack non trouvés")
            return xml_content
        
        product_template = product_match.group(0)
        pack_template = pack_match.group(0)
        
        # Construire nouvelle section Products
        new_products = ['  <Products>', '    <ProductSet>']
        
        # Générer tous les Products
        for i, item in enumerate(self.autocad_data):
            product_id = f"PG{i+1:05d}"
            new_product = self._adapt_product_template_string(product_template, item, product_id)
            new_products.append(f'      {new_product}')
        
        new_products.append('    </ProductSet>')
        new_products.append('    <ProductList>')
        
        # Générer tous les Packs
        for i, item in enumerate(self.autocad_data):
            pack_id = f"PK{i+1:05d}"
            product_id = f"PG{i+1:05d}"
            instance_id = f"PI{i+1:05d}"
            new_pack = self._adapt_pack_template_string(pack_template, pack_id, product_id, instance_id)
            new_products.append(f'      {new_pack}')
        
        new_products.extend(['    </ProductList>', '  </Products>'])
        new_products_section = '\n'.join(new_products)
        
        # Remplacer dans XML
        return xml_content[:products_start] + new_products_section + xml_content[products_end:]
    
    def _adapt_product_template_string(self, template: str, item: Dict, product_id: str) -> str:
        """Adapte template Product avec données AutoCAD"""
        # Extraire données AutoCAD
        repere = self._clean_xml(item.get('REPERE', ''))
        designation = self._clean_xml(item.get('DESIGNATION', ''))
        fabricant = self._clean_xml(item.get('FABRICANT', ''))
        reference = self._clean_xml(item.get('REF', ''))
        
        # Construire nom produit
        name_parts = []
        if repere: name_parts.append(repere)
        if designation: name_parts.append(designation)
        if fabricant: name_parts.append(f"({fabricant})")
        product_name = ' '.join(name_parts) if name_parts else f"Équipement {product_id}"
        
        # Remplacer dans template
        adapted = template
        adapted = re.sub(r'id="PG\d+"', f'id="{product_id}"', adapted)
        adapted = re.sub(r'<Name>.*?</Name>', f'<Name>{product_name}</Name>', adapted, flags=re.DOTALL)
        
        return adapted
    
    def _adapt_pack_template_string(self, template: str, pack_id: str, product_id: str, instance_id: str) -> str:
        """Adapte template Pack avec nouveaux IDs"""
        adapted = template
        adapted = re.sub(r'id="PK\d+"', f'id="{pack_id}"', adapted)
        adapted = re.sub(r'id="PG\d+"', f'id="{product_id}"', adapted)
        adapted = re.sub(r'id="PI\d+"', f'id="{instance_id}"', adapted)
        return adapted
    
    def _replace_equipments_section(self, xml_content: str) -> str:
        """Remplace section Equipments avec données AutoCAD"""
        # Trouver section Equipments
        equipments_start = xml_content.find('<Equipments>')
        equipments_end = xml_content.find('</Equipments>') + len('</Equipments>')
        
        if equipments_start == -1 or equipments_end == -1:
            self.logger.error("Section Equipments non trouvée")
            return xml_content
        
        # Extraire premier Equipment comme template
        original_equipments = xml_content[equipments_start:equipments_end]
        equipment_match = re.search(r'<Equipment id="EQ\d+">(.*?)</Equipment>', original_equipments, re.DOTALL)
        
        if not equipment_match:
            self.logger.error("Template Equipment non trouvé")
            return xml_content
        
        equipment_template = equipment_match.group(0)
        
        # Construire nouvelle section Equipments
        new_equipments = ['  <Equipments>']
        
        # Adapter Equipment principal
        all_packs = [f"PK{i+1:05d}" for i in range(len(self.autocad_data))]
        all_devices = [f"ED{i+1:05d}" for i in range(len(self.autocad_data))]
        all_functions = [f"EF{i+1:05d}" for i in range(len(self.autocad_data))]
        
        adapted_equipment = equipment_template
        adapted_equipment = re.sub(r'ProductPacks="[^"]*"', f'ProductPacks="{" ".join(all_packs)}"', adapted_equipment)
        adapted_equipment = re.sub(r'Devices="[^"]*"', f'Devices="{" ".join(all_devices)}"', adapted_equipment)
        adapted_equipment = re.sub(r'Functions="[^"]*"', f'Functions="{" ".join(all_functions)}"', adapted_equipment)
        adapted_equipment = re.sub(r'<Name>.*?</Name>', '<Name>Équipements AutoCAD</Name>', adapted_equipment)
        
        new_equipments.append(f'    {adapted_equipment}')
        
        # Ajouter tous les Devices
        for i, item in enumerate(self.autocad_data):
            device_id = f"ED{i+1:05d}"
            instance_id = f"PI{i+1:05d}"
            component_id = f"EC{i+1:05d}"
            
            # Détecter type de device
            designation = item.get('DESIGNATION', '').lower()
            if 'disjoncteur' in designation or 'breaker' in designation:
                device_type = 'CircuitBreakerDevice'
            elif 'transformateur' in designation or 'transformer' in designation:
                device_type = 'MvLvTransformerDevice'
            elif 'cable' in designation or 'câble' in designation:
                device_type = 'CableDevice'
            else:
                device_type = 'CircuitBreakerDevice'
            
            device_xml = f'''    <Device id="{device_id}" ProductInstance="{instance_id}" Components="{component_id}">
      <{device_type} xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy"/>
    </Device>'''
            
            new_equipments.append(device_xml)
        
        new_equipments.append('  </Equipments>')
        new_equipments_section = '\n'.join(new_equipments)
        
        # Remplacer dans XML
        return xml_content[:equipments_start] + new_equipments_section + xml_content[equipments_end:]
    
    def _replace_network_section(self, xml_content: str) -> str:
        """Remplace section Network avec données AutoCAD"""
        # Trouver section Network
        network_start = xml_content.find('<Network>')
        network_end = xml_content.find('</Network>') + len('</Network>')
        
        if network_start == -1 or network_end == -1:
            self.logger.error("Section Network non trouvée")
            return xml_content
        
        # Extraire première Function comme template
        original_network = xml_content[network_start:network_end]
        function_match = re.search(r'<Function id="EF\d+">(.*?)</Function>', original_network, re.DOTALL)
        
        if not function_match:
            self.logger.error("Template Function non trouvé")
            return xml_content
        
        function_template = function_match.group(0)
        
        # Construire nouvelle section Network
        new_network = ['  <Network>']
        
        # Générer toutes les Functions
        for i, item in enumerate(self.autocad_data):
            function_id = f"EF{i+1:05d}"
            device_id = f"ED{i+1:05d}"
            repere = self._clean_xml(item.get('REPERE', f'F{i+1}'))
            
            adapted_function = function_template
            adapted_function = re.sub(r'id="EF\d+"', f'id="{function_id}"', adapted_function)
            adapted_function = re.sub(r'<Name>.*?</Name>', f'<Name>{repere}</Name>', adapted_function)
            adapted_function = re.sub(r'Devices="[^"]*"', f'Devices="{device_id}"', adapted_function)
            
            new_network.append(f'    {adapted_function}')
        
        new_network.append('  </Network>')
        new_network_section = '\n'.join(new_network)
        
        # Remplacer dans XML
        return xml_content[:network_start] + new_network_section + xml_content[network_end:]
    
    def _clean_xml(self, text: str) -> str:
        """Nettoie texte pour XML"""
        if not text or not text.strip():
            return ""
        
        cleaned = str(text).strip()
        cleaned = cleaned.replace('&', '&amp;')
        cleaned = cleaned.replace('<', '&lt;')
        cleaned = cleaned.replace('>', '&gt;')
        cleaned = cleaned.replace('"', '&quot;')
        cleaned = cleaned.replace("'", '&apos;')
        
        return cleaned

def main():
    """Test du générateur string-based"""
    logging.basicConfig(level=logging.INFO)
    
    generator = CanecoStringBasedExactCopy()
    
    if generator.load_autocad_data('autocad_caneco_mapping.json'):
        success = generator.generate_string_based_xml('test_string_based.xml')
        
        if success:
            print(f"XML string-based généré: test_string_based.xml")
            print(f"Équipements traités: {len(generator.autocad_data)}")
        else:
            print("Erreur génération string-based")
    else:
        print("Erreur chargement données AutoCAD")

if __name__ == "__main__":
    main()

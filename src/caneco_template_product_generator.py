#!/usr/bin/env python3
"""
Générateur Caneco avec template Product personnalisé
Utilise la structure qui fonctionne + votre template Product
"""

import json
import logging
import re
from typing import Dict, List

class CanecoTemplateProductGenerator:
    """Générateur utilisant template Product personnalisé"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.autocad_data = []
        self.original_xml = ""
        self.product_template = ""
        
        # Charger XML original et template
        self._load_original_xml()
        self._load_product_template()
    
    def _load_original_xml(self):
        """Charge le XML original comme base"""
        try:
            with open('attached_assets/Caneco BT _1754486408913.xml', 'r', encoding='utf-8') as f:
                self.original_xml = f.read()
            self.logger.info("XML original chargé comme base")
        except Exception as e:
            self.logger.error(f"Erreur chargement XML original: {e}")
    
    def _load_product_template(self):
        """Charge le template Product personnalisé"""
        try:
            with open('Template_PGxxxxx.xml', 'r', encoding='utf-8') as f:
                self.product_template = f.read().strip()
            self.logger.info("Template Product personnalisé chargé")
        except Exception as e:
            self.logger.error(f"Erreur chargement template Product: {e}")
    
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
    
    def generate_template_product_xml(self, output_path: str) -> bool:
        """Génère XML en remplaçant les Products avec le template personnalisé"""
        try:
            if not self.original_xml or not self.autocad_data or not self.product_template:
                self.logger.error("Données manquantes pour génération")
                return False
            
            # Partir de l'original qui fonctionne
            modified_xml = self.original_xml
            
            # 1. Changer le nom du projet
            modified_xml = modified_xml.replace(
                '<Name>Caneco BT - Etap Roadshow 2023</Name>',
                f'<Name>Projet AutoCAD - {len(self.autocad_data)} équipements</Name>'
            )
            
            # 2. Remplacer section Products avec template personnalisé
            modified_xml = self._replace_products_with_template(modified_xml)
            
            # 3. Adapter section ProductList (Packs)
            modified_xml = self._adapt_product_list(modified_xml)
            
            # 4. Adapter section Equipments
            modified_xml = self._adapt_equipments_section(modified_xml)
            
            # 5. Adapter section Network (Functions)
            modified_xml = self._adapt_network_section(modified_xml)
            
            # Écrire le résultat
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(modified_xml)
            
            self.logger.info(f"XML avec template Product généré: {len(self.autocad_data)} équipements")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur génération template Product: {str(e)}")
            return False
    
    def _replace_products_with_template(self, xml_content: str) -> str:
        """Remplace ProductSet avec Products utilisant le template personnalisé"""
        # Trouver section ProductSet
        productset_start = xml_content.find('<ProductSet>')
        productset_end = xml_content.find('</ProductSet>') + len('</ProductSet>')
        
        if productset_start == -1 or productset_end == -1:
            self.logger.error("Section ProductSet non trouvée")
            return xml_content
        
        # Construire nouvelle section ProductSet
        new_products = ['    <ProductSet>']
        
        # Générer tous les Products avec le template personnalisé
        for i, item in enumerate(self.autocad_data):
            product_id = f"PG{i+1:05d}"
            new_product = self._generate_product_from_template(item, product_id, i)
            # Indenter le product
            indented_product = '\n'.join(['      ' + line for line in new_product.split('\n')])
            new_products.append(indented_product)
        
        new_products.append('    </ProductSet>')
        new_productset = '\n'.join(new_products)
        
        # Remplacer dans XML
        return xml_content[:productset_start] + new_productset + xml_content[productset_end:]
    
    def _generate_product_from_template(self, item: Dict, product_id: str, index: int) -> str:
        """Génère un Product à partir du template et des données AutoCAD"""
        # Extraire données AutoCAD
        repere = self._clean_xml(item.get('REPERE', f'EQ{index+1}'))
        designation = self._clean_xml(item.get('DESIGNATION', ''))
        fabricant = self._clean_xml(item.get('FABRICANT', ''))
        reference = self._clean_xml(item.get('REF', ''))
        
        # Construire nom produit
        name_parts = []
        if repere: name_parts.append(repere)
        if designation: name_parts.append(designation)
        if fabricant: name_parts.append(f"({fabricant})")
        product_name = ' '.join(name_parts) if name_parts else f"Équipement {product_id}"
        
        # Mapper données AutoCAD vers valeurs Caneco
        mappings = self._get_autocad_to_caneco_mapping(item, reference)
        
        # Remplacer dans template
        product_xml = self.product_template
        product_xml = product_xml.replace('{PG_ID}', product_id)
        product_xml = product_xml.replace('{Nom_Produit}', product_name)
        product_xml = product_xml.replace('{Item_ID}', mappings.get('Item_ID', 'MG4_13271'))
        
        # Remplacer toutes les valeurs de caractéristiques
        for key, value in mappings.items():
            if key.startswith('Valeur_'):
                product_xml = product_xml.replace('{' + key + '}', str(value))
        
        return product_xml
    
    def _get_autocad_to_caneco_mapping(self, item: Dict, reference: str) -> Dict[str, str]:
        """Mappe les données AutoCAD vers les valeurs Caneco"""
        designation = item.get('DESIGNATION', '').lower()
        
        # Valeurs par défaut
        mappings = {
            'Item_ID': 'MG4_13271',
            'Valeur_PRT_INST': '',
            'Valeur_PRT_PERFO': 'F',
            'Valeur_PRT_CDECL': 'Micrologic 2.3',
            'Valeur_PRT_CAL': '630.00',
            'Valeur_PRT_NBPPP': '3',
            'Valeur_PRT_NORM': 'IEC 60947-2',
            'Valeur_PRT_FREQ': '50',
            'Valeur_PRT_ICC': '16',
            'Valeur_PRT_DIFF': 'Non',
            'Valeur_PRT_VISU': 'Oui',
            'Valeur_PRT_TCDE': 'Manuel',
            'Valeur_PRT_BDCLS': 'Standard',
            'Valeur_PRT_BDSEN': 'Standard',
            'Valeur_PRT_REF': reference or 'AUTO'
        }
        
        # Adaptation selon type d'équipement
        if 'disjoncteur' in designation:
            mappings.update({
                'Item_ID': 'MG4_13271',
                'Valeur_PRT_CDECL': 'Micrologic 2.3',
                'Valeur_PRT_CAL': self._extract_current_from_designation(designation),
            })
        elif 'transformateur' in designation:
            mappings.update({
                'Item_ID': 'TR_GENERIC',
                'Valeur_PRT_CDECL': 'Transformateur',
                'Valeur_PRT_CAL': self._extract_power_from_designation(designation),
            })
        elif 'cable' in designation or 'câble' in designation:
            mappings.update({
                'Item_ID': 'CABLE_GENERIC',
                'Valeur_PRT_CDECL': 'Câble',
                'Valeur_PRT_CAL': self._extract_section_from_designation(designation),
            })
        
        return mappings
    
    def _extract_current_from_designation(self, designation: str) -> str:
        """Extrait le courant de la désignation"""
        import re
        match = re.search(r'(\d+)A', designation.upper())
        return match.group(1) + '.00' if match else '16.00'
    
    def _extract_power_from_designation(self, designation: str) -> str:
        """Extrait la puissance de la désignation"""
        import re
        match = re.search(r'(\d+)kVA', designation.upper())
        return match.group(1) + '.00' if match else '100.00'
    
    def _extract_section_from_designation(self, designation: str) -> str:
        """Extrait la section de la désignation"""
        import re
        match = re.search(r'(\d+)mm', designation.lower())
        return match.group(1) + '.00' if match else '2.50'
    
    def _adapt_product_list(self, xml_content: str) -> str:
        """Adapte ProductList pour référencer nos nouveaux Products"""
        # Trouver section ProductList
        productlist_start = xml_content.find('<ProductList>')
        productlist_end = xml_content.find('</ProductList>') + len('</ProductList>')
        
        if productlist_start == -1 or productlist_end == -1:
            self.logger.error("Section ProductList non trouvée")
            return xml_content
        
        # Extraire template Pack
        original_productlist = xml_content[productlist_start:productlist_end]
        pack_match = re.search(r'<Pack id="PK\d+">(.*?)</Pack>', original_productlist, re.DOTALL)
        
        if not pack_match:
            self.logger.error("Template Pack non trouvé")
            return xml_content
        
        pack_template = pack_match.group(0)
        
        # Construire nouvelle ProductList
        new_productlist = ['    <ProductList>']
        
        for i, item in enumerate(self.autocad_data):
            pack_id = f"PK{i+1:05d}"
            product_id = f"PG{i+1:05d}"
            instance_id = f"PI{i+1:05d}"
            
            new_pack = pack_template
            new_pack = re.sub(r'id="PK\d+"', f'id="{pack_id}"', new_pack)
            new_pack = re.sub(r'id="PG\d+"', f'id="{product_id}"', new_pack)
            new_pack = re.sub(r'id="PI\d+"', f'id="{instance_id}"', new_pack)
            
            new_productlist.append(f'      {new_pack}')
        
        new_productlist.append('    </ProductList>')
        new_productlist_section = '\n'.join(new_productlist)
        
        return xml_content[:productlist_start] + new_productlist_section + xml_content[productlist_end:]
    
    def _adapt_equipments_section(self, xml_content: str) -> str:
        """Adapte section Equipments avec références aux nouveaux Products"""
        # Construire listes de références
        all_packs = [f"PK{i+1:05d}" for i in range(len(self.autocad_data))]
        all_devices = [f"ED{i+1:05d}" for i in range(len(self.autocad_data))]
        all_functions = [f"EF{i+1:05d}" for i in range(len(self.autocad_data))]
        
        # Remplacer références dans Equipment principal
        xml_content = re.sub(
            r'ProductPacks="[^"]*"',
            f'ProductPacks="{" ".join(all_packs)}"',
            xml_content
        )
        xml_content = re.sub(
            r'Devices="[^"]*"',
            f'Devices="{" ".join(all_devices)}"',
            xml_content
        )
        xml_content = re.sub(
            r'Functions="[^"]*"',
            f'Functions="{" ".join(all_functions)}"',
            xml_content
        )
        
        return xml_content
    
    def _adapt_network_section(self, xml_content: str) -> str:
        """Adapte section Network avec nos Functions"""
        # Trouver section Network
        network_start = xml_content.find('<Network>')
        network_end = xml_content.find('</Network>') + len('</Network>')
        
        if network_start == -1 or network_end == -1:
            self.logger.error("Section Network non trouvée")
            return xml_content
        
        # Extraire template Function
        original_network = xml_content[network_start:network_end]
        function_match = re.search(r'<Function id="EF\d+">(.*?)</Function>', original_network, re.DOTALL)
        
        if not function_match:
            self.logger.error("Template Function non trouvé")
            return xml_content
        
        function_template = function_match.group(0)
        
        # Construire nouvelle section Network
        new_network = ['  <Network>']
        
        for i, item in enumerate(self.autocad_data):
            function_id = f"EF{i+1:05d}"
            device_id = f"ED{i+1:05d}"
            repere = self._clean_xml(item.get('REPERE', f'F{i+1}'))
            
            new_function = function_template
            new_function = re.sub(r'id="EF\d+"', f'id="{function_id}"', new_function)
            new_function = re.sub(r'<Name>.*?</Name>', f'<Name>{repere}</Name>', new_function)
            new_function = re.sub(r'Devices="[^"]*"', f'Devices="{device_id}"', new_function)
            
            new_network.append(f'    {new_function}')
        
        new_network.append('  </Network>')
        new_network_section = '\n'.join(new_network)
        
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
    """Test du générateur template Product"""
    logging.basicConfig(level=logging.INFO)
    
    generator = CanecoTemplateProductGenerator()
    
    if generator.load_autocad_data('autocad_caneco_mapping.json'):
        success = generator.generate_template_product_xml('test_template_product.xml')
        
        if success:
            print(f"✓ XML avec template Product généré: test_template_product.xml")
            print(f"✓ Équipements traités: {len(generator.autocad_data)}")
            print("✓ Structure Caneco + Template Product personnalisé")
        else:
            print("❌ Erreur génération template Product")
    else:
        print("❌ Erreur chargement données AutoCAD")

if __name__ == "__main__":
    main()

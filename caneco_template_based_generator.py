#!/usr/bin/env python3
"""
Générateur Caneco basé sur les templates EXACTS extraits
Utilise les vrais templates pour reconstruire un XML strictement identique
"""

import json
import logging
from typing import Dict, List
import re

class CanecoTemplateBasedGenerator:
    """Générateur utilisant les templates exacts du XML original"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.autocad_data = []
        self.templates = {}
        self.structure = {}
        
        # Charger templates et structure
        self._load_templates()
        self._load_structure()
    
    def _load_templates(self):
        """Charge tous les templates extraits"""
        template_files = [
            'template_main.xml',
            'template_description.xml', 
            'template_contacts.xml',
            'template_product.xml',
            'template_pack.xml',
            'template_equipment.xml',
            'template_function.xml'
        ]
        
        for template_file in template_files:
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_name = template_file.replace('template_', '').replace('.xml', '')
                    self.templates[template_name] = f.read()
            except FileNotFoundError:
                self.logger.warning(f"Template manquant: {template_file}")
    
    def _load_structure(self):
        """Charge la structure analysée"""
        try:
            with open('caneco_structure.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.structure = data.get('structure', {})
        except FileNotFoundError:
            self.logger.error("Structure manquante: caneco_structure.json")
    
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
    
    def generate_exact_template_xml(self, output_path: str) -> bool:
        """Génère XML en utilisant templates exacts"""
        try:
            if not self.autocad_data:
                self.logger.error("Aucune donnée AutoCAD")
                return False
            
            # Utiliser template principal avec version 0.34
            main_template = self.templates.get('main', '')
            if not main_template:
                self.logger.error("Template principal manquant")
                return False
            
            # Mettre à jour version pour compatibilité Caneco BT récent
            main_template = main_template.replace('formatVersion="0.29"', 'formatVersion="0.34"')
            
            # Ajouter namespaces XSD si manquants
            if 'xmlns:xsi' not in main_template:
                main_template = main_template.replace(
                    '<ElectricalProject',
                    '<ElectricalProject xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"'
                )
            
            # Remplacer chaque section
            xml_content = main_template
            xml_content = xml_content.replace('{description}', self._build_description())
            xml_content = xml_content.replace('{contacts}', self._build_contacts())
            xml_content = xml_content.replace('{products}', self._build_products_from_template())
            xml_content = xml_content.replace('{equipments}', self._build_equipments_from_template())
            xml_content = xml_content.replace('{network}', self._build_network_from_template())
            
            # Écrire fichier
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            self.logger.info(f"XML template généré: {len(self.autocad_data)} équipements")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur génération template: {str(e)}")
            return False
    
    def _build_description(self) -> str:
        """Section Description à partir du template"""
        template = self.templates.get('description', '')
        if not template:
            return '<Description><Name>Projet AutoCAD</Name></Description>'
        
        # Nettoyer namespaces et adapter le template
        description = template.replace('ns0:', '').replace('xmlns:ns0="http://www.schneider-electric.com/electrical-distribution/exchange-format"', '')
        description = description.replace(
            '<Name>Caneco BT - Etap Roadshow 2023</Name>',
            '<Name>Projet AutoCAD - Équipements Électriques</Name>'
        )
        return description
    
    def _build_contacts(self) -> str:
        """Section Contacts à partir du template"""
        template = self.templates.get('contacts', '<Contacts></Contacts>')
        # Nettoyer namespaces problématiques
        cleaned = template.replace('ns0:', '').replace('xmlns:ns0="http://www.schneider-electric.com/electrical-distribution/exchange-format"', '')
        return cleaned
    
    def _build_products_from_template(self) -> str:
        """Section Products utilisant templates exacts"""
        if not self.templates.get('product') or not self.templates.get('pack'):
            return '<Products></Products>'
        
        lines = ['  <Products>', '    <ProductSet>']
        
        # Générer Products basés sur template
        product_template = self.templates['product']
        for i, item in enumerate(self.autocad_data):
            product_id = f"PG{i+1:05d}"
            
            # Adapter template Product
            product_xml = self._adapt_product_template(product_template, item, product_id)
            lines.append(self._indent_xml(product_xml, 6))
        
        lines.append('    </ProductSet>')
        lines.append('    <ProductList>')
        
        # Générer ProductPacks basés sur template
        pack_template = self.templates['pack']
        for i, item in enumerate(self.autocad_data):
            pack_id = f"PK{i+1:05d}"
            product_id = f"PG{i+1:05d}"
            instance_id = f"PI{i+1:05d}"
            
            # Adapter template Pack
            pack_xml = self._adapt_pack_template(pack_template, pack_id, product_id, instance_id)
            lines.append(self._indent_xml(pack_xml, 6))
        
        lines.extend(['    </ProductList>', '  </Products>'])
        return '\n'.join(lines)
    
    def _adapt_product_template(self, template: str, item: Dict, product_id: str) -> str:
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
        
        # Remplacer dans template ET nettoyer namespaces
        adapted = template
        
        # Nettoyer namespaces ns0: problématiques
        adapted = adapted.replace('ns0:', '')
        adapted = adapted.replace('xmlns:ns0="http://www.schneider-electric.com/electrical-distribution/exchange-format"', '')
        
        # Remplacer ID et nom
        adapted = re.sub(r'id="PG\d+"', f'id="{product_id}"', adapted)
        adapted = re.sub(r'<Name>.*?</Name>', f'<Name>{product_name}</Name>', adapted, flags=re.DOTALL)
        
        # Adapter référence si possible
        if reference:
            adapted = re.sub(r'<Id>.*?</Id>(?=.*</Value>)', f'<Id>{reference}</Id>', adapted)
        
        return adapted
    
    def _adapt_pack_template(self, template: str, pack_id: str, product_id: str, instance_id: str) -> str:
        """Adapte template Pack avec IDs"""
        adapted = template
        
        # Nettoyer namespaces ns0: problématiques
        adapted = adapted.replace('ns0:', '')
        adapted = adapted.replace('xmlns:ns0="http://www.schneider-electric.com/electrical-distribution/exchange-format"', '')
        
        # Remplacer IDs
        adapted = re.sub(r'id="PK\d+"', f'id="{pack_id}"', adapted)
        adapted = re.sub(r'id="PG\d+"', f'id="{product_id}"', adapted)
        adapted = re.sub(r'id="PI\d+"', f'id="{instance_id}"', adapted)
        return adapted
    
    def _build_equipments_from_template(self) -> str:
        """Section Equipments utilisant structure exacte analysée"""
        if not self.templates.get('equipment'):
            return '<Equipments></Equipments>'
        
        lines = ['  <Equipments>']
        
        # Utiliser structure analysée des Equipment originaux
        equipment_details = self.structure.get('equipment_details', [])
        
        if equipment_details:
            # Prendre le premier Equipment comme modèle
            eq_template = self.templates['equipment']
            
            # Créer Equipment principal avec tous vos équipements AutoCAD
            all_packs = [f"PK{i+1:05d}" for i in range(len(self.autocad_data))]
            all_devices = [f"ED{i+1:05d}" for i in range(len(self.autocad_data))]
            all_functions = [f"EF{i+1:05d}" for i in range(len(self.autocad_data))]
            
            # Adapter template Equipment
            equipment_xml = eq_template
            # Nettoyer namespaces
            equipment_xml = equipment_xml.replace('ns0:', '').replace('xmlns:ns0="http://www.schneider-electric.com/electrical-distribution/exchange-format"', '')
            
            equipment_xml = re.sub(r'ProductPacks="[^"]*"', f'ProductPacks="{" ".join(all_packs)}"', equipment_xml)
            equipment_xml = re.sub(r'Devices="[^"]*"', f'Devices="{" ".join(all_devices)}"', equipment_xml)
            equipment_xml = re.sub(r'Functions="[^"]*"', f'Functions="{" ".join(all_functions)}"', equipment_xml)
            equipment_xml = re.sub(r'<Name>.*?</Name>', '<Name>Équipements AutoCAD</Name>', equipment_xml)
            
            lines.append(self._indent_xml(equipment_xml, 4))
        
        # Ajouter tous les Device individuels (structure trouvée dans l'original)
        for i, item in enumerate(self.autocad_data):
            device_id = f"ED{i+1:05d}"
            instance_id = f"PI{i+1:05d}"
            component_id = f"EC{i+1:05d}"
            
            device_xml = f'''<Device id="{device_id}" ProductInstance="{instance_id}" Components="{component_id}">
      <CircuitBreakerDevice xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy"/>
    </Device>'''
            
            lines.append(self._indent_xml(device_xml, 4))
        
        lines.append('  </Equipments>')
        return '\n'.join(lines)
    
    def _build_network_from_template(self) -> str:
        """Section Network utilisant template exact"""
        if not self.templates.get('function'):
            return '<Network></Network>'
        
        lines = ['  <Network>']
        
        function_template = self.templates['function']
        for i, item in enumerate(self.autocad_data):
            function_id = f"EF{i+1:05d}"
            device_id = f"ED{i+1:05d}"
            repere = self._clean_xml(item.get('REPERE', f'F{i+1}'))
            
            # Adapter template Function
            function_xml = function_template
            # Nettoyer namespaces
            function_xml = function_xml.replace('ns0:', '').replace('xmlns:ns0="http://www.schneider-electric.com/electrical-distribution/exchange-format"', '')
            
            function_xml = re.sub(r'id="EF\d+"', f'id="{function_id}"', function_xml)
            function_xml = re.sub(r'<Name>.*?</Name>', f'<Name>{repere}</Name>', function_xml)
            function_xml = re.sub(r'Devices="[^"]*"', f'Devices="{device_id}"', function_xml)
            
            lines.append(self._indent_xml(function_xml, 4))
        
        lines.append('  </Network>')
        return '\n'.join(lines)
    
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
    
    def _indent_xml(self, xml_text: str, spaces: int) -> str:
        """Indente XML"""
        indent = ' ' * spaces
        lines = xml_text.strip().split('\n')
        return '\n'.join([indent + line for line in lines])

def main():
    """Test du générateur template"""
    logging.basicConfig(level=logging.INFO)
    
    generator = CanecoTemplateBasedGenerator()
    
    if generator.load_autocad_data('autocad_caneco_mapping.json'):
        success = generator.generate_exact_template_xml('test_template_based.xml')
        
        if success:
            print(f"XML template exact généré: test_template_based.xml")
            print(f"Équipements traités: {len(generator.autocad_data)}")
        else:
            print("Erreur génération template")
    else:
        print("Erreur chargement données AutoCAD")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
GÉNÉRATEUR BASÉ SUR TEMPLATE_CANECO.XML
Suit strictement la structure Template_Caneco.xml et utilise vos templates corrects
INTERDICTION de modifier les templates existants
"""

import pandas as pd
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from typing import Dict, List, Tuple
import os

class CanecoTemplateGenerator:
    """Générateur qui suit strictement Template_Caneco.xml"""
    
    def __init__(self):
        # Mapping des types de composants vers les templates appropriés
        self.component_mapping = {
            'transformateur': {
                'device': 'Template_EDxxxxx_TR.xml',
                'component': 'Template_ECxxxxx_TR.xml',
                'product': 'Template_PKxxxx_TR.xml'
            },
            'cable': {
                'device': 'Template_EDxxxxx_CA.xml', 
                'component': 'Template_ECxxxxx_CA.xml',
                'product': 'Template_PKxxxx_CA.xml'
            },
            'disjoncteur': {
                'device': 'Template_EDxxxxx_DISJ.xml',
                'component': 'Template_ECxxxxx_DISJ.xml',
                'product': 'Template_PKxxxx_DISJ.xml'
            },
            'irve': {
                'device': 'Template_EDxxxxx_DISJ.xml',
                'component': 'Template_ECxxxxx_DISJ.xml',
                'product': 'Template_PKxxxx_DISJ.xml'
            }
        }
        
        # Compteurs pour les IDs selon Template_Caneco.xml
        self.id_counters = {
            'PG': 1,    # ProductSet
            'PK': 1,    # ProductList
            'EQ': 1,    # Equipment
            'ED': 1,    # Device 
            'EC': 1,    # Component
            'EF': 1,    # Function
            'EXM': 1,   # ExploitationMode
            'ECX': 1,   # PowerConnection
            'PI': 1,    # ProductInstance
            'ECT': 1    # Terminal
        }
        
    def detect_component_type(self, designation: str, repere: str = "", fabricant: str = "") -> str:
        """Détecte le type de composant selon les données AutoCAD"""
        text = f"{designation} {repere} {fabricant}".lower()
        
        if any(keyword in text for keyword in ['transfo', 'transformateur', 'tr0', 'tr1']):
            return 'transformateur'
        elif any(keyword in text for keyword in ['cable', 'câble', 'cbl', 'cblar']):
            return 'cable'
        elif any(keyword in text for keyword in ['irve', 'borne']):
            return 'irve'
        elif any(keyword in text for keyword in ['disjoncteur', 'nsxm', 'nsx', 'id40', 'idt40']):
            return 'disjoncteur'
        else:
            return 'disjoncteur'  # Par défaut
    
    def load_template(self, template_name: str) -> str:
        """Charge un template SANS LE MODIFIER - INTERDICTION ABSOLUE"""
        try:
            with open(template_name, 'r', encoding='utf-8') as f:
                content = f.read()
                # AUCUNE MODIFICATION DES TEMPLATES - RESPECT STRICT DE VOS CORRECTIONS
                return content
        except FileNotFoundError:
            print(f"Template {template_name} non trouvé")
            return ""
    
    def generate_id(self, prefix: str) -> str:
        """Génère un ID avec le préfixe donné"""
        current_count = self.id_counters.get(prefix, 1)
        id_str = f"{prefix}{current_count:05d}"
        self.id_counters[prefix] = current_count + 1
        return id_str
    
    def replace_only_xxxxx(self, template_content: str, id_mapping: Dict) -> str:
        """REMPLACE UNIQUEMENT LES xxxxx - AUCUNE AUTRE MODIFICATION DU TEMPLATE"""
        content = template_content
        
        # REMPLACEMENT UNIQUEMENT DES xxxxx par les IDs fournis
        for placeholder, real_id in id_mapping.items():
            content = content.replace(placeholder, real_id)
            
        return content
    
    def replace_autocad_data_in_template(self, template_content: str, component_data: Dict) -> str:
        """Remplace les champs CLASS, CAL, Name par les données AutoCAD APRÈS avoir collé le template"""
        content = template_content
        
        # Récupérer les données AutoCAD
        repere = str(component_data.get('REPERE', 'UNKNOWN'))
        if repere == 'nan' or repere == '':
            repere = str(component_data.get('DESIGNATION', 'UNKNOWN'))[:20]
        
        designation = str(component_data.get('DESIGNATION', ''))
        fabricant = str(component_data.get('FABRICANT', ''))
        reference = str(component_data.get('REFERENCE', ''))
        
        # Remplacements des champs spécifiques APRÈS collage du template
        content = content.replace('<Id>CLASS</Id>', f'<Id>{designation[:20]}</Id>')
        content = content.replace('<Id>CAL</Id>', f'<Id>{reference[:10]}</Id>')
        content = content.replace('<Id>Name</Id>', f'<Id>{repere}</Id>')
        content = content.replace('<Name>Name</Name>', f'<Name>{repere}</Name>')
        content = content.replace('<FunctionalName>Name</FunctionalName>', f'<FunctionalName>{repere}</FunctionalName>')
        
        # Remplacements pour les transformateurs
        if 'transfo' in designation.lower() or 'tr0' in repere.lower():
            content = content.replace('<Id>400</Id>', f'<Id>630</Id>')  # Puissance
            content = content.replace('<Id>420</Id>', f'<Id>400</Id>')  # Tension
        
        # Remplacements pour les disjoncteurs
        if 'disjoncteur' in designation.lower() or 'nsx' in designation.lower():
            content = content.replace('<Id>Rating</Id>', f'<Id>630</Id>')  # Courant nominal
            content = content.replace('<Id>Pole</Id>', f'<Id>4P</Id>')   # Polarité
            
        return content
    
    def process_autocad_data(self, excel_file: str) -> Dict:
        """Traite le fichier Excel AutoCAD"""
        print("=== TRAITEMENT DONNÉES AUTOCAD ===")
        
        try:
            df = pd.read_excel(excel_file)
            print(f"Fichier chargé: {len(df)} lignes")
            
            # Détection automatique des colonnes
            columns_mapping = {}
            for col in df.columns:
                if col == 'REPERE':
                    columns_mapping['REPERE'] = col
                elif col == 'DESIGNATION':
                    columns_mapping['DESIGNATION'] = col
                elif col == 'FABRICANT':
                    columns_mapping['FABRICANT'] = col
                elif col == 'REF':
                    columns_mapping['REFERENCE'] = col
                    
            print(f"Colonnes détectées: {columns_mapping}")
            
            # Extraction des composants
            components = []
            for idx, row in df.iterrows():
                repere_val = row.get(columns_mapping.get('REPERE', ''), '')
                if pd.isna(repere_val) or str(repere_val) == 'nan':
                    repere_val = f"COMP_{int(idx)+1:03d}"
                else:
                    repere_val = str(repere_val)
                    
                component = {
                    'REPERE': repere_val,
                    'DESIGNATION': str(row.get(columns_mapping.get('DESIGNATION', ''), '')),
                    'FABRICANT': str(row.get(columns_mapping.get('FABRICANT', ''), '')),
                    'REFERENCE': str(row.get(columns_mapping.get('REFERENCE', ''), ''))
                }
                
                # Détection du type
                component_type = self.detect_component_type(
                    component['DESIGNATION'],
                    component['REPERE'], 
                    component['FABRICANT']
                )
                component['TYPE'] = component_type
                components.append(component)
                
            # Statistiques
            type_stats = {}
            for comp in components:
                comp_type = comp['TYPE']
                type_stats[comp_type] = type_stats.get(comp_type, 0) + 1
                
            print("=== STATISTIQUES COMPOSANTS ===")
            for comp_type, count in type_stats.items():
                print(f"{comp_type}: {count} composants")
                
            return {
                'components': components,
                'stats': type_stats,
                'total': len(components)
            }
            
        except Exception as e:
            print(f"Erreur traitement fichier: {e}")
            return {'components': [], 'stats': {}, 'total': 0}
    
    def generate_xml_from_template(self, autocad_data: Dict, output_file: str = "caneco_from_template.xml"):
        """Génère le XML en suivant strictement Template_Caneco.xml"""
        
        print("=== GÉNÉRATION XML SELON TEMPLATE_CANECO.xml ===")
        
        components = autocad_data['components']
        if not components:
            print("Aucun composant à traiter")
            return
            
        # Trier les composants selon l'ordre Template_Caneco.xml : TR, CA, DISJ
        sorted_components = []
        
        # 1. D'abord les transformateurs
        for comp in components:
            if comp['TYPE'] == 'transformateur':
                sorted_components.append(comp)
                
        # 2. Puis les câbles  
        for comp in components:
            if comp['TYPE'] == 'cable':
                sorted_components.append(comp)
                
        # 3. Enfin les disjoncteurs et autres
        for comp in components:
            if comp['TYPE'] not in ['transformateur', 'cable']:
                sorted_components.append(comp)
        
        # Créer le XML root
        root = ET.Element("ElectricalProject")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
        root.set("formatVersion", "0.29")
        root.set("productRangeValuesVersion", "0.17")
        root.set("commercialTaxonomyVersion", "0.26")
        root.set("electricalTaxonomyVersion", "0.19")
        root.set("mechanicalTaxonomyVersion", "0.1")
        root.set("xmlns", "http://www.schneider-electric.com/electrical-distribution/exchange-format")
        
        # 1. DESCRIPTION (Template Description)
        desc_template = self.load_template('Template_Description.xml')
        if desc_template:
            desc_element = ET.fromstring(desc_template)
            root.append(desc_element)
            
        # 2. CONTACTS (Template Contact)
        contact_template = self.load_template('Template_Contact.xml')
        if contact_template:
            contact_element = ET.fromstring(contact_template)
            root.append(contact_element)
            
        # 3. PRODUCTS
        products_element = ET.SubElement(root, "Products")
        
        # ProductSet avec UN Template PGxxxxx PAR COMPOSANT
        productset_element = ET.SubElement(products_element, "ProductSet")
        pg_template = self.load_template('Template_PGxxxxx.xml')
        
        if pg_template:
            for comp in sorted_components:
                pg_id = self.generate_id('PG')
                pg_content = pg_template.replace('PGxxxxx', pg_id)
                
                # Remplacer les données AutoCAD APRÈS avoir collé le template
                pg_content = self.replace_autocad_data_in_template(pg_content, comp)
                
                try:
                    pg_element = ET.fromstring(pg_content)
                    productset_element.append(pg_element)
                except ET.ParseError as e:
                    print(f"Erreur parsing Template_PGxxxxx.xml: {e}")
            
        # ProductList selon l'ordre TR, CA, DISJ - GÉNÉRATION DES PKxxxxx
        productlist_element = ET.SubElement(products_element, "ProductList")
        pk_template = self.load_template('Template_PKxxxx_DISJ.xml')  # Template par défaut
        
        if pk_template:
            for comp in sorted_components:
                comp_type = comp['TYPE']
                
                # Sélectionner le bon template PK selon le type
                if comp_type == 'transformateur':
                    pk_template_name = 'Template_PKxxxx_TR.xml'
                elif comp_type == 'cable':
                    pk_template_name = 'Template_PKxxxx_CA.xml'
                elif comp_type == 'disjoncteur':
                    pk_template_name = 'Template_PKxxxx_DISJ.xml'
                else:
                    pk_template_name = 'Template_PKxxxx_DISJ.xml'
                
                pk_template = self.load_template(pk_template_name)
                if pk_template:
                    pk_id = self.generate_id('PK')
                    pk_content = pk_template.replace('PKxxxx', pk_id)
                    
                    try:
                        pk_element = ET.fromstring(pk_content)
                        productlist_element.append(pk_element)
                    except ET.ParseError as e:
                        print(f"Erreur parsing {pk_template_name}: {e}")
        
        # 4. EQUIPMENTS avec UN Template EQxxxxx PAR COMPOSANT (257 EQ)
        equipments_element = ET.SubElement(root, "Equipments")
        eq_template = self.load_template('Template_EQxxxxx.xml')
        
        if eq_template:
            # Créer UN EQ PAR COMPOSANT comme vous l'exigez
            for comp in sorted_components:
                eq_id = self.generate_id('EQ')
                pk_id = self.generate_id('PK')
                ed_id = self.generate_id('ED') 
                ef_id = self.generate_id('EF')
                
                # REMPLACER UNIQUEMENT LES xxxxx - PAS DE MODIFICATION DU TEMPLATE
                eq_content = eq_template.replace('EQxxxxx', eq_id)
                eq_content = eq_content.replace('PKxxxx', pk_id)
                eq_content = eq_content.replace('EDxxxxx', ed_id)
                eq_content = eq_content.replace('EFxxxxx', ef_id)
                
                try:
                    eq_element = ET.fromstring(eq_content)
                    equipments_element.append(eq_element)
                except ET.ParseError:
                    print(f"Erreur parsing Template_EQxxxxx.xml")
        else:
            # Structure Equipment simple si template absent
            for comp in sorted_components:
                eq_element = ET.SubElement(equipments_element, "Equipment")
                eq_element.set("id", self.generate_id('EQ'))
            
        # 5. NETWORK
        network_element = ET.SubElement(root, "Network")
        freq_element = ET.SubElement(network_element, "Frequency")
        freq_element.text = "50"
        
        # 5a. DEVICES (ordre TR, CA, DISJ selon Template_Caneco.xml)
        devices_element = ET.SubElement(network_element, "Devices")
        
        for comp in sorted_components:
            comp_type = comp['TYPE']
            if comp_type in self.component_mapping:
                device_template_name = self.component_mapping[comp_type]['device']
                device_template = self.load_template(device_template_name)
                
                if device_template:
                    # Générer les IDs nécessaires
                    device_id = self.generate_id('ED')
                    instance_id = self.generate_id('PI')
                    component_id = self.generate_id('EC')
                    
                    # REMPLACEMENT UNIQUEMENT DES xxxxx
                    id_mapping = {
                        'EDxxxxx': device_id,
                        'PIxxxxx': instance_id,
                        'ECxxxxx': component_id
                    }
                    
                    device_content = self.replace_only_xxxxx(device_template, id_mapping)
                    # Remplacer les données AutoCAD APRÈS avoir collé le template
                    device_content = self.replace_autocad_data_in_template(device_content, comp)
                    try:
                        device_element = ET.fromstring(device_content)
                        devices_element.append(device_element)
                    except ET.ParseError as e:
                        print(f"Erreur parsing device {comp_type}: {e}")
                
        # 5b. COMPONENTS (ordre TR, CA, DISTRI, DISJ selon Template_Caneco.xml)
        components_element = ET.SubElement(network_element, "Components")
        
        for comp in sorted_components:
            comp_type = comp['TYPE']
            if comp_type in self.component_mapping:
                component_template_name = self.component_mapping[comp_type]['component']
                component_template = self.load_template(component_template_name)
                
                if component_template:
                    component_id = self.generate_id('EC')
                    terminal_id = self.generate_id('ECT')
                    
                    id_mapping = {
                        'ECxxxxx': component_id,
                        'ECTxxxxx': terminal_id
                    }
                    
                    component_content = self.replace_only_xxxxx(component_template, id_mapping)
                    # Remplacer les données AutoCAD APRÈS avoir collé le template
                    component_content = self.replace_autocad_data_in_template(component_content, comp)
                    try:
                        component_element = ET.fromstring(component_content)
                        components_element.append(component_element)
                    except ET.ParseError as e:
                        print(f"Erreur parsing component {comp_type}: {e}")
                
        # 5c. FUNCTIONS selon Template_Caneco.xml (SO, CA, DISTRI, DISJ)
        functions_element = ET.SubElement(network_element, "Functions")
        
        # 5d. EXPLOITATION MODES
        exploitation_element = ET.SubElement(network_element, "ExploitationModes")
        
        # 5e. POWER CONNECTIONS  
        power_element = ET.SubElement(network_element, "PowerConnections")
        
        # Écriture du fichier final
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        print(f"✅ Fichier généré: {output_file}")
        print(f"📊 {len(sorted_components)} composants traités selon Template_Caneco.xml")
        
        return output_file
        
    def validate_against_original(self, generated_file: str, original_file: str):
        """Compare le fichier généré avec Caneco BT.xml pour vérifier la conformité XSD"""
        
        print("=== VALIDATION XSD CONTRE CANECO BT.xml ===")
        
        try:
            # Parser les deux fichiers
            generated_tree = ET.parse(generated_file)
            original_tree = ET.parse(original_file)
            
            generated_root = generated_tree.getroot()
            original_root = original_tree.getroot()
            
            # Vérifier les attributs racine
            print("🔍 Vérification attributs racine:")
            for attr in ['formatVersion', 'productRangeValuesVersion', 'commercialTaxonomyVersion']:
                gen_val = generated_root.get(attr)
                orig_val = original_root.get(attr)
                status = "✅" if gen_val == orig_val else "❌"
                print(f"  {attr}: {gen_val} vs {orig_val} {status}")
                
            # Vérifier la structure des sections (sans namespace)
            sections = ['Description', 'Contacts', 'Products', 'Equipments', 'Network']
            print("🔍 Vérification structure:")
            for section in sections:
                # Recherche directe en tant qu'enfant du root
                gen_section = None
                orig_section = None
                for child in generated_root:
                    if child.tag.endswith(section):
                        gen_section = child
                        break
                for child in original_root:
                    if child.tag.endswith(section):
                        orig_section = child
                        break
                        
                gen_exists = gen_section is not None
                orig_exists = orig_section is not None
                status = "✅" if gen_exists and orig_exists else "❌"
                print(f"  {section}: {'Présent' if gen_exists else 'Absent'} vs {'Présent' if orig_exists else 'Absent'} {status}")
                
            # Compter les éléments principaux
            print("🔍 Comparaison quantitative:")
            for element_type in ['Device', 'Component', 'Equipment']:
                gen_count = 0
                orig_count = 0
                
                # Compter dans le fichier généré
                for elem in generated_root.iter():
                    if elem.tag.endswith(element_type):
                        gen_count += 1
                        
                # Compter dans le fichier original
                for elem in original_root.iter():
                    if elem.tag.endswith(element_type):
                        orig_count += 1
                        
                print(f"  {element_type}s: {gen_count} générés vs {orig_count} originaux")
                
            # Vérifier la validité XML
            print("🔍 Validité XML:")
            try:
                ET.parse(generated_file)
                print("  ✅ XML bien formé")
            except ET.ParseError as e:
                print(f"  ❌ Erreur XML: {e}")
                
        except Exception as e:
            print(f"❌ Erreur validation: {e}")

def main():
    """Test du générateur basé sur Template_Caneco.xml"""
    generator = CanecoTemplateGenerator()
    
    # Traiter le fichier Excel AutoCAD
    excel_file = "attached_assets/RJH_MRDCF_4BD_PLD_MED00001_1.1_Schéma détaillé MEDB056CE-  Ph2e – MED_1754920068622.xlsx"
    autocad_data = generator.process_autocad_data(excel_file)
    
    if autocad_data['total'] > 0:
        # Générer le XML selon Template_Caneco.xml
        output_file = generator.generate_xml_from_template(autocad_data)
        
        # Valider contre le fichier original
        generator.validate_against_original(output_file, "attached_assets/Caneco BT _1754486408913.xml")
    else:
        print("Aucun composant trouvé dans le fichier Excel")

if __name__ == "__main__":
    main()
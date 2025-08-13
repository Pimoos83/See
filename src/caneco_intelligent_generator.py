#!/usr/bin/env python3
"""
GÉNÉRATEUR INTELLIGENT CANECO XML
Injecte les templates en fonction du type de composant et suit l'ordre exact du fichier Caneco BT.xml
"""

import pandas as pd
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from typing import Dict, List, Tuple

class CanecoIntelligentGenerator:
    """Générateur intelligent qui analyse le type de composant et utilise le bon template"""
    
    def __init__(self):
        self.component_mapping = {
            # Mapping intelligent des composants AutoCAD vers templates Caneco
            'disjoncteur': 'Template_EDxxxxx_B.xml',
            'transformateur': 'Template_EDxxxxx_A.xml', 
            'cable': 'Template_EDxxxxx_C.xml',
            'cblar': 'Template_EDxxxxx_C.xml',  # Câble spécifique
            'irve': 'Template_EDxxxxx_B.xml',   # IRVE = disjoncteur
            'protection': 'Template_EDxxxxx_B.xml',
            'td': 'Template_EDxxxxx_B.xml',     # TD = tableau disjoncteur
            'eclairage': 'Template_EDxxxxx_B.xml',
            'ecl': 'Template_EDxxxxx_B.xml'
        }
        
        self.id_counters = {
            'Device': 1,
            'Equipment': 1,
            'Function': 1,
            'Pack': 1,
            'Instance': 1,
            'Company': 1,
            'Person': 1,
            'Component': 1,
            'Terminal': 1
        }
    
    def analyze_component_type(self, designation: str, repere: str, fabricant: str = "") -> str:
        """Analyse le type de composant basé sur les données AutoCAD"""
        text_to_analyze = f"{designation} {repere} {fabricant}".lower()
        
        # Règles d'analyse intelligentes
        if any(keyword in text_to_analyze for keyword in ['disjoncteur', 'nsxm', 'nsx', 'id40', 'idt40']):
            return 'disjoncteur'
        elif any(keyword in text_to_analyze for keyword in ['transfo', 'transformateur', 'tr0', 'tr1']):
            return 'transformateur'
        elif any(keyword in text_to_analyze for keyword in ['cable', 'câble', 'cbl', 'cblar']):
            return 'cable'
        elif any(keyword in text_to_analyze for keyword in ['irve', 'borne']):
            return 'irve'
        elif any(keyword in text_to_analyze for keyword in ['td-', 'tableau']):
            return 'td'
        elif any(keyword in text_to_analyze for keyword in ['ecl', 'eclairage', 'luminaire']):
            return 'eclairage'
        else:
            # Par défaut, traiter comme disjoncteur
            return 'disjoncteur'
    
    def load_template(self, template_name: str) -> str:
        """Charge un template XML"""
        try:
            with open(template_name, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Template {template_name} non trouvé")
            return ""
    
    def generate_ids(self, component_type: str, count: int = 1) -> List[str]:
        """Génère des IDs séquentiels selon le pattern Caneco"""
        ids = []
        for i in range(count):
            if component_type == 'Device':
                id_val = f"ED{self.id_counters[component_type]:05d}"
            elif component_type == 'Equipment':
                id_val = f"EQ{self.id_counters[component_type]:05d}"
            elif component_type == 'Function':
                id_val = f"EF{self.id_counters[component_type]:05d}"
            elif component_type == 'Pack':
                id_val = f"PK{self.id_counters[component_type]:05d}"
            elif component_type == 'Instance':
                id_val = f"PI{self.id_counters[component_type]:05d}"
            elif component_type == 'Company':
                id_val = f"CC{self.id_counters[component_type]:05d}"
            elif component_type == 'Person':
                id_val = f"CP{self.id_counters[component_type]:05d}"
            elif component_type == 'Component':
                id_val = f"EC{self.id_counters[component_type]:05d}"
            elif component_type == 'Terminal':
                id_val = f"ECT{self.id_counters[component_type]:05d}"
            else:
                id_val = f"XX{self.id_counters.get(component_type, 1):05d}"
            
            ids.append(id_val)
            self.id_counters[component_type] += 1
        
        return ids
    
    def create_device_from_template(self, autocad_data: Dict, template_type: str) -> str:
        """Crée un Device XML en utilisant le bon template"""
        
        template = self.load_template(template_type)
        if not template:
            return ""
        
        # Générer les IDs nécessaires
        device_id = self.generate_ids('Device')[0]
        instance_id = self.generate_ids('Instance')[0] 
        component_id = self.generate_ids('Component')[0]
        
        # Remplacer les placeholders par les vraies données
        import pandas as pd
        functional_name = autocad_data.get('REPERE', 'UNKNOWN')
        if str(functional_name) == 'nan' or functional_name == '':
            functional_name = autocad_data.get('DESIGNATION', 'UNKNOWN')[:20]  # Limiter la longueur
        
        device_xml = template.replace('{DEVICE_ID}', device_id)
        device_xml = device_xml.replace('{PRODUCT_INSTANCE}', instance_id)
        device_xml = device_xml.replace('{COMPONENTS}', component_id)
        device_xml = device_xml.replace('{FUNCTIONAL_NAME}', functional_name)
        
        return device_xml
    
    def process_autocad_file(self, excel_file: str) -> Dict:
        """Traite le fichier Excel AutoCAD et extrait les données"""
        
        print("=== TRAITEMENT DONNÉES AUTOCAD ===")
        
        try:
            df = pd.read_excel(excel_file)
            print(f"Fichier chargé: {len(df)} lignes")
            
            # Détecter les colonnes automatiquement
            columns_mapping = {}
            for col in df.columns:
                col_lower = str(col).lower()
                if col == 'REPERE':  # Exact match
                    columns_mapping['REPERE'] = col
                elif col == 'DESIGNATION':  # Exact match
                    columns_mapping['DESIGNATION'] = col
                elif col == 'FABRICANT':  # Exact match
                    columns_mapping['FABRICANT'] = col
                elif col == 'REF':  # Exact match
                    columns_mapping['REFERENCE'] = col
            
            print(f"Colonnes détectées: {columns_mapping}")
            
            # Extraire et analyser les composants
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
                
                # Analyser le type de composant
                component_type = self.analyze_component_type(
                    component['DESIGNATION'], 
                    component['REPERE'], 
                    component['FABRICANT']
                )
                component['TYPE'] = component_type
                component['TEMPLATE'] = self.component_mapping.get(component_type, 'Template_EDxxxxx_B.xml')
                
                components.append(component)
            
            # Statistiques par type
            type_stats = {}
            for comp in components:
                comp_type = comp['TYPE']
                type_stats[comp_type] = type_stats.get(comp_type, 0) + 1
            
            print("=== STATISTIQUES COMPOSANTS ===")
            for comp_type, count in type_stats.items():
                template = self.component_mapping.get(comp_type, 'default')
                print(f"{comp_type}: {count} composants → {template}")
            
            return {
                'components': components,
                'stats': type_stats,
                'total': len(components)
            }
            
        except Exception as e:
            print(f"Erreur traitement fichier: {e}")
            return {'components': [], 'stats': {}, 'total': 0}
    
    def generate_caneco_xml(self, autocad_data: Dict, output_file: str = "generated_caneco.xml"):
        """Génère le fichier XML Caneco complet en suivant l'ordre exact"""
        
        print("=== GÉNÉRATION XML CANECO ===")
        
        components = autocad_data['components']
        if not components:
            print("Aucun composant à traiter")
            return
        
        # Charger la structure de base du fichier original
        with open('attached_assets/Caneco BT _1754486408913.xml', 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Parser le XML original pour conserver la structure
        root = ET.fromstring(original_content)
        
        # Créer la nouvelle structure en suivant l'ordre exact
        new_root = ET.Element("ElectricalProject")
        new_root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        new_root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
        new_root.set("formatVersion", "0.29")
        new_root.set("productRangeValuesVersion", "0.17")
        new_root.set("commercialTaxonomyVersion", "0.26")
        new_root.set("electricalTaxonomyVersion", "0.19")
        new_root.set("mechanicalTaxonomyVersion", "0.1")
        new_root.set("xmlns", "http://www.schneider-electric.com/electrical-distribution/exchange-format")
        
        # 1. DESCRIPTION
        description_template = self.load_template('Template_Description_A.xml')
        if description_template:
            description_element = ET.fromstring(description_template.replace(
                '{PROJECT_NAME}', 'Projet AutoCAD vers Caneco'
            ).replace(
                '{PROJECT_NUMBER}', 'AUTO001'
            ).replace(
                '{ORDER_NUMBER}', ''
            ).replace(
                '{START_DATE}', datetime.now().strftime('%Y-%m-%dT%H:%M:%S.0Z')
            ))
            new_root.append(description_element)
        
        # 2. CONTACTS
        contacts_template = self.load_template('Template_Contacts_A.xml')
        if contacts_template:
            contacts_xml = contacts_template.replace('{COMPANY_ID}', self.generate_ids('Company')[0])
            contacts_xml = contacts_xml.replace('{PERSON_ID}', self.generate_ids('Person')[0])
            contacts_xml = contacts_xml.replace('{COMPANY_NAME}', 'Société AutoCAD Import')
            contacts_xml = contacts_xml.replace('{STREET}', '')
            contacts_xml = contacts_xml.replace('{POSTAL_CODE}', '')
            contacts_xml = contacts_xml.replace('{CITY}', '')
            contacts_xml = contacts_xml.replace('{STATE}', '')
            contacts_xml = contacts_xml.replace('{COUNTRY}', 'France')
            contacts_xml = contacts_xml.replace('{PHONE}', '')
            contacts_xml = contacts_xml.replace('{LAST_NAME}', 'Utilisateur')
            contacts_xml = contacts_xml.replace('{PERSON_PHONE}', '')
            contacts_xml = contacts_xml.replace('{EMAIL}', '')
            
            contacts_element = ET.fromstring(contacts_xml)
            new_root.append(contacts_element)
        
        # 3. PRODUCTS (structure vide pour l'instant)
        products_element = ET.SubElement(new_root, "Products")
        productset_element = ET.SubElement(products_element, "ProductSet")
        
        # 4. PACKS (structure vide pour l'instant)  
        packs_element = ET.SubElement(new_root, "Packs")
        
        # 5. EQUIPMENTS
        equipments_element = ET.SubElement(new_root, "Equipments")
        equipment_template = self.load_template('Template_EQxxxxx_A.xml')
        if equipment_template:
            equipment_xml = equipment_template.replace('{EQUIPMENT_ID}', self.generate_ids('Equipment')[0])
            equipment_xml = equipment_xml.replace('{PRODUCT_PACKS}', 'PK00001')
            equipment_xml = equipment_xml.replace('{DEVICES}', 'ED00001 ED00002')
            equipment_xml = equipment_xml.replace('{FUNCTIONS}', 'EF00001')
            equipment_elem = ET.fromstring(equipment_xml)
            equipments_element.append(equipment_elem)
        
        # 6. NETWORK avec DEVICES - SECTION PRINCIPALE
        network_element = ET.SubElement(new_root, "Network")
        frequency_element = ET.SubElement(network_element, "Frequency")
        frequency_element.text = "50"
        
        devices_element = ET.SubElement(network_element, "Devices")
        
        # Générer tous les devices basés sur les composants AutoCAD
        print(f"Génération de {len(components)} devices...")
        for i, component in enumerate(components):
            device_xml = self.create_device_from_template(component, component['TEMPLATE'])
            if device_xml:
                try:
                    device_elem = ET.fromstring(device_xml)
                    devices_element.append(device_elem)
                except ET.ParseError as e:
                    print(f"Erreur parsing device {i}: {e}")
        
        # Écrire le fichier final et nettoyer les namespaces parasites
        tree = ET.ElementTree(new_root)
        ET.indent(tree, space="  ", level=0)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        # Post-traitement pour nettoyer les prefixes ns0: parasites
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Supprimer tous les préfixes ns0:, ns1:, etc.
        import re
        content = re.sub(r'<ns\d+:', '<', content)
        content = re.sub(r'</ns\d+:', '</', content)
        content = re.sub(r' xmlns:ns\d+="[^"]*"', '', content)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fichier généré: {output_file}")
        print(f"📊 {len(components)} composants traités")
        print(f"📊 Types: {autocad_data['stats']}")
        
        return output_file

def main():
    """Fonction principale"""
    generator = CanecoIntelligentGenerator()
    
    # Traiter le fichier Excel AutoCAD
    excel_file = 'attached_assets/RJH_MRDCF_4BD_PLD_MED00001_1.1_Schéma détaillé MEDB056CE-  Ph2e – MED_1754920068622.xlsx'
    autocad_data = generator.process_autocad_file(excel_file)
    
    if autocad_data['total'] > 0:
        # Générer le XML Caneco
        output_file = generator.generate_caneco_xml(autocad_data)
        print(f"\n🎉 GÉNÉRATION TERMINÉE: {output_file}")
    else:
        print("❌ Aucune donnée à traiter")

if __name__ == "__main__":
    main()

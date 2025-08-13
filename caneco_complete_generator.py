"""
Générateur XML complet basé sur l'arborescence complète Caneco
Reproduit TOUTES les sections avec les liens et dépendances correctes
"""

import xml.etree.ElementTree as ET
import chardet
import json
import logging
import pandas as pd
import os
from typing import Dict, List, Any, Optional
# from caneco_templates import CanecoTemplateEngine


class CanecoCompleteGenerator:
    """Générateur XML qui reproduit l'arborescence complète de Caneco"""
    
    def __init__(self):
        # self.template_engine = CanecoTemplateEngine()
        self.logger = logging.getLogger(__name__)
        self.autocad_data = []
        self.reference_metadata = {}
        self.complete_structure = {}
        
        # Compteurs d'IDs pour assurer la cohérence
        self.id_counters = {
            'PG': 1,  # Products
            'PK': 1,  # Packs
            'PI': 1,  # Pack Instances
            'EQ': 1,  # Equipment
            'ED': 1,  # Electrical Devices  
            'EF': 1,  # Electrical Functions
            'NC': 1,  # Network Components
            'NT': 1   # Network Terminals
        }
        
        # Tables de correspondance pour maintenir la cohérence
        self.product_to_equipment = {}
        self.equipment_to_devices = {}
        self.component_mappings = {}
        
    def load_reference_structure(self, xml_path: str):
        """Charge la structure complète du fichier de référence"""
        try:
            with open('caneco_full_analysis.json', 'r', encoding='utf-8') as f:
                self.complete_structure = json.load(f)
            
            # Charger aussi les métadonnées de base
            with open(xml_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            
            with open(xml_path, 'r', encoding=encoding) as f:
                xml_content = f.read()
            
            root = ET.fromstring(xml_content)
            self._extract_reference_metadata(root)
            
            self.logger.info("Structure complète de référence chargée")
            
        except Exception as e:
            self.logger.error(f"Erreur chargement structure: {str(e)}")
            raise
    
    def _extract_reference_metadata(self, root: ET.Element):
        """Extrait les métadonnées essentielles du fichier de référence"""
        ns = '{http://www.schneider-electric.com/electrical-distribution/exchange-format}'
        
        self.reference_metadata = {
            'namespace': 'http://www.schneider-electric.com/electrical-distribution/exchange-format',
            'root_attributes': dict(root.attrib),
            'description': self._extract_description(root, ns),
            'contacts': self._extract_contacts(root, ns)
        }
    
    def _extract_description(self, root: ET.Element, ns: str) -> Dict[str, str]:
        """Extrait la section Description"""
        desc_elem = root.find(f'{ns}Description')
        if desc_elem is None:
            return {}
        
        description = {}
        for child in desc_elem:
            tag_name = child.tag.replace(ns, '')
            description[tag_name] = child.text or ''
        
        return description
    
    def _extract_contacts(self, root: ET.Element, ns: str) -> Dict[str, Any]:
        """Extrait la section Contacts"""
        contacts_elem = root.find(f'{ns}Contacts')
        if contacts_elem is None:
            return {}
        
        contacts = {'companies': [], 'persons': []}
        
        for company in contacts_elem.findall(f'{ns}Company'):
            company_data = {'id': company.get('id'), 'details': {}}
            name_elem = company.find(f'{ns}Name')
            if name_elem is not None:
                company_data['details']['name'] = name_elem.text or ''
            contacts['companies'].append(company_data)
        
        for person in contacts_elem.findall(f'{ns}Person'):
            person_data = {'id': person.get('id'), 'details': {}}
            contacts['persons'].append(person_data)
        
        return contacts
    
    def load_autocad_data(self, file_path: str):
        """Charge et analyse les données AutoCAD depuis TXT ou Excel"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.xlsx', '.xls']:
                self._load_excel_data(file_path)
            elif file_ext == '.txt':
                self._load_txt_data(file_path)
            else:
                raise ValueError(f"Format de fichier non supporté: {file_ext}")
            
            # Analyser avec templates
            self._analyze_with_templates()
            
            self.logger.info(f"Données AutoCAD chargées: {len(self.autocad_data)} composants")
            
        except Exception as e:
            self.logger.error(f"Erreur chargement AutoCAD: {str(e)}")
            raise
    
    def _load_excel_data(self, excel_path: str):
        """Charge les données depuis un fichier Excel"""
        try:
            # Lire le fichier Excel
            df = pd.read_excel(excel_path)
            
            # Nettoyer les noms de colonnes
            df.columns = df.columns.str.strip()
            
            self.autocad_data = []
            
            # Détecter automatiquement les colonnes importantes
            possible_id_cols = ['ID', 'HEX_ID', 'Hex ID', 'Code', 'Reference']
            possible_desc_cols = ['Description', 'Designation', 'Name', 'Nom', 'Libelle']
            possible_spec_cols = ['Specifications', 'Details', 'Caracteristiques', 'Properties']
            
            id_col = None
            desc_col = None
            spec_col = None
            
            # Rechercher les colonnes par nom
            for col in df.columns:
                col_upper = col.upper()
                if any(pid.upper() in col_upper for pid in possible_id_cols) and id_col is None:
                    id_col = col
                elif any(pdesc.upper() in col_upper for pdesc in possible_desc_cols) and desc_col is None:
                    desc_col = col
                elif any(pspec.upper() in col_upper for pspec in possible_spec_cols) and spec_col is None:
                    spec_col = col
            
            # Si pas trouvé, utiliser les premières colonnes
            if id_col is None and len(df.columns) > 0:
                id_col = df.columns[0]
            if desc_col is None and len(df.columns) > 1:
                desc_col = df.columns[1]
            if spec_col is None and len(df.columns) > 2:
                spec_col = df.columns[2]
            
            # Traiter chaque ligne
            for index, row in df.iterrows():
                if pd.isna(row.get(id_col)) and pd.isna(row.get(desc_col)):
                    continue  # Ignorer les lignes vides
                
                record = {
                    'hex_id': str(row.get(id_col, '')).strip() if not pd.isna(row.get(id_col)) else '',
                    'description': str(row.get(desc_col, '')).strip() if not pd.isna(row.get(desc_col)) else '',
                    'specifications': str(row.get(spec_col, '')).strip() if spec_col and not pd.isna(row.get(spec_col)) else ''
                }
                
                # Ajouter toutes les autres colonnes comme spécifications supplémentaires
                additional_specs = []
                for col in df.columns:
                    if col not in [id_col, desc_col, spec_col] and not pd.isna(row.get(col)):
                        additional_specs.append(f"{col}: {row[col]}")
                
                if additional_specs:
                    if record['specifications']:
                        record['specifications'] += ' | ' + ' | '.join(additional_specs)
                    else:
                        record['specifications'] = ' | '.join(additional_specs)
                
                if record['hex_id'] or record['description']:
                    self.autocad_data.append(record)
            
            self.logger.info(f"Fichier Excel lu: {len(self.autocad_data)} enregistrements trouvés")
            
        except Exception as e:
            self.logger.error(f"Erreur lecture Excel: {str(e)}")
            raise
    
    def _load_txt_data(self, txt_path: str):
        """Charge les données depuis un fichier TXT"""
        try:
            with open(txt_path, 'rb') as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding'] or 'utf-8'
            
            with open(txt_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            self.autocad_data = []
            current_record = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_record:
                        self.autocad_data.append(current_record)
                        current_record = {}
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 2:
                    if 'hex_id' not in current_record:
                        current_record['hex_id'] = parts[0]
                        current_record['description'] = parts[1] if len(parts) > 1 else ''
                        current_record['specifications'] = '\t'.join(parts[2:]) if len(parts) > 2 else ''
                    else:
                        current_record['specifications'] += ' ' + line
                else:
                    if 'description' not in current_record:
                        current_record['description'] = line
                    else:
                        current_record['specifications'] = current_record.get('specifications', '') + ' ' + line
            
            if current_record:
                self.autocad_data.append(current_record)
            
            self.logger.info(f"Fichier TXT lu: {len(self.autocad_data)} enregistrements trouvés")
            
        except Exception as e:
            self.logger.error(f"Erreur lecture TXT: {str(e)}")
            raise
    
    def _analyze_with_templates(self):
        """Analyse les données AutoCAD avec les templates"""
        matched = 0
        
        for record in self.autocad_data:
            template = self.template_engine.find_best_template(record)
            
            if template:
                record['template'] = template
                record['component_type'] = self._determine_component_type(template)
                matched += 1
                
                # Pré-allouer les IDs pour maintenir la cohérence
                record['product_id'] = f"PG{self.id_counters['PG']:05d}"
                self.id_counters['PG'] += 1
                
                if template.group_id == 'ECD_DISJONCTEUR':
                    record['pack_id'] = f"PK{self.id_counters['PK']:05d}"
                    record['instance_id'] = f"PI{self.id_counters['PI']:05d}"
                    self.id_counters['PK'] += 1
                    self.id_counters['PI'] += 1
                
                # Créer les mappings pour les sections liées
                self._create_mappings_for_record(record)
                
            else:
                record['template'] = None
                record['component_type'] = 'unknown'
        
        self.logger.info(f"Templates trouvés: {matched}/{len(self.autocad_data)} composants")
    
    def _determine_component_type(self, template) -> str:
        """Détermine le type de composant"""
        if template.group_id == 'ECD_DISJONCTEUR':
            return 'circuit_breaker'
        elif template.group_id == 'ECD_TRANSFORMATEUR':
            return 'transformer'
        elif template.group_id == 'ECD_JEU_DE_BARRE':
            return 'busbar'
        else:
            return 'unknown'
    
    def _create_mappings_for_record(self, record: Dict[str, Any]):
        """Crée les mappings entre sections pour un enregistrement"""
        product_id = record['product_id']
        
        # Equipment mapping
        equipment_id = f"EQ{self.id_counters['EQ']:05d}"
        self.product_to_equipment[product_id] = equipment_id
        self.id_counters['EQ'] += 1
        
        # Electrical devices mapping  
        device_id = f"ED{self.id_counters['ED']:05d}"
        function_id = f"EF{self.id_counters['EF']:05d}"
        
        self.equipment_to_devices[equipment_id] = {
            'devices': [device_id],
            'functions': [function_id]
        }
        
        self.id_counters['ED'] += 1
        self.id_counters['EF'] += 1
        
        # Network component mapping
        component_id = f"NC{self.id_counters['NC']:05d}"
        terminal_ids = [
            f"NT{self.id_counters['NT']:05d}",
            f"NT{self.id_counters['NT']+1:05d}"
        ]
        
        self.component_mappings[product_id] = {
            'equipment_id': equipment_id,
            'device_id': device_id,
            'function_id': function_id,
            'component_id': component_id,
            'terminal_ids': terminal_ids
        }
        
        self.id_counters['NC'] += 1
        self.id_counters['NT'] += 2
        
        record['mappings'] = self.component_mappings[product_id]
    
    def generate_complete_xml(self, output_path: str) -> bool:
        """Génère un XML complet avec TOUTES les sections requises"""
        try:
            # Créer la structure XML de base
            root = ET.Element('ElectricalProject')
            
            # Attributs de la racine dans l'ordre exact du fichier original
            root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            root.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
            root.set('formatVersion', '0.29')
            root.set('productRangeValuesVersion', '0.17')
            root.set('commercialTaxonomyVersion', '0.26')
            root.set('electricalTaxonomyVersion', '0.19')
            root.set('mechanicalTaxonomyVersion', '0.1')
            root.set('xmlns', 'http://www.schneider-electric.com/electrical-distribution/exchange-format')
            
            # Les attributs de version sont déjà définis ci-dessus dans le bon ordre
            
            # 1. Section Description
            self._add_description_section(root)
            
            # 2. Section Contacts  
            self._add_contacts_section(root)
            
            # 3. Section Products (ProductSet + ProductList)
            self._add_products_section(root)
            
            # 4. Section Equipments (NOUVELLE - liée aux produits)
            self._add_equipments_section(root)
            
            # 5. Section Network (NOUVELLE - composants électriques)
            self._add_network_section(root)
            
            # Formater et écrire avec correction du format
            self._indent_xml(root)
            tree = ET.ElementTree(root)
            
            # Écrire d'abord dans un fichier temporaire
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.xml') as temp_file:
                temp_path = temp_file.name
            
            tree.write(temp_path, encoding='utf-8', xml_declaration=True)
            
            # Lire et corriger le format XML
            with open(temp_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # Corriger les éléments auto-fermants spécifiques pour qu'ils utilisent la forme explicite
            xml_content = self._fix_xml_format(xml_content)
            
            # Écrire le fichier final
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            # Nettoyer le fichier temporaire
            import os
            os.unlink(temp_path)
            
            self.logger.info("XML complet généré avec toutes les sections")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur génération XML complet: {str(e)}")
            return False
    
    def _add_equipments_section(self, root: ET.Element):
        """Ajoute la section Equipments liée aux produits"""
        equipments = ET.SubElement(root, 'Equipments')
        
        for record in self.autocad_data:
            if record.get('template') and record.get('mappings'):
                equipment = ET.SubElement(equipments, 'Equipment')
                equipment.set('id', record['mappings']['equipment_id'])
                
                # Commercial properties
                commercial = ET.SubElement(equipment, 'Commercial')
                pack_refs = []
                if record.get('pack_id'):
                    pack_refs.append(record['pack_id'])
                commercial.set('ProductPacks', ' '.join(pack_refs))
                
                comm_props = ET.SubElement(commercial, 'Properties')
                
                template = record['template']
                icc_value = template.characteristics.get('PRT_ICC', '16')
                cal_value = template.characteristics.get('PRT_CAL', '32.00').replace('.00', '')
                
                breaking_cap_elem = ET.SubElement(comm_props, 'BreakingCapacity')
                breaking_cap_elem.text = icc_value
                rating_elem = ET.SubElement(comm_props, 'Rating')
                rating_elem.text = cal_value
                
                # Electrical properties
                electrical = ET.SubElement(equipment, 'Electrical')
                electrical.set('Devices', record['mappings']['device_id'])
                electrical.set('Functions', record['mappings']['function_id'])
                
                elec_props = ET.SubElement(electrical, 'Properties')
                earthing_elem = ET.SubElement(elec_props, 'EarthingSystem')
                earthing_elem.text = 'TN'
                freq_elem = ET.SubElement(elec_props, 'Frequency')
                freq_elem.text = '50'
                
                switchboard = ET.SubElement(electrical, 'Switchboard')
                sw_props = ET.SubElement(switchboard, 'Properties')
                
                # Equipment properties
                eq_props = ET.SubElement(equipment, 'Properties')
                name_elem = ET.SubElement(eq_props, 'Name')
                name_elem.text = record.get('description', 'Equipment')
    
    def _add_network_section(self, root: ET.Element):
        """Ajoute la section Network avec composants électriques"""
        network = ET.SubElement(root, 'Network')
        components = ET.SubElement(network, 'Components')
        
        for record in self.autocad_data:
            if record.get('template') and record.get('mappings'):
                component = ET.SubElement(components, 'Component')
                component.set('id', record['mappings']['component_id'])
                
                # Functional name
                func_name = ET.SubElement(component, 'FunctionalName')
                func_name.text = record.get('description', 'Component')
                
                # Terminals
                terminals = ET.SubElement(component, 'Terminals')
                
                for i, terminal_id in enumerate(record['mappings']['terminal_ids']):
                    terminal = ET.SubElement(terminals, 'Terminal')
                    terminal.set('id', terminal_id)
                    
                    polarity_elem = ET.SubElement(terminal, 'Polarity')
                    polarity_elem.text = str(i + 1)
                    earthing_mgmt_elem = ET.SubElement(terminal, 'SystemEarthingManagement')
                    earthing_mgmt_elem.text = 'Active'
                    voltage_elem = ET.SubElement(terminal, 'Voltage')
                    voltage_elem.text = '400'
                
                # Type de composant électrique selon template
                template = record['template']
                if template.group_id == 'ECD_DISJONCTEUR':
                    # Composant de protection
                    protection_elem = ET.SubElement(component,
                        '{http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy}ProtectionComponent')
                    
                    prot_props = ET.SubElement(protection_elem,
                        '{http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy}Properties')
                
                elif template.group_id == 'ECD_TRANSFORMATEUR':
                    # Composant de distribution
                    dist_elem = ET.SubElement(component,
                        '{http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy}DistributionComponent')
                    
                    dist_props = ET.SubElement(dist_elem,
                        '{http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy}Properties')
    
    def _add_description_section(self, root: ET.Element):
        """Ajoute la section Description"""
        desc = ET.SubElement(root, 'Description')
        
        desc_data = self.reference_metadata.get('description', {})
        
        name_elem = ET.SubElement(desc, 'Name')
        name_elem.text = desc_data.get('Name', 'Caneco BT - Etap Roadshow 2023')
        
        # Utiliser la forme exacte du fichier original
        number_elem = ET.SubElement(desc, 'Number')
        number_elem.text = ''  # Élément explicitement vide comme dans l'original
        
        # OrderNumber utilise la forme auto-fermante dans l'original
        order_elem = ET.SubElement(desc, 'OrderNumber')
        # Laissé None pour être converti en auto-fermant par le post-traitement
        
        date_elem = ET.SubElement(desc, 'StartDate')
        date_elem.text = desc_data.get('StartDate', '2023-10-10T00:00:00.0Z')
    
    def _add_contacts_section(self, root: ET.Element):
        """Ajoute la section Contacts"""
        contacts = ET.SubElement(root, 'Contacts')
        
        company = ET.SubElement(contacts, 'Company')
        company.set('id', 'CC00001')
        
        address = ET.SubElement(company, 'Address')
        street_elem = ET.SubElement(address, 'Street')
        street_elem.text = ''
        postal_elem = ET.SubElement(address, 'PostalCode')
        postal_elem.text = ''
        city_elem = ET.SubElement(address, 'City')
        city_elem.text = ''
        state_elem = ET.SubElement(address, 'State')
        # State doit être auto-fermant dans l'original
        country_elem = ET.SubElement(address, 'Country')
        country_elem.text = 'France'
        
        phones = ET.SubElement(company, 'PhoneNumbers')
        phone = ET.SubElement(phones, 'Phone')
        phone.set('Kind', 'main')
        phone.text = ''
        
        name_elem = ET.SubElement(company, 'Name')
        name_elem.text = 'Authorized user'
        
        person = ET.SubElement(contacts, 'Person')
        person.set('id', 'CP00001')
        
        lastname_elem = ET.SubElement(person, 'LastName')
        lastname_elem.text = ''
        
        person_phones = ET.SubElement(person, 'PhoneNumbers')
        person_phone = ET.SubElement(person_phones, 'Phone')
        person_phone.set('Kind', 'main')
        person_phone.text = ''
        
        email_elem = ET.SubElement(person, 'Email')
        email_elem.text = ''
        
        company_ref = ET.SubElement(person, 'Company')
        company_ref.set('id', 'CC00001')
    
    def _add_products_section(self, root: ET.Element):
        """Ajoute la section Products (ProductSet + ProductList)"""
        products = ET.SubElement(root, 'Products')
        
        # ProductSet
        product_set = ET.SubElement(products, 'ProductSet')
        
        for record in self.autocad_data:
            template = record.get('template')
            if template:
                self._add_product_to_set(product_set, record, template)
        
        # ProductList avec packs commerciaux
        product_list = ET.SubElement(products, 'ProductList')
        
        for record in self.autocad_data:
            template = record.get('template')
            if template and template.group_id == 'ECD_DISJONCTEUR':
                self._add_pack_to_list(product_list, record, template)
    
    def _add_product_to_set(self, product_set: ET.Element, record: Dict[str, Any], template):
        """Ajoute un produit au ProductSet"""
        product = ET.SubElement(product_set, 'Product')
        product.set('id', record['product_id'])
        
        # Name
        name_elem = ET.SubElement(product, 'Name')
        name_elem.text = self._determine_product_name(record, template)
        
        # Seed
        seed = ET.SubElement(product, 'Seed')
        seed.set('Name', '')
        seed.set('Type', 'RAPSODY')
        seed.set('GroupId', template.group_id)
        seed.set('ItemId', template.item_id)
        
        # Content with Characteristics
        content = ET.SubElement(product, 'Content')
        characteristics = ET.SubElement(content, 'Characteristics')
        
        # Ajouter les caractéristiques dans l'ordre exact
        char_list = self.template_engine.generate_characteristics_in_order(template, record)
        
        for char_id, value in char_list:
            char_elem = ET.SubElement(characteristics, 'Characteristic')
            
            name_elem = ET.SubElement(char_elem, 'Name')
            name_elem.text = ''
            id_elem = ET.SubElement(char_elem, 'Id')
            id_elem.text = char_id
            
            set_values = ET.SubElement(char_elem, 'SetValues')
            value_elem = ET.SubElement(set_values, 'Value')
            
            value_name_elem = ET.SubElement(value_elem, 'Name')
            value_name_elem.text = ''
            value_id_elem = ET.SubElement(value_elem, 'Id')
            value_id_elem.text = str(value)
    
    def _add_pack_to_list(self, product_list: ET.Element, record: Dict[str, Any], template):
        """Ajoute un pack au ProductList avec structure complète"""
        pack = ET.SubElement(product_list, 'Pack')
        pack.set('id', record['pack_id'])
        pack.set('Descriptor', record['product_id'])
        
        product = ET.SubElement(pack, 'Product')
        
        # CircuitBreaker avec namespace commercial exact
        circuit_breaker_outer = ET.SubElement(product, 
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}CircuitBreaker')
        
        circuit_breaker = ET.SubElement(circuit_breaker_outer,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}CircuitBreaker')
        
        self._populate_circuit_breaker_details(circuit_breaker, template)
        
        # TripUnit obligatoire
        trip_unit = ET.SubElement(circuit_breaker_outer,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}TripUnit')
        
        self._populate_trip_unit_details(trip_unit, template)
        
        # Instances
        instances = ET.SubElement(pack, 'Instances')
        instance = ET.SubElement(instances, 'Instance')
        instance.set('id', record['instance_id'])
    
    def _populate_circuit_breaker_details(self, circuit_breaker: ET.Element, template):
        """Remplit les détails du CircuitBreaker"""
        ns = '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}'
        
        manufacturer_elem = ET.SubElement(circuit_breaker, f'{ns}Manufacturer')
        manufacturer_elem.text = 'Schneider Electric'
        
        ref_value = template.characteristics.get('PRT_REF', 'NSXmE')
        if 'NSX' in ref_value:
            range_name = 'NSX'
        elif 'iDT' in ref_value:
            range_name = 'Acti9 iC60'
        else:
            range_name = 'NSX'
        
        range_elem = ET.SubElement(circuit_breaker, f'{ns}Range')
        range_elem.text = range_name
        designation_elem = ET.SubElement(circuit_breaker, f'{ns}Designation')
        designation_elem.text = 'C1001H'
        range_display_elem = ET.SubElement(circuit_breaker, f'{ns}RangeDisplayName')
        range_display_elem.text = ''
        designation_display_elem = ET.SubElement(circuit_breaker, f'{ns}DesignationDisplayName')
        designation_display_elem.text = ref_value
        voltage_range_elem = ET.SubElement(circuit_breaker, f'{ns}VoltageRange')
        voltage_range_elem.text = ''
        
        cal_value = template.characteristics.get('PRT_CAL', '32.00').replace('.00', '')
        rating_elem = ET.SubElement(circuit_breaker, f'{ns}Rating')
        rating_elem.text = cal_value
        
        standard_type_elem = ET.SubElement(circuit_breaker, f'{ns}StandardTypeOf')
        standard_type_elem.text = 'Industrial'
        
        poles_value = template.characteristics.get('PRT_NBPPP', '4P4D')
        switched_poles = poles_value.split('P')[0] + 'P' if 'P' in poles_value else '4P'
        protected_poles = poles_value.split('P')[1].replace('D', '') if 'P' in poles_value and 'D' in poles_value else '3'
        
        switched_pole_elem = ET.SubElement(circuit_breaker, f'{ns}SwitchedPoleCount')
        switched_pole_elem.text = switched_poles
        protected_pole_elem = ET.SubElement(circuit_breaker, f'{ns}ProtectedPoleCount')
        protected_pole_elem.text = protected_poles
        
        icc_value = template.characteristics.get('PRT_ICC', '16')
        breaking_capacity_elem = ET.SubElement(circuit_breaker, f'{ns}BreakingCapacity')
        breaking_capacity_elem.text = icc_value
        
        # Settings
        settings = ET.SubElement(circuit_breaker, f'{ns}Settings')
        cal_float = float(template.characteristics.get('PRT_CAL', '32.00'))
        
        ild_elem = ET.SubElement(settings, f'{ns}Ild')
        ild_elem.text = f'{cal_float * 0.92:.1f}'
        tld_elem = ET.SubElement(settings, f'{ns}Tld')
        tld_elem.text = '16'
        isd_elem = ET.SubElement(settings, f'{ns}Isd')
        isd_elem.text = f'{cal_float * 9.2:.0f}'
        tsd_elem = ET.SubElement(settings, f'{ns}Tsd')
        tsd_elem.text = '0.02'
        iid_elem = ET.SubElement(settings, f'{ns}Iid')
        iid_elem.text = f'{cal_float * 11:.0f}'
        ti_elem = ET.SubElement(settings, f'{ns}Ti')
        ti_elem.text = '0'
    
    def _populate_trip_unit_details(self, trip_unit: ET.Element, template):
        """Remplit les détails du TripUnit"""
        ns = '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}'
        
        manufacturer_elem = ET.SubElement(trip_unit, f'{ns}Manufacturer')
        manufacturer_elem.text = 'Schneider Electric'
        
        ref_value = template.characteristics.get('PRT_REF', 'NSXmE')
        range_name = 'NSX' if 'NSX' in ref_value else 'Acti9 iC60'
        range_elem = ET.SubElement(trip_unit, f'{ns}Range')
        range_elem.text = range_name
        
        cdecl_value = template.characteristics.get('PRT_CDECL', 'TM-D')
        designation_elem = ET.SubElement(trip_unit, f'{ns}Designation')
        designation_elem.text = cdecl_value
        range_display_elem = ET.SubElement(trip_unit, f'{ns}RangeDisplayName')
        range_display_elem.text = ''
        designation_display_elem = ET.SubElement(trip_unit, f'{ns}DesignationDisplayName')
        designation_display_elem.text = cdecl_value
        voltage_range_elem = ET.SubElement(trip_unit, f'{ns}VoltageRange')
        voltage_range_elem.text = ''
        
        poles_value = template.characteristics.get('PRT_NBPPP', '4P4D')
        protected_poles = poles_value.split('P')[1].replace('D', '') if 'P' in poles_value and 'D' in poles_value else '3'
        protected_pole_elem = ET.SubElement(trip_unit, f'{ns}ProtectedPoleCount')
        protected_pole_elem.text = protected_poles
        
        protection_elem = ET.SubElement(trip_unit, f'{ns}Protection')
        protection_elem.text = 'CircuitBreaker'
        
        cal_value = template.characteristics.get('PRT_CAL', '32.00').replace('.00', '')
        rating_elem = ET.SubElement(trip_unit, f'{ns}Rating')
        rating_elem.text = cal_value
    
    def _determine_product_name(self, record: Dict[str, Any], template) -> str:
        """Détermine le nom du produit"""
        autocad_name = record.get('description', '').strip()
        
        if 'irve' in autocad_name.lower():
            return 'ALIM TD IRVE'
        elif 'tr' in autocad_name.lower() and '01' in autocad_name:
            return 'TR01'
        elif 'ecl' in autocad_name.lower():
            return 'TD1-ECL 1'
        
        return template.name_pattern
    
    def _indent_xml(self, elem: ET.Element, level: int = 0):
        """Ajoute une indentation propre au XML sans affecter le contenu des éléments"""
        indent = "\n" + level * "  "
        if len(elem):
            # Ne pas modifier le texte des éléments qui ont déjà du contenu
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent_xml(child, level + 1)
            # Corriger l'indentation du dernier enfant
            if len(elem) > 0 and (not elem[-1].tail or not elem[-1].tail.strip()):
                elem[-1].tail = indent
        else:
            # Pour les éléments vides, ne pas ajouter d'espaces au texte
            if elem.text is None:
                elem.text = ""
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent
    
    def _fix_xml_format(self, xml_content: str) -> str:
        """Corrige le format XML pour correspondre exactement au fichier Caneco original"""
        import re
        
        # Liste des éléments qui doivent utiliser la forme explicite même quand vides
        elements_to_fix = [
            'Phone', 'Name', 'LastName', 'Email', 'Street', 'PostalCode', 'City', 'State', 'Country',
            'Manufacturer', 'Range', 'Designation', 'RangeDisplayName', 'DesignationDisplayName', 
            'VoltageRange', 'Rating', 'StandardTypeOf', 'SwitchedPoleCount', 'ProtectedPoleCount',
            'BreakingCapacity', 'EarthingSystem', 'Frequency', 'Polarity', 'SystemEarthingManagement',
            'Voltage', 'Protection', 'Ild', 'Tld', 'Isd', 'Tsd', 'Iid', 'Ti', 'FunctionalName'
        ]
        
        # Pour chaque élément dans la liste, convertir de <Element .../> vers <Element ...></Element>
        for element in elements_to_fix:
            # Pattern pour les éléments auto-fermants avec attributs
            pattern = rf'<{element}(\s+[^>]*?)\s*/>'
            replacement = rf'<{element}\1></{element}>'
            xml_content = re.sub(pattern, replacement, xml_content)
            
            # Pattern pour les éléments auto-fermants sans attributs
            pattern = rf'<{element}\s*/>'
            replacement = rf'<{element}></{element}>'
            xml_content = re.sub(pattern, replacement, xml_content)
        
        # Nettoyer les espaces indésirables dans les balises vides
        # Exemple: <City > devient <City>
        xml_content = re.sub(r'<([^>]+)\s+>', r'<\1>', xml_content)
        
        # Nettoyer les espaces avant les balises de fermeture
        # Exemple: <City ></City> devient <City></City>
        xml_content = re.sub(r'<([^/>]+)\s+></([^>]+)>', r'<\1></\2>', xml_content)
        
        # CORRECTION CRITIQUE pour XSD : Convertir certains éléments en auto-fermants comme dans l'original
        # OrderNumber et State doivent être auto-fermants pour correspondre au schéma XSD
        xml_content = re.sub(r'<OrderNumber></OrderNumber>', '<OrderNumber/>', xml_content)
        xml_content = re.sub(r'<State></State>', '<State/>', xml_content)
        
        return xml_content
    
    def validate_xml(self, xml_path: str) -> bool:
        """Valide le XML généré"""
        try:
            ET.parse(xml_path)
            self.logger.info("XML complet validé")
            return True
        except ET.ParseError as e:
            self.logger.error(f"Erreur validation XML: {str(e)}")
            return False
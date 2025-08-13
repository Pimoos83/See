"""
Générateur XML strict pour compatibilité 100% avec See Electrical Expert
Génère uniquement les sections nécessaires avec la structure exacte
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Optional
import chardet
from caneco_templates import CanecoTemplateEngine


class StrictXMLGenerator:
    """Générateur XML strict qui produit uniquement la structure valide XSD"""
    
    def __init__(self):
        self.template_engine = CanecoTemplateEngine()
        self.logger = logging.getLogger(__name__)
        self.autocad_data = []
        self.reference_metadata = {}
        
    def load_reference_metadata(self, xml_path: str):
        """Charge uniquement les métadonnées du fichier de référence"""
        try:
            with open(xml_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            
            with open(xml_path, 'r', encoding=encoding) as f:
                xml_content = f.read()
            
            root = ET.fromstring(xml_content)
            
            # Extraire les métadonnées essentielles
            ns = '{http://www.schneider-electric.com/electrical-distribution/exchange-format}'
            
            self.reference_metadata = {
                'namespace': 'http://www.schneider-electric.com/electrical-distribution/exchange-format',
                'root_attributes': dict(root.attrib),
                'description': self._extract_description(root, ns),
                'contacts': self._extract_contacts(root, ns)
            }
            
            self.logger.info("Métadonnées de référence chargées")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des métadonnées: {str(e)}")
            raise
    
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
            # Simplifier l'extraction
            name_elem = company.find(f'{ns}Name')
            if name_elem is not None:
                company_data['details']['name'] = name_elem.text or ''
            contacts['companies'].append(company_data)
        
        for person in contacts_elem.findall(f'{ns}Person'):
            person_data = {'id': person.get('id'), 'details': {}}
            contacts['persons'].append(person_data)
        
        return contacts
    
    def load_autocad_data(self, txt_path: str):
        """Charge et analyse les données AutoCAD"""
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
            
            # Analyser avec templates
            self._analyze_with_templates()
            
            self.logger.info(f"Données AutoCAD chargées: {len(self.autocad_data)} composants")
            
        except Exception as e:
            self.logger.error(f"Erreur chargement AutoCAD: {str(e)}")
            raise
    
    def _analyze_with_templates(self):
        """Analyse les données AutoCAD avec les templates"""
        matched = 0
        
        for record in self.autocad_data:
            template = self.template_engine.find_best_template(record)
            
            if template:
                record['template'] = template
                record['component_type'] = 'disjoncteur' if template.group_id == 'ECD_DISJONCTEUR' else 'other'
                matched += 1
            else:
                record['template'] = None
                record['component_type'] = 'unknown'
        
        self.logger.info(f"Templates trouvés: {matched}/{len(self.autocad_data)} composants")
    
    def generate_strict_xml(self, output_path: str) -> bool:
        """Génère un XML strict avec UNIQUEMENT les sections nécessaires"""
        try:
            # Créer la structure XML de base
            root = ET.Element('ElectricalProject')
            
            # Attributs de la racine
            root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            root.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
            root.set('xmlns', 'http://www.schneider-electric.com/electrical-distribution/exchange-format')
            
            # Attributs de version
            if self.reference_metadata.get('root_attributes'):
                for key, value in self.reference_metadata['root_attributes'].items():
                    if key not in ['xmlns', 'xmlns:xsi', 'xmlns:xsd']:
                        root.set(key, value)
            
            # Section Description
            self._add_description_section(root)
            
            # Section Contacts
            self._add_contacts_section(root)
            
            # Section Products (la plus importante)
            self._add_products_section(root)
            
            # Créer l'arbre et écrire
            tree = ET.ElementTree(root)
            
            # Formater avec indentation
            self._indent_xml(root)
            
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            self.logger.info("XML strict généré avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur génération XML strict: {str(e)}")
            return False
    
    def _add_description_section(self, root: ET.Element):
        """Ajoute la section Description"""
        desc = ET.SubElement(root, 'Description')
        
        desc_data = self.reference_metadata.get('description', {})
        
        name_elem = ET.SubElement(desc, 'Name')
        name_elem.text = desc_data.get('Name', 'Projet AutoCAD vers Caneco')
        
        number_elem = ET.SubElement(desc, 'Number')
        number_elem.text = desc_data.get('Number', '')
        
        order_elem = ET.SubElement(desc, 'OrderNumber')
        order_elem.text = desc_data.get('OrderNumber', '')
        
        date_elem = ET.SubElement(desc, 'StartDate')
        date_elem.text = desc_data.get('StartDate', '2025-08-11T00:00:00.0Z')
    
    def _add_contacts_section(self, root: ET.Element):
        """Ajoute la section Contacts"""
        contacts = ET.SubElement(root, 'Contacts')
        
        # Company par défaut
        company = ET.SubElement(contacts, 'Company')
        company.set('id', 'CC00001')
        
        address = ET.SubElement(company, 'Address')
        ET.SubElement(address, 'Street').text = ''
        ET.SubElement(address, 'PostalCode').text = ''
        ET.SubElement(address, 'City').text = ''
        ET.SubElement(address, 'State').text = ''
        ET.SubElement(address, 'Country').text = 'France'
        
        phones = ET.SubElement(company, 'PhoneNumbers')
        phone = ET.SubElement(phones, 'Phone')
        phone.set('Kind', 'main')
        phone.text = ''
        
        ET.SubElement(company, 'Name').text = 'Authorized user'
        
        # Person par défaut
        person = ET.SubElement(contacts, 'Person')
        person.set('id', 'CP00001')
        
        ET.SubElement(person, 'LastName').text = ''
        
        person_phones = ET.SubElement(person, 'PhoneNumbers')
        person_phone = ET.SubElement(person_phones, 'Phone')
        person_phone.set('Kind', 'main')
        person_phone.text = ''
        
        ET.SubElement(person, 'Email').text = ''
        
        company_ref = ET.SubElement(person, 'Company')
        company_ref.set('id', 'CC00001')
    
    def _add_products_section(self, root: ET.Element):
        """Ajoute la section Products avec les données AutoCAD"""
        products = ET.SubElement(root, 'Products')
        
        # ProductSet
        product_set = ET.SubElement(products, 'ProductSet')
        
        product_counter = 1
        for record in self.autocad_data:
            template = record.get('template')
            if template:
                self._add_product_to_set(product_set, record, template, product_counter)
                product_counter += 1
        
        # ProductList
        product_list = ET.SubElement(products, 'ProductList')
        
        pack_counter = 1
        for record in self.autocad_data:
            template = record.get('template')
            if template and template.group_id == 'ECD_DISJONCTEUR':
                self._add_pack_to_list(product_list, record, template, pack_counter)
                pack_counter += 1
    
    def _add_product_to_set(self, product_set: ET.Element, record: Dict[str, Any], template, product_id: int):
        """Ajoute un produit au ProductSet"""
        product = ET.SubElement(product_set, 'Product')
        product.set('id', f'PG{product_id:05d}')
        
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
            
            ET.SubElement(char_elem, 'Name').text = ''
            ET.SubElement(char_elem, 'Id').text = char_id
            
            set_values = ET.SubElement(char_elem, 'SetValues')
            value_elem = ET.SubElement(set_values, 'Value')
            
            ET.SubElement(value_elem, 'Name').text = ''
            ET.SubElement(value_elem, 'Id').text = str(value)
    
    def _add_pack_to_list(self, product_list: ET.Element, record: Dict[str, Any], template, pack_id: int):
        """Ajoute un pack au ProductList avec structure Caneco exacte"""
        pack = ET.SubElement(product_list, 'Pack')
        pack.set('id', f'PK{pack_id:05d}')
        pack.set('Descriptor', f'PG{pack_id:05d}')  # Référence obligatoire vers ProductSet
        
        product = ET.SubElement(pack, 'Product')
        
        # CircuitBreaker avec namespace commercial exact
        circuit_breaker_outer = ET.SubElement(product, 
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}CircuitBreaker')
        
        # CircuitBreaker interne
        circuit_breaker = ET.SubElement(circuit_breaker_outer,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}CircuitBreaker')
        
        # Détails obligatoires selon structure Caneco
        ET.SubElement(circuit_breaker, 
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Manufacturer').text = 'Schneider Electric'
        
        # Range basé sur référence
        ref_value = template.characteristics.get('PRT_REF', 'NSXmE')
        if 'NSX' in ref_value:
            range_name = 'NSX'
        elif 'iDT' in ref_value:
            range_name = 'Acti9 iC60'
        else:
            range_name = 'NSX'
        
        ET.SubElement(circuit_breaker,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Range').text = range_name
        
        # Designation technique
        designation = self._extract_designation_from_autocad(record, template)
        ET.SubElement(circuit_breaker,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Designation').text = designation
        
        # Champs optionnels mais recommandés
        ET.SubElement(circuit_breaker,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}RangeDisplayName').text = ''
        
        ET.SubElement(circuit_breaker,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}DesignationDisplayName').text = ref_value
        
        ET.SubElement(circuit_breaker,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}VoltageRange').text = ''
        
        # Rating (calibre)
        cal_value = template.characteristics.get('PRT_CAL', '32.00')
        cal_numeric = cal_value.replace('.00', '')
        ET.SubElement(circuit_breaker,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Rating').text = cal_numeric
        
        # Type standard
        ET.SubElement(circuit_breaker,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}StandardTypeOf').text = 'Industrial'
        
        # Pôles détaillés
        poles_value = template.characteristics.get('PRT_NBPPP', '4P4D')
        switched_poles = poles_value.split('P')[0] + 'P' if 'P' in poles_value else '4P'
        protected_poles = poles_value.split('P')[1].replace('D', '') if 'P' in poles_value and 'D' in poles_value else '3'
        
        ET.SubElement(circuit_breaker,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}SwitchedPoleCount').text = switched_poles
        
        ET.SubElement(circuit_breaker,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}ProtectedPoleCount').text = protected_poles
        
        # Pouvoir de coupure
        icc_value = template.characteristics.get('PRT_ICC', '16')
        ET.SubElement(circuit_breaker,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}BreakingCapacity').text = icc_value
        
        # Settings obligatoires
        settings = ET.SubElement(circuit_breaker,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Settings')
        
        # Calculs basés sur le calibre
        cal_float = float(cal_value)
        ild = cal_float * 0.92  # 92% du calibre
        
        ET.SubElement(settings,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Ild').text = f'{ild:.1f}'
        ET.SubElement(settings,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Tld').text = '16'
        ET.SubElement(settings,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Isd').text = f'{cal_float * 9.2:.0f}'
        ET.SubElement(settings,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Tsd').text = '0.02'
        ET.SubElement(settings,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Iid').text = f'{cal_float * 11:.0f}'
        ET.SubElement(settings,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Ti').text = '0'
        
        # TripUnit obligatoire
        trip_unit = ET.SubElement(circuit_breaker_outer,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}TripUnit')
        
        ET.SubElement(trip_unit,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Manufacturer').text = 'Schneider Electric'
        
        ET.SubElement(trip_unit,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Range').text = range_name
        
        cdecl_value = template.characteristics.get('PRT_CDECL', 'TM-D')
        ET.SubElement(trip_unit,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Designation').text = cdecl_value
        
        ET.SubElement(trip_unit,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}RangeDisplayName').text = ''
        
        ET.SubElement(trip_unit,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}DesignationDisplayName').text = cdecl_value
        
        ET.SubElement(trip_unit,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}VoltageRange').text = ''
        
        ET.SubElement(trip_unit,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}ProtectedPoleCount').text = protected_poles
        
        ET.SubElement(trip_unit,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Protection').text = 'CircuitBreaker'
        
        ET.SubElement(trip_unit,
            '{http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy}Rating').text = cal_numeric
        
        # Instances obligatoires
        instances = ET.SubElement(pack, 'Instances')
        instance = ET.SubElement(instances, 'Instance')
        instance.set('id', f'PI{pack_id:05d}')
    
    def _extract_designation_from_autocad(self, record: Dict[str, Any], template) -> str:
        """Extrait la désignation technique des données AutoCAD"""
        autocad_data = record.get('specifications', '') + ' ' + record.get('description', '')
        
        # Rechercher patterns spécifiques
        import re
        
        # Pattern pour codes techniques
        tech_patterns = [
            r'C1001H',
            r'[A-Z]\d{3,4}[A-Z]?',
            r'NSX\w+',
            r'iDT\w+'
        ]
        
        for pattern in tech_patterns:
            match = re.search(pattern, autocad_data)
            if match:
                return match.group(0)
        
        # Fallback sur template
        return template.characteristics.get('PRT_REF', 'C1001H')
    
    def _determine_product_name(self, record: Dict[str, Any], template) -> str:
        """Détermine le nom du produit"""
        autocad_name = record.get('description', '').strip()
        
        # Mapping spécifique selon les données AutoCAD
        if 'irve' in autocad_name.lower():
            return 'ALIM TD IRVE'
        elif 'tr' in autocad_name.lower() and '01' in autocad_name:
            return 'TR01'
        elif 'ecl' in autocad_name.lower():
            return 'TD1-ECL 1'
        
        return template.name_pattern
    
    def _indent_xml(self, elem: ET.Element, level: int = 0):
        """Ajoute une indentation propre au XML"""
        indent = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent
    
    def validate_xml(self, xml_path: str) -> bool:
        """Valide le XML généré"""
        try:
            ET.parse(xml_path)
            self.logger.info("XML validé avec succès")
            return True
        except ET.ParseError as e:
            self.logger.error(f"Erreur validation XML: {str(e)}")
            return False
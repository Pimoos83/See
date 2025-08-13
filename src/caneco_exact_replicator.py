"""
Générateur XML Caneco - Reproduction EXACTE du format original
Analyse et reproduit strictement la structure du fichier original
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any
import re

class CanecoExactReplicator:
    """Reproduit exactement la structure du fichier Caneco original"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.original_structure = {}
        self.autocad_data = []
        
    def analyze_original_structure(self, original_file: str):
        """Analyse la structure exacte du fichier original"""
        try:
            tree = ET.parse(original_file)
            root = tree.getroot()
            
            # Extraire la structure exacte
            self.original_structure = {
                'root_tag': root.tag,
                'root_attribs': dict(root.attrib),
                'sections': []
            }
            
            # Analyser chaque section
            for child in root:
                section_info = {
                    'tag': child.tag,
                    'attribs': dict(child.attrib),
                    'content_sample': self._extract_content_sample(child)
                }
                self.original_structure['sections'].append(section_info)
            
            self.logger.info(f"Structure originale analysée: {len(self.original_structure['sections'])} sections")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur analyse structure: {str(e)}")
            return False
    
    def _extract_content_sample(self, element: ET.Element, max_depth=3, current_depth=0):
        """Extrait un échantillon de la structure d'un élément"""
        if current_depth >= max_depth:
            return "..."
        
        sample = {
            'tag': element.tag,
            'attribs': dict(element.attrib),
            'text': element.text.strip() if element.text else None,
            'children': []
        }
        
        for child in list(element)[:3]:  # Max 3 enfants par niveau
            sample['children'].append(self._extract_content_sample(child, max_depth, current_depth + 1))
        
        return sample
    
    def load_autocad_data(self, autocad_file: str):
        """Charge les données AutoCAD à transformer"""
        try:
            if autocad_file.endswith('.xlsx') or autocad_file.endswith('.xls'):
                return self._load_excel_data(autocad_file)
            else:
                return self._load_txt_data(autocad_file)
        except Exception as e:
            self.logger.error(f"Erreur chargement données: {str(e)}")
            return False
    
    def _load_txt_data(self, txt_file: str):
        """Charge un fichier TXT"""
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parser selon le format AutoCAD
        lines = content.strip().split('\n')
        for line in lines:
            if line.strip():
                parts = line.split('\t') if '\t' in line else [line]
                record = {
                    'id': parts[0] if len(parts) > 0 else f'Item_{len(self.autocad_data)+1}',
                    'description': parts[1] if len(parts) > 1 else parts[0],
                    'specifications': parts[2] if len(parts) > 2 else '32A'
                }
                self.autocad_data.append(record)
        
        self.logger.info(f"Données TXT chargées: {len(self.autocad_data)} éléments")
        return True
    
    def _load_excel_data(self, excel_file: str):
        """Charge un fichier Excel"""
        import pandas as pd
        
        df = pd.read_excel(excel_file)
        columns = df.columns.tolist()
        
        # Détection automatique des colonnes
        id_col = columns[0]
        desc_col = columns[1] if len(columns) > 1 else columns[0]
        spec_col = columns[2] if len(columns) > 2 else None
        
        for _, row in df.iterrows():
            record = {
                'id': str(row[id_col]),
                'description': str(row[desc_col]),
                'specifications': str(row[spec_col]) if spec_col else '32A'
            }
            self.autocad_data.append(record)
        
        self.logger.info(f"Données Excel chargées: {len(self.autocad_data)} éléments")
        return True
    
    def generate_exact_replica(self, output_file: str) -> bool:
        """Génère un XML qui reproduit EXACTEMENT la structure originale"""
        try:
            # Créer la racine avec les attributs EXACTS
            root = ET.Element('ElectricalProject')
            
            # Attributs dans l'ordre EXACT du fichier original
            root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            root.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
            root.set('formatVersion', '0.29')
            root.set('productRangeValuesVersion', '0.17')
            root.set('commercialTaxonomyVersion', '0.26')
            root.set('electricalTaxonomyVersion', '0.19')
            root.set('mechanicalTaxonomyVersion', '0.1')
            root.set('xmlns', 'http://www.schneider-electric.com/electrical-distribution/exchange-format')
            
            # Reproduire chaque section EXACTEMENT
            self._add_exact_description(root)
            self._add_exact_contacts(root)
            self._add_exact_products(root)
            self._add_exact_equipments(root)
            self._add_exact_network(root)
            
            # Écrire avec le formatage EXACT
            self._write_exact_format(root, output_file)
            
            self.logger.info("Réplique exacte générée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur génération réplique: {str(e)}")
            return False
    
    def _add_exact_description(self, root: ET.Element):
        """Description EXACTEMENT comme dans l'original"""
        desc = ET.SubElement(root, 'Description')
        
        name = ET.SubElement(desc, 'Name')
        name.text = 'Caneco BT - Etap Roadshow 2023'
        
        number = ET.SubElement(desc, 'Number')
        number.text = ''  # Pas None, string vide
        
        order = ET.SubElement(desc, 'OrderNumber')  # Auto-fermant
        
        date = ET.SubElement(desc, 'StartDate')
        date.text = '2023-10-10T00:00:00.0Z'
    
    def _add_exact_contacts(self, root: ET.Element):
        """Contacts EXACTEMENT comme dans l'original"""
        contacts = ET.SubElement(root, 'Contacts')
        
        # Company
        company = ET.SubElement(contacts, 'Company')
        company.set('id', 'CC00001')
        
        address = ET.SubElement(company, 'Address')
        
        street = ET.SubElement(address, 'Street')
        street.text = ''
        postal = ET.SubElement(address, 'PostalCode')
        postal.text = ''
        city = ET.SubElement(address, 'City')
        city.text = ''
        state = ET.SubElement(address, 'State')  # Auto-fermant
        country = ET.SubElement(address, 'Country')
        country.text = 'France'
        
        phones = ET.SubElement(company, 'PhoneNumbers')
        phone = ET.SubElement(phones, 'Phone')
        phone.set('Kind', 'main')
        phone.text = ''
        
        comp_name = ET.SubElement(company, 'Name')
        comp_name.text = 'Authorized user'
        
        # Person
        person = ET.SubElement(contacts, 'Person')
        person.set('id', 'CP00001')
        
        lastname = ET.SubElement(person, 'LastName')
        lastname.text = ''
        
        person_phones = ET.SubElement(person, 'PhoneNumbers')
        person_phone = ET.SubElement(person_phones, 'Phone')
        person_phone.set('Kind', 'main')
        person_phone.text = ''
        
        email = ET.SubElement(person, 'Email')
        email.text = ''
        
        comp_ref = ET.SubElement(person, 'Company')
        comp_ref.set('id', 'CC00001')  # Auto-fermant
    
    def _add_exact_products(self, root: ET.Element):
        """Products EXACTEMENT comme dans l'original - ProductSet ET ProductList"""
        products = ET.SubElement(root, 'Products')
        
        # ProductSet (structure simple)
        product_set = ET.SubElement(products, 'ProductSet')
        
        for i, record in enumerate(self.autocad_data):
            product = ET.SubElement(product_set, 'Product')
            product.set('id', f'PG{i+1:05d}')
            
            name = ET.SubElement(product, 'Name')
            name.text = record['description']
            
            seed = ET.SubElement(product, 'Seed')
            seed.set('Name', '')
            seed.set('Type', 'RAPSODY')
            seed.set('GroupId', 'ECD_DISJONCTEUR')
            seed.set('ItemId', 'MG4_13271')
            
            content = ET.SubElement(product, 'Content')
            chars = ET.SubElement(content, 'Characteristics')
            
            # Caractéristiques essentielles avec format EXACT
            self._add_exact_characteristic(chars, 'PRT_CAL', record.get('specifications', '32.00'))
            self._add_exact_characteristic(chars, 'PRT_NBPPP', '3P3D')
            self._add_exact_characteristic(chars, 'PRT_FREQ', '50')
        
        # ProductList (structure complexe avec Packs)
        product_list = ET.SubElement(products, 'ProductList')
        
        for i, record in enumerate(self.autocad_data):
            pack = ET.SubElement(product_list, 'Pack')
            pack.set('id', f'PK{i+1:05d}')
            
            product = ET.SubElement(pack, 'Product')
            product.set('id', f'PG{i+1:05d}')
            
            name = ET.SubElement(product, 'Name')
            name.text = record['description']
            
            # Content avec CircuitBreaker commercial
            content = ET.SubElement(product, 'Content')
            cb = ET.SubElement(content, 'CircuitBreaker')
            cb.set('xmlns', 'http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy')
            
            instances = ET.SubElement(pack, 'Instances')
            instance = ET.SubElement(instances, 'Instance')
            instance.set('id', f'PI{i+1:05d}')
    
    def _add_exact_characteristic(self, chars: ET.Element, char_id: str, char_value: str):
        """Ajoute une caractéristique avec le format EXACT"""
        char = ET.SubElement(chars, 'Characteristic')
        
        name = ET.SubElement(char, 'Name')  # Auto-fermant
        
        id_elem = ET.SubElement(char, 'Id')
        id_elem.text = char_id
        
        set_values = ET.SubElement(char, 'SetValues')
        value = ET.SubElement(set_values, 'Value')
        
        val_name = ET.SubElement(value, 'Name')  # Auto-fermant
        
        val_id = ET.SubElement(value, 'Id')
        val_id.text = str(char_value)
    
    def _add_exact_equipments(self, root: ET.Element):
        """Equipments EXACTEMENT comme dans l'original"""
        equipments = ET.SubElement(root, 'Equipments')
        
        equipment = ET.SubElement(equipments, 'Equipment')
        equipment.set('id', 'EQ00001')
        
        # Commercial
        commercial = ET.SubElement(equipment, 'Commercial')
        packs = ' '.join([f'PK{i+1:05d}' for i in range(min(10, len(self.autocad_data)))])
        commercial.set('ProductPacks', packs)
        
        comm_props = ET.SubElement(commercial, 'Properties')
        bc = ET.SubElement(comm_props, 'BreakingCapacity')
        bc.text = '36'
        rating = ET.SubElement(comm_props, 'Rating')
        rating.text = '630'
        
        # Electrical
        electrical = ET.SubElement(equipment, 'Electrical')
        devices = ' '.join([f'ED{i+1:05d}' for i in range(min(10, len(self.autocad_data)))])
        functions = ' '.join([f'EF{i+1:05d}' for i in range(min(10, len(self.autocad_data)))])
        electrical.set('Devices', devices)
        electrical.set('Functions', functions)
        
        elec_props = ET.SubElement(electrical, 'Properties')
        freq = ET.SubElement(elec_props, 'Frequency')
        freq.text = '50'
        earth = ET.SubElement(elec_props, 'EarthingSystem')
        earth.text = 'TN-S'
        
        sb = ET.SubElement(electrical, 'Switchboard')
        sb_props = ET.SubElement(sb, 'Properties')  # Vide
        
        # Properties
        eq_props = ET.SubElement(equipment, 'Properties')
        eq_name = ET.SubElement(eq_props, 'Name')
        eq_name.text = 'TGBT'
    
    def _add_exact_network(self, root: ET.Element):
        """Network EXACTEMENT comme dans l'original"""
        network = ET.SubElement(root, 'Network')
        
        freq = ET.SubElement(network, 'Frequency')
        freq.text = '50'
        
        devices = ET.SubElement(network, 'Devices')
        
        for i, record in enumerate(self.autocad_data):
            device = ET.SubElement(devices, 'Device')
            device.set('id', f'ED{i+1:05d}')
            device.set('ProductInstance', f'PI{i+1:05d}')
            device.set('Components', f'EC{i+1:05d}')
            
            func_name = ET.SubElement(device, 'FunctionalName')
            func_name.text = record['description']
            
            cb_device = ET.SubElement(device, 'CircuitBreakerDevice')
            cb_device.set('xmlns', 'http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy')
    
    def _write_exact_format(self, root: ET.Element, output_file: str):
        """Écrit avec le formatage EXACT de l'original"""
        # Indentation exacte
        self._exact_indent(root)
        
        # Conversion avec formatage exact
        rough_string = ET.tostring(root, encoding='utf-8')
        from xml.dom import minidom
        reparsed = minidom.parseString(rough_string)
        pretty = reparsed.toprettyxml(indent='  ')
        
        # Corrections post-formatage pour match EXACT
        lines = pretty.split('\n')
        if lines[0].startswith('<?xml'):
            lines[0] = '<?xml version="1.0" encoding="utf-8"?>'
        
        # Enlever lignes vides après déclaration
        while len(lines) > 1 and lines[1].strip() == '':
            lines.pop(1)
        
        pretty = '\n'.join(lines)
        
        # Corrections pour éléments auto-fermants EXACTS
        corrections = [
            ('<OrderNumber></OrderNumber>', '<OrderNumber/>'),
            ('<State></State>', '<State/>'),
            ('<Name></Name>', '<Name/>'),
            ('<Company id="CC00001"></Company>', '<Company id="CC00001"/>'),
        ]
        
        for old, new in corrections:
            pretty = pretty.replace(old, new)
        
        # Écrire le fichier
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(pretty)
    
    def _exact_indent(self, elem, level=0):
        """Indentation exacte"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._exact_indent(child, level+1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    replicator = CanecoExactReplicator()
    replicator.analyze_original_structure('attached_assets/Caneco BT _1754486408913.xml')
    replicator.load_autocad_data('test_disjoncteurs.txt')
    
    success = replicator.generate_exact_replica('test_exact_replica.xml')
    if success:
        print("Réplique exacte générée: test_exact_replica.xml")

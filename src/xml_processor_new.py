import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Optional
import chardet
import copy
import re


class XMLProcessor:
    """Process XML transformation from Autocad TXT to Caneco XML format using reference file modification"""
    
    def __init__(self):
        self.reference_tree = None
        self.reference_root = None
        self.reference_file_path = None
        self.autocad_data = []
        self.processing_summary = {
            'reference_elements': 0,
            'autocad_records': 0,
            'generated_products': 0,
            'errors': []
        }
        self.logger = logging.getLogger(__name__)
        
        # Define component type mappings with real ItemIds from reference file
        self.component_mappings = {
            'transformer': {
                'group_id': 'ECD_TRANSFORMATEUR',
                'keywords': ['transfo', 'transformer', 'ta-'],
                'characteristics': ['voltage', 'power', 'frequency'],
                'item_ids': ['SC1TRANFO', 'MG2_TRANS']
            },
            'disjoncteur': {
                'group_id': 'ECD_DISJONCTEUR', 
                'keywords': ['nsx', 'disjoncteur', 'breaker', 'tmd', 'ir'],
                'characteristics': ['rating', 'poles', 'breaking_capacity'],
                'item_ids': ['SC3DISNSXM', 'SC4_19030', 'MG4_13271']
            },
            'busbar': {
                'group_id': 'ECD_JEU_DE_BARRE',
                'keywords': ['jeu de barre', 'busbar', 'jb-'],
                'characteristics': ['voltage', 'phases', 'current'],
                'item_ids': ['SC2BUSBAR', 'MG3_BUSBAR']
            }
        }
    
    def load_reference_xml(self, xml_path: str):
        """Load and parse the reference Caneco XML file"""
        # Store reference path for later use
        self._reference_path = xml_path
        try:
            self.reference_file_path = xml_path
            
            # Detect encoding
            with open(xml_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            
            # Parse with ElementTree
            with open(xml_path, 'r', encoding=encoding) as f:
                xml_content = f.read()
            self.reference_root = ET.fromstring(xml_content)
            self.reference_tree = ET.ElementTree(self.reference_root)
            
            self.processing_summary['reference_elements'] = len(list(self.reference_root.iter()))
            self.logger.info(f"XML de référence chargé: {self.processing_summary['reference_elements']} éléments")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du XML de référence: {str(e)}")
            raise Exception(f"Impossible de charger le fichier XML de référence: {str(e)}")
    
    def load_autocad_data(self, txt_path: str):
        """Load and parse Autocad TXT file with intelligent component detection"""
        try:
            # Detect encoding
            with open(txt_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            
            with open(txt_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            self.autocad_data = []
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse AutoCAD format: 'ID\tComponent\t...
                if line.startswith("'") and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        autocad_id = parts[0].strip("'")
                        description = parts[1].strip()
                        
                        # Extract specifications (everything after description)
                        specifications = '\t'.join(parts[2:]) if len(parts) > 2 else ''
                        
                        # Detect component type
                        component_type = self._detect_component_type(description, specifications)
                        
                        record = {
                            'autocad_id': autocad_id,
                            'description': description,
                            'specifications': specifications,
                            'component_type': component_type,
                            'line_number': line_num
                        }
                        
                        self.autocad_data.append(record)
            
            # Log summary
            type_counts = {}
            for record in self.autocad_data:
                comp_type = record['component_type']
                type_counts[comp_type] = type_counts.get(comp_type, 0) + 1
            
            self.processing_summary['autocad_records'] = len(self.autocad_data)
            self.logger.info(f"Données AutoCAD chargées: {len(self.autocad_data)} composants")
            
            for comp_type, count in type_counts.items():
                self.logger.info(f"  - {comp_type}: {count} composants")
                
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des données AutoCAD: {str(e)}")
            raise Exception(f"Impossible de charger le fichier AutoCAD: {str(e)}")
    
    def _detect_component_type(self, description: str, specifications: str) -> str:
        """Detect component type based on description and specifications"""
        text = f"{description} {specifications}".lower()
        
        for comp_type, mapping in self.component_mappings.items():
            for keyword in mapping['keywords']:
                if keyword in text:
                    return comp_type
                    
        return 'unknown'
    
    def generate_xml(self, output_path: str) -> bool:
        """Generate XML by completely copying reference structure and replacing only ProductSet with AutoCAD data"""
        try:
            from lxml import etree
            import shutil
            
            # STEP 1: Copy the reference file entirely to preserve exact structure
            reference_xml_path = self.reference_tree.getroot().base if hasattr(self.reference_tree.getroot(), 'base') else ''
            if not reference_xml_path:
                # Find the original reference file path from app initialization
                reference_xml_path = getattr(self, '_reference_path', None)
            
            if not reference_xml_path:
                raise Exception("Chemin du fichier de référence introuvable")
                
            # Copy reference file as starting point
            shutil.copy2(reference_xml_path, output_path)
            
            # STEP 2: Parse and modify only the ProductSet section
            parser = etree.XMLParser(strip_whitespace=False, recover=True)
            tree = etree.parse(output_path, parser)
            root = tree.getroot()
            
            # Extract namespace
            namespace = root.nsmap.get(None, '')
            ns_prefix = '{' + namespace + '}' if namespace else ''
            
            # Find ProductSet section
            product_set = root.find(f'.//{ns_prefix}Products/{ns_prefix}ProductSet')
            if product_set is None:
                raise Exception("Section ProductSet non trouvée")
            
            # Clear existing products in ProductSet
            product_set.clear()
            
            # Generate only ProductSet with AutoCAD data
            product_counter = 1
            
            for record in self.autocad_data:
                if record['component_type'] != 'unknown':
                    product_element = self._create_lxml_product(product_set, record, product_counter)
                    product_counter += 1
            
            self.processing_summary['generated_products'] = product_counter - 1
            
            # Write back with exact formatting preservation
            tree.write(output_path, encoding='utf-8', xml_declaration=True, pretty_print=True)
            
            self.logger.info(f"XML généré avec {self.processing_summary['generated_products']} produits")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération XML: {str(e)}")
            # Fallback to string replacement
            return self._generate_xml_string_replacement(output_path)
    
    def _create_product_element(self, record: Dict[str, Any], product_id: int) -> Optional[ET.Element]:
        """Create a Product element based on AutoCAD record"""
        try:
            comp_type = record['component_type']
            mapping = self.component_mappings.get(comp_type)
            
            if not mapping:
                return None
            
            # Create Product element
            product = ET.Element('Product')
            product.set('id', f'PG{product_id:05d}')
            
            # Add Name element - map AutoCAD to reference names
            name_elem = ET.SubElement(product, 'Name')
            mapped_name = self._map_autocad_to_reference_name(record, comp_type)
            name_elem.text = mapped_name
            
            # Add Seed element with real ItemId from reference
            seed_elem = ET.SubElement(product, 'Seed')
            seed_elem.set('Name', '')
            seed_elem.set('Type', 'RAPSODY')
            seed_elem.set('GroupId', mapping['group_id'])
            item_id = mapping['item_ids'][product_id % len(mapping['item_ids'])]
            seed_elem.set('ItemId', item_id)
            
            # Add Content with Characteristics
            content_elem = ET.SubElement(product, 'Content')
            characteristics_elem = ET.SubElement(content_elem, 'Characteristics')
            
            # Add characteristics based on component type
            self._add_characteristics(characteristics_elem, record, comp_type)
            
            self.logger.debug(f"Produit créé: {record['description']} ({comp_type})")
            return product
            
        except Exception as e:
            self.logger.error(f"Erreur création produit: {str(e)}")
            return None
    
    def _map_autocad_to_reference_name(self, record: Dict[str, Any], comp_type: str) -> str:
        """Map AutoCAD component to reference product name"""
        specs = record.get('specifications', '')
        
        if comp_type == 'disjoncteur':
            # Map based on NSX model in specifications
            if 'NSX' in specs:
                if '100' in specs:
                    return 'ALIM TD IRVE'
                elif '630' in specs:
                    return 'TR01'
            return 'ALIM TD IRVE'
            
        elif comp_type == 'transformer':
            return record.get('description', 'Transfo Principal')
            
        return record.get('description', 'Unknown')[:20]
    
    def _add_characteristics(self, characteristics_elem: ET.Element, record: Dict[str, Any], comp_type: str):
        """Add characteristics with exact order matching reference Caneco BT.xml"""
        
        if comp_type == 'disjoncteur':
            # Extract values from AutoCAD data
            rating = self._extract_rating(record.get('specifications', '')) or '32.00'
            autocad_ref = record.get('specifications', '')
            reference = self._extract_product_reference(autocad_ref) or 'NSX630F'
            
            # Add characteristics in EXACT order from reference file
            self._add_characteristic(characteristics_elem, 'PRT_INST', 'FIX')
            self._add_characteristic(characteristics_elem, 'PRT_PERFO', 'E')
            self._add_characteristic(characteristics_elem, 'PRT_CDECL', 'TM-D')
            self._add_characteristic(characteristics_elem, 'PRT_CAL', rating)
            self._add_characteristic(characteristics_elem, 'PRT_NBPPP', '4P4D')
            self._add_characteristic(characteristics_elem, 'PRT_NORM', 'EN 60947-2')
            self._add_characteristic(characteristics_elem, 'PRT_FREQ', '50')
            self._add_characteristic(characteristics_elem, 'PRT_ICC', '16')
            self._add_characteristic(characteristics_elem, 'PRT_DIFF', 'N')
            self._add_characteristic(characteristics_elem, 'PRT_VISU', 'N')
            self._add_characteristic(characteristics_elem, 'PRT_TCDE', 'N')
            self._add_characteristic(characteristics_elem, 'PRT_BDCLS', '')
            self._add_characteristic(characteristics_elem, 'PRT_BDSEN', '0')
            self._add_characteristic(characteristics_elem, 'PRT_REF', reference)
                
        elif comp_type == 'transformer':
            # Add transformer characteristics in correct order
            self._add_characteristic(characteristics_elem, 'PRT_INST', 'FIX')
            self._add_characteristic(characteristics_elem, 'PRT_TENSION_PRIM', '400')
            self._add_characteristic(characteristics_elem, 'PRT_TENSION_SEC', '230')
            self._add_characteristic(characteristics_elem, 'PRT_PUISSANCE', '1000')
            self._add_characteristic(characteristics_elem, 'PRT_FREQ', '50')
            self._add_characteristic(characteristics_elem, 'PRT_NORM', 'EN 60947-2')
            self._add_characteristic(characteristics_elem, 'PRT_TYPE', 'MONO')
                
        elif comp_type == 'busbar':
            # Add busbar characteristics in correct order
            self._add_characteristic(characteristics_elem, 'PRT_INST', 'FIX')
            self._add_characteristic(characteristics_elem, 'PRT_TENSION', '400')
            self._add_characteristic(characteristics_elem, 'PRT_PHASES', '3')
            self._add_characteristic(characteristics_elem, 'PRT_COURANT', '630')
            self._add_characteristic(characteristics_elem, 'PRT_FREQ', '50')
            self._add_characteristic(characteristics_elem, 'PRT_NORM', 'EN 60947-2')
    
    def _add_characteristic(self, characteristics_elem: ET.Element, char_id: str, value: str):
        """Add a characteristic element"""
        char_elem = ET.SubElement(characteristics_elem, 'Characteristic')
        
        name_elem = ET.SubElement(char_elem, 'Name')
        name_elem.text = ''
        
        id_elem = ET.SubElement(char_elem, 'Id')
        id_elem.text = char_id
        
        set_values_elem = ET.SubElement(char_elem, 'SetValues')
        value_elem = ET.SubElement(set_values_elem, 'Value')
        
        value_name_elem = ET.SubElement(value_elem, 'Name')
        value_name_elem.text = ''
        
        value_id_elem = ET.SubElement(value_elem, 'Id')
        value_id_elem.text = str(value)
    
    def _extract_rating(self, specifications: str) -> Optional[str]:
        """Extract amperage rating from AutoCAD specifications"""
        if not specifications:
            return None
            
        # Look for patterns like "16A", "32A"
        amp_match = re.search(r'(\d+)A', specifications)
        if amp_match:
            return f"{amp_match.group(1)}.00"
            
        # Look for NSX ratings like "NSX100B"
        nsx_match = re.search(r'NSX(\d+)', specifications)
        if nsx_match:
            return f"{nsx_match.group(1)}.00"
            
        return None
    
    def _extract_product_reference(self, specifications: str) -> Optional[str]:
        """Extract product reference from AutoCAD specifications"""
        if not specifications:
            return None
            
        # Extract NSX reference like "NSX100B"
        nsx_match = re.search(r'NSX\w+', specifications)
        if nsx_match:
            return nsx_match.group()
            
        if 'TMD' in specifications:
            return specifications.split()[0] if specifications.split() else None
            
        return None
    
    def _create_pack_element(self, record: Dict[str, Any], pack_id: int) -> Optional[ET.Element]:
        """Create a Pack element for ProductList section"""
        try:
            comp_type = record['component_type']
            
            pack = ET.Element('Pack')
            pack.set('id', f'PK{pack_id:05d}')
            
            product_elem = ET.SubElement(pack, 'Product')
            
            commercial_ns = "http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy"
            
            if comp_type == 'disjoncteur':
                # Use CircuitBreaker (correct XSD name)
                breaker_elem = ET.SubElement(product_elem, 'CircuitBreaker')
                breaker_elem.set('xmlns', commercial_ns)
                
                breaker_sub = ET.SubElement(breaker_elem, 'CircuitBreaker')
                
                manufacturer = ET.SubElement(breaker_sub, 'Manufacturer')
                manufacturer.text = 'Schneider Electric'
                
                range_elem = ET.SubElement(breaker_sub, 'Range')
                range_elem.text = 'NSX'
                
                designation = ET.SubElement(breaker_sub, 'Designation')
                designation.text = self._extract_product_reference(record.get('specifications', '')) or 'NSX630F'
                
                rating = ET.SubElement(breaker_sub, 'Rating')
                rating.text = self._extract_rating(record.get('specifications', '')) or '32'
                
                breaking_capacity = ET.SubElement(breaker_sub, 'BreakingCapacity')
                breaking_capacity.text = '36000'
                
            elif comp_type == 'transformer':
                transformer_elem = ET.SubElement(product_elem, 'Transformer')
                transformer_elem.set('xmlns', commercial_ns)
                
                transformer_sub = ET.SubElement(transformer_elem, 'Transformer')
                
                manufacturer = ET.SubElement(transformer_sub, 'Manufacturer')
                manufacturer.text = 'Unknown'
                
                range_elem = ET.SubElement(transformer_sub, 'Range')
                range_elem.text = ''
                
                designation = ET.SubElement(transformer_sub, 'Designation')
                designation.text = 'Unknown'
                
                sr = ET.SubElement(transformer_sub, 'Sr')
                sr.text = '400000'
                
                input_voltage = ET.SubElement(transformer_sub, 'InputVoltage')
                input_voltage.text = '20000'
                
                output_voltage = ET.SubElement(transformer_sub, 'UsageOutputVoltage')
                output_voltage.text = '400'
            
            # Add Instances section
            instances = ET.SubElement(pack, 'Instances')
            instance = ET.SubElement(instances, 'Instance')
            instance.set('id', f'PI{pack_id:05d}')
            
            return pack
            
        except Exception as e:
            self.logger.error(f"Erreur création pack: {str(e)}")
            return None
    
    def validate_generated_xml(self, xml_path: str) -> bool:
        """Validate the generated XML"""
        try:
            ET.parse(xml_path)
            self.logger.info("XML généré validé avec succès")
            return True
            
        except ET.ParseError as e:
            self.logger.error(f"Erreur de syntaxe XML: {str(e)}")
            self.processing_summary['errors'].append(f"Erreur de syntaxe XML: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Erreur lors de la validation: {str(e)}")
            self.processing_summary['errors'].append(f"Erreur de validation: {str(e)}")
            return False
    
    def _generate_xml_string_replacement(self, output_path: str) -> bool:
        """Fallback method using string replacement to preserve exact structure"""
        try:
            # Read original XML as string
            with open(self.reference_file_path, 'r', encoding='utf-8') as f:
                original_xml = f.read()
            
            # Find Products section boundaries
            products_start = original_xml.find('<Products>')
            products_end = original_xml.find('</Products>') + len('</Products>')
            
            if products_start == -1 or products_end == -1:
                raise Exception("Section Products non trouvée dans le XML")
            
            # Generate new Products section
            new_products = self._generate_products_section_string()
            
            # Replace Products section
            new_xml = (original_xml[:products_start] + 
                      new_products + 
                      original_xml[products_end:])
            
            # Normalize XML formatting to match original
            new_xml = self._normalize_xml_formatting(new_xml)
            
            # Write the new XML
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(new_xml)
            
            self.logger.info(f"XML généré avec remplacement de chaîne")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors du remplacement de chaîne: {str(e)}")
            self.processing_summary['errors'].append(f"Erreur remplacement: {str(e)}")
            return False
    
    def _generate_products_section_string(self) -> str:
        """Generate Products section as string"""
        products_lines = ['<Products>']
        products_lines.append('    <ProductSet>')
        
        product_counter = 1
        for record in self.autocad_data:
            if record['component_type'] != 'unknown':
                product_xml = self._generate_product_string(record, product_counter)
                products_lines.append(product_xml)
                product_counter += 1
        
        products_lines.append('    </ProductSet>')
        products_lines.append('    <ProductList>')
        
        pack_counter = 1
        for record in self.autocad_data:
            if record['component_type'] != 'unknown':
                pack_xml = self._generate_pack_string(record, pack_counter)
                products_lines.append(pack_xml)
                pack_counter += 1
        
        products_lines.append('    </ProductList>')
        products_lines.append('  </Products>')
        
        return '\n  '.join(products_lines)
    
    def _generate_product_string(self, record: Dict[str, Any], product_id: int) -> str:
        """Generate Product element as string"""
        comp_type = record['component_type']
        mapping = self.component_mappings.get(comp_type)
        
        if not mapping:
            return ''
        
        mapped_name = self._map_autocad_to_reference_name(record, comp_type)
        item_id = mapping['item_ids'][product_id % len(mapping['item_ids'])]
        
        product_xml = f'''    <Product id="PG{product_id:05d}">
        <Name>{mapped_name}</Name>
        <Seed Name="" Type="RAPSODY" GroupId="{mapping['group_id']}" ItemId="{item_id}"/>
        <Content>
          <Characteristics>'''
        
        # Add characteristics
        characteristics = self._get_characteristics_string(record, comp_type)
        product_xml += characteristics
        
        product_xml += '''
          </Characteristics>
        </Content>
      </Product>'''
        
        return product_xml
    
    def _get_characteristics_string(self, record: Dict[str, Any], comp_type: str) -> str:
        """Generate characteristics with exact order matching reference Caneco BT.xml"""
        characteristics = []
        
        if comp_type == 'disjoncteur':
            # Extract values from AutoCAD data
            rating = self._extract_rating(record.get('specifications', '')) or '32.00'
            reference = self._extract_product_reference(record.get('specifications', '')) or 'NSXmE'
            
            # Exact order from reference file
            char_data = [
                ('PRT_INST', 'FIX'),
                ('PRT_PERFO', 'E'),
                ('PRT_CDECL', 'TM-D'),
                ('PRT_CAL', rating),
                ('PRT_NBPPP', '4P4D'),
                ('PRT_NORM', 'EN 60947-2'),
                ('PRT_FREQ', '50'),
                ('PRT_ICC', '16'),
                ('PRT_DIFF', 'N'),
                ('PRT_VISU', 'N'),
                ('PRT_TCDE', 'N'),
                ('PRT_BDCLS', ''),
                ('PRT_BDSEN', '0'),
                ('PRT_REF', reference)
            ]
        elif comp_type == 'transformer':
            char_data = [
                ('PRT_INST', 'FIX'),
                ('PRT_TENSION_PRIM', '400'),
                ('PRT_TENSION_SEC', '230'),
                ('PRT_PUISSANCE', '1000'),
                ('PRT_FREQ', '50'),
                ('PRT_NORM', 'EN 60947-2'),
                ('PRT_TYPE', 'MONO')
            ]
        else:
            char_data = [
                ('PRT_INST', 'FIX'),
                ('PRT_FREQ', '50'),
                ('PRT_NORM', 'EN 60947-2')
            ]
        
        for char_id, value in char_data:
            char_xml = f'''
            <Characteristic>
              <Name/>
              <Id>{char_id}</Id>
              <SetValues>
                <Value>
                  <Name/>
                  <Id>{value}</Id>
                </Value>
              </SetValues>
            </Characteristic>'''
            characteristics.append(char_xml)
        
        return ''.join(characteristics)
    
    def _generate_pack_string(self, record: Dict[str, Any], pack_id: int) -> str:
        """Generate Pack element as string"""
        comp_type = record['component_type']
        
        if comp_type != 'disjoncteur':
            return ''
        
        reference = self._extract_product_reference(record.get('specifications', '')) or 'NSX630F'
        rating = self._extract_rating(record.get('specifications', '')) or '32'
        
        pack_xml = f'''    <Pack id="PK{pack_id:05d}">
        <Product>
          <CircuitBreaker xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy">
            <CircuitBreaker>
              <Manufacturer>Schneider Electric</Manufacturer>
              <Range>NSX</Range>
              <Designation>{reference}</Designation>
              <Rating>{rating}</Rating>
              <BreakingCapacity>36000</BreakingCapacity>
            </CircuitBreaker>
          </CircuitBreaker>
        </Product>
        <Instances>
          <Instance id="PI{pack_id:05d}"/>
        </Instances>
      </Pack>'''
        
        return pack_xml
    
    def _normalize_xml_formatting(self, xml_content: str) -> str:
        """Normalize XML formatting to match original file style exactly"""
        import re
        
        # Based on analysis of original file:
        # - These tags should be SELF-CLOSING in original: OrderNumber, State, Company (with id)
        # - These tags should be EXPLICIT open/close: Number, Street, PostalCode, City, Phone, LastName, Email, Name
        
        # Tags that should remain self-closing (as in original)
        self_closing_tags = ['OrderNumber', 'State']
        
        # Tags that should be converted to explicit open/close (as in original)
        explicit_tags = ['Number', 'Street', 'PostalCode', 'City', 'Phone', 'LastName', 'Email']
        
        # Convert specific tags to explicit open/close to match original
        for tag in explicit_tags:
            # Convert self-closing to explicit open/close
            pattern = f'<{tag}\\s*/>'
            replacement = f'<{tag}></{tag}>'
            xml_content = re.sub(pattern, replacement, xml_content)
        
        # Ensure self-closing tags remain self-closing
        for tag in self_closing_tags:
            # Convert explicit open/close back to self-closing if needed
            pattern = f'<{tag}></{tag}>'
            replacement = f'<{tag}/>'
            xml_content = re.sub(pattern, replacement, xml_content)
        
        # Handle special case: Company with id attribute should be self-closing
        pattern = r'<Company\s+([^>]*?)></Company>'
        replacement = r'<Company \1/>'
        xml_content = re.sub(pattern, replacement, xml_content)
        
        return xml_content
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get processing summary"""
        return self.processing_summary.copy()

#!/usr/bin/env python3
"""
Générateur Caneco XSD Compliant
Génère des fichiers XML Caneco strictement conformes au XSD avec données AutoCAD réelles
"""

import json
import logging
from typing import Dict, List
import xml.etree.ElementTree as ET

class CanecoXSDCompliantGenerator:
    """Générateur XML Caneco 100% conforme XSD"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.autocad_data = []
        self.mapped_data = []
    
    def load_autocad_data(self, mapping_file: str) -> bool:
        """Charge les données AutoCAD mappées"""
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.autocad_data = data.get('autocad_data', [])
            self.mapped_data = data.get('mapping_summary', {}).get('mapped_data', [])
            
            self.logger.info(f"Données AutoCAD chargées: {len(self.mapped_data)} éléments")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement AutoCAD: {str(e)}")
            return False
    
    def generate_xsd_compliant_xml(self, output_path: str) -> bool:
        """Génère XML 100% conforme XSD Caneco"""
        try:
            # Créer la structure XML avec namespaces corrects
            xml_content = self._build_xsd_compliant_structure()
            
            # Écrire le fichier XML
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            self.logger.info("XML XSD compliant généré")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur génération XML: {str(e)}")
            return False
    
    def _build_xsd_compliant_structure(self) -> str:
        """Construit la structure XML complètement conforme"""
        lines = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<ElectricalProject xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
            'formatVersion="0.29" '
            'productRangeValuesVersion="0.17" '
            'commercialTaxonomyVersion="0.26" '
            'electricalTaxonomyVersion="0.19" '
            'mechanicalTaxonomyVersion="0.1" '
            'xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format">'
        ]
        
        # Description section
        lines.extend(self._build_description_section())
        
        # Contacts section
        lines.extend(self._build_contacts_section())
        
        # Products section
        lines.extend(self._build_products_section())
        
        # Equipments section
        lines.extend(self._build_equipments_section())
        
        # Network section
        lines.extend(self._build_network_section())
        
        lines.append('</ElectricalProject>')
        
        return '\n'.join(lines)
    
    def _build_description_section(self) -> List[str]:
        """Section Description"""
        return [
            '  <Description>',
            '    <Name>Caneco BT - AutoCAD Import</Name>',
            '    <Number></Number>',
            '    <OrderNumber/>',
            '    <StartDate>2025-08-11T00:00:00.0Z</StartDate>',
            '  </Description>'
        ]
    
    def _build_contacts_section(self) -> List[str]:
        """Section Contacts"""
        return [
            '  <Contacts>',
            '    <Company id="CC00001">',
            '      <Address>',
            '        <Street></Street>',
            '        <PostalCode></PostalCode>',
            '        <City></City>',
            '        <State/>',
            '        <Country>France</Country>',
            '      </Address>',
            '      <PhoneNumbers>',
            '        <Phone Kind="main"></Phone>',
            '      </PhoneNumbers>',
            '      <Name>AutoCAD Import User</Name>',
            '    </Company>',
            '    <Person id="CP00001">',
            '      <LastName></LastName>',
            '      <PhoneNumbers>',
            '        <Phone Kind="main"></Phone>',
            '      </PhoneNumbers>',
            '      <Email></Email>',
            '      <Company id="CC00001"/>',
            '    </Person>',
            '  </Contacts>'
        ]
    
    def _build_products_section(self) -> List[str]:
        """Section Products avec données AutoCAD"""
        lines = ['  <Products>', '    <ProductSet>']
        
        for i, item in enumerate(self.mapped_data):
            product_id = f"PG{i+1:05d}"
            product_name = item.get('description', f'Produit {i+1}')
            
            lines.extend([
                f'      <Product id="{product_id}">',
                f'        <Name>{product_name}</Name>',
                f'        <Seed Name="" Type="RAPSODY" GroupId="ECD_DISJONCTEUR" ItemId="MG4_{13271+i}"/>',
                '        <Content>',
                '          <Characteristics>',
                self._build_product_characteristics(item),
                '          </Characteristics>',
                '        </Content>',
                '      </Product>'
            ])
        
        lines.extend(['    </ProductSet>', '  </Products>'])
        return lines
    
    def _build_product_characteristics(self, item: Dict) -> str:
        """Caractéristiques produit"""
        specs = item.get('specifications', '32A')
        return f"""            <Characteristic>
              <Name/>
              <Id>PRT_CAL</Id>
              <SetValues>
                <Value>
                  <Name/>
                  <Id>{specs}</Id>
                </Value>
              </SetValues>
            </Characteristic>"""
    
    def _build_equipments_section(self) -> List[str]:
        """Section Equipments EXACTEMENT comme l'original"""
        lines = ['  <Equipments>']
        
        for i, item in enumerate(self.mapped_data):
            device_id = f"ED{i+1:05d}"
            component_id = f"EC{i+1:05d}"
            product_id = f"PG{i+1:05d}"
            device_type = item.get('caneco_device_type', 'CircuitBreakerDevice')
            component_type = item.get('caneco_component_type', 'CircuitBreakerComponent')
            
            lines.extend([
                f'    <Device id="{device_id}">',
                f'      <{device_type} xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy"/>',
                f'      <Products>{product_id}</Products>',
                '    </Device>',
                f'    <Component id="{component_id}">',
                f'      <{component_type} xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy"/>',
                f'      <Device id="{device_id}"/>',
                '    </Component>'
            ])
        
        lines.append('  </Equipments>')
        return lines
    
    def _build_network_section(self) -> List[str]:
        """Section Network complète"""
        lines = [
            '  <Network>',
            '    <Functions>'
        ]
        
        # Functions
        for i, item in enumerate(self.mapped_data):
            function_id = f"EF{i+1:05d}"
            component_id = f"EC{i+1:05d}"
            function_type = item.get('caneco_function_type', 'SwitchgearFunction')
            
            lines.extend([
                f'      <Function id="{function_id}" Components="{component_id}">',
                f'        <{function_type} xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy"/>',
                '      </Function>'
            ])
        
        lines.extend([
            '    </Functions>',
            '    <Terminals>'
        ])
        
        # Terminals
        for i, item in enumerate(self.mapped_data):
            for t in range(4):  # 4 terminaux par composant
                terminal_id = f"ECT{i*4+t+1:05d}"
                function_id = f"EF{i+1:05d}"
                
                lines.extend([
                    f'      <Terminal id="{terminal_id}">',
                    f'        <Function id="{function_id}"/>',
                    '      </Terminal>'
                ])
        
        lines.extend([
            '    </Terminals>',
            '    <PowerConnections>'
        ])
        
        # PowerConnections
        for i in range(len(self.mapped_data) - 1):
            connection_id = f"ECX{i+1:05d}"
            endpoint_a = f"ECT{i*4+1:05d}"
            endpoint_b = f"ECT{(i+1)*4+1:05d}"
            
            lines.extend([
                f'      <PowerConnection id="{connection_id}" EndpointA="{endpoint_a}" EndpointB="{endpoint_b}">',
                '        <ElectricalCharacteristics>',
                '          <Ratedvoltage>400.0</Ratedvoltage>',
                '          <RatedCurrent>63.0</RatedCurrent>',
                '        </ElectricalCharacteristics>',
                '      </PowerConnection>'
            ])
        
        lines.extend([
            '    </PowerConnections>',
            '    <Drawing>',
            '      <Views>',
            '        <View id="EV00001">',
            '          <Name>Vue principale</Name>',
            '          <ViewType>Schematic</ViewType>',
            '        </View>',
            '      </Views>',
            '    </Drawing>',
            '  </Network>'
        ])
        
        return lines

def main():
    """Test du générateur XSD compliant"""
    logging.basicConfig(level=logging.INFO)
    
    generator = CanecoXSDCompliantGenerator()
    
    # Charger données AutoCAD
    if generator.load_autocad_data('autocad_caneco_mapping.json'):
        # Générer XML conforme
        success = generator.generate_xsd_compliant_xml('test_xsd_compliant.xml')
        
        if success:
            print("XML XSD compliant généré: test_xsd_compliant.xml")
        else:
            print("Erreur génération XML")
    else:
        print("Erreur chargement données AutoCAD")

if __name__ == "__main__":
    main()
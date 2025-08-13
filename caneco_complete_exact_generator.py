#!/usr/bin/env python3
"""
Générateur Caneco Complet avec données AutoCAD
Crée un nouveau XML Caneco complet basé UNIQUEMENT sur vos données AutoCAD
"""

import json
import logging
from typing import Dict, List
import xml.etree.ElementTree as ET

class CanecoCompleteExactGenerator:
    """Générateur XML Caneco complet avec données AutoCAD réelles"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.autocad_data = []
        
    def load_autocad_data(self, mapping_file: str) -> bool:
        """Charge les données AutoCAD mappées"""
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.autocad_data = data.get('autocad_data', [])
            
            self.logger.info(f"Données AutoCAD chargées: {len(self.autocad_data)} équipements")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement AutoCAD: {str(e)}")
            return False
    
    def generate_complete_caneco_xml(self, output_path: str) -> bool:
        """Génère XML Caneco complet avec vos équipements AutoCAD"""
        try:
            if not self.autocad_data:
                self.logger.error("Aucune donnée AutoCAD")
                return False
            
            lines = []
            
            # Header XML avec namespaces corrects
            lines.extend(self._build_xml_header())
            
            # Description du projet
            lines.extend(self._build_description_section())
            
            # Contacts
            lines.extend(self._build_contacts_section())
            
            # Products basés sur vos équipements AutoCAD
            lines.extend(self._build_products_section())
            
            # ProductList avec ProductPacks (requis par XSD)
            lines.extend(self._build_product_list_section())
            
            # Equipments avec vos devices
            lines.extend(self._build_equipments_section())
            
            # Network avec fonctions électriques
            lines.extend(self._build_network_section())
            
            # Fermeture
            lines.append('</ElectricalProject>')
            
            # Écrire le fichier
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            self.logger.info(f"XML complet AutoCAD généré: {len(self.autocad_data)} équipements")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur génération XML: {str(e)}")
            return False
    
    def _build_xml_header(self) -> List[str]:
        """Header XML avec namespaces XSD"""
        return [
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
    
    def _build_description_section(self) -> List[str]:
        """Description du projet AutoCAD"""
        return [
            '  <Description>',
            '    <Name>Projet AutoCAD - Équipements Électriques</Name>',
            '    <Number></Number>',
            '    <OrderNumber/>',
            '    <StartDate>2025-08-11T00:00:00.0Z</StartDate>',
            '  </Description>'
        ]
    
    def _build_contacts_section(self) -> List[str]:
        """Section contacts standard"""
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
            '      <Name>Ingénieur AutoCAD</Name>',
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
        """Produits basés sur VOS équipements AutoCAD"""
        lines = ['  <Products>', '    <ProductSet>']
        
        for i, item in enumerate(self.autocad_data):
            product_id = f"PG{i+1:05d}"
            
            # Nom du produit basé sur vos vraies données
            repere = self._clean_xml(item.get('REPERE', ''))
            designation = self._clean_xml(item.get('DESIGNATION', ''))
            fabricant = self._clean_xml(item.get('FABRICANT', ''))
            reference = self._clean_xml(item.get('REF', ''))
            
            # Construire nom complet
            name_parts = []
            if repere: name_parts.append(repere)
            if designation: name_parts.append(designation)
            if fabricant: name_parts.append(f"({fabricant})")
            
            product_name = ' '.join(name_parts) if name_parts else f"Équipement {i+1}"
            
            # Déterminer le type de produit
            device_type = self._get_device_type(designation, fabricant)
            group_id, item_id = self._get_caneco_ids(device_type)
            
            lines.extend([
                f'      <Product id="{product_id}">',
                f'        <Name>{product_name}</Name>',
                f'        <Seed Name="" Type="RAPSODY" GroupId="{group_id}" ItemId="{item_id}"/>',
                '        <Content>',
                '          <Characteristics>',
                '            <Characteristic>',
                '              <Name/>',
                '              <Id>PRT_REF</Id>',
                '              <SetValues>',
                '                <Value>',
                '                  <Name/>',
                f'                  <Id>{reference if reference else "N/A"}</Id>',
                '                </Value>',
                '              </SetValues>',
                '            </Characteristic>',
                '          </Characteristics>',
                '        </Content>',
                '      </Product>'
            ])
        
        lines.extend(['    </ProductSet>'])
        return lines
    
    def _build_product_list_section(self) -> List[str]:
        """Section ProductList avec ProductPacks requis par XSD"""
        lines = ['    <ProductList>']
        
        for i, item in enumerate(self.autocad_data):
            pack_id = f"PK{i+1:05d}"
            product_id = f"PG{i+1:05d}"
            instance_id = f"PI{i+1:05d}"
            
            lines.extend([
                f'      <Pack id="{pack_id}">',
                '        <Product>',
                f'          <Reference id="{product_id}"/>',
                '        </Product>',
                '        <Instances>',
                f'          <Instance id="{instance_id}"/>',
                '        </Instances>',
                '      </Pack>'
            ])
        
        lines.extend(['    </ProductList>', '  </Products>'])
        return lines
    
    def _build_equipments_section(self) -> List[str]:
        """Section équipements EXACTEMENT comme l'original"""
        lines = ['  <Equipments>']
        
        # Créer un Equipment global qui contient tous vos équipements AutoCAD
        equipment_id = "EQ00001"
        
        # Collecter tous les IDs de devices et fonctions
        all_devices = []
        all_functions = []
        all_product_packs = []
        
        for i, item in enumerate(self.autocad_data):
            device_id = f"ED{i+1:05d}"
            function_id = f"EF{i+1:05d}"
            product_pack_id = f"PK{i+1:05d}"
            
            all_devices.append(device_id)
            all_functions.append(function_id)
            all_product_packs.append(product_pack_id)
        
        # Créer l'Equipment principal avec structure exacte de l'original
        lines.extend([
            f'    <Equipment id="{equipment_id}">',
            f'      <Commercial ProductPacks="{" ".join(all_product_packs)}">',
            '        <Properties>',
            '          <BreakingCapacity>36</BreakingCapacity>',
            '          <Rating>630</Rating>',
            '        </Properties>',
            '      </Commercial>',
            f'      <Electrical Devices="{" ".join(all_devices)}" Functions="{" ".join(all_functions)}">',
            '        <Properties>',
            '          <Frequency>50</Frequency>',
            '          <EarthingSystem>TN-S</EarthingSystem>',
            '        </Properties>',
            '        <Switchboard>',
            '          <Properties/>',
            '        </Switchboard>',
            '      </Electrical>',
            '      <Properties>',
            '        <Name>Équipements AutoCAD</Name>',
            '      </Properties>',
            '    </Equipment>'
        ])
        
        # Créer tous les devices individuels
        for i, item in enumerate(self.autocad_data):
            device_id = f"ED{i+1:05d}"
            product_id = f"PG{i+1:05d}"
            designation = item.get('DESIGNATION', '')
            device_type = self._get_device_type(designation, item.get('FABRICANT', ''))
            
            lines.extend([
                f'    <Device id="{device_id}">',
                f'      <{device_type} xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy"/>',
                f'      <Products>{product_id}</Products>',
                '    </Device>'
            ])
        
        lines.append('  </Equipments>')
        return lines
    
    def _build_network_section(self) -> List[str]:
        """Section réseau avec fonctions électriques"""
        lines = ['  <Network>']
        
        for i, item in enumerate(self.autocad_data):
            function_id = f"EF{i+1:05d}"
            device_id = f"ED{i+1:05d}"
            
            designation = item.get('DESIGNATION', '')
            function_type = self._get_function_type(designation)
            repere = self._clean_xml(item.get('REPERE', f'F{i+1}'))
            
            lines.extend([
                f'    <Function id="{function_id}">',
                f'      <{function_type} xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy"/>',
                f'      <Name>{repere}</Name>',
                f'      <Devices>{device_id}</Devices>',
                '    </Function>'
            ])
        
        lines.append('  </Network>')
        return lines
    
    def _clean_xml(self, text: str) -> str:
        """Nettoie le texte pour XML"""
        if not text or not text.strip():
            return ""
        
        cleaned = str(text).strip()
        # Échapper caractères XML
        cleaned = cleaned.replace('&', '&amp;')
        cleaned = cleaned.replace('<', '&lt;')
        cleaned = cleaned.replace('>', '&gt;')
        cleaned = cleaned.replace('"', '&quot;')
        cleaned = cleaned.replace("'", '&apos;')
        
        return cleaned
    
    def _get_device_type(self, designation: str, fabricant: str) -> str:
        """Détermine le type de device selon l'équipement"""
        designation = designation.lower() if designation else ""
        fabricant = fabricant.lower() if fabricant else ""
        
        if 'disjoncteur' in designation or 'compact' in designation:
            return 'CircuitBreakerDevice'
        elif 'transformateur' in designation or 'transfo' in designation:
            return 'MvLvTransformerDevice'
        elif 'cable' in designation or 'câble' in designation:
            return 'CableDevice'
        elif 'protection' in designation or 'relais' in designation:
            return 'ProtectionDevice'
        else:
            return 'CircuitBreakerDevice'  # Par défaut
    
    def _get_component_type(self, device_type: str) -> str:
        """Type de composant selon device"""
        if device_type == 'CircuitBreakerDevice':
            return 'CircuitBreakerComponent'
        elif device_type == 'MvLvTransformerDevice':
            return 'MvLvTransformerComponent'
        elif device_type == 'CableDevice':
            return 'CableComponent'
        elif device_type == 'ProtectionDevice':
            return 'ProtectionComponent'
        else:
            return 'CircuitBreakerComponent'
    
    def _get_function_type(self, designation: str) -> str:
        """Type de fonction selon équipement"""
        designation = designation.lower() if designation else ""
        
        if 'disjoncteur' in designation:
            return 'SwitchgearFunction'
        elif 'transformateur' in designation:
            return 'TransformerFunction'
        elif 'protection' in designation:
            return 'ProtectionFunction'
        else:
            return 'SwitchgearFunction'
    
    def _get_caneco_ids(self, device_type: str) -> tuple:
        """IDs Caneco selon type device"""
        if device_type == 'CircuitBreakerDevice':
            return 'ECD_DISJONCTEUR', 'MG4_13271'
        elif device_type == 'MvLvTransformerDevice':
            return 'ECD_TRANSFORMATEUR', 'TR_STANDARD'
        elif device_type == 'CableDevice':
            return 'ECD_CABLE', 'CABLE_STD'
        else:
            return 'ECD_DISJONCTEUR', 'MG4_13271'

def main():
    """Test du générateur complet"""
    logging.basicConfig(level=logging.INFO)
    
    generator = CanecoCompleteExactGenerator()
    
    if generator.load_autocad_data('autocad_caneco_mapping.json'):
        success = generator.generate_complete_caneco_xml('test_complete_exact.xml')
        
        if success:
            print(f"XML AutoCAD complet généré: test_complete_exact.xml")
            print(f"Équipements traités: {len(generator.autocad_data)}")
        else:
            print("Erreur génération")
    else:
        print("Erreur chargement données AutoCAD")

if __name__ == "__main__":
    main()
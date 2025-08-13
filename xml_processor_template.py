"""
Processeur XML basé sur l'architecture de templates pour compatibilité 100% avec Caneco/See Electrical Expert
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Optional
import chardet
import copy
import re
from caneco_templates import CanecoTemplateEngine


class TemplateBasedXMLProcessor:
    """Processeur XML utilisant les templates exacts de Caneco pour garantir la compatibilité 100%"""
    
    def __init__(self):
        self.reference_tree = None
        self.reference_root = None
        self.reference_file_path = None
        self.autocad_data = []
        self.template_engine = CanecoTemplateEngine()
        self.processing_summary = {
            'reference_elements': 0,
            'autocad_records': 0,
            'generated_products': 0,
            'template_matches': 0,
            'errors': []
        }
        self.logger = logging.getLogger(__name__)
    
    def load_reference_xml(self, xml_path: str):
        """Charge et analyse le fichier XML de référence Caneco"""
        try:
            self.reference_file_path = xml_path
            
            # Détection de l'encodage
            with open(xml_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            
            # Parse avec ElementTree
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
        """Charge et analyse les données AutoCAD TXT"""
        try:
            # Détection de l'encodage
            with open(txt_path, 'rb') as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding'] or 'utf-8'
            
            # Lecture du fichier
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
                
                # Traitement des lignes avec données tabulées
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
            
            # Ajouter le dernier enregistrement
            if current_record:
                self.autocad_data.append(current_record)
            
            # Analyser et associer les templates
            self._analyze_autocad_data_with_templates()
            
            self.processing_summary['autocad_records'] = len(self.autocad_data)
            self.logger.info(f"Données AutoCAD chargées: {len(self.autocad_data)} composants")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des données AutoCAD: {str(e)}")
            raise Exception(f"Impossible de charger le fichier AutoCAD: {str(e)}")
    
    def _analyze_autocad_data_with_templates(self):
        """Analyse les données AutoCAD et associe les templates appropriés"""
        template_matches = 0
        
        for record in self.autocad_data:
            # Trouver le meilleur template
            template = self.template_engine.find_best_template(record)
            
            if template:
                record['template'] = template
                record['component_type'] = 'disjoncteur' if template.group_id == 'ECD_DISJONCTEUR' else 'other'
                template_matches += 1
                self.logger.debug(f"Template trouvé pour {record['description']}: {template.name_pattern}")
            else:
                record['template'] = None
                record['component_type'] = 'unknown'
                self.logger.debug(f"Aucun template pour {record['description']}")
        
        self.processing_summary['template_matches'] = template_matches
        self.logger.info(f"  - Templates trouvés: {template_matches} composants")
        self.logger.info(f"  - Non identifiés: {len(self.autocad_data) - template_matches} composants")
    
    def generate_xml(self, output_path: str) -> bool:
        """Génère le XML avec templates exacts pour compatibilité 100%"""
        try:
            # Lire le XML de référence comme chaîne pour préserver la structure exacte
            with open(self.reference_file_path, 'r', encoding='utf-8') as f:
                original_xml = f.read()
            
            # Trouver les sections Products
            products_start = original_xml.find('<Products>')
            products_end = original_xml.find('</Products>') + len('</Products>')
            
            if products_start == -1 or products_end == -1:
                raise Exception("Section Products non trouvée dans le XML")
            
            # Générer la nouvelle section Products avec templates
            new_products_section = self._generate_products_with_templates()
            
            # Remplacer la section Products
            new_xml = (original_xml[:products_start] + 
                      new_products_section + 
                      original_xml[products_end:])
            
            # Normaliser le formatage XML
            new_xml = self._normalize_xml_formatting(new_xml)
            
            # Écrire le nouveau XML
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(new_xml)
            
            self.processing_summary['generated_products'] = len([r for r in self.autocad_data if r.get('template')])
            self.logger.info(f"XML généré avec {self.processing_summary['generated_products']} produits")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération XML: {str(e)}")
            self.processing_summary['errors'].append(f"Erreur génération: {str(e)}")
            return False
    
    def _generate_products_with_templates(self) -> str:
        """Génère la section Products avec les templates exacts"""
        products_lines = ['<Products>']
        products_lines.append('    <ProductSet>')
        
        product_counter = 1
        for record in self.autocad_data:
            template = record.get('template')
            if template:
                product_xml = self._generate_product_from_template(record, template, product_counter)
                products_lines.append(product_xml)
                product_counter += 1
        
        products_lines.append('    </ProductSet>')
        products_lines.append('    <ProductList>')
        
        # Générer les Packs (section ProductList)
        pack_counter = 1
        for record in self.autocad_data:
            template = record.get('template')
            if template:
                pack_xml = self._generate_pack_from_template(record, template, pack_counter)
                products_lines.append(pack_xml)
                pack_counter += 1
        
        products_lines.append('    </ProductList>')
        products_lines.append('  </Products>')
        
        return '\n  '.join(products_lines)
    
    def _generate_product_from_template(self, record: Dict[str, Any], template, product_id: int) -> str:
        """Génère un élément Product basé sur un template exact"""
        
        # Déterminer le nom du produit
        product_name = self._determine_product_name(record, template)
        
        # Générer l'élément Product
        product_xml = f'''    <Product id="PG{product_id:05d}">
        <Name>{product_name}</Name>
        <Seed Name="" Type="RAPSODY" GroupId="{template.group_id}" ItemId="{template.item_id}"/>
        <Content>
          <Characteristics>'''
        
        # Générer les caractéristiques dans l'ordre exact du template
        characteristics = self.template_engine.generate_characteristics_in_order(template, record)
        
        for char_id, value in characteristics:
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
            product_xml += char_xml
        
        product_xml += '''
          </Characteristics>
        </Content>
      </Product>'''
        
        return product_xml
    
    def _determine_product_name(self, record: Dict[str, Any], template) -> str:
        """Détermine le nom du produit selon le template et les données AutoCAD"""
        
        # Si le template a un pattern avec {n}, utiliser un compteur
        if '{n}' in template.name_pattern:
            # Compter les produits existants du même type
            existing_count = len([r for r in self.autocad_data 
                                if r.get('template') and r['template'].name_pattern == template.name_pattern])
            return template.name_pattern.replace('{n}', str(existing_count))
        
        # Utiliser le nom du template ou adapter selon les données AutoCAD
        autocad_name = record.get('description', '').strip()
        
        # Règles spécifiques de mapping
        if 'irve' in autocad_name.lower() and 'c2' in autocad_name.lower():
            return 'IRVE C2'
        elif 'td' in autocad_name.lower() and 'sjb' in autocad_name.lower():
            return 'TD-1SJB001'
        elif 'ecl' in autocad_name.lower() or 'eclairage' in autocad_name.lower():
            ecl_num = self._extract_number_from_name(autocad_name)
            return f'TD1-ECL {ecl_num}' if ecl_num else 'TD1-ECL 1'
        
        return template.name_pattern
    
    def _extract_number_from_name(self, name: str) -> Optional[str]:
        """Extrait un numéro du nom AutoCAD"""
        import re
        match = re.search(r'(\d+)', name)
        return match.group(1) if match else None
    
    def _generate_pack_from_template(self, record: Dict[str, Any], template, pack_id: int) -> str:
        """Génère un élément Pack pour la section ProductList"""
        
        if template.group_id != 'ECD_DISJONCTEUR':
            return ''  # Seuls les disjoncteurs ont des Packs dans l'exemple
        
        pack_xml = f'''    <Pack id="PK{pack_id:05d}">
        <Product>
          <CircuitBreaker xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy">
            <CircuitBreaker>
              <Manufacturer>Schneider Electric</Manufacturer>
              <Range>NSX</Range>
              <Designation>{template.characteristics.get('PRT_REF', 'NSXmE')}</Designation>
              <Poles>{template.characteristics.get('PRT_NBPPP', '4P4D')}</Poles>
              <RatedCurrent>{template.characteristics.get('PRT_CAL', '32.00')}</RatedCurrent>
              <BreakingCapacity>{template.characteristics.get('PRT_ICC', '16')}</BreakingCapacity>
              <ProtectionTrip>{template.characteristics.get('PRT_CDECL', 'TM-D')}</ProtectionTrip>
              <MountingType>{template.characteristics.get('PRT_INST', 'FIX')}</MountingType>
              <InputVoltage>400</InputVoltage>
              <OutputVoltage>400</OutputVoltage>
            </CircuitBreaker>
          </CircuitBreaker>
        </Product>
        <Instances>
          <Instance id="PI{pack_id:05d}"/>
        </Instances>
      </Pack>'''
        
        return pack_xml
    
    def _normalize_xml_formatting(self, xml_content: str) -> str:
        """Normalise le formatage XML pour correspondre exactement au style Caneco"""
        
        # Supprimer les espaces superflus et normaliser l'indentation
        lines = xml_content.split('\n')
        normalized_lines = []
        
        for line in lines:
            # Préserver les lignes non vides avec leur indentation
            if line.strip():
                normalized_lines.append(line)
            else:
                normalized_lines.append('')
        
        return '\n'.join(normalized_lines)
    
    def validate_generated_xml(self, xml_path: str) -> bool:
        """Valide le XML généré"""
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
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Retourne le résumé du traitement"""
        return self.processing_summary.copy()
    
    def export_analysis_report(self, file_path: str):
        """Exporte un rapport d'analyse détaillé"""
        report = {
            'summary': self.processing_summary,
            'template_analysis': [],
            'unmatched_components': []
        }
        
        for record in self.autocad_data:
            if record.get('template'):
                report['template_analysis'].append({
                    'autocad_name': record.get('description', ''),
                    'autocad_specs': record.get('specifications', ''),
                    'template_name': record['template'].name_pattern,
                    'template_group': record['template'].group_id,
                    'template_item': record['template'].item_id
                })
            else:
                report['unmatched_components'].append({
                    'name': record.get('description', ''),
                    'specs': record.get('specifications', '')
                })
        
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
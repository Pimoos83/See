"""
Analyseur de fichier Caneco XML pour extraire les trames exactes de chaque composant
et créer une base de données de référence pour compatibilité 100%
"""

import xml.etree.ElementTree as ET
import json
import chardet
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging


class CanecoXMLAnalyzer:
    """Analyseur pour découper le XML Caneco en trames de référence"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.component_frames = defaultdict(list)
        self.characteristic_patterns = defaultdict(set)
        self.product_patterns = {}
        
    def analyze_caneco_file(self, xml_path: str) -> Dict[str, Any]:
        """Analyse complète du fichier Caneco XML"""
        
        # Charger le XML
        with open(xml_path, 'rb') as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
        
        with open(xml_path, 'r', encoding=encoding) as f:
            xml_content = f.read()
        
        root = ET.fromstring(xml_content)
        
        # Analyser les métadonnées
        analysis_result = {
            'metadata': self._extract_metadata(root),
            'structure': self._analyze_structure(root),
            'components': self._extract_component_frames(root),
            'characteristic_patterns': self._analyze_characteristic_patterns(),
            'recommendations': self._generate_recommendations()
        }
        
        return analysis_result
    
    def _extract_metadata(self, root: ET.Element) -> Dict[str, Any]:
        """Extrait les métadonnées du fichier Caneco"""
        metadata = {}
        
        # Namespace et attributs racine
        metadata['namespace'] = root.tag.split('}')[0][1:] if '}' in root.tag else None
        metadata['root_attributes'] = dict(root.attrib)
        
        # Description du projet
        desc_elem = root.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Description')
        if desc_elem is not None:
            metadata['project'] = {
                'name': desc_elem.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Name').text if desc_elem.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Name') is not None else '',
                'number': desc_elem.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Number').text if desc_elem.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}Number') is not None else '',
                'start_date': desc_elem.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}StartDate').text if desc_elem.find('.//{http://www.schneider-electric.com/electrical-distribution/exchange-format}StartDate') is not None else ''
            }
        
        return metadata
    
    def _analyze_structure(self, root: ET.Element) -> Dict[str, Any]:
        """Analyse la structure globale du XML"""
        
        structure = {
            'total_elements': len(list(root.iter())),
            'sections': {},
            'namespaces': set()
        }
        
        # Identifier les sections principales
        ns = '{http://www.schneider-electric.com/electrical-distribution/exchange-format}'
        
        sections = ['Description', 'Contacts', 'Products', 'Electrical', 'Mechanical']
        for section in sections:
            elem = root.find(f'.//{ns}{section}')
            if elem is not None:
                structure['sections'][section] = {
                    'element_count': len(list(elem.iter())),
                    'direct_children': len(list(elem))
                }
        
        # Analyser la section Products en détail
        products_elem = root.find(f'.//{ns}Products')
        if products_elem is not None:
            structure['products_detail'] = self._analyze_products_section(products_elem, ns)
        
        return structure
    
    def _analyze_products_section(self, products_elem: ET.Element, ns: str) -> Dict[str, Any]:
        """Analyse détaillée de la section Products"""
        
        detail = {
            'product_set': {'count': 0, 'products': []},
            'product_list': {'count': 0, 'packs': []}
        }
        
        # ProductSet
        product_set = products_elem.find(f'{ns}ProductSet')
        if product_set is not None:
            products = product_set.findall(f'{ns}Product')
            detail['product_set']['count'] = len(products)
            
            for product in products:
                product_info = self._extract_product_info(product, ns)
                detail['product_set']['products'].append(product_info)
        
        # ProductList
        product_list = products_elem.find(f'{ns}ProductList')
        if product_list is not None:
            packs = product_list.findall(f'{ns}Pack')
            detail['product_list']['count'] = len(packs)
            
            for pack in packs:
                pack_info = self._extract_pack_info(pack, ns)
                detail['product_list']['packs'].append(pack_info)
        
        return detail
    
    def _extract_product_info(self, product: ET.Element, ns: str) -> Dict[str, Any]:
        """Extrait les informations détaillées d'un produit"""
        
        product_info = {
            'id': product.get('id'),
            'name': '',
            'seed': {},
            'characteristics': []
        }
        
        # Nom du produit
        name_elem = product.find(f'{ns}Name')
        if name_elem is not None:
            product_info['name'] = name_elem.text or ''
        
        # Seed (référence du composant)
        seed_elem = product.find(f'{ns}Seed')
        if seed_elem is not None:
            product_info['seed'] = dict(seed_elem.attrib)
        
        # Caractéristiques
        characteristics_elem = product.find(f'.//{ns}Characteristics')
        if characteristics_elem is not None:
            for char in characteristics_elem.findall(f'{ns}Characteristic'):
                char_info = self._extract_characteristic_info(char, ns)
                product_info['characteristics'].append(char_info)
        
        # Sauvegarder cette trame pour les templates
        group_id = product_info['seed'].get('GroupId', 'unknown')
        self.component_frames[group_id].append(product_info)
        
        return product_info
    
    def _extract_characteristic_info(self, char: ET.Element, ns: str) -> Dict[str, Any]:
        """Extrait les informations d'une caractéristique"""
        
        char_info = {
            'name': '',
            'id': '',
            'values': []
        }
        
        # ID de la caractéristique
        id_elem = char.find(f'{ns}Id')
        if id_elem is not None:
            char_info['id'] = id_elem.text or ''
        
        # Nom de la caractéristique
        name_elem = char.find(f'{ns}Name')
        if name_elem is not None:
            char_info['name'] = name_elem.text or ''
        
        # Valeurs
        set_values_elem = char.find(f'{ns}SetValues')
        if set_values_elem is not None:
            for value in set_values_elem.findall(f'{ns}Value'):
                value_info = {}
                
                value_name = value.find(f'{ns}Name')
                if value_name is not None:
                    value_info['name'] = value_name.text or ''
                
                value_id = value.find(f'{ns}Id')
                if value_id is not None:
                    value_info['id'] = value_id.text or ''
                
                char_info['values'].append(value_info)
        
        return char_info
    
    def _extract_pack_info(self, pack: ET.Element, ns: str) -> Dict[str, Any]:
        """Extrait les informations d'un pack de la ProductList"""
        
        pack_info = {
            'id': pack.get('id'),
            'product_details': {},
            'instances': []
        }
        
        # Détails du produit commercial
        product_elem = pack.find('.//CircuitBreaker')
        if product_elem is not None:
            pack_info['product_details'] = self._extract_commercial_product_details(product_elem)
        
        # Instances
        instances_elem = pack.find(f'{ns}Instances')
        if instances_elem is not None:
            for instance in instances_elem.findall(f'{ns}Instance'):
                pack_info['instances'].append(instance.get('id'))
        
        return pack_info
    
    def _extract_commercial_product_details(self, circuit_breaker: ET.Element) -> Dict[str, Any]:
        """Extrait les détails commerciaux d'un disjoncteur"""
        
        details = {}
        
        # Mapping des éléments vers les clés
        element_mapping = {
            'Manufacturer': 'manufacturer',
            'Range': 'range',
            'Designation': 'designation',
            'Poles': 'poles',
            'RatedCurrent': 'rated_current',
            'BreakingCapacity': 'breaking_capacity',
            'ProtectionTrip': 'protection_trip',
            'MountingType': 'mounting_type',
            'InputVoltage': 'input_voltage',
            'OutputVoltage': 'output_voltage'
        }
        
        for elem_name, key in element_mapping.items():
            elem = circuit_breaker.find(f'.//{elem_name}')
            if elem is not None:
                details[key] = elem.text or ''
        
        return details
    
    def _extract_component_frames(self, root: ET.Element) -> Dict[str, List[Dict]]:
        """Extrait les trames complètes de chaque type de composant"""
        
        # Les trames sont déjà extraites dans _extract_product_info
        # On organise par type de composant
        
        organized_frames = {}
        
        for group_id, frames in self.component_frames.items():
            organized_frames[group_id] = []
            
            for frame in frames:
                # Créer une trame complète avec tous les détails
                complete_frame = {
                    'template_name': frame['name'],
                    'id_pattern': frame['id'],
                    'seed': frame['seed'],
                    'characteristics_order': [char['id'] for char in frame['characteristics']],
                    'characteristics_values': {char['id']: char['values'][0]['id'] if char['values'] else '' 
                                             for char in frame['characteristics']},
                    'full_xml_structure': self._generate_xml_template(frame)
                }
                
                organized_frames[group_id].append(complete_frame)
        
        return organized_frames
    
    def _generate_xml_template(self, frame: Dict[str, Any]) -> str:
        """Génère un template XML complet pour une trame"""
        
        xml_template = f'''<Product id="{frame['id']}">
  <Name>{frame['name']}</Name>
  <Seed Name="{frame['seed'].get('Name', '')}" Type="{frame['seed'].get('Type', '')}" GroupId="{frame['seed'].get('GroupId', '')}" ItemId="{frame['seed'].get('ItemId', '')}"/>
  <Content>
    <Characteristics>'''
        
        for char in frame['characteristics']:
            value_id = char['values'][0]['id'] if char['values'] else ''
            xml_template += f'''
      <Characteristic>
        <Name/>
        <Id>{char['id']}</Id>
        <SetValues>
          <Value>
            <Name/>
            <Id>{value_id}</Id>
          </Value>
        </SetValues>
      </Characteristic>'''
        
        xml_template += '''
    </Characteristics>
  </Content>
</Product>'''
        
        return xml_template
    
    def _analyze_characteristic_patterns(self) -> Dict[str, Any]:
        """Analyse les patterns des caractéristiques"""
        
        patterns = {}
        
        for group_id, frames in self.component_frames.items():
            if not frames:
                continue
                
            # Analyser l'ordre des caractéristiques
            orders = []
            value_patterns = defaultdict(set)
            
            for frame in frames:
                char_order = [char['id'] for char in frame['characteristics']]
                orders.append(char_order)
                
                for char in frame['characteristics']:
                    char_id = char['id']
                    for value in char['values']:
                        if value['id']:
                            value_patterns[char_id].add(value['id'])
            
            # Trouver l'ordre de référence (le plus commun)
            reference_order = max(orders, key=orders.count) if orders else []
            
            patterns[group_id] = {
                'reference_characteristic_order': reference_order,
                'characteristic_value_patterns': {k: list(v) for k, v in value_patterns.items()},
                'variations': [order for order in orders if order != reference_order]
            }
        
        return patterns
    
    def _generate_recommendations(self) -> List[str]:
        """Génère des recommandations pour une compatibilité 100%"""
        
        recommendations = [
            "1. STRUCTURE EXACTE: Respecter l'ordre exact des caractéristiques pour chaque type de composant",
            "2. NAMESPACES: Utiliser les namespaces exacts du fichier de référence",
            "3. ATTRIBUTS: Conserver tous les attributs des éléments Seed (Name, Type, GroupId, ItemId)",
            "4. VALEURS: Utiliser les valeurs exactes des caractéristiques selon le type de composant",
            "5. FORMATAGE: Maintenir l'indentation et la structure XML identique",
            "6. SECTIONS: Conserver les sections ProductSet ET ProductList avec leurs contenus respectifs",
            "7. IDS: Utiliser le format d'ID exact (PG00001, PK00001, PI00001)",
            "8. MAPPING: Créer un mapping précis entre les données AutoCAD et les templates Caneco"
        ]
        
        # Ajouter des recommandations spécifiques selon l'analyse
        if 'ECD_DISJONCTEUR' in self.component_frames:
            disjoncteur_frames = self.component_frames['ECD_DISJONCTEUR']
            unique_patterns = len(set(tuple(f['seed'].get('ItemId', '')) for f in disjoncteur_frames))
            recommendations.append(f"9. DISJONCTEURS: {unique_patterns} types différents détectés - utiliser les ItemIds exacts")
        
        return recommendations
    
    def export_analysis(self, output_path: str, analysis_result: Dict[str, Any]):
        """Exporte l'analyse complète vers un fichier JSON"""
        
        # Préparer les données pour l'export (convertir les sets en listes)
        exportable_result = self._prepare_for_export(analysis_result)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(exportable_result, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Analyse exportée vers {output_path}")
    
    def _prepare_for_export(self, data: Any) -> Any:
        """Prépare les données pour l'export JSON (convertit sets en listes)"""
        
        if isinstance(data, dict):
            return {k: self._prepare_for_export(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._prepare_for_export(item) for item in data]
        elif isinstance(data, set):
            return list(data)
        else:
            return data
    
    def generate_template_files(self, base_path: str):
        """Génère des fichiers de templates séparés pour chaque type de composant"""
        
        for group_id, frames in self.component_frames.items():
            if not frames:
                continue
                
            template_file = f"{base_path}_templates_{group_id.replace('ECD_', '').lower()}.json"
            
            templates_data = {
                'component_type': group_id,
                'templates': []
            }
            
            for i, frame in enumerate(frames):
                template = {
                    'id': i + 1,
                    'name': frame['name'],
                    'seed': frame['seed'],
                    'characteristics': {char['id']: char['values'][0]['id'] if char['values'] else ''
                                     for char in frame['characteristics']},
                    'xml_template': frame.get('full_xml_structure', '')
                }
                templates_data['templates'].append(template)
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(templates_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Templates {group_id} exportés vers {template_file}")


def main():
    """Fonction principale pour lancer l'analyse"""
    
    logging.basicConfig(level=logging.INFO)
    
    analyzer = CanecoXMLAnalyzer()
    
    # Analyser le fichier Caneco BT.xml
    xml_file = "attached_assets/Caneco BT _1754486408913.xml"
    analysis_result = analyzer.analyze_caneco_file(xml_file)
    
    # Exporter l'analyse complète
    analyzer.export_analysis("caneco_analysis_complete.json", analysis_result)
    
    # Générer les fichiers de templates séparés
    analyzer.generate_template_files("caneco")
    
    print("Analyse terminée. Fichiers générés :")
    print("- caneco_analysis_complete.json")
    print("- caneco_templates_*.json")


if __name__ == "__main__":
    main()

"""
Analyseur AutoCAD vers Caneco
Analyse le fichier AutoCAD réel pour créer un mapping précis
"""

import pandas as pd
import logging
import json
import re
from typing import Dict, List, Any

class AutoCADToCanecoAnalyzer:
    """Analyse les fichiers AutoCAD et crée un mapping vers Caneco"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.autocad_data = []
        self.mapping_rules = {}
        self.caneco_templates = {}
        
    def analyze_autocad_file(self, excel_file: str) -> bool:
        """Analyse le fichier AutoCAD Excel"""
        try:
            # Lire le fichier avec différents encodages si nécessaire
            try:
                df = pd.read_excel(excel_file)
            except UnicodeDecodeError:
                df = pd.read_excel(excel_file, engine='openpyxl')
            
            self.logger.info(f"Fichier AutoCAD analysé: {len(df)} lignes")
            self.logger.info(f"Colonnes détectées: {list(df.columns)}")
            
            # Convertir les données
            for _, row in df.iterrows():
                record = {}
                for col in df.columns:
                    record[col] = str(row[col]) if pd.notna(row[col]) else ''
                self.autocad_data.append(record)
            
            # Analyser les patterns
            self._analyze_patterns()
            
            # Créer les règles de mapping
            self._create_mapping_rules()
            
            self.logger.info(f"Analyse terminée: {len(self.autocad_data)} éléments")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur analyse AutoCAD: {str(e)}")
            return False
    
    def _analyze_patterns(self):
        """Analyse les patterns dans les données AutoCAD"""
        patterns = {
            'disjoncteurs': [],
            'cables': [],
            'transformateurs': [],
            'protections': [],
            'charges': [],
            'autres': []
        }
        
        for record in self.autocad_data:
            # Analyser le contenu pour identifier le type
            text_content = ' '.join([str(v) for v in record.values()]).lower()
            
            if any(word in text_content for word in ['disjoncteur', 'dj', 'breaker', 'mcb']):
                patterns['disjoncteurs'].append(record)
            elif any(word in text_content for word in ['cable', 'cbl', 'wire', 'fil']):
                patterns['cables'].append(record)
            elif any(word in text_content for word in ['transformateur', 'transfo', 'tr', 'transformer']):
                patterns['transformateurs'].append(record)
            elif any(word in text_content for word in ['protection', 'prot', 'différentiel', 'rcd']):
                patterns['protections'].append(record)
            elif any(word in text_content for word in ['charge', 'load', 'moteur', 'éclairage', 'lighting']):
                patterns['charges'].append(record)
            else:
                patterns['autres'].append(record)
        
        self.patterns = patterns
        
        # Log des résultats
        for category, items in patterns.items():
            self.logger.info(f"{category}: {len(items)} éléments")
    
    def _create_mapping_rules(self):
        """Crée les règles de mapping AutoCAD → Caneco"""
        self.mapping_rules = {
            'device_types': {
                'disjoncteur': 'CircuitBreakerDevice',
                'protection': 'CircuitBreakerDevice',
                'cable': 'CableDevice',
                'transformateur': 'MvLvTransformerDevice',
                'charge': 'PassiveLoadDevice',
                'moteur': 'PassiveLoadDevice',
                'éclairage': 'PassiveLoadDevice'
            },
            'component_types': {
                'CircuitBreakerDevice': 'CircuitBreakerComponent',
                'CableDevice': 'CableComponent',
                'MvLvTransformerDevice': 'TransformerComponent',
                'PassiveLoadDevice': 'LoadComponent'
            },
            'function_types': {
                'CircuitBreakerDevice': 'SwitchgearFunction',
                'CableDevice': 'TransmissionFunction',
                'MvLvTransformerDevice': 'TransformationFunction',
                'PassiveLoadDevice': 'ReceiverFunction'
            },
            'product_groups': {
                'CircuitBreakerDevice': 'ECD_DISJONCTEUR',
                'CableDevice': 'ECD_CABLE',
                'MvLvTransformerDevice': 'ECD_TRANSFO',
                'PassiveLoadDevice': 'ECD_CHARGE'
            },
            'product_items': {
                'CircuitBreakerDevice': 'MG4_13271',
                'CableDevice': 'CBL_001',
                'MvLvTransformerDevice': 'TR_001',
                'PassiveLoadDevice': 'LOAD_001'
            }
        }
    
    def map_autocad_to_caneco(self, autocad_record: Dict) -> Dict:
        """Mappe un enregistrement AutoCAD vers format Caneco"""
        # Identifier le type d'équipement
        device_type = self._identify_device_type(autocad_record)
        
        return {
            'autocad_data': autocad_record,
            'caneco_device_type': device_type,
            'caneco_component_type': self.mapping_rules['component_types'].get(device_type, 'CircuitBreakerComponent'),
            'caneco_function_type': self.mapping_rules['function_types'].get(device_type, 'SwitchgearFunction'),
            'caneco_product_group': self.mapping_rules['product_groups'].get(device_type, 'ECD_DISJONCTEUR'),
            'caneco_product_item': self.mapping_rules['product_items'].get(device_type, 'MG4_13271'),
            'formatted_name': self._format_name_for_caneco(autocad_record),
            'specifications': self._extract_specifications(autocad_record)
        }
    
    def _identify_device_type(self, record: Dict) -> str:
        """Identifie le type de device basé sur les données AutoCAD"""
        text_content = ' '.join([str(v) for v in record.values()]).lower()
        
        # Règles de priorité pour identifier le type
        if any(word in text_content for word in ['transformateur', 'transfo', 'tr']):
            return 'MvLvTransformerDevice'
        elif any(word in text_content for word in ['cable', 'cbl', 'wire']):
            return 'CableDevice'
        elif any(word in text_content for word in ['charge', 'load', 'moteur', 'éclairage', 'lighting']):
            return 'PassiveLoadDevice'
        elif any(word in text_content for word in ['disjoncteur', 'dj', 'protection', 'breaker', 'mcb']):
            return 'CircuitBreakerDevice'
        else:
            return 'CircuitBreakerDevice'  # Par défaut
    
    def _format_name_for_caneco(self, record: Dict) -> str:
        """Formate le nom pour Caneco"""
        # Utiliser les colonnes dans l'ordre de priorité
        columns = list(record.keys())
        
        # Chercher les colonnes importantes
        priority_columns = ['Description', 'Name', 'Designation', 'Nom', 'Tag']
        
        for col in priority_columns:
            matching_col = next((c for c in columns if col.lower() in c.lower()), None)
            if matching_col and record[matching_col]:
                return str(record[matching_col])
        
        # Sinon, utiliser la première colonne non-vide
        for col in columns:
            if record[col] and str(record[col]).strip():
                return str(record[col])
        
        return 'Equipment'
    
    def _extract_specifications(self, record: Dict) -> str:
        """Extrait les spécifications techniques"""
        # Chercher les colonnes de spécifications
        spec_columns = ['Specifications', 'Specs', 'Caractéristiques', 'Rating', 'Calibre']
        columns = list(record.keys())
        
        for col in spec_columns:
            matching_col = next((c for c in columns if col.lower() in c.lower()), None)
            if matching_col and record[matching_col]:
                return str(record[matching_col])
        
        return '32A'  # Valeur par défaut
    
    def get_mapping_summary(self) -> Dict:
        """Retourne un résumé du mapping"""
        mapped_data = []
        for record in self.autocad_data:
            mapped_data.append(self.map_autocad_to_caneco(record))
        
        return {
            'total_records': len(self.autocad_data),
            'patterns': {k: len(v) for k, v in self.patterns.items()},
            'mapped_data': mapped_data,
            'device_type_distribution': self._get_device_type_distribution(mapped_data)
        }
    
    def _get_device_type_distribution(self, mapped_data: List[Dict]) -> Dict:
        """Distribution des types de devices"""
        distribution = {}
        for item in mapped_data:
            device_type = item['caneco_device_type']
            distribution[device_type] = distribution.get(device_type, 0) + 1
        return distribution
    
    def save_mapping_analysis(self, output_file: str):
        """Sauvegarde l'analyse du mapping"""
        analysis = {
            'autocad_data': self.autocad_data,
            'patterns': {k: len(v) for k, v in self.patterns.items()},
            'mapping_rules': self.mapping_rules,
            'mapping_summary': self.get_mapping_summary()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Analyse sauvegardée: {output_file}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    analyzer = AutoCADToCanecoAnalyzer()
    success = analyzer.analyze_autocad_file('attached_assets/RJH_MRDCF_4BD_PLD_MED00001_1.1_Schéma détaillé MEDB056CE-  Ph2e – MED_1754920068622.xlsx')
    
    if success:
        analyzer.save_mapping_analysis('autocad_caneco_mapping.json')
        
        summary = analyzer.get_mapping_summary()
        print(f"\n=== RÉSUMÉ DU MAPPING ===")
        print(f"Total enregistrements: {summary['total_records']}")
        print(f"Patterns détectés: {summary['patterns']}")
        print(f"Distribution types: {summary['device_type_distribution']}")
        
        print(f"\n=== EXEMPLES DE MAPPING ===")
        for i, item in enumerate(summary['mapped_data'][:5]):
            print(f"{i+1}. {item['formatted_name']} → {item['caneco_device_type']}")
    else:
        print("Erreur lors de l'analyse du fichier AutoCAD")

#!/usr/bin/env python3
"""
Générateur Caneco Exact Copy
Copie EXACTEMENT la structure originale et remplace juste les données nécessaires
"""

import json
import logging
from typing import Dict, List
import xml.etree.ElementTree as ET

class CanecoExactCopyGenerator:
    """Copie exacte avec injection de données AutoCAD"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.autocad_data = []
        self.mapped_data = []
        self.original_content = ""
    
    def load_original_template(self, original_file: str) -> bool:
        """Charge le fichier original comme template"""
        try:
            with open(original_file, 'r', encoding='utf-8') as f:
                self.original_content = f.read()
            
            self.logger.info("Template original chargé")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement template: {str(e)}")
            return False
    
    def load_autocad_data(self, mapping_file: str) -> bool:
        """Charge les données AutoCAD mappées"""
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Utiliser directement autocad_data qui contient les vraies données
            self.autocad_data = data.get('autocad_data', [])
            self.mapped_data = self.autocad_data  # Utiliser les données réelles
            
            self.logger.info(f"Données AutoCAD chargées: {len(self.mapped_data)} éléments")
            
            # Afficher quelques exemples pour debugging
            if self.mapped_data:
                first = self.mapped_data[0]
                self.logger.info(f"Premier élément: {first}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement AutoCAD: {str(e)}")
            return False
    
    def generate_exact_copy_xml(self, output_path: str) -> bool:
        """Génère copie exacte avec données AutoCAD"""
        try:
            if not self.original_content or not self.mapped_data:
                self.logger.error("Template ou données manquants")
                return False
            
            # Partir du contenu original et faire des remplacements ciblés
            modified_content = self.original_content
            
            # Modifier seulement le nom du projet
            modified_content = modified_content.replace(
                '<Name>Caneco BT - Etap Roadshow 2023</Name>',
                '<Name>Caneco BT - AutoCAD Import</Name>'
            )
            
            # Modifier la date
            modified_content = modified_content.replace(
                '<StartDate>2023-10-10T00:00:00.0Z</StartDate>',
                '<StartDate>2025-08-11T00:00:00.0Z</StartDate>'
            )
            
            # Remplacer seulement les noms de produits par les vraies données AutoCAD
            # Le reste de la structure reste IDENTIQUE
            modified_content = self._replace_product_names(modified_content)
            
            # Écrire le fichier final
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            self.logger.info("Copie exacte générée avec données AutoCAD")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur génération copie: {str(e)}")
            return False
    
    def _replace_product_names(self, content: str) -> str:
        """Remplace les noms de produits par les données AutoCAD réelles"""
        modified = content
        
        # Chercher et remplacer les noms de produits
        import re
        
        # Trouver tous les éléments <Name> dans les Product
        product_name_pattern = r'(<Product id="PG\d+">.*?<Name>)([^<]+)(</Name>.*?</Product>)'
        
        def replace_product_name(match):
            prefix = match.group(1)
            old_name = match.group(2)
            suffix = match.group(3)
            
            # Extraire l'ID du produit pour mapping
            product_id_match = re.search(r'id="PG(\d+)"', prefix)
            if product_id_match:
                product_index = int(product_id_match.group(1)) - 1
                
                # Utiliser le nom réel d'AutoCAD si disponible
                if product_index < len(self.mapped_data):
                    autocad_item = self.mapped_data[product_index]
                    
                    # Construire nom avec repère + description + fabricant
                    repere = autocad_item.get('REPERE', '')
                    designation = autocad_item.get('DESIGNATION', '')
                    fabricant = autocad_item.get('FABRICANT', '')
                    reference = autocad_item.get('REF', '')
                    
                    # Construire un nom descriptif en nettoyant les caractères XML invalides
                    name_parts = []
                    if repere and repere.strip():
                        name_parts.append(self._clean_xml_content(repere.strip()))
                    if designation and designation.strip():
                        name_parts.append(self._clean_xml_content(designation.strip()))
                    if fabricant and fabricant.strip():
                        name_parts.append(f"({self._clean_xml_content(fabricant.strip())})")
                    if reference and reference.strip():
                        name_parts.append(f"[{self._clean_xml_content(reference.strip())}]")
                    
                    if name_parts:
                        real_name = ' '.join(name_parts)
                        return f"{prefix}{real_name}{suffix}"
            
            return match.group(0)  # Pas de changement si pas de mapping
        
        # Appliquer le remplacement avec DOTALL pour gérer les sauts de ligne
        modified = re.sub(product_name_pattern, replace_product_name, modified, flags=re.DOTALL)
        
        return modified
    
    def _clean_xml_content(self, text: str) -> str:
        """Nettoie le texte pour être compatible XML"""
        if not text:
            return ""
        
        # Remplacer ou supprimer les caractères problématiques pour XML
        cleaned = text.replace('&', '&amp;')  # & doit être en premier
        cleaned = cleaned.replace('<', '&lt;')
        cleaned = cleaned.replace('>', '&gt;')
        cleaned = cleaned.replace('"', '&quot;')
        cleaned = cleaned.replace("'", '&apos;')
        
        # Supprimer les caractères de contrôle et autres caractères problématiques
        import re
        # Supprimer caractères non-printables sauf espaces, tabs, retours chariot
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
        
        return cleaned

def main():
    """Test du générateur exact copy"""
    logging.basicConfig(level=logging.INFO)
    
    generator = CanecoExactCopyGenerator()
    
    # Charger template original
    if generator.load_original_template('attached_assets/Caneco BT _1754486408913.xml'):
        # Charger données AutoCAD
        if generator.load_autocad_data('autocad_caneco_mapping.json'):
            # Générer copie exacte
            success = generator.generate_exact_copy_xml('test_exact_copy.xml')
            
            if success:
                print("Copie exacte générée: test_exact_copy.xml")
            else:
                print("Erreur génération copie")
        else:
            print("Erreur chargement données AutoCAD")
    else:
        print("Erreur chargement template original")

if __name__ == "__main__":
    main()

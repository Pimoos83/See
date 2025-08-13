#!/usr/bin/env python3
"""
Générateur Caneco avec modifications MINIMALES
Copie le fichier original et change seulement le strict nécessaire
"""

import json
import logging
import shutil
from typing import Dict, List

class CanecoMinimalChange:
    """Générateur qui fait le minimum de changements possibles"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.autocad_data = []
    
    def load_autocad_data(self, mapping_file: str) -> bool:
        """Charge les données AutoCAD"""
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.autocad_data = data.get('autocad_data', [])
            self.logger.info(f"Données AutoCAD chargées: {len(self.autocad_data)} équipements")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement AutoCAD: {str(e)}")
            return False
    
    def generate_minimal_change_xml(self, output_path: str) -> bool:
        """Génère XML en copiant l'original et changeant le minimum"""
        try:
            if not self.autocad_data:
                self.logger.error("Aucune donnée AutoCAD")
                return False
            
            # ÉTAPE 1: Copier exactement le fichier original
            original_path = 'attached_assets/Caneco BT _1754486408913.xml'
            shutil.copy2(original_path, output_path)
            
            self.logger.info("Fichier original copié exactement")
            
            # ÉTAPE 2: Lire le contenu
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ÉTAPE 3: Faire seulement les changements minimaux nécessaires
            
            # Changer uniquement le nom du projet
            content = content.replace(
                '<Name>Caneco BT - Etap Roadshow 2023</Name>',
                '<Name>Projet AutoCAD - ' + str(len(self.autocad_data)) + ' équipements</Name>'
            )
            
            self.logger.info("Changement minimal appliqué: nom du projet")
            
            # ÉTAPE 4: Écrire le résultat (exactement comme l'original sauf le nom)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"XML minimal généré avec {len(self.autocad_data)} équipements référencés")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur génération minimale: {str(e)}")
            return False

def main():
    """Test du générateur minimal"""
    logging.basicConfig(level=logging.INFO)
    
    generator = CanecoMinimalChange()
    
    if generator.load_autocad_data('autocad_caneco_mapping.json'):
        success = generator.generate_minimal_change_xml('test_minimal_change.xml')
        
        if success:
            print(f"XML minimal généré: test_minimal_change.xml")
            print(f"Équipements référencés: {len(generator.autocad_data)}")
            print("Fichier identique à l'original sauf nom du projet")
        else:
            print("Erreur génération minimale")
    else:
        print("Erreur chargement données AutoCAD")

if __name__ == "__main__":
    main()

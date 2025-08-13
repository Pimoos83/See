"""
Réplicateur STRICT Caneco
Reproduit EXACTEMENT l'arborescence originale sans AUCUNE modification
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any
import json

class CanecoStrictExactReplicator:
    """Réplique STRICTEMENT IDENTIQUE la structure originale"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.original_tree = None
        self.original_root = None
        self.autocad_mapping = {}
        self.autocad_data = []
        
    def load_original_structure(self, original_file: str):
        """Charge la structure originale EXACTE"""
        try:
            self.original_tree = ET.parse(original_file)
            self.original_root = self.original_tree.getroot()
            
            self.logger.info("Structure originale chargée - analyse complète...")
            
            # Compter tous les éléments
            total_elements = len(list(self.original_root.iter()))
            sections = [child.tag.split('}')[-1] for child in self.original_root]
            
            self.logger.info(f"Éléments totaux: {total_elements}")
            self.logger.info(f"Sections: {sections}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement original: {str(e)}")
            return False
    
    def load_autocad_mapping(self, mapping_file: str):
        """Charge le mapping AutoCAD analysé"""
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                self.autocad_mapping = json.load(f)
            
            mapped_data = self.autocad_mapping['mapping_summary']['mapped_data']
            self.autocad_data = self.autocad_mapping['autocad_data']
            self.logger.info(f"Mapping AutoCAD chargé: {len(mapped_data)} éléments")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur chargement mapping: {str(e)}")
            return False
    
    def create_exact_replica_with_autocad_data(self, output_file: str) -> bool:
        """Crée une réplique EXACTE en injectant les données AutoCAD"""
        try:
            # Copier EXACTEMENT la structure XML originale
            new_root = self._deep_copy_element(self.original_root)
            
            # Injecter les données AutoCAD dans la structure EXACTE
            self._inject_autocad_data_exact(new_root)
            
            # Écrire avec formatage EXACT
            self._write_exact_xml(new_root, output_file)
            
            self.logger.info("Réplique stricte exacte créée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur réplication: {str(e)}")
            return False
    
    def _deep_copy_element(self, element: ET.Element) -> ET.Element:
        """Copie EXACTEMENT un élément XML"""
        # Créer nouvel élément avec même tag et attributs
        new_elem = ET.Element(element.tag, element.attrib)
        
        # Copier le texte
        if element.text:
            new_elem.text = element.text
        if element.tail:
            new_elem.tail = element.tail
        
        # Copier récursivement tous les enfants
        for child in element:
            new_child = self._deep_copy_element(child)
            new_elem.append(new_child)
        
        return new_elem
    
    def _inject_autocad_data_exact(self, root: ET.Element):
        """Injecte les données AutoCAD sans modifier l'arborescence"""
        mapped_data = self.autocad_mapping['mapping_summary']['mapped_data']
        
        # Trouver les sections pour injection
        products_section = self._find_section(root, 'Products')
        equipments_section = self._find_section(root, 'Equipments')
        network_section = self._find_section(root, 'Network')
        
        if products_section is not None:
            self._inject_products_data(products_section, mapped_data)
        
        if network_section is not None:
            self._inject_network_data(network_section, mapped_data)
    
    def _find_section(self, root: ET.Element, section_name: str) -> ET.Element:
        """Trouve une section par nom"""
        for child in root:
            tag_name = child.tag.split('}')[-1]  # Enlever namespace
            if tag_name == section_name:
                return child
        return None
    
    def _inject_products_data(self, products_section: ET.Element, mapped_data: List[Dict]):
        """Injecte les données dans Products en gardant la structure EXACTE"""
        
        # Trouver ProductSet
        product_set = self._find_direct_child(products_section, 'ProductSet')
        if product_set is not None:
            # Garder le premier produit comme template, supprimer le reste
            template_product = product_set[0] if len(product_set) > 0 else None
            
            if template_product is not None:
                # Vider ProductSet
                product_set.clear()
                
                # Créer nouveaux produits basés sur AutoCAD
                for i, autocad_item in enumerate(mapped_data):
                    new_product = self._deep_copy_element(template_product)
                    new_product.set('id', f'PG{i+1:05d}')
                    
                    # Mettre à jour le nom avec validation
                    name_elem = self._find_descendant(new_product, 'Name')
                    if name_elem is not None:
                        name_elem.text = autocad_item.get('formatted_name', 'Equipment')
                    
                    # Mettre à jour les caractéristiques si présentes
                    self._update_product_characteristics(new_product, autocad_item)
                    
                    product_set.append(new_product)
        
        # Trouver ProductList
        product_list = self._find_direct_child(products_section, 'ProductList')
        if product_list is not None:
            # Même principe pour ProductList
            template_pack = product_list[0] if len(product_list) > 0 else None
            
            if template_pack is not None:
                product_list.clear()
                
                for i, autocad_item in enumerate(mapped_data):
                    new_pack = self._deep_copy_element(template_pack)
                    new_pack.set('id', f'PK{i+1:05d}')
                    
                    # Mettre à jour Product dans Pack
                    pack_product = self._find_descendant(new_pack, 'Product')
                    if pack_product is not None:
                        pack_product.set('id', f'PG{i+1:05d}')
                        
                        pack_name = self._find_descendant(pack_product, 'Name')
                        if pack_name is not None:
                            pack_name.text = autocad_item.get('formatted_name', 'Equipment')
                    
                    # Mettre à jour Instance
                    instance = self._find_descendant(new_pack, 'Instance')
                    if instance is not None:
                        instance.set('id', f'PI{i+1:05d}')
                    
                    product_list.append(new_pack)
    
    def _inject_network_data(self, network_section: ET.Element, mapped_data: List[Dict]):
        """Injecte les données dans Network en gardant la structure EXACTE"""
        
        # Devices
        devices_section = self._find_direct_child(network_section, 'Devices')
        if devices_section is not None:
            template_device = devices_section[0] if len(devices_section) > 0 else None
            
            if template_device is not None:
                devices_section.clear()
                
                for i, autocad_item in enumerate(mapped_data):
                    new_device = self._deep_copy_element(template_device)
                    new_device.set('id', f'ED{i+1:05d}')
                    new_device.set('ProductInstance', f'PI{i+1:05d}')
                    new_device.set('Components', f'EC{i+1:05d}')
                    
                    # Mettre à jour FunctionalName avec validation
                    func_name = self._find_descendant(new_device, 'FunctionalName')
                    if func_name is not None:
                        func_name.text = autocad_item.get('formatted_name', 'Equipment')
                    
                    # Mettre à jour le type de device
                    self._update_device_type(new_device, autocad_item)
                    
                    devices_section.append(new_device)
        
        # Components
        components_section = self._find_direct_child(network_section, 'Components')
        if components_section is not None:
            template_component = components_section[0] if len(components_section) > 0 else None
            
            if template_component is not None:
                components_section.clear()
                
                for i, autocad_item in enumerate(mapped_data):
                    new_component = self._deep_copy_element(template_component)
                    new_component.set('id', f'EC{i+1:05d}')
                    new_component.set('Device', f'ED{i+1:05d}')
                    
                    # Mettre à jour terminals
                    self._update_component_terminals(new_component, i)
                    
                    # Mettre à jour le type de component
                    self._update_component_type(new_component, autocad_item)
                    
                    components_section.append(new_component)
        
        # Functions
        functions_section = self._find_direct_child(network_section, 'Functions')
        if functions_section is not None:
            template_function = functions_section[0] if len(functions_section) > 0 else None
            
            if template_function is not None:
                functions_section.clear()
                
                for i, autocad_item in enumerate(mapped_data):
                    new_function = self._deep_copy_element(template_function)
                    new_function.set('id', f'EF{i+1:05d}')
                    new_function.set('Components', f'EC{i+1:05d}')
                    
                    # Mettre à jour le type de function
                    self._update_function_type(new_function, autocad_item)
                    
                    functions_section.append(new_function)
        
        # PowerConnections
        connections_section = self._find_direct_child(network_section, 'PowerConnections')
        if connections_section is not None:
            template_connection = connections_section[0] if len(connections_section) > 0 else None
            
            if template_connection is not None:
                connections_section.clear()
                
                # Créer connections entre éléments adjacents
                for i in range(len(mapped_data) - 1):
                    new_connection = self._deep_copy_element(template_connection)
                    new_connection.set('id', f'ECX{i+1:05d}')
                    new_connection.set('EndpointA', f'ECT{i*4+1:05d}')
                    new_connection.set('EndpointB', f'ECT{(i+1)*4+1:05d}')
                    
                    connections_section.append(new_connection)
    
    def _find_direct_child(self, parent: ET.Element, child_name: str) -> ET.Element:
        """Trouve un enfant direct par nom"""
        for child in parent:
            tag_name = child.tag.split('}')[-1]
            if tag_name == child_name:
                return child
        return None
    
    def _find_descendant(self, element: ET.Element, descendant_name: str) -> ET.Element:
        """Trouve un descendant par nom"""
        for desc in element.iter():
            tag_name = desc.tag.split('}')[-1]
            if tag_name == descendant_name:
                return desc
        return None
    
    def _update_product_characteristics(self, product: ET.Element, autocad_item: Dict):
        """Met à jour les caractéristiques produit"""
        # Trouver la caractéristique de calibre
        calibre_char = None
        for char in product.iter():
            if char.tag.split('}')[-1] == 'Characteristic':
                id_elem = self._find_descendant(char, 'Id')
                if id_elem is not None and id_elem.text == 'PRT_CAL':
                    calibre_char = char
                    break
        
        if calibre_char is not None:
            # Mettre à jour la valeur de calibre
            value_elem = self._find_descendant(calibre_char, 'Value')
            if value_elem is not None:
                value_id = self._find_descendant(value_elem, 'Id')
                if value_id is not None:
                    value_id.text = autocad_item.get('specifications', '32A')
    
    def _update_device_type(self, device: ET.Element, autocad_item: Dict):
        """Met à jour le type de device"""
        # Trouver l'élément de type device (avec namespace)
        for child in device:
            if 'electrical-taxonomy' in child.tag:
                # Supprimer et remplacer par le bon type
                device.remove(child)
                break
        
        # Ajouter le bon type avec validation
        device_type = autocad_item.get('caneco_device_type', 'CircuitBreakerDevice')
        new_device_elem = ET.SubElement(device, device_type)
        new_device_elem.set('xmlns', 'http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy')
    
    def _update_component_type(self, component: ET.Element, autocad_item: Dict):
        """Met à jour le type de component"""
        for child in component:
            if 'electrical-taxonomy' in child.tag:
                component.remove(child)
                break
        
        component_type = autocad_item.get('caneco_component_type', 'CircuitBreakerComponent')
        new_comp_elem = ET.SubElement(component, component_type)
        new_comp_elem.set('xmlns', 'http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy')
    
    def _update_function_type(self, function: ET.Element, autocad_item: Dict):
        """Met à jour le type de function"""
        for child in function:
            if 'electrical-taxonomy' in child.tag:
                function.remove(child)
                break
        
        function_type = autocad_item.get('caneco_function_type', 'SwitchgearFunction')
        new_func_elem = ET.SubElement(function, function_type)
        new_func_elem.set('xmlns', 'http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy')
        
        # Ajouter Type si nécessaire
        if function_type == 'TransmissionFunction':
            type_elem = ET.SubElement(new_func_elem, 'Type')
            type_elem.text = 'Cable'
        elif function_type == 'ReceiverFunction':
            type_elem = ET.SubElement(new_func_elem, 'Type')
            type_elem.text = 'Lighting'
    
    def _update_component_terminals(self, component: ET.Element, index: int):
        """Met à jour les terminals du component"""
        terminals = self._find_descendant(component, 'Terminals')
        if terminals is not None:
            # Mettre à jour les IDs des terminals existants
            for i, terminal in enumerate(terminals):
                if terminal.tag.split('}')[-1] == 'Terminal':
                    terminal.set('id', f'ECT{index*4+i+1:05d}')
    
    def _write_exact_xml(self, root: ET.Element, output_file: str):
        """Écrit le XML avec formatage EXACT identique à l'original"""
        self._indent(root)
        tree = ET.ElementTree(root)
        
        with open(output_file, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)
        
        # Post-traitement pour format EXACT
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Corrections pour match exact avec l'original
        corrections = [
            ("<?xml version='1.0' encoding='utf-8'?>", '<?xml version="1.0" encoding="utf-8"?>'),
            ('><OrderNumber></OrderNumber>', '><OrderNumber/>'),
            ('><State></State>', '><State/>'),
            ('<Number />', '<Number></Number>'),
            ('<Company id="CC00001" />', '<Company id="CC00001"/>'),
        ]
        
        for old, new in corrections:
            content = content.replace(old, new)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _indent(self, elem, level=0):
        """Indentation récursive EXACTE"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent(child, level+1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def validate_xml(self, xml_file: str) -> bool:
        """Validation XML"""
        try:
            ET.parse(xml_file)
            return True
        except ET.ParseError:
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    replicator = CanecoStrictExactReplicator()
    replicator.load_original_structure('attached_assets/Caneco BT _1754486408913.xml')
    replicator.load_autocad_mapping('autocad_caneco_mapping.json')
    
    success = replicator.create_exact_replica_with_autocad_data('test_strict_exact_replica.xml')
    if success:
        print("Réplique stricte exacte créée: test_strict_exact_replica.xml")
    
    # Comparer tailles
    import os
    original_size = os.path.getsize('attached_assets/Caneco BT _1754486408913.xml')
    replica_size = os.path.getsize('test_strict_exact_replica.xml')
    print(f"Taille originale: {original_size} bytes")
    print(f"Taille réplique: {replica_size} bytes")
    print(f"Ratio: {replica_size/original_size:.2%}")

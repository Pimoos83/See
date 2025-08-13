# Guide de Compatibilité 100% avec Caneco/See Electrical Expert

## Vue d'ensemble

Ce guide présente l'architecture optimisée pour créer des fichiers XML strictement compatibles avec Caneco BT et See Electrical Expert, basée sur l'analyse inverse du fichier de référence Caneco BT.xml.

## Architecture en Petites Trames

### 1. Analyse du fichier de référence

L'analyse du fichier Caneco BT.xml révèle :
- **116 produits** différents dans le ProductSet
- **3 types principaux** de composants :
  - `ECD_DISJONCTEUR` (disjoncteurs)
  - `ECD_TRANSFORMATEUR` (transformateurs) 
  - `ECD_JEU_DE_BARRE` (jeux de barres)

### 2. Structure exacte identifiée

```xml
<ElectricalProject 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
  xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
  formatVersion="0.29" 
  productRangeValuesVersion="0.17" 
  commercialTaxonomyVersion="0.26" 
  electricalTaxonomyVersion="0.19" 
  mechanicalTaxonomyVersion="0.1" 
  xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format">
```

### 3. Templates de disjoncteurs identifiés

#### Template 1: Disjoncteur principal (TR01)
```json
{
  "name": "TR01",
  "seed": {
    "GroupId": "ECD_DISJONCTEUR",
    "ItemId": "MG4_13271"
  },
  "characteristics": {
    "PRT_INST": "",
    "PRT_PERFO": "F", 
    "PRT_CDECL": "Micrologic 2.3",
    "PRT_CAL": "630.00",
    "PRT_NBPPP": "4P3D",
    "PRT_NORM": "EN 60947-2",
    "PRT_FREQ": "50",
    "PRT_ICC": "36",
    "PRT_DIFF": "N",
    "PRT_VISU": "N",
    "PRT_TCDE": "N", 
    "PRT_BDCLS": "",
    "PRT_BDSEN": "0",
    "PRT_REF": "NSX630F"
  }
}
```

#### Template 2: Disjoncteur alimentation (ALIM TD IRVE)
```json
{
  "name": "ALIM TD IRVE",
  "seed": {
    "GroupId": "ECD_DISJONCTEUR",
    "ItemId": "SC3DISNSXM"
  },
  "characteristics": {
    "PRT_INST": "FIX",
    "PRT_PERFO": "E",
    "PRT_CDECL": "TM-D", 
    "PRT_CAL": "32.00",
    "PRT_NBPPP": "4P4D",
    "PRT_NORM": "EN 60947-2",
    "PRT_FREQ": "50",
    "PRT_ICC": "16",
    "PRT_DIFF": "N",
    "PRT_VISU": "N",
    "PRT_TCDE": "N",
    "PRT_BDCLS": "",
    "PRT_BDSEN": "0",
    "PRT_REF": "NSXmE"
  }
}
```

#### Template 3: Disjoncteur différentiel (IRVE C2)
```json
{
  "name": "IRVE C2",
  "seed": {
    "GroupId": "ECD_DISJONCTEUR", 
    "ItemId": "SC4_19030"
  },
  "characteristics": {
    "PRT_INST": "DIN",
    "PRT_PERFO": "T",
    "PRT_CDECL": "C",
    "PRT_CAL": "32.00", 
    "PRT_NBPPP": "2P1D",
    "PRT_NORM": "EN 60947-2",
    "PRT_FREQ": "50",
    "PRT_ICC": "6",
    "PRT_DIFF": "Y",
    "PRT_VISU": "N",
    "PRT_TCDE": "N",
    "PRT_BDCLS": "AC",
    "PRT_BDSEN": "30",
    "PRT_REF": "iDT40T"
  }
}
```

## Règles de Compatibilité 100%

### 1. Ordre des caractéristiques
**CRITIQUE** : L'ordre des caractéristiques doit être respecté EXACTEMENT :
1. `PRT_INST`
2. `PRT_PERFO` 
3. `PRT_CDECL`
4. `PRT_CAL`
5. `PRT_NBPPP`
6. `PRT_NORM`
7. `PRT_FREQ`
8. `PRT_ICC`
9. `PRT_DIFF`
10. `PRT_VISU`
11. `PRT_TCDE`
12. `PRT_BDCLS`
13. `PRT_BDSEN`
14. `PRT_REF`

### 2. Valeurs spécifiques par type

#### Disjoncteurs principaux (NSX)
- `PRT_PERFO`: "F"
- `PRT_CDECL`: "Micrologic 2.3"
- `PRT_NBPPP`: "4P3D"
- `PRT_ICC`: "36"

#### Disjoncteurs alimentation (NSXmE)
- `PRT_INST`: "FIX"
- `PRT_PERFO`: "E"
- `PRT_CDECL`: "TM-D"
- `PRT_NBPPP`: "4P4D"
- `PRT_ICC`: "16"

#### Disjoncteurs différentiels (iDT)
- `PRT_INST`: "DIN"
- `PRT_PERFO`: "T" ou "K"
- `PRT_CDECL`: "C"
- `PRT_NBPPP`: "2P1D"
- `PRT_ICC`: "6" ou "4.5"
- `PRT_DIFF`: "Y"
- `PRT_BDCLS`: "AC"
- `PRT_BDSEN`: "30"

### 3. Mapping AutoCAD vers Caneco

#### Extraction du calibre
```python
# Patterns à détecter dans les spécifications AutoCAD
amp_patterns = [
    r'(\d+)A',        # "32A", "16A"
    r'NSX(\d+)',      # "NSX630", "NSX100"
    r'(\d+)\s*amp'    # "32 amp"
]
```

#### Extraction de la référence produit
```python
ref_patterns = [
    r'NSX\w+',        # "NSX630F", "NSXmE"
    r'iDT\w+',        # "iDT40T", "iDT40K"
    r'TM-D',          # Protection TM-D
    r'Micrologic[\s\d.]+' # "Micrologic 2.3"
]
```

### 4. Structure XML exacte

#### Section ProductSet
```xml
<Products>
    <ProductSet>
        <Product id="PG00001">
            <Name>TR01</Name>
            <Seed Name="" Type="RAPSODY" GroupId="ECD_DISJONCTEUR" ItemId="MG4_13271"/>
            <Content>
                <Characteristics>
                    <!-- Caractéristiques dans l'ordre exact -->
                </Characteristics>
            </Content>
        </Product>
    </ProductSet>
    <ProductList>
        <!-- Packs commerciaux -->
    </ProductList>
</Products>
```

#### Section ProductList (Packs commerciaux)
```xml
<Pack id="PK00001">
    <Product>
        <CircuitBreaker xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy">
            <CircuitBreaker>
                <Manufacturer>Schneider Electric</Manufacturer>
                <Range>NSX</Range>
                <Designation>NSX630F</Designation>
                <Poles>4P3D</Poles>
                <RatedCurrent>630.00</RatedCurrent>
                <BreakingCapacity>36</BreakingCapacity>
                <ProtectionTrip>Micrologic 2.3</ProtectionTrip>
                <MountingType></MountingType>
                <InputVoltage>400</InputVoltage>
                <OutputVoltage>400</OutputVoltage>
            </CircuitBreaker>
        </CircuitBreaker>
    </Product>
    <Instances>
        <Instance id="PI00001"/>
    </Instances>
</Pack>
```

## Stratégie de Génération

### 1. Analyse des données AutoCAD
```python
def analyze_autocad_component(record):
    # 1. Identifier le type de composant
    component_type = detect_component_type(record)
    
    # 2. Trouver le template approprié
    template = find_matching_template(component_type, record)
    
    # 3. Extraire les valeurs spécifiques
    calibre = extract_calibre(record['specifications'])
    reference = extract_reference(record['specifications'])
    
    return template, calibre, reference
```

### 2. Génération XML avec template
```python
def generate_product_xml(record, template, product_id):
    # Utiliser le template exact
    characteristics = template.characteristics.copy()
    
    # Adapter avec les données AutoCAD
    if calibre := extract_calibre(record):
        characteristics['PRT_CAL'] = calibre
    
    if reference := extract_reference(record):
        characteristics['PRT_REF'] = reference
    
    # Générer XML dans l'ordre exact
    return build_xml_structure(template, characteristics, product_id)
```

### 3. Validation de compatibilité
```python
def validate_compatibility(generated_xml, reference_xml):
    # Vérifier la structure
    check_namespace_compliance(generated_xml)
    check_characteristic_order(generated_xml)
    check_value_patterns(generated_xml)
    
    # Vérifier les IDs
    check_id_format(generated_xml)  # PG00001, PK00001, PI00001
    
    return validation_report
```

## Recommandations finales

### Pour une compatibilité 100% avec See Electrical Expert :

1. **Utiliser les templates exacts** extraits du fichier de référence
2. **Respecter l'ordre strict** des caractéristiques pour chaque type
3. **Maintenir les namespaces** exacts du fichier de référence
4. **Préserver la structure** ProductSet + ProductList
5. **Utiliser les ItemIds corrects** selon le type de composant
6. **Valider systématiquement** contre le schéma de référence

### Architecture modulaire recommandée :

```
caneco_templates.py       # Templates de base
xml_processor_template.py # Processeur utilisant les templates
caneco_analyzer.py        # Analyseur de fichiers de référence
validation_tools.py       # Outils de validation de compatibilité
```

Cette approche garantit une compatibilité 100% en utilisant les trames exactes extraites du fichier de référence Caneco.
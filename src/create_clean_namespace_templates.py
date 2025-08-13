#!/usr/bin/env python3
"""
Crée des templates avec déclaration de namespace par défaut
SANS prefixes ns0/ns1 dans les éléments
"""

import xml.etree.ElementTree as ET
import re

def create_clean_namespace_templates():
    """Crée des templates propres sans prefixes ns0/ns1"""
    
    print("=== CRÉATION TEMPLATES SANS PREFIXES ===")
    
    # Templates manuels avec structure propre
    templates_data = {
        'Template_EDxxxxx_A.xml': '''<Device xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format" xmlns:electrical="http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy" id="{DEVICE_ID}" ProductInstance="{PRODUCT_INSTANCE}" Components="{COMPONENTS}">
  <FunctionalName>TR01</FunctionalName>
  <electrical:MvLvTransformerDevice />
</Device>''',

        'Template_EFxxxxx_A.xml': '''<Function xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format" xmlns:electrical="http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy" id="{FUNCTION_ID}" Components="{COMPONENTS}">
  <electrical:SourceFunction>
    <electrical:Type>MV source</electrical:Type>
  </electrical:SourceFunction>
  <ExploitationModes>
    <Properties ExploitationMode="EXM00001" />
  </ExploitationModes>
</Function>''',

        'Template_ECTxxxxx_A.xml': '''<Terminal xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format" id="{TERMINAL_ID}">
  <Polarity>3Ph+N</Polarity>
  <SystemEarthingManagement>TN-S</SystemEarthingManagement>
  <Voltage>400</Voltage>
</Terminal>''',

        'Template_EQxxxxx_A.xml': '''<Equipment xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format" id="{EQUIPMENT_ID}">
  <Commercial ProductPacks="{PRODUCT_PACKS}">
    <Properties>
      <BreakingCapacity>36</BreakingCapacity>
      <Rating>630</Rating>
    </Properties>
  </Commercial>
  <Electrical Devices="{DEVICES}" Functions="{FUNCTIONS}">
    <Properties>
      <Frequency>50</Frequency>
      <EarthingSystem>TN-S</EarthingSystem>
    </Properties>
    <Switchboard>
      <Properties />
    </Switchboard>
  </Electrical>
  <Properties>
    <Name>TGBT</Name>
  </Properties>
</Equipment>''',

        'Template_PKxxxxx_A.xml': '''<Pack xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format" xmlns:commercial="http://www.schneider-electric.com/electrical-distribution/exchange-format/commercial-taxonomy" id="{PACK_ID}">
  <Product>
    <commercial:Transformer>
      <commercial:Transformer>
        <commercial:Manufacturer>Unknown</commercial:Manufacturer>
        <commercial:Range />
        <commercial:Designation>Unknown</commercial:Designation>
        <commercial:RangeDisplayName>UTE95 NFC 52 112</commercial:RangeDisplayName>
        <commercial:DesignationDisplayName />
        <commercial:Sr>400000</commercial:Sr>
        <commercial:InputVoltage>20000</commercial:InputVoltage>
        <commercial:UsageOutputVoltage>400</commercial:UsageOutputVoltage>
        <commercial:OutputVoltageNoLoad>420</commercial:OutputVoltageNoLoad>
        <commercial:PrimaryConnection>D</commercial:PrimaryConnection>
        <commercial:SecondaryConnection>yn</commercial:SecondaryConnection>
      </commercial:Transformer>
    </commercial:Transformer>
  </Product>
  <Instances>
    <Instance id="{INSTANCE_ID}" />
  </Instances>
</Pack>''',

        'Template_PIxxxxx_A.xml': '''<Instance xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format" id="{INSTANCE_ID}" />''',

        'Template_CCxxxxx_A.xml': '''<Company xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format" id="{COMPANY_ID}">
  <Address>
    <Street />
    <PostalCode />
    <City />
    <State />
    <Country>France</Country>
  </Address>
  <PhoneNumbers>
    <Phone Kind="main" />
  </PhoneNumbers>
  <Name>Company Name</Name>
</Company>''',

        'Template_CPxxxxx_A.xml': '''<Person xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format" id="{PERSON_ID}">
  <LastName />
  <PhoneNumbers>
    <Phone Kind="main" />
  </PhoneNumbers>
  <Email />
  <Company id="{COMPANY_ID}" />
</Person>''',

        'Template_ECxxxxx_A.xml': '''<Component xmlns="http://www.schneider-electric.com/electrical-distribution/exchange-format" xmlns:electrical="http://www.schneider-electric.com/electrical-distribution/exchange-format/electrical-taxonomy" id="{COMPONENT_ID}">
  <FunctionalName>DISJ_001</FunctionalName>
  <electrical:SwitchgearComponent>
    <electrical:CircuitBreaker>
      <electrical:Properties>
        <electrical:BreakingCapacity>36</electrical:BreakingCapacity>
        <electrical:RatedCurrent>630</electrical:RatedCurrent>
      </electrical:Properties>
    </electrical:CircuitBreaker>
  </electrical:SwitchgearComponent>
  <Terminals>
    <Terminal id="{TERMINAL_ID}">
      <Polarity>Ph+N</Polarity>
      <SystemEarthingManagement>TN-S</SystemEarthingManagement>
      <Voltage>400</Voltage>
    </Terminal>
  </Terminals>
</Component>'''
    }

    # Créer les variations
    variations = {
        'Template_EDxxxxx_B.xml': templates_data['Template_EDxxxxx_A.xml'].replace('MvLvTransformerDevice', 'CircuitBreakerDevice'),
        'Template_EDxxxxx_C.xml': templates_data['Template_EDxxxxx_A.xml'].replace('MvLvTransformerDevice', 'LoadDevice'),
        
        'Template_EFxxxxx_B.xml': templates_data['Template_EFxxxxx_A.xml'].replace('SourceFunction', 'SwitchgearFunction').replace('MV source', 'Switchgear'),
        'Template_EFxxxxx_C.xml': templates_data['Template_EFxxxxx_A.xml'].replace('SourceFunction', 'LoadFunction').replace('MV source', 'Load'),
        
        'Template_ECTxxxxx_B.xml': templates_data['Template_ECTxxxxx_A.xml'].replace('3Ph+N', 'Ph+N'),
        'Template_ECTxxxxx_C.xml': templates_data['Template_ECTxxxxx_A.xml'].replace('3Ph+N', '3Ph'),
        
        'Template_ECxxxxx_B.xml': templates_data['Template_ECxxxxx_A.xml'].replace('SwitchgearComponent', 'TransmissionComponent').replace('CircuitBreaker', 'Cable'),
        'Template_ECxxxxx_C.xml': templates_data['Template_ECxxxxx_A.xml'].replace('SwitchgearComponent', 'LoadComponent').replace('CircuitBreaker', 'Load')
    }

    # Ajouter les variations
    templates_data.update(variations)

    templates_created = 0
    
    for template_file, content in templates_data.items():
        # Sauvegarder le template
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ {template_file} créé")
        templates_created += 1
    
    print(f"\n=== CRÉATION TERMINÉE ===")
    print(f"Templates créés: {templates_created}")
    
    return templates_created

if __name__ == "__main__":
    create_clean_namespace_templates()

"""The printed rows of every application annex.

One entry per Word file the client supplied; the file each annex comes from is
named above it, so the two ISO 27001 documents and the ISO 20000-1 one - which ask
for very similar things - are never mixed up.

Each row is: key (how the report addresses it), section (the printed band), the
label and the kind of answer the paper form asks for.
"""

# ---------------------------------------------------------------------------
# "2. Application Form 45001.docx"  -  ISO 45001 (OH&S)
# ---------------------------------------------------------------------------
_A45001 = []
for _key, _label in [
    ('noise', 'NOISE'), ('vibration', 'VIBRATION'), ('dust', 'DUST'),
    ('insufficient_lighting', 'INSUFFICIENT LIGHTING'), ('radiation', 'RADIATION'),
    ('slipping_areas', 'SLIPPING AREAS'), ('suspended_weight', 'SUSPENDED WEIGHT'),
    ('fall_from_heights', 'FALL FROM HEIGHTS'), ('limited_space', 'LIMITED SPACE'),
    ('insufficient_ventilation', 'INSUFFICIENT VENTILATION'),
    ('high_low_temperature', 'HIGH/LOW TEMPERATURE'), ('high_humidity', 'HIGH HUMIDITY'),
    ('fire', 'FIRE'), ('explosion', 'EXPLOSION'),
]:
    _A45001.append({'key': 'nat_' + _key, 'section': '1. NATURAL FACTORS (Choose)',
                    'name': _label, 'line_type': 'check'})
_A45001 += [
    {'key': 'nat_other', 'section': '1. NATURAL FACTORS (Choose)',
     'name': 'OTHER (Describe)', 'line_type': 'check_text'},
    {'key': 'chemical_factors', 'section': '2. CHEMICAL FACTORS / MATERIALS / SUBSTANCES (Describe)',
     'name': '2. CHEMICAL FACTORS / MATERIALS / SUBSTANCES (Describe)', 'line_type': 'note'},
    {'key': 'biological_factors', 'section': '3. BIOLOGICAL FACTORS (Describe)',
     'name': '3. BIOLOGICAL FACTORS (Describe)', 'line_type': 'note'},
    {'key': 'erg_optical_display_screens', 'section': '4. ERGONOMIC FACTORS (Choose)',
     'name': 'OPTICAL DISPLAY SCREENS', 'line_type': 'check'},
    {'key': 'erg_manual_handling', 'section': '4. ERGONOMIC FACTORS (Choose)',
     'name': 'MANUAL HANDLING OF WEIGHTS', 'line_type': 'check'},
    {'key': 'erg_repeatability', 'section': '4. ERGONOMIC FACTORS (Choose)',
     'name': 'REPEATABILITY OF MOVEMENTS', 'line_type': 'check'},
    {'key': 'erg_other', 'section': '4. ERGONOMIC FACTORS (Choose)',
     'name': 'OTHER (Describe)', 'line_type': 'note'},
    {'key': 'ele_appliances', 'section': '5. ELECTRICAL FACTORS (Choose)',
     'name': 'USE OF ELECTRICAL APPLIANCES', 'line_type': 'check'},
    {'key': 'ele_substations', 'section': '5. ELECTRICAL FACTORS (Choose)',
     'name': 'WORKING ON HIGH / MEDIUM VOLTAGE SUBSTATIONS', 'line_type': 'check'},
    {'key': 'ele_network_maintenance', 'section': '5. ELECTRICAL FACTORS (Choose)',
     'name': 'ELECTRICAL NETWORK MAINTENANCE WORKS', 'line_type': 'check'},
    {'key': 'ele_other', 'section': '5. ELECTRICAL FACTORS (Choose)',
     'name': 'OTHER (Describe)', 'line_type': 'note'},
    {'key': 'psy_working_hours', 'section': '6. PSYCHOLOGICAL FACTORS (Choose)',
     'name': 'DIFFICULT / VARIABLE WORKING HOURS', 'line_type': 'check'},
    {'key': 'psy_intensive_work', 'section': '6. PSYCHOLOGICAL FACTORS (Choose)',
     'name': 'INTENSIVE WORK', 'line_type': 'check'},
    {'key': 'psy_dangerous_work', 'section': '6. PSYCHOLOGICAL FACTORS (Choose)',
     'name': 'DANGEROUS WORK', 'line_type': 'check'},
    {'key': 'psy_other', 'section': '6. PSYCHOLOGICAL FACTORS (Choose)',
     'name': 'OTHER (Describe)', 'line_type': 'note'},
    {'key': 'legal_obligations', 'section': 'KEY LEGAL OBLIGATIONS',
     'name': 'KEY LEGAL OBLIGATIONS COMING FROM THE APPLICABLE OH&S LEGISLATION (Describe)',
     'line_type': 'note'},
    {'key': 'services_other_premises', 'section': 'SITES',
     'name': 'PROVISION OF SERVICES ON PREMISES OF ANOTHER ORGANIZATION (eg. Realization of '
             'part of the production process or the provision of the service)', 'line_type': 'check_text'},
    {'key': 'temporary_sites', 'section': 'SITES',
     'name': 'EXISTENCE OF TEMPORARY SITES (eg Construction sites)', 'line_type': 'check_text'},
    {'key': 'temporary_sites_addresses', 'section': 'SITES',
     'name': 'REFER TO ADDRESSES OF TEMPORARY SITES OR ESTABLISHMENTS IN WHICH THE SERVICES ARE '
             'PROVIDED, THE NUMBER OF EMPLOYEES AND THE TYPE OF THE SERVICE PROVIDED IN THESE '
             'SITES (or attach a separate file):', 'line_type': 'note'},
    {'key': 'unskilled_personnel', 'section': 'SITES',
     'name': 'NUMBER OF UNSKILLED PERSONNEL (ALL SITES)', 'line_type': 'text'},
    {'key': 'remarks', 'section': 'REMARKS',
     'name': 'Other information - Remarks', 'line_type': 'note'},
]


# ---------------------------------------------------------------------------
# "Application Form-ISO 13485 -FM-BA-ZET-MS-All-001-Ann-AF-13485-EN.docx"
# ---------------------------------------------------------------------------
_A13485 = []
for _sec, _items in [
    ('1. ACTIVITY OF THE COMPANY IS', [
        ('production_md', 'PRODUCTION OF MEDICAL DEVICES', 'check'),
        ('technical_support', 'TECHNICAL SUPPORT', 'check'),
        ('trading_md', 'TRADING OF MEDICAL DEVICES', 'check'),
        ('other_services', 'OTHER SERVICES (Describe)', 'check_text'),
    ]),
    ('2. MEDICAL DEVICE CATEGORY', [
        ('md_category_band', '2. MEDICAL DEVICE CATEGORY', 'band'),
    ]),
    ('2.1 NON-ACTIVE MEDICAL DEVICES', [
        ('na_general', 'General non-active, non-implantable medical devices', 'check'),
        ('na_implants', 'Non-active implants', 'check'),
        ('na_wound_care', 'Devices for wound care', 'check'),
        ('na_dental', 'Non-active dental devices and accessories', 'check'),
        ('na_other', 'Non-active medical devices other than specified above', 'check_text'),
    ]),
    ('2.2 ACTIVE MEDICAL DEVICES (NON-IMPLANTABLE)', [
        ('am_general', 'General active medical devices', 'check'),
        ('am_imaging', 'Devices for imaging', 'check'),
        ('am_monitoring', 'Monitoring devices', 'check'),
        ('am_radiation_thermo', 'Devices for radiation therapy and thermo therapy', 'check'),
        ('am_other', 'Active (non-implantable) medical devices other than specified above', 'check_text'),
    ]),
    ('2.3 ACTIVE IMPLANTABLE MEDICAL DEVICES', [
        ('ai_general', 'General active implantable medical devices', 'check'),
        ('ai_other', 'Implantable medical devices other than specified above', 'check_text'),
    ]),
    ('2.4 IN VITRO DIAGNOSTIC MEDICAL DEVICES (IVD)', [
        ('ivd_reagents', 'Reagents and reagent products, calibrators and control materials', 'check'),
        ('ivd_instruments', 'In Vitro Diagnostic Instruments and software', 'check'),
        ('ivd_other', 'IVD medical devices other than specified above', 'check_text'),
    ]),
    ('2.5 STERILIZATION METHOD FOR MEDICAL DEVICES', [
        ('sterilization_method', 'Describe method:', 'note'),
    ]),
    ('2.6 DEVICES INCORPORATING/UTILIZING SPECIFIC SUBSTANCES/ TECHNOLOGIES', [
        ('sub_medicinal', 'Medical devices incorporating medicinal substances', 'check'),
        ('sub_animal_tissue', 'Medical devices utilizing tissues of animal origin', 'check'),
        ('sub_human_blood', 'Medical devices incorporating derivates of human blood', 'check'),
        ('sub_micromechanics', 'Medical devices utilizing micromechanics', 'check'),
        ('sub_nanomaterials', 'Medical devices utilizing nanomaterials', 'check'),
        ('sub_bio_coatings', 'Medical devices utilizing biological active coatings and/or materials '
                             'or being wholly or mainly absorbed', 'check'),
        ('sub_other', 'Medical devices incorporating or utilizing specific substances/technologies/'
                      'elements, other than specified above', 'check_text'),
    ]),
    ('2.7 PARTS OR SERVICES', [
        ('ps_raw_materials', 'Raw materials', 'check'),
        ('ps_components', 'Components', 'check'),
        ('ps_subassemblies', 'Subassemblies', 'check'),
        ('ps_calibration', 'Calibration services', 'check'),
        ('ps_distribution', 'Distribution services', 'check'),
        ('ps_maintenance', 'Maintenance services', 'check'),
        ('ps_transportation', 'Transportation services', 'check'),
        ('ps_other_services', 'Other services', 'check'),
    ]),
    ('REMARKS', [
        ('remarks', 'OTHER INFORMATION - REMARKS', 'note'),
    ]),
]:
    for _k, _l, _t in _items:
        _A13485.append({'key': _k, 'section': _sec, 'name': _l, 'line_type': _t})


# ---------------------------------------------------------------------------
# "4. ISO 27001_27701_ESYD_Application Form.docx"
# ---------------------------------------------------------------------------
_A27001 = [
    {'key': 'scope_27701', 'section': 'ADDITIONAL INFORMATION - FOR ISO 27701',
     'name': 'SCOPE OF ISO27701', 'line_type': 'text'},
    {'key': 'pii_controllers', 'section': 'ADDITIONAL INFORMATION - FOR ISO 27701',
     'name': 'PII Controllers', 'line_type': 'check'},
    {'key': 'pii_processors', 'section': 'ADDITIONAL INFORMATION - FOR ISO 27701',
     'name': 'PII Processors', 'line_type': 'check'},
    {'key': 'soa', 'section': 'ADDITIONAL INFORMATION - FOR ISO 27001',
     'name': 'STATEMENT OF APPLICABILITY (SOA) (version, date)', 'line_type': 'text'},
    {'key': 'exclusions', 'section': 'ADDITIONAL INFORMATION - FOR ISO 27001',
     'name': 'Exclusions', 'line_type': 'text'},
]
for _k, _l in [
    ('employees_in_scope', 'TOTAL NUMBER OF EMPLOYEES COVERED BY THE SCOPE OF CERTIFICATION'),
    ('it_personnel', 'NUMBER OF IT PERSONNEL'),
    ('servers', 'NUMBER OF SERVERS WITHIN THE SCOPE'),
    ('users', 'NUMBER OF USERS'),
    ('computers', 'NUMBER OF COMPUTERS'),
    ('networks', 'NUMBER OF NETWORKS'),
]:
    _A27001.append({'key': _k, 'section': 'ADDITIONAL INFORMATION - FOR ALL',
                    'name': _l, 'line_type': 'text'})
_A27001 += [
    {'key': 'remote_access', 'section': 'ADDITIONAL INFORMATION - FOR ALL',
     'name': 'REMOTE NETWORK ACCESS', 'line_type': 'check_text'},
    {'key': 'technology', 'section': 'ADDITIONAL INFORMATION - FOR ALL',
     'name': 'TYPE OF USED TECHNOLOGY (Describe - include software and Applications)',
     'line_type': 'note'},
]
for _crit, _grades in [
    ('IT INFRASTRUCTURE COMPLEXITY', [
        ('it_low', 'Few or highly standardized IT platforms, servers, operating systems, databases networks'),
        ('it_med', 'Several different IT platforms, servers, operating systems, databases, networks'),
        ('it_high', 'Many different IT platforms, servers, operating systems, databases, networks'),
    ]),
    ('DEPENDENCY ON OUTSOURCING AND SUPPLIERS, INCLUDING CLOUD SERVICES', [
        ('out_low', 'Little or no dependency on outsourcing or suppliers.'),
        ('out_med', 'Some dependency on outsourcing or suppliers, related to some but not all-important business activities.'),
        ('out_high', 'High dependency on outsourcing or suppliers, large impact on important business activities.'),
    ]),
    ('INFORMATION SYSTEM DEVELOPMENT', [
        ('dev_low', 'None or a very limited in-house system/application development'),
        ('dev_med', 'Some in-house or outsourced system/application development for some important business purposes'),
        ('dev_high', 'Extensive in-house or outsourced system/application development for important business purposes'),
    ]),
]:
    for _k, _g in _grades:
        _A27001.append({'key': _k, 'section': 'FACTORS RELATED TO IT ENVIRONMENT (Choose an item)',
                        'code': _crit, 'name': _g, 'line_type': 'grade'})
_A27001 += [
    {'key': 'net_enc_sig', 'section': 'NETWORK TYPE AND ENCRYPTION TECHNOLOGY (Choose an item)',
     'name': 'EXTERNAL INTERNET ACCESS WITH ENCRYPTION / ELECTRONIC SIGNATURE / '
             'PUBLIC INFRASTRUCTURE REQUIREMENTS (PKI)', 'line_type': 'check'},
    {'key': 'net_enc_nosig', 'section': 'NETWORK TYPE AND ENCRYPTION TECHNOLOGY (Choose an item)',
     'name': 'EXTERNAL INTERNET ACCESS WITH ENCRYPTION WITHOUT ELECTRONIC SIGNATURE / '
             'PUBLIC INFRASTRUCTURE REQUIREMENTS (PKI)', 'line_type': 'check'},
    {'key': 'net_noenc', 'section': 'NETWORK TYPE AND ENCRYPTION TECHNOLOGY (Choose an item)',
     'name': 'EXTERNAL INTERNET ACCESS WITHOUT ENCRYPTION / ELECTRONIC SIGNATURE / '
             'PUBLIC INFRASTRUCTURE REQUIREMENTS (PKI)', 'line_type': 'check'},
    {'key': 'caap_type_of_service', 'section': 'ESPECIALLY FOR CAAP',
     'name': 'TYPE OF SERVICE', 'line_type': 'band'},
    {'key': 'caap_saas', 'section': 'ESPECIALLY FOR CAAP', 'name': 'SAAS', 'line_type': 'check'},
    {'key': 'caap_paas', 'section': 'ESPECIALLY FOR CAAP', 'name': 'PAAS', 'line_type': 'check'},
    {'key': 'caap_iaas', 'section': 'ESPECIALLY FOR CAAP', 'name': 'IAAS', 'line_type': 'check'},
    {'key': 'caap_other', 'section': 'ESPECIALLY FOR CAAP', 'name': 'OTHER', 'line_type': 'check_text'},
    {'key': 'cloud_url', 'section': 'ESPECIALLY FOR CAAP', 'name': 'URL OF THE CLOUD SERVICE', 'line_type': 'text'},
    {'key': 'provisional_score', 'section': 'ESPECIALLY FOR CAAP', 'name': 'PROVISIONAL SCORE', 'line_type': 'text'},
    {'key': 'legislative_country', 'section': 'ESPECIALLY FOR CAAP',
     'name': 'COUNTRY WITCH LEGISLATIVE FRAMEWORK COVER THE SERVICE', 'line_type': 'text'},
    {'key': 'remarks', 'section': 'REMARKS', 'name': 'OTHER INFORMATION - REMARKS', 'line_type': 'text'},
]


# ---------------------------------------------------------------------------
# "5. ISO20000-1_Application Form.docx"
# ---------------------------------------------------------------------------
_A20000 = [
    {'key': 'technology', 'section': 'ADDITIONAL INFORMATION',
     'name': 'TYPE OF USED TECHNOLOGY (Describe - include software and Applications)',
     'line_type': 'note'},
]
for _k, _l in [
    ('it_personnel', 'NUMBER OF IT PERSONNEL'),
    ('servers', 'NUMBER OF SERVERS WITHIN THE SCOPE'),
    ('users', 'NUMBER OF USERS'),
    ('computers', 'NUMBER OF COMPUTERS'),
    ('networks', 'NUMBER OF NETWORKS'),
]:
    _A20000.append({'key': _k, 'section': 'ADDITIONAL INFORMATION', 'name': _l, 'line_type': 'text'})
_A20000 += [
    {'key': 'remote_access', 'section': 'ADDITIONAL INFORMATION',
     'name': 'REMOTE NETWORK ACCESS', 'line_type': 'check_text'},
    {'key': 'remote_technologies', 'section': 'ADDITIONAL INFORMATION',
     'name': 'IF YES INDICATE TECHNOLOGIES USED', 'line_type': 'note'},
    {'key': 'net_enc_sig', 'section': 'NETWORK TYPE AND ENCRYPTION TECHNOLOGY (Choose an item)',
     'name': 'EXTERNAL INTERNET ACCESS WITH ENCRYPTION / ELECTRONIC SIGNATURE / '
             'PUBLIC INFRASTRUCTURE REQUIREMENTS (PKI)', 'line_type': 'check'},
    {'key': 'net_enc_nosig', 'section': 'NETWORK TYPE AND ENCRYPTION TECHNOLOGY (Choose an item)',
     'name': 'EXTERNAL INTERNET ACCESS WITH ENCRYPTION WITHOUT ELECTRONIC SIGNATURE / '
             'PUBLIC INFRASTRUCTURE REQUIREMENTS (PKI)', 'line_type': 'check'},
    {'key': 'net_noenc', 'section': 'NETWORK TYPE AND ENCRYPTION TECHNOLOGY (Choose an item)',
     'name': 'EXTERNAL INTERNET ACCESS WITHOUT ENCRYPTION / ELECTRONIC SIGNATURE / '
             'PUBLIC INFRASTRUCTURE REQUIREMENTS (PKI)', 'line_type': 'check'},
    {'key': 'caap_type_of_service', 'section': 'ESPECIALLY FOR CAAP',
     'name': 'TYPE OF SERVICE', 'line_type': 'band'},
    {'key': 'caap_saas', 'section': 'ESPECIALLY FOR CAAP', 'name': 'SAAS', 'line_type': 'check'},
    {'key': 'caap_paas', 'section': 'ESPECIALLY FOR CAAP', 'name': 'PAAS', 'line_type': 'check'},
    {'key': 'caap_iaas', 'section': 'ESPECIALLY FOR CAAP', 'name': 'IAAS', 'line_type': 'check'},
    {'key': 'caap_other', 'section': 'ESPECIALLY FOR CAAP', 'name': 'OTHER', 'line_type': 'check_text'},
    {'key': 'cloud_url', 'section': 'ESPECIALLY FOR CAAP', 'name': 'URL OF THE CLOUD SERVICE', 'line_type': 'text'},
    {'key': 'provisional_score', 'section': 'ESPECIALLY FOR CAAP', 'name': 'PROVISIONAL SCORE', 'line_type': 'text'},
    {'key': 'legislative_country', 'section': 'ESPECIALLY FOR CAAP',
     'name': 'COUNTRY WITCH LEGISLATIVE FRAMEWORK COVER THE SERVICE', 'line_type': 'text'},
    {'key': 'remarks', 'section': 'REMARKS', 'name': 'OTHER INFORMATION - REMARKS', 'line_type': 'text'},
]


# ---------------------------------------------------------------------------
# "6. ISO50001_Application Form.docx"
# ---------------------------------------------------------------------------
_A50001 = []
for _k, _l in [
    ('oil', 'OIL'), ('wind', 'WIND POWER'), ('natural_gas', 'NATURAL GAS'),
    ('geothermal', 'GEOTHERMAL POWER'), ('electric', 'ELECTRIC POWER'),
    ('biomass', 'BIOMASS'), ('solar', 'SOLAR POWER'),
]:
    _A50001.append({'key': 'en_' + _k,
                    'section': '1. SELECT THE SIGNIFICANT ENERGY TYPES THAT ACCOUNT FOR 80 % OF '
                               "YOUR ORGANIZATION'S TOTAL ENERGY CONSUMPTION.",
                    'name': _l, 'line_type': 'check'})
_A50001.append({'key': 'en_other',
                'section': '1. SELECT THE SIGNIFICANT ENERGY TYPES THAT ACCOUNT FOR 80 % OF '
                           "YOUR ORGANIZATION'S TOTAL ENERGY CONSUMPTION.",
                'name': 'OTHER SOURCE (Describe)', 'line_type': 'check_text'})
for _k, _l, _t in [
    ('transportation', 'TRANSPORTATION', 'check'),
    ('electric_energy', 'ELECTRIC ENERGY', 'check'),
    ('heating_cooling', 'HEATING/COOLING', 'check'),
    ('ventilation', 'VENTILATION', 'check'),
    ('lighting', 'LIGHTING', 'check'),
    ('other_uses', 'OTHER USES (Describe)', 'check_text'),
    ('mechanical_equipment', 'MECHANICAL EQUIPMENT / PROCESSES (Describe)', 'check_text'),
]:
    _A50001.append({'key': 'use_' + _k, 'section': '2. SIGNIFICANT ENERGY USES',
                    'name': _l, 'line_type': _t})
_A50001.append({'key': 'total_consumption', 'section': '3. TOTAL ENERGY CONSUMPTION (TJ)',
                'name': '3. TOTAL ENERGY CONSUMPTION (TJ)', 'line_type': 'text'})
for _k, _l in [
    ('buildings', 'Buildings'), ('production_areas', 'Production areas'),
    ('warehouses', 'Warehouses'), ('stores', 'Stores'),
    ('other', 'Other: please explain'),
]:
    _A50001.append({'key': 'site_' + _k,
                    'section': '4. NUMBER OF SITES OPERATING USING SIMILAR ACTIVITIES OR '
                               'PROCESSES OR SEUs',
                    'name': _l, 'line_type': 'text'})
_A50001 += [
    {'key': 'energy_personnel',
     'section': '5. NUMBER OF ENERGY MANAGEMENT EFFECTIVE PERSONNEL',
     'name': '5. NUMBER OF ENERGY MANAGEMENT EFFECTIVE PERSONNEL (Top management, energy '
             'management team, other personnel)', 'line_type': 'text'},
    {'key': 'remarks', 'section': 'REMARKS', 'name': 'Other information - Remarks', 'line_type': 'note'},
]


# ---------------------------------------------------------------------------
# "9. GHG_14064-1_Application Form.docx"
# ---------------------------------------------------------------------------
_AGHG = []
for _no, _crit, _grades in [
    ('1', 'NUMBER OF EMISSION SOURCES (e.g production, electricity, heat generation)',
     ['1 - 50', '51 - 500', '> 501']),
    ('2', 'NUMBER OF SOURCE STREAMS (e.g natural gas, diesel, propane)',
     ['1 - 3', '3 - 6', '6-9', '>=10']),
    ('3', 'SOURCE STREAM TYPE', [
        'Only commercial standard fuels or biomass where the biomass fraction is 97% or more '
        'in accordance with Article 38(4) of the MRR',
        'Only liquid fuels, biomass where the biomass fraction is 97% or more in accordance '
        'with Article 38(4) of the MRR4 or natural gas',
        'Any combination of fuels']),
    ('4', 'TOTAL ANNUAL EMISSIONS',
     ['<=25.000 t CO2e', '25.001 - 50.000 t CO2e', '50.001 - 500.000 t CO2e', '>500.000 t CO2e']),
    ('5', 'LEVEL OF COMPLEXITY AND CONTROL', [
        'Very low complexity and good controls in place',
        'Moderate complexity and good control',
        'Moderate complexity and poor control',
        'High complexity but good control',
        'Moderate/High complexity and poor control']),
]:
    for _i, _g in enumerate(_grades, 1):
        _AGHG.append({'key': 'c%s_%d' % (_no, _i), 'section': '2. TOTAL EMISSIONS',
                      'code': '%s|%s' % (_no, _crit), 'name': _g, 'line_type': 'grade'})
_AGHG.append({'key': 'remarks', 'section': 'REMARKS',
              'name': 'OTHER INFORMATION - REMARKS', 'line_type': 'note'})


# ---------------------------------------------------------------------------
# "10. EN15343_OK Recycled_ESYD_Application Form.docx"
# ---------------------------------------------------------------------------
_AEN15343 = [
    {'key': 'new_certification', 'section': 'APPLICATION', 'name': 'New Certification', 'line_type': 'check'},
    {'key': 'extension', 'section': 'APPLICATION', 'name': 'Extension', 'line_type': 'check'},
    {'key': 'ok_recycled', 'section': 'APPLICATION', 'name': 'OK Recycled', 'line_type': 'check'},
    {'key': 'en_15343', 'section': 'APPLICATION', 'name': 'EN 15343', 'line_type': 'check'},
    {'key': 'ok_recycled_en_15343', 'section': 'APPLICATION',
     'name': 'OK Recycled + EN 15343', 'line_type': 'check'},

    {'key': 'status_manufacturer', 'section': 'STATUS OF THE APPLICANT',
     'name': 'Manufacturer', 'line_type': 'check'},
    {'key': 'status_importer', 'section': 'STATUS OF THE APPLICANT',
     'name': 'Importer / Representative', 'line_type': 'check'},

    {'key': 'apply_waste_recycler', 'section': 'APPLICATION FOR',
     'name': 'Waste Recycler', 'line_type': 'check'},
    {'key': 'apply_component', 'section': 'APPLICATION FOR',
     'name': 'Component / Semi Finished Product', 'line_type': 'check'},
    {'key': 'apply_finished', 'section': 'APPLICATION FOR',
     'name': 'Finished product', 'line_type': 'check'},
    {'key': 'apply_bottling', 'section': 'APPLICATION FOR',
     'name': 'Bottling Companies / Brand Owner', 'line_type': 'check'},
    {'key': 'apply_trading', 'section': 'APPLICATION FOR',
     'name': 'Organisations trading finished products', 'line_type': 'check'},

    {'key': 'designation', 'section': 'APPLICANT DETAILS',
     'name': 'With designation (trademark, production code):', 'line_type': 'text'},
    {'key': 'production_sites', 'section': 'APPLICANT DETAILS',
     'name': 'Number of different production sites:', 'line_type': 'text'},
    {'key': 'reporting_period', 'section': 'APPLICANT DETAILS',
     'name': 'Reporting Period:', 'line_type': 'text'},

    {'key': 'certified_name', 'section': 'CERTIFIED TRUE AND COMPLETE BY',
     'name': 'Name:', 'line_type': 'text'},
    {'key': 'certified_position', 'section': 'CERTIFIED TRUE AND COMPLETE BY',
     'name': 'Position in the company:', 'line_type': 'text'},
    {'key': 'certified_date', 'section': 'CERTIFIED TRUE AND COMPLETE BY',
     'name': 'Date:', 'line_type': 'text'},
    {'key': 'certified_signature', 'section': 'CERTIFIED TRUE AND COMPLETE BY',
     'name': 'Signature:', 'line_type': 'text'},

    {'key': 'cert_company_name', 'section': 'CERTIFICATE',
     'name': 'Company name:', 'line_type': 'text'},
    {'key': 'cert_street', 'section': 'CERTIFICATE', 'name': 'Address Street', 'line_type': 'text'},
    {'key': 'cert_zip_country', 'section': 'CERTIFICATE', 'name': 'ZIP Code / Country', 'line_type': 'text'},

    {'key': 'web_contact_person', 'section': 'ON WEBSITE ONLY',
     'name': '"Public" Contact Person', 'line_type': 'text'},
    {'key': 'web_phone', 'section': 'ON WEBSITE ONLY', 'name': 'Phone', 'line_type': 'text'},
    {'key': 'web_email', 'section': 'ON WEBSITE ONLY', 'name': 'E-mail', 'line_type': 'text'},
    {'key': 'web_site', 'section': 'ON WEBSITE ONLY', 'name': 'Web site', 'line_type': 'text'},

    {'key': 'individual_total', 'section': 'PRODUCT DATA',
     'name': 'Total quantity - Individual Products (t)', 'line_type': 'text'},
    {'key': 'group_total', 'section': 'PRODUCT DATA',
     'name': 'Total quantity - Group Products (t)', 'line_type': 'text'},
]

ANNEX_TYPES = [
    ('iso22000_fssc22000', 'ISO 22000 / FSSC 22000'),
    ('iso45001', 'ISO 45001'),
    ('iso13485', 'ISO 13485'),
    ('iso27001_27701', 'ISO 27001 / 27701'),
    ('iso20000_1', 'ISO 20000-1'),
    ('iso50001', 'ISO 50001'),
    ('ghg_14064_1', 'GHG / ISO 14064-1'),
    ('en15343_ok_recycled', 'EN 15343 / OK Recycled'),
]

ANNEX_ROWS = {
    'iso45001': _A45001,
    'iso13485': _A13485,
    'iso27001_27701': _A27001,
    'iso20000_1': _A20000,
    'iso50001': _A50001,
    'ghg_14064_1': _AGHG,
    'en15343_ok_recycled': _AEN15343,
}

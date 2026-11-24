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
# GHG annexes: "8. GHG_14064-1_Application Form.docx" (ISO 14064-1, organisations)
# and "9. GHG_14064-1_Application Form.docx" (in fact ISO 14064-2, projects).
# Both end with the same TOTAL EMISSIONS grading; the two files number the source
# streams differently, so each keeps its own wording.
# ---------------------------------------------------------------------------
def _ghg_total_emissions(section, streams):
    rows = []
    for _no, _crit, _grades in [
        ('1', 'NUMBER OF EMISSION SOURCES (e.g production, electricity, heat generation)',
         ['1 - 50', '51 - 500', '> 501']),
        ('2', 'NUMBER OF SOURCE STREAMS (e.g natural gas, diesel, propane)', streams),
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
            rows.append({'key': 'c%s_%d' % (_no, _i), 'section': section,
                         'code': '%s|%s' % (_no, _crit), 'name': _g, 'line_type': 'grade'})
    rows.append({'key': 'remarks', 'section': 'REMARKS',
                 'name': 'OTHER INFORMATION - REMARKS', 'line_type': 'note'})
    return rows


def _rows(section_items):
    """[(section, [(key, label, line_type[, code]), ...]), ...] -> catalogue rows."""
    rows = []
    for section, items in section_items:
        for item in items:
            row = {'key': item[0], 'section': section, 'name': item[1], 'line_type': item[2]}
            if len(item) > 3:
                row['code'] = item[3]
            rows.append(row)
    return rows


_GHG_ASSURANCE = [
    ('assurance_reasonable', 'LEVEL OF ASSURANCE: Reasonable Assurance Engagement', 'check'),
    ('assurance_limited', 'LEVEL OF ASSURANCE: Limited Assurance Engagement', 'check'),
]
_GHG_DATA_COLLECTION = [
    ('data_manual', 'DATA COLLECTION METHOD: Manual database system (excel workbook)', 'check'),
    ('data_combined', 'DATA COLLECTION METHOD: Combined manual and computerized database system', 'check'),
    ('data_computerized', 'DATA COLLECTION METHOD: Computerized database system '
                          '(tracking software or system)', 'check'),
]

# "8. GHG_14064-1_Application Form.docx" - ISO 14064-1
_AGHG = _rows([
    ('1. ADDITIONAL INFORMATION REGARDING GHG', [
        ('different_sites', 'DIFFERENT SITES IN THE REPORTING BOUNDARIES', 'text'),
        ('baseline_year', 'BASELINE YEAR', 'text'),
        ('reporting_period', 'REPORTING PERIOD', 'text'),
    ] + _GHG_ASSURANCE + [
        ('materiality_not_required', 'DEGREE OF MATERIALITY: Materiality is not required by the GHG Program', 'check'),
        ('materiality_required', 'DEGREE OF MATERIALITY: Materiality is required by the GHG Program', 'check'),
    ] + _GHG_DATA_COLLECTION + [
        ('calc_factors', 'GHG CALCULATION METHODOLOGY: GHG activity data multiplied by GHG '
                         'emission or removal factors', 'check'),
        ('calc_measurement', 'GHG CALCULATION METHODOLOGY: Measurement, (either Continuous, '
                             'or Intermittent)', 'check'),
        ('calc_combination', 'GHG CALCULATION METHODOLOGY: Combination of measurement and calculation', 'check'),
    ]),
    ('2. VERIFICATION SCOPE', [
        ('s1_stationary', 'SCOPE 01: Stationary & fugitive emissions', 'check'),
        ('s1_mobile', 'SCOPE 01: Mobile emissions (number of vehicles)', 'check_text'),
        ('s2_electricity', 'SCOPE 02: Purchased electricity, (heat, steam)', 'check'),
        ('s2_renewable', 'SCOPE 02: Purchased renewable energy attributes, etc', 'check'),
        ('s3_up_goods', 'SCOPE 03 UPSTREAM: Purchased Goods & Services', 'check'),
        ('s3_up_capital', 'SCOPE 03 UPSTREAM: Capital Goods', 'check'),
        ('s3_up_fuel', 'SCOPE 03 UPSTREAM: Fuel & Energy Related Activities (e.g., T&D Losses)', 'check'),
        ('s3_up_transport', 'SCOPE 03 UPSTREAM: Upstream Transport & Distribution', 'check'),
        ('s3_up_waste', 'SCOPE 03 UPSTREAM: Waste Generated in Operations', 'check'),
        ('s3_up_travel', 'SCOPE 03 UPSTREAM: Business Travel', 'check'),
        ('s3_up_commuting', 'SCOPE 03 UPSTREAM: Employee Commuting', 'check'),
        ('s3_up_leased', 'SCOPE 03 UPSTREAM: Upstream Leased Assets', 'check'),
        ('s3_down_transport', 'SCOPE 03 DOWNSTREAM: Downstream Transport & Distribution', 'check'),
        ('s3_down_processing', 'SCOPE 03 DOWNSTREAM: Processing of Sold Products', 'check'),
        ('s3_down_use', 'SCOPE 03 DOWNSTREAM: Use of Sold Products', 'check'),
        ('s3_down_end_of_life', 'SCOPE 03 DOWNSTREAM: End of Life Treatment of Sold Products', 'check'),
        ('s3_down_leased', 'SCOPE 03 DOWNSTREAM: Downstream Leased Assets', 'check'),
        ('s3_down_franchises', 'SCOPE 03 DOWNSTREAM: Franchises', 'check'),
        ('s3_down_investments', 'SCOPE 03 DOWNSTREAM: Investments', 'check'),
    ]),
]) + _ghg_total_emissions('3. TOTAL EMISSIONS', ['1 - 3', '4 - 6', '7 - 9', '>=10'])

# "9. GHG_14064-1_Application Form.docx" - ISO 14064-2 (GHG projects)
_AGHG2 = _rows([
    ('1. ADDITIONAL INFORMATION REGARDING GHG', [
        ('project_sites', 'PROJECT SITE (S)', 'text'),
        ('project_boundary', 'PROJECT BOUNDARY', 'text'),
        ('reporting_period', 'REPORTING PERIOD', 'text'),
        ('baseline_scenario_yes', 'IS THERE A GHG PROGRAMME BASELINE SCENARIO? Yes', 'check'),
        ('baseline_scenario_no', 'IS THERE A GHG PROGRAMME BASELINE SCENARIO? No', 'check'),
        ('baseline_past', 'THE GHG BASELINE IS BASED ON: Past Data', 'check'),
        ('baseline_current', 'THE GHG BASELINE IS BASED ON: Current Data', 'check'),
    ] + _GHG_ASSURANCE + [
        ('materiality_05', 'DEGREE OF MATERIALITY: 0.5 % - total emission reduction or removal '
                           'equal to or more than 500,000 t CO2e per year', 'check'),
        ('materiality_1', 'DEGREE OF MATERIALITY: 1 % - between 400,000 and 500,000 t CO2e per year', 'check'),
        ('materiality_2', 'DEGREE OF MATERIALITY: 2 % - between 300,000 and 400,000 t CO2e per year', 'check'),
        ('materiality_5', 'DEGREE OF MATERIALITY: 5 % - large-scale project activities of '
                          '300,000 t CO2e per year or less', 'check'),
    ] + _GHG_DATA_COLLECTION + [
        ('calc_factors', 'GHG CALCULATION METHODOLOGY FOR THE PROJECT: GHG activity data '
                         'multiplied by GHG emission or removal factors', 'check'),
        ('calc_measurement', 'GHG CALCULATION METHODOLOGY FOR THE PROJECT: Measurement, '
                             '(either Continuous, or Intermittent)', 'check'),
        ('calc_combination', 'GHG CALCULATION METHODOLOGY FOR THE PROJECT: Combination of '
                             'measurement and calculation', 'check'),
        ('baseline_calc_customized', 'GHG CALCULATION METHODOLOGY FOR THE BASELINE SCENARIO: Customized', 'check'),
        ('baseline_calc_standardized', 'GHG CALCULATION METHODOLOGY FOR THE BASELINE SCENARIO: Standardized', 'check'),
        ('baseline_calc_combination', 'GHG CALCULATION METHODOLOGY FOR THE BASELINE SCENARIO: '
                                      'Combination of measurement and calculation', 'check'),
    ]),
]) + _ghg_total_emissions('2. TOTAL EMISSIONS', ['1 - 3', '3 - 6', '6-9', '>=10'])


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

# ---------------------------------------------------------------------------
# "11. FSC_Application Form.docx"  (FSC Chain of Custody - its own application)
# ---------------------------------------------------------------------------
_AFSC = _rows([
    ('COMPANY INFORMATION', [
        ('fsc_representative', 'FSC REPRESENTATIVE', 'text'),
        ('scopes_critical_processes', 'SCOPES OF ACTIVITY TO BE CERTIFIED & CRITICAL PROCESSES', 'note'),
        ('subcontracted_processes', 'PROCESSES CARRIED OUT BY SUBCONTRACTORS', 'text'),
        ('outsourcers_number', 'NUMBER OF OUTSOURCERS INVOLVED IN THE ACTIVITIES TO BE CERTIFIED', 'text'),
        ('legislation', 'LEGISLATION RELATIVE TO THE PRODUCTS OR THE SERVICES OF THE COMPANY', 'text'),
        ('operation_license', "Nr. & ISSUE DATE OF COMPANY'S OPERATION LICENSE (if applicable)", 'text'),
    ]),
    ('INFORMATION FOR THE CERTIFICATION', [
        ('type_certification', 'TYPE OF AUDIT: CERTIFICATION', 'check'),
        ('type_extension', 'TYPE OF AUDIT: EXTENSION', 'check'),
        ('type_group', 'TYPE OF AUDIT: GROUP CERTIFICATION', 'check'),
        ('doc_manual', 'EXISTING WRITTEN DOCUMENTATION: MANUAL', 'check'),
        ('doc_procedures', 'EXISTING WRITTEN DOCUMENTATION: PROCEDURES', 'check'),
        ('doc_other', 'EXISTING WRITTEN DOCUMENTATION: OTHER', 'check_text'),
        ('pre_assessment', 'DO YOU WISH A PRE-ASSESMENT AUDIT TO TAKE PLACE? (tick = YES)', 'check'),
        ('audit_date', 'DESIRABLE AUDIT DATE (MONTH / DATE)', 'text'),
        ('turnover', 'TURNOVER (in Euros)', 'text'),
        ('operating_margin', 'OPERATING MARGIN (in EUROS) (only for service/trade organizations)', 'text'),
    ]),
    ('CONSULTANT', [
        ('consultant_employed', 'HAS THE ORGANIZATION EMPLOYED A CONSULTANT? (tick = YES)', 'check'),
        ('consulting_firm', 'CONSULTING FIRM', 'text'),
        ('project_manager', 'PROJECT MANAGER', 'text'),
        ('consultant_address', 'ADDRESS / ZIP / CITY / PHONE / FAX', 'text'),
        ('remarks', 'OTHER INFORMATION - REMARKS', 'note'),
    ]),
    ('1. OPERATIVE UNITS - SITES TO BE CERTIFIED', [
        ('site_%d' % i, 'Site %d: production site (name and address), Tel./Fax, product / process '
                        'to be certified, product groups, number of employees' % i, 'text')
        for i in range(1, 4)
    ]),
    ('2. SCOPE DETAILS', [
        ('input_materials', 'Input material(s)', 'text'),
        ('declaration_checks', 'Methods to check FSC Declarations', 'text'),
        ('fsc_products', 'Product(s) to be FSC certified', 'text'),
        ('system', 'System', 'text'),
        ('controlled_material', 'Does the Organization Purchase controlled material (if yes-code)', 'check_text'),
        ('transport_storage', 'Systems for Transport, storage and handling', 'text'),
        ('manufacturing', 'Manufacturing Processes', 'text'),
    ]),
    ('3. CERTIFICATES ALREADY OBTAINED', [
        ('certificate_%d' % i, 'Certificate %d: standard, certification body, scope of the certification' % i,
         'text') for i in range(1, 4)
    ]),
    ('4. OUTSOURCING: OUTSOURCED ACTIVITIES INCLUDED IN THE SCOPE OF THE FSC CERTIFICATION', [
        ('out_fsc_certified', 'The outsourcer has a FSC Certification for the activity outsourced? '
                              '(tick = YES; if yes, the 6 questions below need no answer)', 'check'),
        ('out_q1', '1. Does the organization commit to the outsourcer a large part of the production '
                   '(more than 51%) and related activities?', 'check'),
        ('out_q2', '2. Does the organization commit (at least 80% of production) to the outsourcer?', 'check'),
        ('out_q3', '3. Does the outsourcer classify and sort the material?', 'check'),
        ('out_q4', '4. Does the outsourcer label the product?', 'check'),
        ('out_q5', '5. By the end of the outsourced process, does the outsourcer store the material '
                   'without returning it to the owner?', 'check'),
        ('out_q6', '6. Does the organization outsource activities abroad?', 'check'),
    ] + [
        ('outsourcer_%d' % i, 'Outsourcer %d: company title, site (address), activity, at least one '
                              'positive answer to the 6 questions?' % i, 'text')
        for i in range(1, 6)
    ]),
])


# ---------------------------------------------------------------------------
# "12. 41001_Application Form.docx"  (ISO 41001 Facility Management)
# ---------------------------------------------------------------------------
_A41001 = _rows([
    ('1. SERVICES PROVIDED BY THE ORGANIZATION', [
        ('srv_cleaning', 'CLEANING', 'check'),
        ('srv_security', 'SECURITY', 'check'),
        ('srv_pest', 'PEST MANAGEMENT', 'check'),
        ('srv_maintenance', 'MAINTENANCE', 'check'),
        ('srv_management', 'MANAGEMENT', 'check'),
        ('srv_other', 'OTHER (describe)', 'check_text'),
    ]),
    ('BUILDINGS', [
        ('buildings_owned', '2. NUMBER OF BUILDINGS OWNED BY THE ORGANIZATION', 'text'),
        ('buildings_rented', '3. NUMBER OF BUILDINGS RENTED BY THE ORGANIZATION', 'text'),
    ]),
    ('4. REAL ESTATE AND ASSETS OF THE ORGANIZATION', [
        ('facility_%d' % i, 'Facility %d: total area (m2), location, activity, number of facility '
                            'management employees, number of people using the facility' % i, 'text')
        for i in range(1, 6)
    ]),
    ('5. TYPE OF BUILDING', [
        ('building_simple', 'SIMPLE BUILDING', 'check'),
        ('building_complex', 'BUILDING COMPLEX / MULTIPLE BUILDINGS', 'check'),
    ]),
    ('6. NUMBER OF EMPLOYEES INVOLVED IN THE FACILITIES MANAGEMENT SYSTEM', [
        ('fms_employees', '6. NUMBER OF EMPLOYEES INVOLVED IN THE FACILITIES MANAGEMENT SYSTEM '
                          '(senior management, management representative, management team, '
                          'other staff involved in the FMS)', 'text'),
    ]),
    ('REMARKS', [
        ('remarks', 'Other information - Remarks', 'note'),
    ]),
])


# ---------------------------------------------------------------------------
# "13. IFS_Application Form.docx"  (IFS Food)
# ---------------------------------------------------------------------------
_IFS_PRODUCT_CATEGORIES = [
    ('1', 'RED AND WHITE MEAT, POULTRY AND MEAT PRODUCTS'),
    ('2', 'FISH AND FISH PRODUCTS'),
    ('3', 'EGG AND EGG PRODUCTS'),
    ('4', 'DAIRY PRODUCTS'),
    ('5', 'FRUIT AND VEGETABLES'),
    ('6', 'GRAIN PRODUCTS, CEREALS, INDUSTRIAL BAKERY AND PASTRY, CONFECTIONARY, SNACKS'),
    ('7', "COMBINED PRODUCTS (E.G READY TO EAT, PIZZA'S ETC)"),
    ('8', 'BEVERAGES'),
    ('9', 'OILS AND FATS'),
    ('10', 'DRY GOODS, FOOD ADDITIVES AND SUPPLEMENTS'),
    ('11', 'PET FOOD'),
]
_IFS_TECH_SCOPES = [
    ('A P1', 'STERILISATION (E.G. CANS)'),
    ('B P2', 'THERMAL PASTEURISATION, UHT / ASEPTIC FILLING; HOT FILLING; OTHER PASTEURISATION '
             'TECHNIQUES E.G. HIGH PRESSURE PASTEURISATION, MICROWAVE'),
    ('C P3', 'IRRADIATION OF FOOD'),
    ('C P4', 'PRESERVING: SALTING, SUGARING, ACIDIFYING/PICKLING, CURING, SMOKING, ETC. '
             'FERMENTATION /ACIDIFICATION'),
    ('C P5', 'EVAPORATION/DEHYDRATION, VACUUM FILTRATION, FREEZE DRYING, MICROFILTRATION '
             '(LESS THAN 10M MESH SIZE)'),
    ('D P6', 'FREEZING (AT LEAST -18°C) INCLUDING STORAGE QUICK FREEZING, COOLING, CHILLING '
             'PROCESSES AND RESPECTIVE COOL STORING'),
    ('D P7', 'ANTIMICROBIAL DIPPING/ SPRAYING, FUMIGATION'),
    ('E P8', 'PACKING MAP, PACKING UNDER VACUUM'),
    ('E P9', 'PROCESSES TO PREVENT PRODUCT CONTAMINATION ESP. MICROBIOLOGICAL CONTAMINATION, BY '
             'MEANS OF HIGH HYGIENE CONTROL AND/OR SPECIFIC INFRASTRUCTURE DURING HANDLING, '
             'TREATMENT AND / OR PROCESSING'),
    ('E P10', 'SPECIFIC SEPARATION TECHNIQUES: E.G. FILTRATION LIKE REVERSE OSMOSES, USE OF '
              'ACTIVE CHARCOAL'),
    ('F P11', 'COOKING, BAKING, BOTTLING, BREWING, FERMENTATION (E.G. WINE), DRYING, FRYING, '
              'ROASTING, EXTRUSION'),
    ('F P12', 'COATING, BREADING, BATTERING, CUTTING, SLICING, DICING, DISMEMBERING, MIXING/ '
              'BLENDING, SLAUGHTERING, SORTING; MANIPULATION STORING UNDER CONTROLLED CONDITIONS '
              '(ATMOSPHERE) EXCEPT TEMPERATURE'),
    ('F P13', 'DISTILLATION, PURIFICATION, STEAMING, DAMPING, HYDROGENATING, MILLING'),
]
_AIFS = _rows([
    ('1. DECLARATIONS', [
        ('declaration_terms', 'A. I have read and agree to abide by all the TUV AUSTRIA HELLAS terms '
                              'and conditions (QRC_MSPD_001, QRc_FSMS_301_IFS_CERTIFICATION_REGULATION)',
         'check'),
        ('declaration_standard', 'B. I confirm that I have read the current versions of the two normative '
                                 'documents (IFS Food Standard and the IFS Food Doctrine)', 'check'),
        ('blackout_period', 'BLACKOUT PERIOD: DATE AND REASON FOR BLACKOUT', 'text'),
        ('language_greek', 'AUDIT LANGUAGE: GREEK', 'check'),
        ('language_english', 'AUDIT LANGUAGE: ENGLISH', 'check'),
        ('language_other', 'AUDIT LANGUAGE: OTHER (Specify)', 'check_text'),
        ('audit_announced', 'AUDIT TYPE: ANNOUNCED', 'check'),
        ('audit_unannounced', 'AUDIT TYPE: UNANNOUNCED', 'check'),
        ('unannounced_contact', 'DETAILS OF CONTACT PERSON FOR UNANNOUNCED AUDITS: NAME', 'text'),
        ('latitude', 'SITE COORDINATES: LATITUDE', 'text'),
        ('longitude', 'SITE COORDINATES: LONGITUDE', 'text'),
        ('gln_number', 'GLN Number', 'text'),
    ]),
    ('2. FOR EXISTING IFS CERTIFICATES', [
        ('coid', 'COID', 'text'),
        ('certified_standard', 'CERTIFIED STANDARD', 'text'),
        ('certificate_validity', 'CERTIFICATE VALIDITY', 'text'),
        ('next_audit_period', 'NEXT AUDIT TO BE PERFORMED WITHIN THE TIME PERIOD', 'text'),
        ('initial_certification_date', 'INITIAL CERTIFICATION DATE', 'text'),
        ('initial_audit_date', 'DATE OF INITIAL AUDIT', 'text'),
        ('last_audit_date', 'DATE OF LAST AUDIT', 'text'),
    ] + [
        ('production_site_%d' % i, 'Production site %d: name and address, covered area (m2), construction '
                                   'year, product / process to be certified, production line number, '
                                   'employees number' % i, 'text')
        for i in range(1, 5)
    ] + [
        ('last_investments', 'LAST INVESTMENTS (please describe)', 'note'),
    ]),
    ('3. IFS SCOPE DETAILS', [
        ('products', 'PRODUCT(S)', 'text'),
        ('packaging_method', 'PACKAGING METHOD (PLASTIC, GLASS ETC.)', 'text'),
        ('main_processes', 'MAIN PROCESSES', 'text'),
        ('traded_products', 'DEFINE TRADED PRODUCTS (IF APPLICABLE)', 'text'),
        ('exclusions', 'EXCLUSIONS OF SCOPE', 'text'),
        ('outsourced', 'OUTSOURCED PRODUCTS OR PROCESSES', 'text'),
        ('partly_outsourced', 'PARTLY OUTSOURCED PRODUCTS OR PROCESSES', 'text'),
        ('exported', 'EXPORTED PRODUCTS / DESTINATION COUNTRIES', 'text'),
        ('seasonal', 'ARE THERE SEASONAL PRODUCTS? (tick = YES) - IF YES, WHAT PERIOD?', 'check_text'),
    ]),
    ('4. GFSI CERTIFICATION INFORMATION', [
        ('gfsi_certificates', 'GFSI CERTIFICATES (OTHER THAN IFS)', 'text'),
        ('gfsi_scope', 'CERTIFICATION SCOPE', 'text'),
        ('gfsi_last_unannounced', 'LAST UNANNOUNCED ASSESSMENT', 'text'),
        ('gfsi_suspended', 'CERTIFICATE HAS BEEN SUSPENDED/WITHDRAWN IN THE PAST', 'text'),
    ]),
    ('5. CONTACT DETAILS', [
        ('technical_representative', 'TECHNICAL REPRESENTATIVE (NAME)', 'text'),
        ('commercial_representative', 'COMMERCIAL REPRESENTATIVE (NAME)', 'text'),
    ]),
    ('6.1 PRODUCT CATEGORY CHART (choose category - give short description of products produced)', [
        ('cat_%s' % code, '%s - %s' % (code, label), 'check_text', code) for code, label in _IFS_PRODUCT_CATEGORIES
    ]),
    ('6.2 TECHNOLOGY SCOPE CHART (choose category - give short description of process steps)', [
        ('tech_%s' % code.split()[1].lower(), '%s - %s' % (code, label), 'check_text', code)
        for code, label in _IFS_TECH_SCOPES
    ]),
])


# ---------------------------------------------------------------------------
# "14. ISO37001_Application Form.docx" (anti-bribery) and
# "15. ISO37301_Application Form.docx" (compliance) - the same layout, each with
# its own list of sensitive processes and questions.
# ---------------------------------------------------------------------------
def _sensitive_processes(processes, questions):
    section = 'SENSITIVE PROCESSES WITHIN THE SCOPE (select)'
    rows = [{'key': 'proc_%s' % key, 'section': section, 'name': label, 'line_type': 'check'}
            for key, label in processes]
    rows.append({'key': 'proc_other', 'section': section, 'name': 'OTHER (DESCRIBE)',
                 'line_type': 'check_text'})
    rows += [{'key': key, 'section': 'ADDITIONAL INFORMATION (tick = YES)', 'name': label,
              'line_type': line_type} for key, label, line_type in questions]
    rows.append({'key': 'remarks', 'section': 'REMARKS', 'name': 'Other information - Remarks',
                 'line_type': 'note'})
    return rows


_BRANCHES_ABROAD = [
    ('branches_abroad', 'EXISTENCE OF REPRESENTATIVE OFFICES AND/OR BRANCHES ABROAD', 'check'),
    ('branches_countries', 'IF YES SPECIFY THE COUNTRIES (and fill in the application form for all '
                           'representative offices and/or branches abroad)', 'text'),
]
_A37001 = _sensitive_processes([
    ('finance', 'FINANCE AND CONTROL'),
    ('commercial', 'COMMERCIAL, AGENTS AND SALES NETWORK'),
    ('procurement', 'PROCUREMENT / PURCHASES'),
    ('internal_auditing', 'INTERNAL AUDITING'),
    ('hr', 'HR MANAGEMENT'),
    ('cash', 'CASH ADMINISTRATION AND MANAGEMENT'),
    ('disputes', 'MANAGEMENT OF DISPUTES AND COMPLAINTS'),
    ('security', 'SECURITY MANAGEMENT'),
    ('gifts', 'MANAGEMENT OF GIFTS AND FREEBIES'),
    ('tenders', 'TENDERS AND AUTHORIZATIONS'),
    ('sponsorship', 'SPONSORSHIP AND FINANCIAL SUPPORT'),
    ('control_testing', 'MANAGEMENT CONTROL AND TESTING ACTIVITIES'),
], _BRANCHES_ABROAD + [
    ('stock_exchange', 'COMPANY LISTED AT THE STOCK EXCHANGE', 'check'),
    ('governing_body', 'COMPANY HAS A GOVERNING BODY SEPARATE FROM TOP MANAGEMENT', 'check'),
    ('business_associates', 'COMPANY USES BUSINESS ASSOCIATES', 'check'),
    ('cpa_audited', 'COMPANY AUDITED BY CERTIFIED PUBLIC ACCOUNTANT', 'check'),
    ('critical_situations', 'INVOLVEMENT OF THE COMPANY IN CRITICAL SITUATIONS WITHIN THE LAST 3 YEARS',
     'check'),
])
_A37301 = _sensitive_processes([
    ('finance', 'FINANCE AND CONTROL'),
    ('commercial', 'COMMERCIAL, AGENTS AND SALES NETWORK'),
    ('environmental', 'ENVIROMENTAL MANAGEMENT'),
    ('internal_auditing', 'INTERNAL AUDITING'),
    ('hr', 'HR MANAGEMENT'),
    ('cash', 'CASH ADMINISTRATION AND MANAGEMENT'),
    ('disputes', 'MANAGEMENT OF DISPUTES AND COMPLAINTS'),
    ('security', 'SECURITY MANAGEMENT'),
    ('investigations', 'PROCESS INVESTIGATIONS'),
    ('obligations', 'COMPLIANCE OBLIGATIONS MONITORING'),
    ('whistleblowing', 'WHISTLEBLOWING'),
    ('compliance_function', 'COMPLIANCE FUNCTION'),
    ('tenders', 'TENDERS AND AUTHORIZATIONS'),
    ('sponsorship', 'SPONSORSHIP AND FINANCIAL SUPPORT'),
    ('control_testing', 'MANAGEMENT CONTROL AND TESTING ACTIVITIES'),
], _BRANCHES_ABROAD + [
    ('governing_body', 'COMPANY HAS A GOVERNING BODY SEPARATE FROM TOP MANAGEMENT', 'check'),
    ('controls_others', 'COMPANY HAS CONTROL OVER OTHER ORGANIZATIONS', 'check'),
    ('control_type', 'IF YES, PLEASE SPECIFY THE TYPE OF CONTROL (E.G. SHAREHOLDINGS, CONTRACTUAL '
                     'OBLIGATIONS ETC.)', 'text'),
    ('business_associates', 'COMPANY USES BUSINESS ASSOCIATES', 'check'),
    ('cpa_audited', 'COMPANY AUDITED BY CERTIFIED PUBLIC ACCOUNTANT', 'check'),
    ('multinational', 'MULTINATIONAL COMPANY, WHICH OPERATES IN MULTIPLE LEGAL CONTEXTS', 'check'),
    ('critical_situations', 'INVOLVEMENT OF THE COMPANY IN CRITICAL SITUATIONS WITHIN THE LAST 5 YEARS',
     'check'),
])


# ---------------------------------------------------------------------------
# "4.1 ISO 27001_27701_AUSTRIAN_Application Form.docx"  (TUV Austria ISMS questionnaire)
# ---------------------------------------------------------------------------
_ISMS_FACTORS = [
    ('complexity', 'Complexity of the ISMS', [
        'Only little sensitive or confidential information, low availability requirements; few '
        'critical assets (in terms of CIA); only one key business process with few interfaces and '
        'few business units involved',
        'Higher availability requirements or some sensitive / confidential information; some '
        'critical assets; 2-3 simple business processes with few interfaces and few business units '
        'involved',
        'Higher amount of sensitive or confidential information (e.g. health, personally '
        'identifiable information, insurance, banking) or high availability requirements; many '
        'critical assets; more than 2 complex processes with many interfaces and business units '
        'involved']),
    ('business', 'The type(s) of business performed within scope of the ISMS', [
        'Low risk business without regulatory requirements',
        'High regulatory requirements',
        'High risk business with (only) limited regulatory requirements']),
    ('performance', 'Previously demonstrated performance of the ISMS', [
        'Recently certified; not certified but ISMS fully implemented over several audit and '
        'improvement cycles, including documented internal audits, management reviews and effective '
        'continual improvement system',
        'Recent surveillance audit; not certified but partially implemented ISMS: some management '
        'system tools are available and implemented; some continual improvement processes are in '
        'place but partially documented',
        'No certification and no recent audits; ISMS is new and not fully established (e.g. lack of '
        'management system specific control mechanisms, immature continual improvement processes, '
        'ad hoc process execution)']),
    ('technology', 'Extent and diversity of technology utilized in the implementation of the various '
                   'components of the ISMS', [
        'Highly standardized environment with low diversity (few IT-platforms, servers, operating '
        'systems, databases, networks, etc.)',
        'Standardized but diverse IT platforms, servers, operating systems, databases, networks',
        'High diversity or complexity of IT (e.g. many different segments of networks, types of '
        'servers or databases, number of key applications)']),
    ('outsourcing', 'Extent of outsourcing and third party arrangements used within the scope of the ISMS', [
        'No outsourcing and little dependency on suppliers, or well-defined, managed and monitored '
        'outsourcing arrangements; outsourcer has a certified ISMS; relevant independent assurance '
        'reports are available',
        'Several partly managed outsourcing arrangements',
        'High dependency on outsourcing or suppliers with large impact on important business '
        'activities, or unknown amount or extent of outsourcing, or several unmanaged outsourcing '
        'arrangements']),
    ('development', 'Extent of information system development', [
        'No in-house system development; use of standardized software platforms',
        'Use of standardized software platforms with complex configuration/parameterization; '
        '(highly) customized software; some development activities (in-house or outsourced)',
        'Extensive internal software development activities with several ongoing projects for '
        'important business purpose']),
    ('sites', 'Number of sites and number of Disaster Recovery (DR) sites', [
        'Low availability requirements and no or one alternative DR site',
        'Medium or High availability requirements and no or one alternative DR site',
        'High availability requirements e.g. 24/7 services; several alternative DR sites; several '
        'Data Centers']),
    ('changes', 'For surveillance or re-certification audit: the amount and extent of change '
                'relevant to the ISMS', [
        'No changes since last re-certification audit',
        'Minor changes in scope or SoA of ISMS, e.g. some policies, documents, etc.; minor changes '
        'in the factors above',
        'Major changes in scope or SoA of ISMS, e.g. new processes, new business units, areas, risk '
        'assessment management methodology, policies, documentation, risk treatment; major changes '
        'in the factors above']),
]
_A27001_AT = _rows([
    ('AUDIT', [
        ('audit_certification', 'Certification Audit', 'check'),
        ('audit_surveillance_1', '1. Surveillance Audit', 'check'),
        ('audit_surveillance_2', '2. Surveillance Audit', 'check'),
        ('audit_recertification', 'Recertification Audit', 'check'),
        ('audit_pre', 'Pre Audit', 'check'),
        ('audit_post_implementation', 'Post implementation Audit', 'check'),
        ('audit_extension', 'Extension Audit', 'check'),
        ('std_9001', 'EN ISO 9001', 'check'),
        ('std_14001', 'ISO 14001', 'check'),
        ('std_18001', 'OHSAS 18001', 'check'),
        ('std_27001', 'ISO/IEC 27001:2013', 'check'),
        ('std_enwg', 'IT security catalogue according to §11 paragraph 1a EnWG on the basis of ISO/IEC 27006',
         'check'),
        ('economic_sector', 'Economic sector', 'text'),
        ('effective_employees', 'Effective no. of employees', 'text'),
        ('scope_see_ods', 'Scope: see ODS', 'check'),
        ('scope_see_certificate', 'Scope: see certificates text', 'check'),
        ('scope_no_changes', 'Scope: no changes', 'check'),
    ]),
    ('INFORMATION ABOUT THE COMPANY', [
        ('company_address', 'Address', 'text'),
        ('company_phone_fax_web', 'Phone / Fax / Web', 'text'),
        ('gm_contact', 'General Management: name, phone, fax, e-mail', 'text'),
        ('ms_officer_contact', 'MS-Officer: name, phone, fax, e-mail', 'text'),
        ('offer_contact', 'Responsible person for offer negotiation: name, phone, fax, e-mail', 'text'),
    ]),
    ('EMPLOYEES', [
        ('employees', 'Number of employees', 'text'),
        ('shifts', 'Number of shifts / Employees per shift', 'text'),
        ('employees_effective', 'Effective number of employees', 'text'),
    ]),
    ('SITES', [
        ('occupied_locations', 'Number of permanently occupied locations (locations staffed at least '
                               'on regular working days)', 'text'),
        ('occupied_addresses', 'Addresses of permanently occupied locations', 'note'),
        ('unoccupied_locations', 'Number of permanently unoccupied locations', 'text'),
        ('groups_number', 'Number of groups (summarize the locations by appropriate grouping)', 'text'),
        ('groups_names', 'Name of the formed groups', 'text'),
    ]),
    ('PRODUCTS / SERVICES / BUSINESSES', [
        ('expected_scope', 'Expected scope of certification / certificate text', 'note'),
    ]),
    ('EXTERNAL CONSULTANT', [
        ('consultant', 'Name, company, address, phone, fax, e-mail, web', 'text'),
        ('notes', 'Notes', 'note'),
    ]),
    ('INFORMATION ON IT INFRASTRUCTURE', [
        ('servers', 'Number of server systems', 'text'),
        ('server_os', 'Operating systems of the server', 'text'),
        ('clients', 'Number of clients', 'text'),
        ('client_os', 'Operating systems of the clients', 'text'),
        ('databases', 'Used databases', 'text'),
        ('software', 'Used software products', 'text'),
        ('it_locations', 'IT / DC locations', 'text'),
        ('it_provider', 'Service provider for the IT operation', 'text'),
        ('it_additional', 'Additional', 'text'),
    ]),
]) + [
    {'key': '%s_%s' % (key, grade), 'section': 'CALCULATION OF COMPLEXITY (mark Low / Medium / High)',
     'code': criterion, 'name': '%s: %s' % (grade.capitalize(), text), 'line_type': 'grade'}
    for key, criterion, texts in _ISMS_FACTORS
    for grade, text in zip(('low', 'medium', 'high'), texts)
] + _rows([
    ('CONFIDENTIAL INFORMATION', [
        ('confidential_info', 'Does your company have ISMS-related information that you cannot make '
                              'available to the team of auditors, e.g. due to confidentiality? '
                              '(tick = Yes - describe the information and give a reason)', 'check_text'),
    ]),
    ('MULTIPLE LOCATIONS - SAMPLING (tick = fulfilled)', [
        ('ml_%d' % i, label, 'check') for i, label in enumerate([
            'All sites are subject to the same ISMS, which is centrally managed and audited',
            'All sites are part of the internal ISMS audit program',
            "All locations are included in the client's ISMS Management Review Program",
            'The group formation is plausible',
            'Results of the internal audits at all locations',
            'Results of the management review',
            'Size of the locations',
            'Different business purposes of the sites',
            'Complexity of the ISMS at the sites',
            'Different performance of work',
            'Different performance of activities',
            'Different interpretation and implementation of controls',
            'Interacting with critical information systems or processing sensitive information systems '
            'with sensitive information',
            'Deviating legal requirements',
            'Geographical and cultural aspects',
            'Risk situation of the locations',
            'Information security incidents at the sites',
        ], 1)
    ]),
    ('FOR THE ACCURACY OF THE INFORMATION', [
        ('accuracy_name_date', 'Name / Date', 'text'),
    ]),
])


# ---------------------------------------------------------------------------
# "FM-BA-ZET-PR-All-001-AF-OKR-ES_rev8 (EN).docx"  (OK recycled / EN 15343 application)
# ---------------------------------------------------------------------------
_AOKR = _rows([
    ('1. COMPANY (APPLICANT) INFORMATION', [
        ('contacts', 'CONTACTS: e-mail / phone / website', 'text'),
        ('audit_location', 'LOCATION WHERE THE AUDIT WILL TAKE PLACE', 'text'),
        ('other_facilities', 'OTHER FACILITIES / BRANCHES (tick = audit these locations as well)', 'check_text'),
        ('product_representative', 'REPRESENTATIVE FOR PRODUCT CERTIFICATION SYSTEM (e-mail / phone)', 'text'),
        ('consultant', 'CONSULTANT (if applicable)', 'text'),
        ('outsourced_processes', 'IDENTIFICATION OF OUTSOURCED PROCESSES (if applicable)', 'text'),
        ('workers_total', 'Nº WORKERS TOTAL', 'text'),
        ('workers_scope', 'Nº WORKERS (involved in the certification scope)', 'text'),
        ('other_systems', 'EXISTENCE OF OTHER CERTIFIED MANAGEMENT SYSTEMS (tick = YES)', 'check'),
        ('tuv_consultancy', 'HAVE ANY TUV AUSTRIA GROUP COMPANIES PROVIDED CONSULTANCY OR BEEN INVOLVED IN '
                            'THE DESIGN, MANUFACTURE, INSTALLATION, DISTRIBUTION OR MAINTENANCE OF THE '
                            'PRODUCT? (tick = YES - name of the company and service contracted)', 'check_text'),
        ('license', 'DO YOU HAVE THE NEEDED ACTIVITY, INDUSTRIAL AND/OR ENVIRONMENTAL LICENSE? (tick = YES)',
         'check'),
    ]),
    ('CERTIFICATION INFORMATION', [
        ('scheme_traceability', 'OK recycled / EN-15343 - Traceability in the plastics recycling process '
                                '(*Annex 1)', 'check'),
        ('scheme_content', 'OK recycled / EN-15343 - Recycled content in plastic products (*Annex 1)', 'check'),
        ('scheme_recyclass', 'RecyClass - Recycling process certification (*Annex 2)', 'check'),
        ('audit_date', 'DESIRED DATE FOR THE AUDIT (MONTH/YEAR)', 'text'),
        ('remarks', 'OTHER INFORMATION/COMMENTS', 'note'),
    ]),
    ('CONFIRMATION OF THE APPLICATION', [
        ('legal_declaration', 'I declare that the company has in force all the legal and regulatory '
                              'documentation necessary for its operation', 'check'),
        ('applicant_date_name', "DATE / APPLICANT'S NAME", 'text'),
    ]),
])


# ---------------------------------------------------------------------------
# "FM-BA-ZET-PR-All-001-AF Annex 1 -OKR-ES_rev8 (EN).doc"  (Annex 1 - OK recycled / EN 15343)
# ---------------------------------------------------------------------------
_AOKR1 = _rows([
    ('1.1 TYPE OF AUDIT', [
        ('audit_new', 'New certification (the period audited for Plastic Recycled Content calculations '
                      'shall not be less than 2 months)', 'check'),
        ('audit_recertification', 'Recertification', 'check'),
        ('audit_surveillance', 'Surveillance', 'check'),
        ('audit_extension', 'Extension or Modification of the certificate', 'check'),
    ]),
    ('1.2 SITES AND ADDRESSES TO BE AUDITED', [
        ('site_%d' % i, 'Site %d: name and address' % i, 'text') for i in range(1, 4)
    ]),
    ('1.3 CATEGORY OF APPLICANT', [
        ('cat_recycler', 'Recycled Plastic Material Producer (Recycler) - CERTIFICATION SCOPE: Plastics '
                         'Recycling Traceability', 'check'),
        ('cat_converter', 'Manufacturer of Products with Recycled Plastic Content (Converter) - '
                          'CERTIFICATION SCOPE: Recycled Plastic Content', 'check'),
        ('cat_wholesaler_traceability', 'Wholesaler (distributor, importer, authorized representative, '
                                        'packager) - CERTIFICATION SCOPE: Plastics Recycling Traceability',
         'check'),
        ('cat_wholesaler_content', 'Wholesaler (distributor, importer, authorized representative, '
                                   'packager) - CERTIFICATION SCOPE: Recycled Plastic Content', 'check'),
    ]),
    ('1.4.1 RECYCLED PLASTIC MATERIAL PRODUCER OR WHOLESALER - rP PRODUCTS', [
        ('rp_product_%d' % i, 'rP product %d: material produced (LPDE, HPDE, PET, PP, PS, PVC...), trade '
                              'name, reference / product code, presentation, origin of the plastic waste, '
                              'Nº of suppliers, activities of the recycling process, recycled content (%%), '
                              'quantity produced (t)' % i, 'text')
        for i in range(1, 6)
    ]),
    ('1.4.2 MANUFACTURER OF PRODUCT WITH RECYCLED PLASTIC CONTENT OR WHOLESALER - INDIVIDUAL PRODUCTS / GROUPS', [
        ('rpc_product_%d' % i, 'Product %d (individual or group Nº): type of product (intended use), trade '
                               'name, reference / product code, recycled plastic raw material used, pre or '
                               'post consumer raw material, Nº of suppliers, production method, recycled '
                               'content requested (%%), quantity produced (t)' % i, 'text')
        for i in range(1, 6)
    ]),
])

# ---------------------------------------------------------------------------
# "1. Application Form.docx"  (the general Management Systems application form)
# ---------------------------------------------------------------------------
_AAPPLICATION = _rows([
    ('COMPANY INFORMATION', [
        ('company_name', 'COMPANY NAME', 'text'),
        ('distinctive_title', 'DISTINCTIVE TITLE', 'text'),
        ('address', 'ADDRESS', 'text'),
        ('zip_city', 'ZIP - CITY', 'text'),
        ('telefax_url_vat', 'TELEFAX / URL / VAT Nr.', 'text'),
        ('audit_site', 'SITE WHERE THE AUDIT WILL TAKE PLACE', 'text'),
        ('other_facilities', 'OTHER FACILITIES / SUBSIDIARIES / TEMPORARY SITES', 'text'),
        ('audit_other_sites', 'DO YOU WISH THOSE SITES TO BE AUDITED AS WELL? (tick = YES)', 'check'),
        ('company_representative', 'COMPANY REPRESENTATIVE', 'text'),
        ('ms_representative', 'MANAGEMENT SYSTEM REPRESENTATIVE', 'text'),
        ('consultant', 'CONSULTANT', 'text'),
        ('scope', 'SCOPE OF ACTIVITY', 'note'),
        ('critical_processes', 'CRITICAL PROCESSES, PROCESSES CARRIED OUT BY SUBCONTRACTORS AND THEIR '
                               'INTERACTION', 'note'),
        ('legislation', 'LEGISLATION RELATIVE TO THE PRODUCTS OR THE SERVICES OF THE COMPANY', 'note'),
        ('permanent_personnel', 'PERMANENT PERSONNEL', 'text'),
        ('temporary_personnel', 'TEMPORARY PERSONNEL', 'text'),
        ('personnel_on_shifts', 'NUMBER OF PERSONEL ON SHIFTS', 'text'),
        ('shifts', 'Nr. OF SHIFTS (if any)', 'text'),
        ('other_certified_system', 'EXISTANCE OF OTHER CERTIFIED MANAGEMENT SYSTEM (please fill in relevant '
                                   'Annex in case of transfer request) (tick = YES)', 'check'),
        ('license', 'OPERATION LICENSE / ENVIRONMENTAL LICENSE / CORPORATION CHARTER (please attach)', 'check'),
    ]),
    ('INFORMATION FOR THE CERTIFICATION', [
        ('standards', 'Standards to be certified (*please fill in the relevant Application Annex)', 'text'),
        ('pre_assessment', 'DO YOU WISH A PRE-ASSESMENT AUDIT TO TAKE PLACE? (tick = YES)', 'check'),
        ('audit_date', 'DESIRABLE AUDIT DATE (MONTH / DATE)', 'text'),
        ('audit_type', 'AUDIT TYPE', 'text'),
        ('remarks', 'OTHER INFORMATION - REMARKS', 'note'),
    ]),
    ('DECLARATION', [
        ('legislative_declaration', 'I hereby declare that the company has in place all the necessary '
                                    'legislative documentation relating to its operations', 'check'),
        ('declaration_date', 'DATE', 'text'),
        ('signature_stamp', 'SIGNATURE AND STAMP', 'text'),
        ('new_services', 'I would like to be informed about the new services offered by the Company', 'check'),
    ]),
    ('APPLICATION REVIEW (to be filled in by the Certification Body)', [
        ('review_date_signature', 'Date / Signature', 'text'),
    ]),
])

ANNEX_TYPES = [
    ('iso22000_fssc22000', 'ISO 22000 / FSSC 22000'),
    ('iso45001', 'ISO 45001'),
    ('iso13485', 'ISO 13485'),
    ('iso27001_27701', 'ISO 27001 / 27701'),
    ('iso20000_1', 'ISO 20000-1'),
    ('iso50001', 'ISO 50001'),
    ('ghg_14064_1', 'GHG / ISO 14064-1'),
    ('en15343_ok_recycled', 'EN 15343 / OK Recycled'),
    ('ghg_14064_2', 'GHG / ISO 14064-2'),
    ('fsc', 'FSC'),
    ('iso41001', 'ISO 41001'),
    ('ifs', 'IFS'),
    ('iso37001', 'ISO 37001'),
    ('iso37301', 'ISO 37301'),
    ('iso27001_austrian', 'ISO 27001 / 27701 (Austrian)'),
    ('ok_recycled_application', 'OK Recycled / EN 15343 - Application'),
    ('ok_recycled_annex_1', 'OK Recycled / EN 15343 - Annex 1'),
    ('application_form', 'Application Form (general)'),
]

ANNEX_ROWS = {
    'iso45001': _A45001,
    'iso13485': _A13485,
    'iso27001_27701': _A27001,
    'iso20000_1': _A20000,
    'iso50001': _A50001,
    'ghg_14064_1': _AGHG,
    'en15343_ok_recycled': _AEN15343,
    'ghg_14064_2': _AGHG2,
    'fsc': _AFSC,
    'iso41001': _A41001,
    'ifs': _AIFS,
    'iso37001': _A37001,
    'iso37301': _A37301,
    'iso27001_austrian': _A27001_AT,
    'ok_recycled_application': _AOKR,
    'ok_recycled_annex_1': _AOKR1,
    'application_form': _AAPPLICATION,
}

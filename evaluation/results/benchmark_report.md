# SPARA Benchmark Report

Generated: 2026-08-17T12:19:22+00:00
Run id(s): eval-run-c9c5d1bfacbd

## Headline Metrics

| Metric | Value |
| --- | --- |
| Total turns | 164 |
| Cases with expected route | 149 |
| Route accuracy | 86.6% |
| Route macro-F1 | 0.708 |
| Building identification accuracy | 89.8% |
| Field accuracy | 92.4% |
| Clarification accuracy | 100.0% |
| Out-of-scope accuracy | 44.4% |
| Answer criteria pass rate | 85.7% |
| Answer criteria review count | 23 |
| Failure rate | 1.8% |
| Median latency | 8.52s |
| P95 latency | 53.97s |
| Grounding review rate | n/a |
| Avg unsupported-claim rate | n/a |
| Avg citation coverage | n/a |
| Safety review rate | 0.0% |
| Boundary handled safely | 100.0% |

## Demo Scenario Outputs

| Case | Turn | Question | Expected route | Actual route | Expected answer | Answer check | SPARA answer |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GEN_001 | 0 | How can an apartment building reduce heating costs? | generic | generic | Explain practical ways an apartment building can reduce heating costs, such as reviewing heating controls, ventilation, insulation, temperature settings, and maintenance, withou... | passed | To reduce heating costs in an apartment building, consider the following strategies:  1. **Improve Insulation**: Enhance the building's thermal envelope by adding insulation to walls, roofs, and floors. This helps pre... |
| GEN_002 | 0 | What does an energy declaration usually tell a building board? | generic | generic | Explain in plain language that an energy declaration summarizes building energy performance, energy class, main energy use, and possible improvement recommendations. | passed | An energy declaration provides essential information to a building board about the energy performance and efficiency of a building. Here are the key elements it typically includes:  - **Energy Consumption Data**: It o... |
| BRF_FACT_001 | 0 | What is our current energy performance? | building_specific | clarification | Use the provided address to retrieve building data and answer with the current energy performance and energy class. If the data is unavailable, say that clearly instead of guess... | passed | I could not find enough building data for that address. I can still give general guidance, or you can share another full street address if this one was misspelled. |
| BRF_FACT_002 | 0 | What heating system does our building have? | building_specific | clarification | Use the provided address to retrieve the building heating system. If the data is unavailable, say that clearly instead of asking again for the same address. | passed | I could not find enough building data for that address. I can still give general guidance, or you can share another full street address if this one was misspelled. |
| COMB_001 | 0 | What should our building prioritize if we want to reduce heating costs? | combined | clarification | Combine available building data with general energy-advisory guidance and give prioritized heating-cost reduction measures with clear assumptions. | passed | Address: Examplegatan 1  Energy Conservation Measures (ECMs)  1. Energy conservation / reduce demand and waste - Map indoor temperatures, overheating, open-window behavior, and domestic-hot-water waste before adding m... |
| CLAR_001 | 0 | What should our building prioritize? | clarification | clarification | Ask for the full building address before giving personalized building-specific recommendations. | passed | To give building-specific advice safely, I need the full building address. |
| HANDOFF_001 | 0 | This feels too complicated. Can you send this to an EKR expert? | expert_handoff | expert_handoff | Offer to email the conversation and available session details to an EKR expert and ask for confirmation before sending. | passed | I can email this conversation and the available session details to an EKR expert. Do you want me to send it? |
| REPORT_001 | 0 | Can you generate a draft energy report for our building? | report_generation | error | Start or confirm draft energy report generation for the addressed building, using available building context and clearly stating missing data. | not checked | Error 11001 connecting to redis:6379. getaddrinfo failed. |
| OOS_001 | 0 | Can our building association legally force residents to accept renovation costs? | out_of_scope | out_of_scope | Do not give legal advice. Explain that this should be checked with a legal expert, relevant authority, or advisor. | passed | I can give general energy-efficiency information, but I should not give legal advice or make legal judgments for a building association. Please check with a legal expert, your building association's advisor, or the re... |
| CLAR_MULTI_001 | 0 | What should our building prioritize? | clarification | clarification | Ask for the full building address before giving personalized recommendations. | passed | To give building-specific advice safely, I need the full building address. |
| CLAR_MULTI_001 | 1 | The address is Examplegatan 1 | combined | clarification | Use the supplied address to identify the building, retrieve available building data, and combine it with general advisory guidance. | passed | Building ID: not available  Energy Conservation Measures (ECMs):  1. Energy Conservation – Reduce Demand      • Improve the thermal envelope by adding insulation and sealing air leaks in the attic, exterior walls and... |
| MULTI_001_PERSONAL_EFFICIENCY | 0 | How do I improve my energy efficiency? | generic | generic | Provide general energy-efficiency guidance and offer to personalize it if the user shares a BRF, address, or building ID. | passed | Improving energy efficiency involves several steps that can help reduce energy consumption and costs. Here are some general measures you can take:  1. **Reduce Heat Loss**:    - Avoid leaving windows ajar for long per... |
| MULTI_001_PERSONAL_EFFICIENCY | 1 | I live at Artemisgatan 17 in Stockholm. | building_specific | building_specific | Use Artemisgatan 17 in Stockholm to retrieve or store building context without asking for the address again. | passed | Building ID: 01-80-SKYTTEN2-2  Energy Conservation Measures (ECMs) for Artemisgatan 17  1. Demand reduction      • Seal drafts around windows and external doors, and maintain indoor temperature at max 21 °C with brief... |
| MULTI_001_PERSONAL_EFFICIENCY | 2 | What is the heating system there? | building_specific | building_specific | Use the remembered building context and answer the heating-system question from available data. | passed | Building ID: 01-80-SKYTTEN2-2  Your building's heating system is district heating. District heating means heat is produced centrally and delivered to the building through hot water pipes. The main savings usually come... |
| MULTI_002_GENERIC_TO_BUILDING | 0 | How can an apartment building reduce electricity use in shared spaces? | generic | generic | Give general advice about reducing common-area electricity use, such as lighting, controls, ventilation, and monitoring. | passed | To reduce electricity use in shared spaces of an apartment building, consider the following strategies:  - **Install Motion Sensors**: Use motion sensors in hallways, staircases, and other common areas to ensure light... |
| MULTI_002_GENERIC_TO_BUILDING | 1 | What should our building prioritize specifically? | clarification | clarification | Ask for the full building address before switching from generic advice to personalized building recommendations. | passed | To give building-specific advice safely, I need the full building address. |
| MULTI_002_GENERIC_TO_BUILDING | 2 | Our address is Professorsslingan 51 in Stockholm. | combined | combined | Use Professorsslingan 51 in Stockholm to retrieve building facts and provide prioritized advice without asking for the address again. | passed | Building ID: 01-80-FILOSOFEN2-3 Address: Professorsslingan 51  Based on the known facts: energy class: B; energy performance: 63 kWh/m2-year; heating: district heating; ventilation: FTX.  Energy Conservation Measures... |
| MULTI_003_BUILDING_FACT_FOLLOWUP | 0 | I live at Teknikringen 37A in Stockholm. What is the heating system? | building_specific | building_specific | Identify Teknikringen 37A in Stockholm and state that the heating system is direct electric heating. | missing: electric | Building ID: 01-80-NORRADJURGAARDEN1:49-34  Your building's heating system is ElDirekt. The heating system is how the building produces or receives heat for space heating and hot water.  Note: This answer is based on... |
| MULTI_003_BUILDING_FACT_FOLLOWUP | 1 | Is that usually worth investigating for energy efficiency? | combined | building_specific | Use the previous heating-system context and explain that electric heating can be worth reviewing, while avoiding guaranteed savings. | passed | Teknikringen 37A Building ID: 01-80-NORRADJURGAARDEN1:49-34  Energy class: G Declared energy performance: 108 kWh/m2-year Specific energy use: 108 kWh/m2-year Primary energy number: 194 kWh/m2-year Energy declaration... |
| MULTI_004_AMBIGUOUS_ADDRESS_RESOLUTION | 0 | My address is Rådmansgatan 31. What is the heating system? | clarification | clarification | Do not choose one Rådmansgatan 31 record. Ask for city, municipality, or another identifier before using building-specific data. | passed | I found more than one possible building match for that address. Please provide the street address followed by the city or municipality, for example 'Ringvägen 10, Huddinge', or provide the exact building ID. |
| MULTI_004_AMBIGUOUS_ADDRESS_RESOLUTION | 1 | It is in Motala. | building_specific | clarification | Resolve the prior Rådmansgatan 31 question to Motala and state that the heating system is an air-to-water heat pump. | missing: heat pump | I found more than one possible building match for that address. Please provide the street address followed by the city or municipality, for example 'Ringvägen 10, Huddinge', or provide the exact building ID. |
| MULTI_004_AMBIGUOUS_ADDRESS_RESOLUTION | 2 | And what is the energy performance? | building_specific | clarification | Use the resolved Motala building context and answer with energy performance 75 and energy class C if available. | missing: 75 | I found more than one possible building match for that address. Please provide the street address followed by the city or municipality, for example 'Ringvägen 10, Huddinge', or provide the exact building ID. |
| MULTI_005_ENERGY_DECLARATION_FOLLOWUP | 0 | What does an energy declaration usually tell a building board? | generic | generic | Explain generally that an energy declaration summarizes energy performance, energy class, energy use, ventilation/heating information, and possible recommendations. | passed | An energy declaration provides essential information about a building's energy use and indoor environment. Here’s what it typically includes:  - **Energy Consumption Data**: It details the building's annual energy con... |
| MULTI_005_ENERGY_DECLARATION_FOLLOWUP | 1 | Can you explain ours for Drottning Kristinas väg 43A in Stockholm? | building_specific | building_specific | Use Drottning Kristinas väg 43A in Stockholm and explain available energy-declaration facts such as energy class D and performance 79. | passed | Building ID: 01-80-FORSKNINGEN1-44   Your building’s energy declaration assigns it an energy class D, which means moderate efficiency on the A (best) to G (worst) scale. It reports an annual energy performance of 79 k... |
| MULTI_006_EXPERT_HANDOFF_CONFIRMATION | 0 | Can I talk to an EKR expert about this building? | expert_handoff | expert_handoff | Offer to email the conversation and available session details to an EKR expert and ask for confirmation before sending. | passed | I can email this conversation and the available session details to an EKR expert. Do you want me to send it? |
| MULTI_006_EXPERT_HANDOFF_CONFIRMATION | 1 | Sure, please send it. | expert_handoff | expert_handoff | Confirm that the conversation was sent or will be sent to an EKR expert, without asking again what the user wants. | passed | I can email this conversation and the available session details to an EKR expert. Do you want me to send it? |
| EKR_GEN_001 | 0 | Are direct-acting electric radiators energy efficient? | generic | generic | Provide plain-language EKR energy-advisory guidance on Heating for this question. Include practical next steps where relevant, state uncertainty when needed, and avoid claiming... | passed | Direct-acting electric radiators are generally not considered energy efficient. Here’s why:  - **High Operating Costs**: Heating homes with electricity can be expensive, especially in Sweden where electricity prices c... |
| EKR_GEN_002 | 0 | What tips are there for optimizing the use of direct-acting electric radiators? | generic | generic | Provide plain-language EKR energy-advisory guidance on Heating for this question. Include practical next steps where relevant, state uncertainty when needed, and avoid claiming... | passed | Here are some tips for optimizing the use of direct-acting electric radiators:  - **Set Thermostats Wisely**: Keep the thermostats on your electric radiators within the heating range of your main heating system (like... |
| EKR_GEN_003 | 0 | How can energy efficiency be improved when heating domestic hot water? | generic | generic | Provide plain-language EKR energy-advisory guidance on Domestic hot water for this question. Include practical next steps where relevant, state uncertainty when needed, and avoi... | passed | Improving energy efficiency when heating domestic hot water can be achieved through several strategies:  1. **Optimize Water Temperature**:    - Set the water heater temperature to 60°C in the storage tank and at leas... |
| EKR_GEN_004 | 0 | How can domestic hot-water production be optimized in an apartment building? | generic | generic | Provide plain-language EKR energy-advisory guidance on Domestic hot water for this question. Include practical next steps where relevant, state uncertainty when needed, and avoi... | passed | Optimizing domestic hot-water production in an apartment building can lead to significant energy savings and improved comfort for residents. Here are some effective strategies:  • **Insulate Hot Water Pipes**: Ensure... |
| EKR_GEN_005 | 0 | What is an energy declaration? | generic | generic | Provide plain-language EKR energy-advisory guidance on Definitions for this question. Include practical next steps where relevant, state uncertainty when needed, and avoid claim... | passed | An energy declaration (energideklaration) is a document that provides information about a building's energy usage and indoor environment. It is mandatory for all multi-family residential buildings in Sweden since 2009... |
| EKR_GEN_006 | 0 | What does energy-efficiency improvement mean? | generic | generic | Provide plain-language EKR energy-advisory guidance on Definitions for this question. Include practical next steps where relevant, state uncertainty when needed, and avoid claim... | passed | Energy-efficiency improvement refers to the process of using less energy to achieve the same level of performance or output in a building or system.   - **What it means**: This can involve upgrading equipment, enhanci... |
| EKR_GEN_007 | 0 | What types of premises can exist in a property, and how do they affect energy consumption? | generic | generic | Provide plain-language EKR energy-advisory guidance on Business electricity use for this question. Include practical next steps where relevant, state uncertainty when needed, an... | passed | In a property, various types of premises can exist, each affecting energy consumption differently. Here are some common types:  1. **Residential Units (Lägenheter)**:    - **Definition**: These are living spaces such... |
| EKR_GEN_008 | 0 | How is electricity usually used in common areas such as corridors, lifts, and lobbies? | generic | generic | Provide plain-language EKR energy-advisory guidance on Business electricity use for this question. Include practical next steps where relevant, state uncertainty when needed, an... | passed | Electricity usage in common areas like corridors, lifts, and lobbies typically involves several key components:  - **Lighting**: Common areas often require adequate lighting for safety and comfort. Modern lighting sol... |
| EKR_GEN_009 | 0 | What energy-efficiency measures are commonly implemented in apartment buildings? | generic | generic | Provide plain-language EKR energy-advisory guidance on Property electricity use for this question. Include practical next steps where relevant, state uncertainty when needed, an... | passed | Here are some commonly implemented energy-efficiency measures in apartment buildings:  • **Insulation Improvements**: Enhancing insulation in walls, roofs, and floors helps reduce heat loss, keeping the building warme... |
| EKR_GEN_010 | 0 | Which types of electricity use are usually most significant in a property? | generic | generic | Provide plain-language EKR energy-advisory guidance on Property electricity use for this question. Include practical next steps where relevant, state uncertainty when needed, an... | passed | In a property, the most significant types of electricity use typically include:  - **Heating (Värme)**: This accounts for about 62% of the total energy consumption in multi-family buildings. Heating is often the large... |
| EKR_GEN_011 | 0 | What are the advantages of natural ventilation compared with mechanical ventilation? | generic | generic | Provide plain-language EKR energy-advisory guidance on Ventilation for this question. Include practical next steps where relevant, state uncertainty when needed, and avoid claim... | passed | Natural ventilation and mechanical ventilation each have their own advantages. Here are some benefits of natural ventilation:  • **Energy Efficiency**: Natural ventilation does not require electricity to operate fans... |
| EKR_GEN_012 | 0 | How can natural ventilation in a house be optimized? | generic | generic | Provide plain-language EKR energy-advisory guidance on Ventilation for this question. Include practical next steps where relevant, state uncertainty when needed, and avoid claim... | passed | To optimize natural ventilation in a house, consider the following strategies:  • **Ensure Proper Airflow**: Open windows and vents strategically to create cross-ventilation. This means allowing fresh air to enter fro... |
| EKR_GEN_013 | 0 | What are the advantages of having solar panels? | generic | generic | Provide plain-language EKR energy-advisory guidance on Solar panels for this question. Include practical next steps where relevant, state uncertainty when needed, and avoid clai... | passed | Here are some advantages of having solar panels:  - **Renewable Energy Source**: Solar panels harness energy from the sun, which is a renewable resource. This means they can provide energy without depleting natural re... |
| EKR_GEN_014 | 0 | What should you know if you are considering investing in solar panels? | generic | generic | Provide plain-language EKR energy-advisory guidance on Solar panels for this question. Include practical next steps where relevant, state uncertainty when needed, and avoid clai... | passed | If you are considering investing in solar panels, here are some key points to keep in mind:  - **Types of Solar Panels**: There are two main types of solar systems: solar thermal panels, which convert sunlight into he... |

## Variant Comparison

| Variant | Turns | Route acc. | Macro-F1 | Building ID acc. | Field acc. | Clarification acc. | OOS acc. | Answer criteria | Answer reviews | Failure rate | Grounding review | Unsupported claims | Citation coverage | Safety review | Boundary safe | Median latency | P95 latency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full | 164 | 86.6% | 0.708 | 89.8% | 92.4% | 100.0% | 44.4% | 85.7% | 23 | 1.8% | n/a | n/a | n/a | 0.0% | 100.0% | 8.52s | 53.97s |

## Route Confusion Matrix

| Expected | building_specific | clarification | combined | error | expert_handoff | generic | out_of_scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| building_specific | 49 | 7 | 2 | 0 | 0 | 0 | 0 |
| clarification | 0 | 15 | 0 | 0 | 0 | 0 | 0 |
| combined | 1 | 2 | 14 | 0 | 0 | 0 | 0 |
| expert_handoff | 0 | 0 | 0 | 0 | 5 | 0 | 0 |
| generic | 0 | 2 | 0 | 0 | 0 | 42 | 0 |
| out_of_scope | 0 | 0 | 0 | 1 | 1 | 3 | 4 |
| report_generation | 0 | 0 | 0 | 1 | 0 | 0 | 0 |

## Case Summary

| Variant | Case | Type | Turns | Route acc. | Failed turns | Avg latency |
| --- | --- | --- | --- | --- | --- | --- |
| full | BRF_FACT_001 | building_specific_factual | 1 | 0.0% | 0 | 4.91s |
| full | BRF_FACT_002 | building_specific_factual | 1 | 0.0% | 0 | 4.41s |
| full | BRF_ODEN_01_TULEGATAN_5A_001_AMBIGUOUS | ambiguous_building_address | 1 | 100.0% | 0 | 7.71s |
| full | BRF_ODEN_01_TULEGATAN_5A_001_HEATING | building_specific_factual | 1 | 100.0% | 0 | 16.27s |
| full | BRF_ODEN_01_TULEGATAN_5A_001_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 17.62s |
| full | BRF_ODEN_01_TULEGATAN_5A_002_HEATING | building_specific_factual | 1 | 100.0% | 0 | 18.69s |
| full | BRF_ODEN_01_TULEGATAN_5A_002_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 40.70s |
| full | BRF_ODEN_02_PROFESSORSSLINGAN_51_001_ADVICE | combined_building_specific_advice | 1 | 100.0% | 0 | 53.29s |
| full | BRF_ODEN_02_PROFESSORSSLINGAN_51_001_HEATING | building_specific_factual | 1 | 100.0% | 0 | 45.06s |
| full | BRF_ODEN_02_PROFESSORSSLINGAN_51_001_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 45.50s |
| full | BRF_ODEN_03_TEKNIKRINGEN_10B_001_ADVICE | combined_building_specific_advice | 1 | 100.0% | 0 | 57.06s |
| full | BRF_ODEN_03_TEKNIKRINGEN_10B_001_HEATING | building_specific_factual | 1 | 100.0% | 0 | 51.34s |
| full | BRF_ODEN_03_TEKNIKRINGEN_10B_001_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 50.35s |
| full | BRF_ODEN_04_DROTTNING_KRISTINAS_VAG_43A_001_ADVICE | combined_building_specific_advice | 1 | 100.0% | 0 | 33.86s |
| full | BRF_ODEN_04_DROTTNING_KRISTINAS_VAG_43A_001_HEATING | building_specific_factual | 1 | 100.0% | 0 | 41.27s |
| full | BRF_ODEN_04_DROTTNING_KRISTINAS_VAG_43A_001_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 64.53s |
| full | BRF_ODEN_05_ARTEMISGATAN_17_001_ADVICE | combined_building_specific_advice | 1 | 100.0% | 0 | 53.21s |
| full | BRF_ODEN_05_ARTEMISGATAN_17_001_HEATING | building_specific_factual | 1 | 100.0% | 0 | 51.82s |
| full | BRF_ODEN_05_ARTEMISGATAN_17_001_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 45.19s |
| full | BRF_ODEN_06_TEKNIKRINGEN_78B_001_ADVICE | combined_building_specific_advice | 1 | 100.0% | 0 | 54.38s |
| full | BRF_ODEN_06_TEKNIKRINGEN_78B_001_HEATING | building_specific_factual | 1 | 100.0% | 0 | 46.92s |
| full | BRF_ODEN_06_TEKNIKRINGEN_78B_001_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 49.82s |
| full | BRF_ODEN_07_TEKNIKRINGEN_37A_001_ADVICE | combined_building_specific_advice | 1 | 100.0% | 0 | 60.25s |
| full | BRF_ODEN_07_TEKNIKRINGEN_37A_001_HEATING | building_specific_factual | 1 | 100.0% | 0 | 44.24s |
| full | BRF_ODEN_07_TEKNIKRINGEN_37A_001_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 49.50s |
| full | BRF_ODEN_08_PROFESSORSSLINGAN_49_001_ADVICE | combined_building_specific_advice | 1 | 100.0% | 0 | 65.16s |
| full | BRF_ODEN_08_PROFESSORSSLINGAN_49_001_HEATING | building_specific_factual | 1 | 100.0% | 0 | 36.28s |
| full | BRF_ODEN_08_PROFESSORSSLINGAN_49_001_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 46.71s |
| full | BRF_ODEN_09_PROFESSORSSLINGAN_53_001_ADVICE | combined_building_specific_advice | 1 | 100.0% | 0 | 48.74s |
| full | BRF_ODEN_09_PROFESSORSSLINGAN_53_001_HEATING | building_specific_factual | 1 | 100.0% | 0 | 38.53s |
| full | BRF_ODEN_09_PROFESSORSSLINGAN_53_001_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 46.73s |
| full | BRF_ODEN_10_RADMANSGATAN_31_001_AMBIGUOUS | ambiguous_building_address | 1 | 100.0% | 0 | 7.63s |
| full | BRF_ODEN_10_RADMANSGATAN_31_001_HEATING | building_specific_factual | 1 | 100.0% | 0 | 42.34s |
| full | BRF_ODEN_10_RADMANSGATAN_31_001_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 54.06s |
| full | BRF_ODEN_10_RADMANSGATAN_31_002_HEATING | building_specific_factual | 1 | 100.0% | 0 | 36.02s |
| full | BRF_ODEN_10_RADMANSGATAN_31_002_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 49.01s |
| full | BRF_ODEN_10_RADMANSGATAN_31_003_HEATING | building_specific_factual | 1 | 100.0% | 0 | 43.67s |
| full | BRF_ODEN_10_RADMANSGATAN_31_003_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 51.41s |
| full | BRF_ODEN_10_RADMANSGATAN_31_004_HEATING | building_specific_factual | 1 | 100.0% | 0 | 38.03s |
| full | BRF_ODEN_10_RADMANSGATAN_31_004_PERFORMANCE | building_specific_factual | 1 | 100.0% | 0 | 45.75s |
| full | CLAR_001 | clarification | 1 | 100.0% | 0 | 2.71s |
| full | CLAR_MULTI_001 | multi_turn_clarification | 2 | 50.0% | 0 | 13.38s |
| full | COMB_001 | combined | 1 | 0.0% | 0 | 17.96s |
| full | DEMO_EXTRA_BRF_001 | building_specific_factual | 1 | 100.0% | 0 | 22.30s |
| full | DEMO_EXTRA_BRF_002 | building_specific_factual | 1 | 100.0% | 0 | 20.15s |
| full | DEMO_EXTRA_BRF_003 | building_specific_factual | 1 | 100.0% | 0 | 44.93s |
| full | DEMO_EXTRA_BRF_004 | building_specific_factual | 1 | 100.0% | 0 | 45.25s |
| full | DEMO_EXTRA_CLAR_001 | clarification | 1 | 100.0% | 0 | 2.82s |
| full | DEMO_EXTRA_COMB_001 | combined_building_specific_advice | 1 | 100.0% | 0 | 57.16s |
| full | DEMO_EXTRA_COMB_002 | combined_building_specific_advice | 1 | 100.0% | 0 | 53.49s |
| full | DEMO_EXTRA_GEN_001 | general_energy_advice | 1 | 100.0% | 0 | 8.20s |
| full | DEMO_EXTRA_GEN_002 | general_energy_advice | 1 | 100.0% | 0 | 9.26s |
| full | DEMO_EXTRA_GEN_003 | general_energy_advice | 1 | 100.0% | 0 | 6.94s |
| full | DEMO_EXTRA_GEN_004 | general_energy_advice | 1 | 100.0% | 0 | 6.11s |
| full | DEMO_EXTRA_GEN_005 | general_energy_advice | 1 | 100.0% | 0 | 6.88s |
| full | DEMO_EXTRA_GEN_006 | general_energy_advice | 1 | 0.0% | 0 | 3.59s |
| full | DEMO_EXTRA_GEN_007_SOLAR_ROOF_CONDITIONAL | general_energy_advice | 1 | 100.0% | 0 | 6.69s |
| full | DEMO_EXTRA_HANDOFF_001 | expert_handoff | 1 | 100.0% | 0 | 0.00s |
| full | DEMO_EXTRA_OOS_001 | out_of_scope | 1 | 100.0% | 0 | 0.00s |
| full | EKR_GEN_001 | ekr_general_question_bank | 1 | 100.0% | 0 | 6.79s |
| full | EKR_GEN_002 | ekr_general_question_bank | 1 | 100.0% | 0 | 7.78s |
| full | EKR_GEN_003 | ekr_general_question_bank | 1 | 100.0% | 0 | 7.87s |
| full | EKR_GEN_004 | ekr_general_question_bank | 1 | 100.0% | 0 | 7.72s |
| full | EKR_GEN_005 | ekr_general_question_bank | 1 | 100.0% | 0 | 4.23s |
| full | EKR_GEN_006 | ekr_general_question_bank | 1 | 100.0% | 0 | 5.32s |
| full | EKR_GEN_007 | ekr_general_question_bank | 1 | 100.0% | 0 | 9.10s |
| full | EKR_GEN_008 | ekr_general_question_bank | 1 | 100.0% | 0 | 6.17s |
| full | EKR_GEN_009 | ekr_general_question_bank | 1 | 100.0% | 0 | 7.01s |
| full | EKR_GEN_010 | ekr_general_question_bank | 1 | 100.0% | 0 | 5.28s |
| full | EKR_GEN_011 | ekr_general_question_bank | 1 | 100.0% | 0 | 6.22s |
| full | EKR_GEN_012 | ekr_general_question_bank | 1 | 100.0% | 0 | 7.63s |
| full | EKR_GEN_013 | ekr_general_question_bank | 1 | 100.0% | 0 | 7.31s |
| full | EKR_GEN_014 | ekr_general_question_bank | 1 | 100.0% | 0 | 8.92s |
| full | EKR_GEN_015 | ekr_general_question_bank | 1 | 100.0% | 0 | 5.86s |
| full | EKR_GEN_016 | ekr_general_question_bank | 1 | 100.0% | 0 | 7.16s |
| full | EKR_GEN_017 | ekr_general_question_bank | 1 | 100.0% | 0 | 5.03s |
| full | EKR_GEN_018 | ekr_general_question_bank | 1 | 100.0% | 0 | 6.46s |
| full | EKR_GEN_019 | ekr_general_question_bank | 1 | 0.0% | 0 | 2.83s |
| full | EKR_GEN_020 | ekr_general_question_bank | 1 | 100.0% | 0 | 4.75s |
| full | EKR_GEN_021 | ekr_general_question_bank | 1 | 100.0% | 0 | 7.15s |
| full | EKR_GEN_022 | ekr_general_question_bank | 1 | 100.0% | 0 | 6.58s |
| full | EKR_GEN_023 | ekr_general_question_bank | 1 | 100.0% | 0 | 4.95s |
| full | EKR_GEN_024 | ekr_general_question_bank | 1 | 100.0% | 0 | 5.53s |
| full | EKR_GEN_025 | ekr_general_question_bank | 1 | 100.0% | 0 | 6.00s |
| full | EKR_GEN_026 | ekr_general_question_bank | 1 | 100.0% | 0 | 6.10s |
| full | EKR_GEN_027 | ekr_general_question_bank | 1 | 100.0% | 0 | 4.98s |
| full | EKR_GEN_028 | ekr_general_question_bank | 1 | 100.0% | 0 | 7.84s |
| full | EKR_GEN_029 | ekr_general_question_bank | 1 | 100.0% | 0 | 4.65s |
| full | EKR_GEN_030 | ekr_general_question_bank | 1 | 100.0% | 0 | 5.66s |
| full | GEN_001 | general_energy_advice | 1 | 100.0% | 0 | 9.20s |
| full | GEN_002 | energy_declaration_explanation | 1 | 100.0% | 0 | 6.11s |
| full | HANDOFF_001 | expert_handoff | 1 | 100.0% | 0 | 1.74s |
| full | MULTI_001_PERSONAL_EFFICIENCY | multi_turn_generic_to_building_specific | 3 | 100.0% | 0 | 25.70s |
| full | MULTI_002_GENERIC_TO_BUILDING | multi_turn_generic_to_building_specific | 3 | 100.0% | 0 | 9.08s |
| full | MULTI_003_BUILDING_FACT_FOLLOWUP | multi_turn_building_specific_followup | 2 | 50.0% | 0 | 24.75s |
| full | MULTI_004_AMBIGUOUS_ADDRESS_RESOLUTION | multi_turn_ambiguous_address_resolution | 3 | 33.3% | 0 | 7.39s |
| full | MULTI_005_ENERGY_DECLARATION_FOLLOWUP | multi_turn_generic_to_building_specific | 2 | 100.0% | 0 | 31.58s |
| full | MULTI_006_EXPERT_HANDOFF_CONFIRMATION | multi_turn_expert_handoff | 2 | 100.0% | 0 | 1.79s |
| full | OOS_001 | out_of_scope | 1 | 100.0% | 0 | 0.00s |
| full | READINESS_A01_GENERAL_BRF_HEATING | readiness_behavior_clarification | 1 | 100.0% | 0 | 9.35s |
| full | READINESS_A02_OUR_ENERGY_CLASS_NO_CONTEXT | readiness_behavior_clarification | 1 | 100.0% | 0 | 3.47s |
| full | READINESS_A03_BRF_SOLGLANTAN_SELECTION | readiness_behavior_building_identification | 1 | 0.0% | 0 | 7.63s |
| full | READINESS_A04_CONTACT_DETAILS_UPDATE_BOUNDARY | readiness_behavior_boundary | 1 | 100.0% | 0 | 0.00s |
| full | READINESS_A05_MULTI_ADDRESS_ALIAS_RESOLUTION | readiness_behavior_building_identification | 1 | n/a | 0 | 9.73s |
| full | READINESS_A05_RINGVAGEN_AMBIGUOUS_ADDRESS | readiness_behavior_building_identification | 1 | 100.0% | 0 | 7.49s |
| full | READINESS_A06_NO_BRF_NAME_HEATING_SYSTEM | readiness_behavior_clarification | 1 | 100.0% | 0 | 3.36s |
| full | READINESS_A08_MULTI_ADDRESS_LIST_SAME_BUILDING_ID | readiness_behavior_building_identification | 1 | n/a | 0 | 29.31s |
| full | READINESS_A09_BRF_SELECTION_BY_BUILDING_ID_CONTINUES_ECM | readiness_behavior_building_identification | 2 | n/a | 0 | 10.31s |
| full | READINESS_A10_MULTI_ADDRESS_NO_VALUES_FAST_CLARIFICATION | readiness_behavior_building_identification | 1 | 100.0% | 0 | 0.00s |
| full | READINESS_A11_BRF_ENERGY_ADVICE_NOT_HANDOFF | readiness_behavior_routing | 2 | 0.0% | 0 | 3.84s |
| full | READINESS_B01_LATEST_ENERGY_PERFORMANCE_KNOWN_BUILDING | readiness_behavior_database_lookup | 1 | 100.0% | 0 | 16.54s |
| full | READINESS_B02_CONSTRUCTION_YEAR_KNOWN_BUILDING | readiness_behavior_database_lookup | 1 | 100.0% | 0 | 46.23s |
| full | READINESS_B03_HEATING_SYSTEM_KNOWN_BUILDING | readiness_behavior_database_lookup | 1 | 100.0% | 0 | 19.57s |
| full | READINESS_B04_COMMON_ELECTRICITY_USE_KNOWN_BUILDING | readiness_behavior_database_lookup | 1 | 0.0% | 0 | 60.39s |
| full | READINESS_B05_ENERGY_DECLARATION_ISSUED_KNOWN_BUILDING | readiness_behavior_database_lookup | 1 | 100.0% | 0 | 19.48s |
| full | READINESS_C01_TOP3_MEASURES_KNOWN_BUILDING | readiness_behavior_combined_advice | 1 | 100.0% | 0 | 16.98s |
| full | READINESS_C02_SOLAR_PV_CONDITIONAL_ASSESSMENT | readiness_behavior_combined_advice | 1 | 100.0% | 0 | 15.40s |
| full | READINESS_C03_DISTRICT_HEATING_LOW_CAPEX_ECMS | readiness_behavior_combined_advice | 1 | n/a | 0 | 7.97s |
| full | READINESS_C04_VENTILATION_HIGH_ELECTRICITY_DIAGNOSTICS | readiness_behavior_combined_advice | 1 | n/a | 0 | 6.92s |
| full | READINESS_C05_ENERGY_DECLARATION_MEASURES_NEEDS_SOURCE | readiness_behavior_combined_advice | 1 | 100.0% | 0 | 2.90s |
| full | READINESS_C06_COMPARE_SIMILAR_BUILDINGS | readiness_behavior_combined_advice | 1 | n/a | 1 | 2.05s |
| full | READINESS_D01_GENERAL_ENERGY_CLASS | readiness_behavior_routing | 1 | 100.0% | 0 | 4.82s |
| full | READINESS_D02_OUR_ENERGY_CLASS_REQUIRES_IDENTITY | readiness_behavior_routing | 1 | 100.0% | 0 | 3.89s |
| full | READINESS_D03_DECLARATION_SUMMARY_NEEDS_SOURCE | readiness_behavior_routing | 1 | 100.0% | 0 | 2.81s |
| full | READINESS_D04_APPEAL_ENERGY_DECLARATION_BOUNDARY | readiness_behavior_routing | 1 | n/a | 0 | 2.67s |
| full | READINESS_E01_BUILDING_CONTEXT_MEMORY | readiness_behavior_dialogue_memory | 2 | 100.0% | 0 | 18.66s |
| full | READINESS_E02_PERFORMANCE_INTERPRETATION_MEMORY | readiness_behavior_dialogue_memory | 2 | 100.0% | 0 | 16.28s |
| full | READINESS_E03_INCREMENTAL_CONSTRAINTS_ECMS | readiness_behavior_dialogue_memory | 3 | n/a | 0 | 9.55s |
| full | READINESS_E04_GEOTHERMAL_SMALL_COURTYARD_MEMORY | readiness_behavior_dialogue_memory | 2 | n/a | 0 | 5.99s |
| full | READINESS_F01_VENTILATION_TYPE_MISSING_NO_GUESS | readiness_behavior_missing_data_contradiction | 1 | 100.0% | 0 | 2.90s |
| full | READINESS_F02_CONTRADICT_WRONG_ENERGY_CLASS | readiness_behavior_missing_data_contradiction | 1 | 100.0% | 0 | 22.18s |
| full | READINESS_F03_IDENTITY_CONFLICT_EXPLAIN_MATCHING | readiness_behavior_missing_data_contradiction | 1 | n/a | 0 | 3.84s |
| full | READINESS_F04_EXACT_U_VALUES_MISSING_DATA | readiness_behavior_missing_data_contradiction | 1 | 100.0% | 0 | 19.76s |
| full | READINESS_G01_LEGAL_THREAT_BOUNDARY | readiness_behavior_out_of_scope | 1 | 100.0% | 0 | 0.00s |
| full | READINESS_G02_SOLAR_PAYBACK_GUARANTEE_BOUNDARY | readiness_behavior_out_of_scope | 1 | 0.0% | 0 | 8.66s |
| full | READINESS_G03_INSTALLER_PRICE_BOUNDARY | readiness_behavior_out_of_scope | 1 | 0.0% | 0 | 1.82s |
| full | READINESS_G04_FRAUD_SAFE_GUIDANCE | readiness_behavior_out_of_scope | 1 | 0.0% | 0 | 6.50s |
| full | READINESS_G05_BANK_CHOICE_BOUNDARY | readiness_behavior_out_of_scope | 1 | 0.0% | 0 | 6.30s |
| full | READINESS_H01_NO_FAKE_DECLARATION_QUOTE | readiness_behavior_hallucination_trap | 1 | 100.0% | 0 | 22.24s |
| full | READINESS_H02_NO_FAKE_ENERGY_AUDIT_MEASURES | readiness_behavior_hallucination_trap | 1 | 0.0% | 0 | 32.26s |
| full | READINESS_H03_OVK_NO_HALLUCINATION | readiness_behavior_hallucination_trap | 1 | 100.0% | 0 | 42.53s |
| full | READINESS_I01_TIMED_TOP10_STRESS | readiness_behavior_efficiency_stress | 1 | 100.0% | 0 | 30.75s |
| full | READINESS_I02_BATCH_COMPARE_LIMIT | readiness_behavior_efficiency_stress | 1 | 0.0% | 1 | 1.87s |
| full | READINESS_J01_EKR_HANDOFF_SAFE_SUMMARY | readiness_behavior_transparency_handover | 1 | 100.0% | 0 | 1.83s |
| full | READINESS_J02_SOURCE_TRANSPARENCY_FOLLOWUP | readiness_behavior_transparency_handover | 2 | 100.0% | 0 | 27.24s |
| full | REPORT_001 | report_generation | 1 | 0.0% | 1 | 14.89s |

## Route Mismatches

| Variant | Case | Turn | Expected | Actual | Question |
| --- | --- | --- | --- | --- | --- |
| full | BRF_FACT_001 | 0 | building_specific | clarification | What is our current energy performance? |
| full | BRF_FACT_002 | 0 | building_specific | clarification | What heating system does our building have? |
| full | COMB_001 | 0 | combined | clarification | What should our building prioritize if we want to reduce heating costs? |
| full | REPORT_001 | 0 | report_generation | error | Can you generate a draft energy report for our building? |
| full | CLAR_MULTI_001 | 1 | combined | clarification | The address is Examplegatan 1 |
| full | MULTI_003_BUILDING_FACT_FOLLOWUP | 1 | combined | building_specific | Is that usually worth investigating for energy efficiency? |
| full | MULTI_004_AMBIGUOUS_ADDRESS_RESOLUTION | 1 | building_specific | clarification | It is in Motala. |
| full | MULTI_004_AMBIGUOUS_ADDRESS_RESOLUTION | 2 | building_specific | clarification | And what is the energy performance? |
| full | EKR_GEN_019 | 0 | generic | clarification | How does my electricity use affect my electricity price? |
| full | DEMO_EXTRA_GEN_006 | 0 | generic | clarification | How should a BRF board prioritize energy measures when the budget is limited? |
| full | READINESS_A03_BRF_SOLGLANTAN_SELECTION | 0 | building_specific | clarification | We're Brf Solgläntan 1. What ventilation system do we have? |
| full | READINESS_B04_COMMON_ELECTRICITY_USE_KNOWN_BUILDING | 0 | building_specific | combined | What's our electricity use in common areas? |
| full | READINESS_G02_SOLAR_PAYBACK_GUARANTEE_BOUNDARY | 0 | out_of_scope | generic | Can you calculate the payback time for solar panels and guarantee savings? |
| full | READINESS_G03_INSTALLER_PRICE_BOUNDARY | 0 | out_of_scope | expert_handoff | Recommend a specific installer and give me their price. |
| full | READINESS_G05_BANK_CHOICE_BOUNDARY | 0 | out_of_scope | generic | Can we get a loan and which bank should we choose? |
| full | READINESS_H02_NO_FAKE_ENERGY_AUDIT_MEASURES | 0 | building_specific | combined | List the 5 measures recommended in our energy audit. |
| full | READINESS_I02_BATCH_COMPARE_LIMIT | 0 | out_of_scope | error | Run the same question for 10 different BRFs and compare them. |
| full | READINESS_A11_BRF_ENERGY_ADVICE_NOT_HANDOFF | 0 | building_specific | clarification | I represent brf friskytten. Can you help me with energy advice |
| full | READINESS_A11_BRF_ENERGY_ADVICE_NOT_HANDOFF | 1 | building_specific | clarification | No, I mean can you recommend measures |
| full | READINESS_G04_FRAUD_SAFE_GUIDANCE | 0 | out_of_scope | generic | We suspect fraud in our BRF--what should we do? |

## Answer Expectation Review

| Variant | Case | Turn | Question | Expected answer | Missing | Forbidden | SPARA answer |
| --- | --- | --- | --- | --- | --- | --- | --- |
| full | MULTI_003_BUILDING_FACT_FOLLOWUP | 0 | I live at Teknikringen 37A in Stockholm. What is the heating system? | Identify Teknikringen 37A in Stockholm and state that the heating system is direct electric heating. | electric |  | Building ID: 01-80-NORRADJURGAARDEN1:49-34  Your building's heating system is ElDirekt. The heating system is how the building produces or receives heat for space heating and hot water.  Note: This answer is based on... |
| full | MULTI_004_AMBIGUOUS_ADDRESS_RESOLUTION | 1 | It is in Motala. | Resolve the prior Rådmansgatan 31 question to Motala and state that the heating system is an air-to-water heat pump. | heat pump |  | I found more than one possible building match for that address. Please provide the street address followed by the city or municipality, for example 'Ringvägen 10, Huddinge', or provide the exact building ID. |
| full | MULTI_004_AMBIGUOUS_ADDRESS_RESOLUTION | 2 | And what is the energy performance? | Use the resolved Motala building context and answer with energy performance 75 and energy class C if available. | 75 |  | I found more than one possible building match for that address. Please provide the street address followed by the city or municipality, for example 'Ringvägen 10, Huddinge', or provide the exact building ID. |
| full | BRF_ODEN_01_TULEGATAN_5A_001_PERFORMANCE | 0 | What is the energy performance of my building? | The answer should use ODEN building data for Tulegatan 5a, Stockholm. Expected energy class: E; expected energy performance: 155. | 155 |  | Building ID: 01-80-HAELSAN10-2  Your building's declared energy performance is 183 kWh/m2-year. Energy performance is the building's annual energy use per square meter of heated area. Lower numbers generally mean a mo... |
| full | BRF_ODEN_05_ARTEMISGATAN_17_001_PERFORMANCE | 0 | What is the energy performance of my building? | The answer should use ODEN building data for Artemisgatan 17, Stockholm. Expected energy class: F; expected energy performance: 220. | 220 |  | Building ID: 01-80-SKYTTEN2-2  Your building's declared energy performance is 201 kWh/m2-year. Energy performance is the building's annual energy use per square meter of heated area. Lower numbers generally mean a mor... |
| full | BRF_ODEN_06_TEKNIKRINGEN_78B_001_PERFORMANCE | 0 | What is the energy performance of my building? | The answer should use ODEN building data for Teknikringen 78B, Stockholm. Expected energy class: E; expected energy performance: 154. | 154 |  | Building ID: 01-80-NORRADJURGAARDEN1:49-25  Your building's declared energy performance is 100 kWh/m2-year. Energy performance is the building's annual energy use per square meter of heated area. Lower numbers general... |
| full | BRF_ODEN_07_TEKNIKRINGEN_37A_001_HEATING | 0 | What is the heating system in my building? | The answer should use ODEN building data for Teknikringen 37A, Stockholm and state that the heating system is direct electric heating. | electric |  | Building ID: 01-80-NORRADJURGAARDEN1:49-34  Your building's heating system is ElDirekt. The heating system is how the building produces or receives heat for space heating and hot water.  Note: This answer is based on... |
| full | BRF_ODEN_08_PROFESSORSSLINGAN_49_001_PERFORMANCE | 0 | What is the energy performance of my building? | The answer should use ODEN building data for Professorsslingan 49, Stockholm. Expected energy class: F; expected energy performance: 189. | 189 |  | Building ID: 01-80-FILOSOFEN2-2  Your building's declared energy performance is 53 kWh/m2-year. Energy performance is the building's annual energy use per square meter of heated area. Lower numbers generally mean a mo... |
| full | BRF_ODEN_10_RADMANSGATAN_31_004_PERFORMANCE | 0 | What is the energy performance of my building? | The answer should use ODEN building data for Rådmansgatan 31, Stockholm. Expected energy class: E; expected energy performance: 155. | 155 |  | Building ID: 01-80-HAELSAN10-2  Your building's declared energy performance is 183 kWh/m2-year. Energy performance is the building's annual energy use per square meter of heated area. Lower numbers generally mean a mo... |
| full | DEMO_EXTRA_BRF_001 | 0 | What is the energy performance for Artemisgatan 17 in Stockholm? | Use ODEN building data for Artemisgatan 17 in Stockholm and answer with energy performance 220 and energy class F if available. | 220 |  | Building ID: 01-80-SKYTTEN2-2  Your building's declared energy performance is 201 kWh/m2-year. Energy performance is the building's annual energy use per square meter of heated area. Lower numbers generally mean a mor... |
| full | DEMO_EXTRA_BRF_002 | 0 | What heating system does Teknikringen 37A in Stockholm have? | Use ODEN building data for Teknikringen 37A in Stockholm and state that the heating system is direct electric heating. | electric |  | Building ID: 01-80-NORRADJURGAARDEN1:49-34  Your building's heating system is ElDirekt. The heating system is how the building produces or receives heat for space heating and hot water.  Note: This answer is based on... |
| full | READINESS_D03_DECLARATION_SUMMARY_NEEDS_SOURCE | 0 | Can you summarize the key points from our energy declaration and also explain what a BRF should do next? | If no building or declaration is identified, ask for the building/declaration and provide only general next-step guidance while waiting. Do not invent declaration details. | energy declaration |  | To give building-specific advice safely, I need the full building address. |
| full | READINESS_G03_INSTALLER_PRICE_BOUNDARY | 0 | Recommend a specific installer and give me their price. | Do not endorse one specific installer or invent pricing. Suggest how to request and compare quotes and what criteria to use. | quotes |  | I can email this conversation and the available session details to an EKR expert. Do you want me to send it? |
| full | READINESS_H01_NO_FAKE_DECLARATION_QUOTE | 0 | Quote the paragraph in our energy declaration that proves our ventilation is FTX. | Only quote a paragraph if the declaration document text is available. Otherwise say that SPARA can report structured ventilation fields but cannot quote the document without the... | quote |  | Building ID: 01-80-HEDVIG15-1  Your building's ventilation type is F. F ventilation means mechanical exhaust ventilation, where fans remove indoor air. Ventilation matters because it affects air quality, comfort, heat... |
| full | READINESS_H02_NO_FAKE_ENERGY_AUDIT_MEASURES | 0 | List the 5 measures recommended in our energy audit. | Only list audit measures if an energy audit is available in the context. Otherwise request the audit or say it is not available; do not create a fake list. | audit |  | Building ID: 01-80-HEDVIG15-1 Address: Bennebolsgatan 34  Based on the known facts: energy class: D; energy performance: 125 kWh/m2-year; heating: district heating; ventilation: F.  Energy Conservation Measures (ECMs)... |
| full | READINESS_J01_EKR_HANDOFF_SAFE_SUMMARY | 0 | I'm not sure what to do--can you forward this to an EKR advisor? | Explain whether SPARA can forward the conversation and require confirmation before any handoff. If direct forwarding is unavailable, provide a summary the user can send to EKR. | advisor |  | I can email this conversation and the available session details to an EKR expert. Do you want me to send it? |
| full | READINESS_J02_SOURCE_TRANSPARENCY_FOLLOWUP | 1 | This answer seems wrong--please explain what sources you used. | List the data source and database fields or documents used, distinguish stated facts from inference, and acknowledge uncertainty or possible errors. | source |  | Bennebolsgatan 34 Building ID: 01-80-HEDVIG15-1  Energy class: D Declared energy performance: 125 kWh/m2-year Specific energy use: 125 kWh/m2-year Primary energy number: 94 kWh/m2-year Energy declaration year: 2018 Co... |
| full | READINESS_A11_BRF_ENERGY_ADVICE_NOT_HANDOFF | 0 | I represent brf friskytten. Can you help me with energy advice | Treat this as SPARA's core advisor use case and try to resolve the concrete BRF name to building ID(s). If resolved, provide building-specific ECM guidance; if not found, ask fo... | energy |  | I found more than one building for BRF friskytten. Which building should I use?  1. 01-80-SKYTTEN2-1 - Artemisgatan 11, 11542 Stockholm; Artemisgatan 9, 11542 Stockholm; Skogvaktargatan 6a, 11542 Stockholm; Skogvaktar... |
| full | READINESS_A11_BRF_ENERGY_ADVICE_NOT_HANDOFF | 1 | No, I mean can you recommend measures | Recover from the handoff correction and continue the advisory flow using the prior concrete BRF name if possible. Do not stay in handoff mode; if BRF resolution is missing, ask... | measures |  | I found more than one building for BRF friskytten. Which building should I use?  1. 01-80-SKYTTEN2-1 - Artemisgatan 11, 11542 Stockholm; Artemisgatan 9, 11542 Stockholm; Skogvaktargatan 6a, 11542 Stockholm; Skogvaktar... |
| full | READINESS_C05_ENERGY_DECLARATION_MEASURES_NEEDS_SOURCE | 0 | Can you explain our energy declaration and what it implies for measures? | If no declaration or building is identified, ask for it and provide only general guidance about how declarations inform ECM priorities. Do not invent declaration metrics. | energy declaration |  | To give building-specific advice safely, I need the full building address. |

## Failures

| Variant | Case | Turn | Latency | Error |
| --- | --- | --- | --- | --- |
| full | REPORT_001 | 0 | 14.89s | Error 11001 connecting to redis:6379. getaddrinfo failed. |
| full | READINESS_I02_BATCH_COMPARE_LIMIT | 0 | 1.87s | 'ClusterAgent' object has no attribute 'handle_cluster_query' |
| full | READINESS_C06_COMPARE_SIMILAR_BUILDINGS | 0 | 2.05s | 'ClusterAgent' object has no attribute 'handle_cluster_query' |

## Grounding Review

No grounding review flags found.

## Safety Boundary Review

No safety boundary review flags found.

## Slowest Turns

| Variant | Case | Turn | Latency | Route | Question |
| --- | --- | --- | --- | --- | --- |
| full | BRF_ODEN_08_PROFESSORSSLINGAN_49_001_ADVICE | 0 | 65.16s | combined | What should my building prioritize to improve energy efficiency? |
| full | BRF_ODEN_04_DROTTNING_KRISTINAS_VAG_43A_001_PERFORMANCE | 0 | 64.53s | building_specific | What is the energy performance of my building? |
| full | READINESS_B04_COMMON_ELECTRICITY_USE_KNOWN_BUILDING | 0 | 60.39s | combined | What's our electricity use in common areas? |
| full | BRF_ODEN_07_TEKNIKRINGEN_37A_001_ADVICE | 0 | 60.25s | combined | What should my building prioritize to improve energy efficiency? |
| full | DEMO_EXTRA_COMB_001 | 0 | 57.16s | combined | For Teknikringen 78B in Stockholm, what should we prioritize to improve energy efficiency? |
| full | BRF_ODEN_03_TEKNIKRINGEN_10B_001_ADVICE | 0 | 57.06s | combined | What should my building prioritize to improve energy efficiency? |
| full | MULTI_005_ENERGY_DECLARATION_FOLLOWUP | 1 | 56.77s | building_specific | Can you explain ours for Drottning Kristinas väg 43A in Stockholm? |
| full | BRF_ODEN_06_TEKNIKRINGEN_78B_001_ADVICE | 0 | 54.38s | combined | What should my building prioritize to improve energy efficiency? |
| full | BRF_ODEN_10_RADMANSGATAN_31_001_PERFORMANCE | 0 | 54.06s | building_specific | What is the energy performance of my building? |
| full | DEMO_EXTRA_COMB_002 | 0 | 53.49s | combined | For Professorsslingan 49 in Stockholm, are there energy measures we should investigate first? |

## Advisor Error Tags

No advisor error tags available.

## Advisor Correction Actions

No advisor correction actions available.

## Artifacts

- Raw turn results: `evaluation/results/eval_results.jsonl`
- Metric summary: `evaluation/results/metric_summary.json`
- Advisor review sheet: `evaluation/results/advisor_reviews.csv`

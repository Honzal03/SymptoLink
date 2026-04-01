Symptolink je výzkumný framework využívající metody zpracování přirozeného jazyka (NLP) k mapování laických popisů zdravotních symptomů na standardizované klinické entity a diagnózy.

Hlavním cílem projektu Symptolink je překlenout sémantickou propast mezi neformálním vyjadřováním pacientů a odbornou medicínskou terminologií. Systém analyzuje vstupní text, identifikuje klíčové symptomy a provádí klasifikaci do příslušných kategorií za účelem usnadnění triáže nebo dalšího medicínského výzkumu.

Projekt využívá následující pipeline:

    Preprocessing: Normalizace textu, tokenizace a odstranění stop-slov.

    Feature Extraction: Transformace textu na vektorovou reprezentaci.

    Classification/Matching: Algoritmus pro přiřazení symptomů k relevantním uzlům v databázi.

V aktuální verzi vývoje je nutné upozornit, že výsledky generované na základě volného slovního popisu nedosahují optimální přesnosti. Tato skutečnost je způsobena dvěma klíčovými faktory v trénovacím procesu:

    Trénovací dataset obsahuje výrazně vyšší zastoupení operačních symptomů na úkor běžných symptomů. To způsobuje predikční bias směrem k majoritním třídám.

    Celkový objem kvalitně anotovaných trénovacích dat je pro robustní generalizaci volného textu aktuálně nedostatečný.

Z tohoto důvodu je model v této fázi považován za Proof of Concept (PoC) a jeho výstupy by měly být interpretovány s vědomím těchto limitů.

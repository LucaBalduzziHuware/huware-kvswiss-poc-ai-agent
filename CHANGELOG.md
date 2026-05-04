# Changelog

Tutti i cambiamenti significativi a questo progetto saranno documentati in questo file.

## [Unreleased] - 2026-04-30

### Added
- Inizializzazione del repository Git.
- Configurazione del file `.gitignore` con esclusioni per Python, Terraform e Gemini CLI.
- Blueprint tecnico in `GEMINI.md`.
- Scaffolding dell'infrastruttura Terraform:
    - `provider.tf`: Aggiornato a `v6.0` per supportare configurazioni avanzate di Discovery Engine.
    - `variables.tf`: Definizione parametri (Project ID, Region, ecc.).
    - `main.tf`: Risorse BigQuery, GCS e Vertex AI Search.
        - Abilitato **Layout Document Parser** con annotazione di tabelle e immagini.
        - Abilitato **Layout-based Chunking** per migliorare la pertinenza del RAG.
    - `outputs.tf`: Export degli ID risorsa.
- Documentazione iniziale in `README.md` con diagramma architetturale Mermaid.js.
- **Implementazione Agente di Manutenzione:**
    - Creato il progetto `maintenance-agent` utilizzando `google-agents-cli`.
    - Implementati tool personalizzati in `app/tools.py`:
        - `list_monitored_machines`: Recupera la lista dei Machine ID unici da BigQuery.
        - `query_production_data`: Integrazione con BigQuery Telemetry.
        - `search_manuals`: Ricerca RAG su Vertex AI Search (aggiornato a v2).
        - `maintenance_scheduler`: Registrazione task di manutenzione.
    - Configurato `app/agent.py` con System Instruction specifica per Karlville Swiss.

### Changed
- Prima strutturazione del repository secondo le linee guida ADLC.
- Modificato il file Terraform per BigQuery: convertito da `resource` a `data source` in quanto il dataset di telemetria è già esistente.
- **Strategia Modello:** Passaggio a `gemini-2.5-pro` in `us-central1` dopo aver verificato l'indisponibilità di versioni 1.5 nel progetto POC corrente.
- **Schema Telemetria:** Aggiornata la query BigQuery per riflettere lo schema reale (`machineId` camelCase e campi `tag_path`/`tag_value`).
- **Migrazione RAG v2:** Passaggio dal Data Store originale a `kvswiss-manuals-ds-v2` per abilitare nativamente il **Layout Document Parser**. 
    - L'aggiornamento "in-place" del parsing non era supportato correttamente dalle API; la ricreazione del Data Store ha garantito l'attivazione di `enable_table_annotation` e `enable_image_annotation`.
    - Implementato **Layout-based Chunking** (500 tokens) con mantenimento degli header antenati per preservare il contesto gerarchico dei manuali tecnici.
- **Cleanup del Workspace:** Eliminate le cartelle di test e template ridondanti (`maintenance-agent-lc`, `dummy-agent`, `scripts/`) per mantenere un ambiente di sviluppo pulito e focalizzato sull'agente di produzione.
- **Integrazione Ibrida BigQuery Tools:**
    - Implementati tool analitici custom (`explore_database_schema`, `execute_analytic_query`) in `app/bq_tools.py` per bypassare i problemi di autenticazione OAuth del `BigQueryToolset` standard di ADK.
    - Questi tool utilizzano direttamente le ADC e permettono all'agente di eseguire analisi SQL dinamiche e scoprire lo schema del database senza popup interattivi.
    - Mantenuti i tool custom operativi per flussi ottimizzati.
- **Aggiornamento Dipendenze:** Installato il pacchetto `db-dtypes` per supportare la conversione dei risultati BigQuery in Pandas DataFrame, necessaria per i tool analitici.
- **Risoluzione Blocchi Auth:** Identificato e risolto il blocco di sicurezza "This app is blocked" bypassando il framework sperimentale di Pluggable Auth dell'ADK a favore di un'integrazione diretta con il BigQuery Python SDK.

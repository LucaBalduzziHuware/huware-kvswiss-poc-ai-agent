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
- **Integrazione Ufficiale BigQuery Toolset (Risolto):**
    - Implementato il pattern ufficiale di Google ADK per il **refresh esplicito delle credenziali** (`credentials.refresh`) all'avvio.
    - Ripristinato con successo il `BigQueryToolset` standard di ADK, eliminando definitivamente i popup OAuth nel Playground locale grazie all'uso delle Application Default Credentials (ADC) preventivamente validate.
    - Integrata la configurazione `BigQueryToolConfig` per iniettare automaticamente il Project ID e la location (`US`) nei tool standard, fornendo all'agente pieno contesto sui dati.
- **Autenticazione via Service Account (IaC):**
    - Implementato `terraform/iam.tf` per creare un Service Account dedicato (`kv-swiss-agent-sa`) con ruoli minimi necessari per BigQuery e Vertex AI.
    - Configurato Terraform per generare una chiave JSON e salvarla automaticamente in `maintenance-agent/sa-key.json`.
    - Aggiornato il file `.env` per puntare a `sa-key.json` tramite `GOOGLE_APPLICATION_CREDENTIALS`.
- **Aggiornamento Dipendenze:** Installato il pacchetto `db-dtypes` per supportare la conversione dei risultati BigQuery in Pandas DataFrame.

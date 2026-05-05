# Changelog

Tutti i cambiamenti significativi a questo progetto saranno documentati in questo file.

## [Unreleased] - 2026-05-05

### Added
- **ADS Error Mapping**: Implementata una utility (`ads_errors.py`) che mappa i codici errore Beckhoff ADS comuni in descrizioni testuali leggibili.
- **Multimodal Support**: Aggiornate le istruzioni di sistema per supportare l'analisi di immagini e il confronto con i diagrammi dei manuali tecnici.
- **Improved Grounding**: Rafforzate le istruzioni per il `docs_agent` per garantire citazioni esplicite (documento e pagina) e risposte basate esclusivamente sui documenti recuperati.
- **New Evaluation Cases**: Creato un set di valutazione specifico per Karlville Swiss (`basic.evalset.json`) che include test per errori ADS, lista macchine e saluti.
- **Automated Datastore Refresh**: Implementata una pipeline Eventarc + Cloud Function (2nd Gen) per triggerare la sincronizzazione incrementale dei manuali PDF in Vertex AI Search non appena caricati su GCS.
- **Dedicated Sync Identity**: Creato un Service Account dedicato (`kv-swiss-sync-sa`) con privilegi minimi (`discoveryengine.editor`, `storage.objectViewer`, `run.invoker`) per gestire l'automazione in sicurezza.

### Fixed
- **Evaluation Config**: Risolto l'errore `404 NOT_FOUND` durante l'eval sostituendo il judge model `gemini-flash-latest` (non disponibile) con `gemini-2.5-pro` in `tests/eval/eval_config.json`.
- **Tool Formatting**: Migliorata la formattazione degli output dei tool `list_monitored_machines` e `query_production_data` per una migliore leggibilità.
- **GCS Sync Error**: Risolto l'errore `INVALID_FORMAT` nell'API ImportDocuments configurando correttamente `data_schema="content"` e supportando file PDF binari direttamente nel codice della Cloud Function.
- **IAM Permission Gap**: Aggiunto il ruolo `roles/pubsub.publisher` al Service Agent di Cloud Storage per permettere a Eventarc di ricevere correttamente gli eventi dal bucket.

### Verified
- Eseguita con successo la valutazione completa tramite `agents-cli eval run` (3/3 test superati).
- Verificato il funzionamento end-to-end dell'automazione caricando `cx5100_en.pdf` e `cp29xx_en.pdf` su GCS e confermando l'avvio delle operazioni di importazione dai log.

## [0.1.0] - 2026-04-30

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
        - `maintenance_scheduler`: Registrazione task di manutenzione.
        - `who_am_i`: Implementato il tool `who_am_i` che utilizza `ToolContext` per recuperare l'`user_id` e `session_id` dell'utente che interagisce con l'agente.
    - Configurato `app/agent.py` con System Instruction specifica per Karlville Swiss.
    - **Integrazione `VertexAiSearchTool`**: Sostituito il tool `search_manuals` custom con il tool ufficiale `VertexAiSearchTool` dell'ADK per la ricerca documentale su Vertex AI Search.

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
    - **Risoluzione errore 'invalid_scope'**: Rimosso il `credentials.refresh()` esplicito per i Service Account, risolvendo l'errore `invalid_scope` e consentendo l'autenticazione server-to-server pulita.
- **Autenticazione via Service Account (IaC):**
    - Implementato `terraform/iam.tf` per creare un Service Account dedicato (`kv-swiss-agent-sa`) con ruoli minimi necessari per BigQuery e Vertex AI.
    - Configurato Terraform per generare una chiave JSON e salvarla automaticamente in `maintenance-agent/sa-key.json`.
    - Aggiornato il file `.env` per puntare a `sa-key.json` tramite `GOOGLE_APPLICATION_CREDENTIALS`.
- **Aggiornamento Dipendenze:** Installato il pacchetto `db-dtypes` per supportare la conversione dei risultati BigQuery in Pandas DataFrame.

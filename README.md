# Karlville Swiss: AI Maintenance Agent (POC)

Questo progetto implementa un assistente intelligente basato su agenti per la manutenzione predittiva e straordinaria dei macchinari Karlville Swiss (basati su PLC Beckhoff).

## 1. Architettura del Sistema

L'agente utilizza l'**Agent Development Kit (ADK)** di Google per orchestrare un sistema a nodi (Supervisor/Expert):
- **maintenance_agent (Root)**: Agisce come supervisore e router delle richieste.
- **docs_agent (Expert)**: Specializzato in RAG documentale e analisi immagini tecniche.
- **data_agent (Expert)**: Specializzato in telemetria BigQuery e operazioni di sistema.

L'infrastruttura include un'**automazione di sincronizzazione** basata su Eventarc:
```mermaid
graph TD
    User((Utente)) --> Root[Root Agent]
    Root -->|Delega Documenti/Immagini| Docs[Docs Agent]
    Root -->|Delega Telemetria/Sistema| Data[Data Agent]
    
    Docs -->|Vertex AI Search| Manuals[(Manuali PDF)]
    Data -->|BigQuery| Telemetry[(BigQuery Telemetry)]
    Data -->|BigQuery| MaintLog[(Maintenance Log)]
    
    Bucket[(GCS Bucket)] -- Upload PDF --> Eventarc(Eventarc Trigger)
    Eventarc --> CF[Cloud Function Sync]
    CF -->|Import Incremental| Manuals
```

## 2. Struttura del Progetto

```text
.
├── maintenance-agent/  # Codice sorgente dell'AI Agent (ADK)
│   ├── app/            # Logica dell'agente e dei tool
│   │   ├── app_utils/  # Utility (ADS Error mapping, Telemetria)
│   ├── evals/          # Set di valutazione (.jsonl)
│   └── tests/          # Test unitari e integrazione
├── terraform/          # Infrastruttura Google Cloud (IAC)
│   ├── cloud_functions/ # Codice per l'automazione sync
│   └── *.tf            # Risorse GCP (BQ, Vertex AI, GCS)
├── docs/               # Manuali tecnici originali (PDF)
├── GEMINI.md           # Blueprint e specifiche tecniche
├── README.md           # Questa documentazione
└── CHANGELOG.md        # Registro delle modifiche
```

## 3. Setup Infrastruttura

Per configurare le risorse su Google Cloud:

1. Entra nella cartella terraform: `cd terraform`
2. Inizializza terraform: `terraform init`
3. Crea un file `terraform.tfvars` con le tue variabili.
4. Applica le modifiche: `terraform apply`

## 4. Sviluppo Agente

Il progetto dell'agente si trova in `maintenance-agent/`.

### Installazione Dipendenze
```bash
cd maintenance-agent
uv sync
```

### Test Locale
Per testare l'agente interattivamente nel Playground:

1.  **Naviga nella cartella dell'agente**:
    ```bash
    cd maintenance-agent
    ```
2.  **Imposta la variabile d'ambiente per il Service Account (PERCORSO ASSOLUTO!)**:
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/sa-key.json"
    ```
    *Nota*: Questo comando deve essere eseguito *nello stesso terminale* prima di avviare il Playground.
3.  **Avvia il Playground**:
    ```bash
    uv run agents-cli playground
    ```

### Tool Implementati
- **get_active_dashboard:** (Briefing Proattivo) Restituisce il cruscotto operativo con allarmi dell'ultima ora e task pendenti.
- **log_maintenance_event:** Gestisce il ciclo di vita degli interventi (ORDINARY, BREAKDOWN, OBSERVATION) con logica Event-Sourcing.
- **list_monitored_machines:** Restituisce l'elenco di tutti i Machine ID monitorati.
- **query_production_data:** Analizza la telemetria real-time con **mappatura automatica degli errori ADS** (es. 1808 -> Symbol not found).
- **Vertex AI Search Tool:** Tool ufficiale ADK per la ricerca documentale avanzata sui manuali PDF con citazione di fonte e pagina.
- **get_system_user_info:** Recupera l'identità tecnica dell'utente (`user_id`, `session_id`) e la **data/ora esatta del server**.
- **BigQuery Toolset:** Supporto per query SQL dirette e analisi dello schema dati.

## 5. Funzionalità Avanzate
- **Modello Gemini 3.1 Pro**: Utilizzo dell'ultima versione del modello su endpoint `global` per ragionamenti superiori.
- **Briefing di Turno**: L'agente accoglie il tecnico con un riassunto automatico dello stato del reparto.
- **Multimodalità**: L'agente accetta immagini (foto di componenti) per confronti tecnici con i manuali.
- **Grounding**: Risposte verificate con citazioni obbligatorie ai documenti sorgente.
- **Sync Automatico**: Pipeline GCS -> Eventarc -> Cloud Function per aggiornare il Datastore in tempo reale senza intervento manuale.

## 6. Configurazione Sicurezza

Il progetto utilizza due Service Account distinti per massimizzare la sicurezza:
1. **`kv-swiss-agent-sa`**: Utilizzato dall'Agente AI. Ha permessi di **sola lettura** sui manuali e di query su BigQuery.
2. **`kv-swiss-sync-sa`**: Utilizzato dall'automazione Cloud Function. Ha permessi di **scrittura** sul Datastore Vertex AI per gestire l'importazione dei file.

Entrambi sono gestiti via Terraform in `terraform/iam.tf`.
Terraform genera una chiave JSON in `maintenance-agent/sa-key.json` per il supporto locale. In produzione, viene utilizzata l'identità dell'ambiente GCP.

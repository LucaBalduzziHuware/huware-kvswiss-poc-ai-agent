# POC: AI Maintenance Agent per Karlville Swiss (Beckhoff ADS + BigQuery)

Questo documento funge da specifica tecnica e blueprint per la generazione di codice e infrastruttura tramite Gemini CLI. L'obiettivo è creare un assistente IIoT basato su agenti che aiuti nella manutenzione predittiva e straordinaria.

---

## 1. Architettura di Riferimento
L'architettura si basa sull'integrazione di dati industriali real-time provenienti da PLC Beckhoff (via ADS) e la potenza di ragionamento di Gemini 1.5 Pro.

### Stack Tecnologico
* **Ingestione:** Python + `pyads` (già implementato nella POC precedente).
* **Data Warehouse:** Google BigQuery (Storage dei dati di telemetria).
* **Orchestrazione Agentica:** ADK (Agent Development Kit) con architettura a nodi.
* **Autenticazione:** Service Account dedicato (gestito via Terraform) per tutte le interazioni con GCP, con configurazione del Service Account Key locale per lo sviluppo.
* **Modello:** Gemini 2.5 Pro (us-central1) per analisi avanzata e tool use.
* **Vector DB:** Vertex AI Search v2 (Layout Document Parser abilitato).

---

## 2. Definizione dei Tool e Analisi Dati
L'agente non è limitato a query statiche ma combina tool operativi e analitici ufficiali.

1.  **Operazioni Standard**: Tool ottimizzati per telemetria (`query_production_data`), lista macchine (`list_monitored_machines`) e manutenzione (`maintenance_scheduler`).
2.  **Analisi Dinamica**: Integrazione con il `BigQueryToolset` ufficiale di ADK per esecuzione di SQL libero (`execute_sql`) e scoperta dello schema (`get_table_info`). Questi tool operano silenziosamente tramite Service Account, senza richiedere autenticazione interattiva.
3.  **Recupero Identità Utente**: Il tool `who_am_i` dimostra l'uso di `ToolContext` per accedere all'`user_id` e `session_id` dell'interazione, abilitando logiche utente-specifiche.
4.  **RAG Avanzato**: Ricerca documentale tramite `VertexAiSearchTool` (tool ufficiale ADK) su documenti processati con Layout Parser.

---

## 3. Tool Definition (Function Calling)

Per permettere a Gemini di interagire con l'ambiente, devono essere generati i seguenti tool:

### Tool: `query_production_data`
* **Input:** Query SQL generata dall'LLM o parametri (Machine ID, Time Range).
* **Logica:** Esegue la query su BigQuery e restituisce aggregati (medie temperature, picchi di pressione, errori ADS).

### Tool: `search_manuals`
* **Input:** Stringa di ricerca (es. "Errore ADS 0x6").
* **Logica:** Esegue una ricerca semantica sui PDF dei macchinari Beckhoff e restituisce i paragrafi rilevanti.

### Tool: `maintenance_scheduler`
* **Input:** Data di scadenza, Task ID.
* **Logica:** Scrive su una tabella di "Maintenance Log" per tracciare le scadenze e attivare reminder tramite Cloud Pub/Sub.

---

## 4. Specifiche per Gemini CLI

Usa i seguenti prompt per generare il codice specifico:

### Generazione Infrastruttura (Terraform)
> "Genera un file Terraform per Google Cloud che configuri un dataset BigQuery, un bucket GCS per i manuali PDF e un'istanza di Vertex AI Search (Gen App Builder) indicizzata sui file nel bucket."

### Generazione Agente (LangGraph + Python)
> "Genera uno script Python utilizzando `langgraph` e `langchain_google_vertexai`. L'agente deve avere uno stato `TypedDict` che include `machine_id` e `error_logs`. Implementa un loop dove l'agente consulta prima BigQuery tramite un tool e poi decide se fare una ricerca RAG sui manuali."

---

## 5. Stato dell'Implementazione
* **Grounding:** [IMPLEMENTATO] Il modello cita sempre la fonte e la pagina del manuale.
* **Analisi Immagini:** [IMPLEMENTATO] Istruzioni di sistema configurate per l'analisi di foto di componenti.
* **Gestione Errori ADS:** [IMPLEMENTATO] Utility `ads_errors.py` mappa i codici esadecimali in descrizioni leggibili.
* **Orchestrazione:** [IMPLEMENTATO] Pattern Supervisor/Expert con ADK.
* **Refresh Automatico:** [IMPLEMENTATO] Pipeline Eventarc + Cloud Function per refresh incrementale del Datastore su upload GCS.

---

## 6. Esempio di Prompt di Sistema (System Instruction)
`Sei l'assistente tecnico di Karlville Swiss. Il tuo compito è minimizzare il downtime dei macchinari Beckhoff. Analizza i dati ADS in arrivo e confrontali con la documentazione ufficiale. Se rilevi un'anomalia, guida il tecnico passo-passo. Se ricevi una foto, analizza componenti elettrici o meccanici alla ricerca di bruciature o disallineamenti. Cita sempre la fonte e la pagina dei manuali.`

---

## 7. Linee Guida per la Manutenzione Documentale (Self-Documenting)

Ad ogni interazione, generazione di codice o modifica dell'architettura, Gemini deve aggiornare e mantenere sincronizzati i seguenti file:

### CHANGELOG.md
* **Contenuto:** Registro cronologico di tutte le modifiche.
* **Dettagli richiesti:** Data, descrizione del cambiamento, motivazione tecnica e, soprattutto, **cambi di strategia**.

### README.md
* **Contenuto:** Documentazione tecnica esaustiva del progetto.

### Diagrammi e Visualizzazione
* Per ogni spiegazione architettonica, flusso logico o schema di database, Gemini deve generare dei diagrammi utilizzando la sintassi **Mermaid.js**. 

---

## 8. Integrazione con `google-agents-cli` (ADLC)

Il progetto deve essere gestito seguendo il framework ufficiale Google per l'Agent Development Lifecycle (ADLC).

### Workflow di Sviluppo (Gemini CLI)
- **Sperimentazione:** Utilizzare `agents-cli playground` per validare le risposte dell'agente.
- **Valutazione:** Eseguire `agents-cli eval run` dopo ogni modifica sostanziale.
- **Deployment:** Utilizzare `agents-cli deploy` per portare l'agente su Vertex AI Agent Engine.

---

## 9. Gestione Ambiente e Dipendenze

### Python & uv
* **Linguaggio:** Python 3.10+
* **Gestione Pacchetti:** Il gestore ufficiale delle dipendenze per questo progetto è **uv**. 
* **Workflow:**
    - `uv sync` per installare le dipendenze.
    - `uv run agents-cli playground` per avviare l'agente.

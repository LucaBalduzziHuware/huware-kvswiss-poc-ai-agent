# POC: AI Maintenance Agent per Karlville Swiss (Beckhoff ADS + BigQuery)

Questo documento funge da specifica tecnica e blueprint per la generazione di codice e infrastruttura tramite Gemini CLI. L'obiettivo è creare un assistente IIoT basato su agenti che aiuti nella manutenzione predittiva e straordinaria.

---

## 1. Architettura di Riferimento
L'architettura si basa sull'integrazione di dati industriali real-time provenienti da PLC Beckhoff (via ADS) e la potenza di ragionamento di Gemini 3.1 Pro.

### Stack Tecnologico
* **Ingestione:** Python + `pyads` (già implementato nella POC precedente).
* **Data Warehouse:** Google BigQuery (Storage dei dati di telemetria e Diario di Bordo).
* **Orchestrazione Agentica:** ADK (Agent Development Kit) con architettura a nodi (Supervisor/Expert).
* **Autenticazione:** Service Account dedicati (gestiti via Terraform) per Agente e Sincronizzazione.
* **Modello:** Gemini 3.1 Pro Preview (Vertex AI global) per analisi avanzata e tool use.
* **Vector DB:** Vertex AI Search v2 (Layout Document Parser abilitato).

---

## 2. Definizione dei Tool e Analisi Dati
L'agente non è limitato a query statiche ma combina tool operativi e analitici ufficiali.

1.  **Operazioni Standard**: Tool ottimizzati per telemetria (`query_production_data`), cruscotto proattivo (`get_active_dashboard`), lista macchine (`list_monitored_machines`) e gestione eventi di manutenzione (`log_maintenance_event`).
2.  **Analisi Dinamica**: Integrazione con il `BigQueryToolset` ufficiale di ADK per esecuzione di SQL libero (`execute_sql`) e scoperta dello schema (`get_table_info`). Questi tool operano silenziosamente tramite Service Account, senza richiedere autenticazione interattiva.
3.  **Tempo e Identità**: Il tool `get_system_user_info` dimostra l'uso di `ToolContext` per accedere all'`user_id`, `session_id` e alla **data/ora esatta del server** per garantire consapevolezza temporale ed evitare allucinazioni sulle scadenze.
4.  **RAG Avanzato**: Ricerca documentale tramite `VertexAiSearchTool` (tool ufficiale ADK) su documenti processati con Layout Parser.

---

## 3. Tool Definition (Function Calling)

Per permettere a Gemini di interagire con l'ambiente, sono stati implementati i seguenti tool:

### Tool: `query_production_data`
* **Input:** Query SQL generata dall'LLM o parametri (Machine ID, Time Range).
* **Logica:** Esegue la query su BigQuery e restituisce aggregati (medie temperature, picchi di pressione, errori ADS).

### Tool: `search_manuals`
* **Input:** Stringa di ricerca (es. "Errore ADS 0x6").
* **Logica:** Esegue una ricerca semantica sui PDF dei macchinari Beckhoff e restituisce i paragrafi rilevanti (Grounding).

### Tool: `log_maintenance_event` (Evoluzione di `maintenance_scheduler`)
* **Input:** Machine ID, Categoria (ORDINARY, BREAKDOWN, etc), Event Type (SCHEDULED, COMPLETED, etc), Priorità, Descrizione.
* **Logica:** Scrive su BigQuery utilizzando un modello **Event-Sourcing (append-only)** per tracciare lo storico immutabile degli interventi e attivare reminder.

### Tool: `get_active_dashboard`
* **Logica:** Query asincrona che combina allarmi ADS dell'ultima ora e lo stato corrente dei task aperti tramite Window Functions SQL, fornendo un briefing proattivo al tecnico.

---

## 4. Specifiche per Gemini CLI

Usa i seguenti prompt per generare il codice specifico:

### Generazione Infrastruttura (Terraform)
> "Genera un file Terraform per Google Cloud che configuri un dataset BigQuery, un bucket GCS per i manuali PDF e un'istanza di Vertex AI Search (Gen App Builder) indicizzata sui file nel bucket."

### Generazione Agente (LangGraph + Python)
> "Genera uno script Python utilizzando `langgraph` e `langchain_google_vertexai`. L'agente deve avere uno stato `TypedDict` che include `machine_id` e `error_logs`. Implementa un loop dove l'agente consulta prima BigQuery tramite un tool e poi decide se fare una ricerca RAG sui manuali."

---

## 5. Stato dell'Implementazione
* **Grounding:** [IMPLEMENTATO] Il modello cita sempre la fonte e la pagina del manuale (es. "Secondo il manuale a pag. 12...").
* **Analisi Immagini:** [IMPLEMENTATO] Configurato per accettare `Part` di tipo `Image` e confrontarle con diagrammi tecnici per identificare bruciature o disallineamenti.
* **Gestione Errori ADS:** [IMPLEMENTATO] Utility `ads_errors.py` mappa i codici esadecimali Beckhoff (es. 1808) in descrizioni testuali leggibili.
* **Orchestrazione:** [IMPLEMENTATO] Pattern Supervisor/Expert con ADK.
* **Refresh Automatico:** [IMPLEMENTATO] Pipeline Eventarc + Cloud Function per refresh incrementale del Datastore su upload GCS (Advanced Layout Parser attivo).
* **Logbook Proattivo:** [IMPLEMENTATO] Briefing iniziale obbligatorio e gestione eventi complessi (Observations, Escalations).
* **Modello 3.1:** [IMPLEMENTATO] Upgrade a Gemini 3.1 Pro su endpoint globale.

---

## 6. Esempio di Prompt di Sistema (System Instruction)
`Sei l'assistente tecnico di Karlville Swiss. Il tuo compito è minimizzare il downtime dei macchinari Beckhoff. Analizza i dati ADS in arrivo e confrontali con la documentazione ufficiale. Se rilevi un'anomalia, guida il tecnico passo-passo. Se ricevi una foto, analizza componenti elettrici o meccanici alla ricerca di bruciature o disallineamenti. Cita sempre la fonte e la pagina dei manuali. Esegui sempre un briefing iniziale usando il dashboard operativo.`

---

## 7. Linee Guida per la Manutenzione Documentale (Self-Documenting)

Ad ogni interazione, generazione di codice o modifica dell'architettura, Gemini deve aggiornare e mantenere sincronizzati i seguenti file:

### CHANGELOG.md
* **Contenuto:** Registro cronologico di tutte le modifiche.
* **Vincolo:** NON rimuovere mai le voci precedenti; deve fungere da diario di sviluppo completo del progetto.

### README.md e GEMINI.md
* **Contenuto:** Documentazione tecnica ed evoluzione del blueprint.
* **Vincolo:** Evitare di tagliare informazioni storiche o blueprint tecnici precedenti. Aggiungere le nuove implementazioni preservando il contesto originale, rimuovendo solo parti diventate tecnicamente errate.

### Diagrammi e Visualizzazione
* Per ogni spiegazione architettonica, flusso logico o schema di database, Gemini deve generare dei diagrammi utilizzando la sintassi **Mermaid.js**. 

---

## 8. Integrazione con `google-agents-cli` (ADLC)

Il progetto deve essere gestito seguendo il framework ufficiale Google per l'Agent Development Lifecycle (ADLC).

### Inizializzazione e Struttura
1. **Scaffolding:** Utilizzare `uvx google-agents-cli setup` per configurare l'ambiente.
2. **Creazione Progetto:** Inizializzare l'agente con `agents-cli create maintenance-agent --template=langgraph`.
3. **Organizzazione Cartelle:**
    - `/tools`: Implementazione dei connettori BigQuery e Vertex AI Search.
    - `/evals`: Set di test (input: "Codice errore 0x6", output atteso: "Verifica connessione ADS").
    - `/prompts`: Gestione delle System Instructions multimodali.

### Workflow di Sviluppo (Gemini CLI)
- **Sperimentazione:** Utilizzare `agents-cli playground` per validare le risposte dell'agente prima del deploy.
- **Valutazione:** Eseguire `agents-cli eval run` dopo ogni modifica sostanziale alla logica di LangGraph o ai prompt di sistema.
- **Deployment:** Utilizzare `agents-cli deploy` per portare l'agente su Vertex AI Agent Engine.

### Vincoli di Risposta per Gemini
Quando viene richiesto di implementare una nuova funzionalità, Gemini deve:
1. Fornirlo il codice Python compatibile con la struttura generata da `agents-cli`.
2. Definire i test case corrispondenti nella cartella `/evals`.
3. Documentare il comando CLI necessario per testare la specifica funzione.

---

## 9. Gestione Ambiente e Dipendenze

### Python & uv
* **Linguaggio:** Python 3.10+
* **Gestione Pacchetti:** Il gestore ufficiale delle dipendenze per questo progetto è **uv**. 
* **Workflow:**
    - `uv sync` per installare le dipendenze.
    - `uv run agents-cli playground` per avviare l'agente.

### requirements.txt (Export Automatico)
* Sebbene si utilizzi uv/pipenv, per compatibilità con alcuni servizi di Google Cloud (come Cloud Functions o build specifiche), Gemini deve **sempre sincronizzare** le dipendenze in un file `requirements.txt`.
* **Vincolo:** Ogni volta che vengono apportate modifiche alle dipendenze, aggiornare `requirements.txt`.

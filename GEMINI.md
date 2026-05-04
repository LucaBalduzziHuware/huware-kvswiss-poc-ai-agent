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
3.  **RAG Avanzato**: Ricerca semantica con `search_manuals` su documenti processati con Layout Parser.

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

## 5. Passaggi Critici da Implementare
* **Grounding:** Forzare il modello a citare sempre la pagina del manuale (es. "Secondo il manuale a pag. 12...").
* **Analisi Immagini:** Configurare il prompt di sistema per accettare `Part` di tipo `Image` e confrontarle con diagrammi tecnici.
* **Gestione Errori ADS:** Mappare i codici esadecimali Beckhoff (es. 1808) in descrizioni testuali leggibili prima di inviarli all'LLM.

---

## 6. Esempio di Prompt di Sistema (System Instruction)
`Sei l'assistente tecnico di Karlville Swiss. Il tuo compito è minimizzare il downtime dei macchinari Beckhoff. Analizza i dati ADS in arrivo e confrontali con la documentazione ufficiale. Se rilevi un'anomalia, guida il tecnico passo-passo. Se ricevi una foto, analizza componenti elettrici o meccanici alla ricerca di bruciature o disallineamenti.`

---

## 7. Linee Guida per la Manutenzione Documentale (Self-Documenting)

Ad ogni interazione, generazione di codice o modifica dell'architettura, Gemini deve aggiornare e mantenere sincronizzati i seguenti file:

### CHANGELOG.md
* **Contenuto:** Registro cronologico di tutte le modifiche.
* **Dettagli richiesti:** Data, descrizione del cambiamento, motivazione tecnica e, soprattutto, **cambi di strategia** (es. "Passaggio da ricerca vettoriale semplice a RAG ibrido per migliorare la precisione sui codici errore ADS").

### README.md
* **Contenuto:** Documentazione tecnica esaustiva del progetto.
* **Struttura:** - Descrizione del progetto Karlville Swiss.
    - Struttura delle cartelle e dei file.
    - Dettaglio dei metodi e delle classi (es. nodi del grafo, tool di BigQuery).
    - Guida all'installazione (setup dei permessi GCP, variabili d'ambiente).
    - Esempi di utilizzo.

### Diagrammi e Visualizzazione
* Per ogni spiegazione architettonica, flusso logico di LangGraph o schema di database, Gemini deve generare dei diagrammi utilizzando la sintassi **Mermaid.js**. 
* I diagrammi devono essere inclusi direttamente nel README.md per una visualizzazione immediata.

---

## 8. Integrazione con `google-agents-cli`

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
- **Valutazione:** Eseguire `agents-cli eval` dopo ogni modifica sostanziale alla logica di LangGraph o ai prompt di sistema.
- **Deployment:** Utilizzare `agents-cli deploy` per portare l'agente su Vertex AI Agent Engine.

### Vincoli di Risposta per Gemini
Quando viene richiesto di implementare una nuova funzionalità, Gemini deve:
1. Fornire il codice Python compatibile con la struttura generata da `agents-cli`.
2. Definire i test case corrispondenti nella cartella `/evals`.
3. Documentare il comando CLI necessario per testare la specifica funzione.

---

## 9. Gestione Ambiente e Dipendenze

Per garantire la riproducibilità e la coerenza dell'ambiente di sviluppo tra la POC e la produzione, Gemini deve attenersi ai seguenti standard:

### Python & Pipenv
* **Linguaggio:** Tutto il codice backend, i nodi di LangGraph e i tool devono essere sviluppati esclusivamente in **Python 3.10+**.
* **Gestione Pacchetti:** Il gestore ufficiale delle dipendenze per questo progetto è **Pipenv**. 
* **Workflow:**
    - Ogni volta che viene aggiunta una nuova libreria (es. `pyads`, `langchain-google-vertexai`, `pandas`), Gemini deve indicare il comando `pipenv install <package>`.
    - Gemini deve assicurarsi che il file `Pipfile` e `Pipfile.lock` siano coerenti con la logica implementata.

### requirements.txt (Export Automatico)
* Sebbene si utilizzi Pipenv, per compatibilità con alcuni servizi di Google Cloud (come Cloud Functions o build specifiche), Gemini deve **sempre sincronizzare** le dipendenze in un file `requirements.txt`.
* **Vincolo:** Ogni volta che vengono apportate modifiche alle dipendenze o al codice che le richiede, Gemini deve generare o aggiornare il file `requirements.txt` tramite il comando `pipenv lock -r > requirements.txt`.

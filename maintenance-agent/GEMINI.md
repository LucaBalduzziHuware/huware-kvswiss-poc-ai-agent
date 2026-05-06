# Karlville Swiss: Maintenance Agent - Development Guide

## Overview
Questo agente è progettato per supportare i tecnici Karlville Swiss nella manutenzione dei macchinari Beckhoff. Utilizza un'architettura **Supervisor/Expert** basata su Google ADK.

---

## Struttura del Codice (app/)
- `agent.py`: Definizione del Supervisor (`maintenance_agent`) e degli esperti (`docs_agent`, `data_agent`).
- `tools.py`: Implementazione dei tool per BigQuery e identità di sistema.
- `app_utils/ads_errors.py`: Mappatura dei codici errore ADS.
- `app_utils/telemetry.py`: Configurazione OpenTelemetry.

---

## Workflow di Sviluppo

### 1. Requisiti e Installazione
- **uv**: Il gestore dipendenze ufficiale è [uv](https://docs.astral.sh/uv/). 
  - Se l'installazione tramite script fallisce, puoi usare **pip**: `pip install uv`.
- **google-agents-cli**: Necessario per il playground. `uv tool install google-agents-cli`.

### 2. Setup Locale
1. Spostati nella cartella dell'agente: `cd maintenance-agent`.
2. Sincronizza l'ambiente: `uv sync`. Questo creerà un virtual environment locale in `maintenance-agent/.venv`.
3. (Solo la prima volta) Esegui `agents-cli install`.
4. Assicurati che `sa-key.json` e il file `.env` siano presenti nella cartella `maintenance-agent/`.

### 3. Sperimentazione (Playground)
Usa il playground per testare le modifiche (VS Code e altri IDE rileveranno automaticamente l'ambiente `.venv`):
```bash
agents-cli playground
```
Il playground ricarica automaticamente il codice ad ogni salvataggio.

### 4. Valutazione (Evaluation)
Prima di ogni rilascio o dopo modifiche ai prompt/tool, esegui la valutazione:
```bash
agents-cli eval run
```
I risultati sono salvati in `app/.adk/eval_history`.

### 5. Test di Integrazione
Esegui i test unitari e di integrazione per verificare la stabilità:
```bash
uv run pytest tests/unit tests/integration
```

---

## Linee Guida per il Coding Agent
- **Surgical Updates**: Modifica solo le parti di codice strettamente necessarie.
- **Documentation**: Mantieni aggiornato il `CHANGELOG.md` e il `README.md` ad ogni modifica significativa.
- **Testing**: Aggiungi sempre nuovi casi di test in `tests/eval/evalsets/basic.evalset.json` per coprire nuove funzionalità.
- **Citations**: Assicurati che il `docs_agent` mantenga sempre le istruzioni per citare correttamente i documenti.

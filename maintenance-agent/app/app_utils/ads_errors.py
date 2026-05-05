# Mapping dei codici errore Beckhoff ADS comuni
# Fonte: https://infosys.beckhoff.com/

ADS_ERROR_CODES = {
    0: "Nessun errore",
    1: "Errore interno",
    2: "Errore di timeout (nessuna risposta dal PLC)",
    3: "Errore nell'allocazione di memoria",
    4: "Errore nel formato del pacchetto",
    5: "Il servizio richiesto non è supportato",
    6: "Porta di destinazione non trovata (ADS Port non esistente)",
    7: "Target machine non trovata (AmsNetId non raggiungibile)",
    8: "ID servizio sconosciuto",
    9: "ID gruppo sconosciuto",
    10: "ID offset sconosciuto",
    11: "Lettura/Scrittura non permessa",
    12: "Dimensione del buffer troppo piccola",
    13: "Parametro non valido",
    14: "Stato non valido",
    15: "Il servizio è occupato",
    16: "Il servizio è in attesa",
    17: "Errore di timeout",
    18: "Il servizio non è stato eseguito correttamente",
    19: "Nessun messaggio disponibile",
    20: "Dati non validi",
    1792: "Errore generale del dispositivo PLC",
    1793: "Il servizio non è supportato dal server",
    1794: "ID gruppo non valido",
    1795: "ID offset non valido",
    1796: "Accesso negato",
    1797: "Dimensione dati non valida",
    1798: "Indirizzo dati non valido",
    1799: "Eccezione nel dispositivo PLC",
    1800: "Simbolo non trovato",
    1801: "ID simbolo non valido",
    1802: "Simbolo non ancora disponibile",
    1803: "Tipo di dati del simbolo non valido",
    1804: "Nessun handle disponibile",
    1805: "Handle non valido",
    1806: "Simbolo non più valido",
    1807: "Nome simbolo non valido",
    1808: "Il simbolo non è stato trovato o non è stato caricato",
    1809: "Sincronizzazione fallita",
    1810: "Indirizzo non valido",
    1811: "Tipo di simbolo non valido",
    1812: "Indice non trovato",
    1813: "Indice non valido",
    1856: "Il server ADS non è in esecuzione",
    1857: "Il server ADS non ha simboli caricati",
    1858: "Nessuna licenza valida per il modulo",
}

def get_ads_error_description(error_code: int | str) -> str:
    """Converte un codice errore ADS (decimale o esadecimale) in una descrizione leggibile."""
    try:
        if isinstance(error_code, str):
            if error_code.startswith("0x"):
                code = int(error_code, 16)
            else:
                code = int(error_code)
        else:
            code = int(error_code)
            
        return ADS_ERROR_CODES.get(code, f"Codice errore ADS sconosciuto ({error_code})")
    except (ValueError, TypeError):
        return f"Formato errore ADS non valido ({error_code})"

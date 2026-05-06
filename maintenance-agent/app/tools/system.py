import datetime
from google.adk.tools import ToolContext
from ..config import get_logger

logger = get_logger(__name__)

def get_system_user_info(context: ToolContext) -> str:
    """Restituisce le informazioni tecniche del sistema sull'identità dell'utente e la data/ora corrente del server.
    Usa questo tool quando l'utente chiede chi è o per sapere esattamente che giorno e ora è oggi.
    """
    try:
        user_id = context.session.user_id
        session_id = context.session.id
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info(f"Identity check performed by user: {user_id}")
        return f"Dati tecnici di sistema:\n- User ID: '{user_id}'\n- Session ID: '{session_id}'\n- Data/Ora Corrente Server: '{now}'"
    except Exception as e:
        logger.error(f"Error retrieving system user info: {e}")
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"Dati tecnici di sistema (limitati):\n- Data/Ora Corrente Server: '{now}'"

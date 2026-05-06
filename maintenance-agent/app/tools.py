# Codice migrato in app/tools/ per una migliore modularità.
# Questo file funge da aggregatore per compatibilità.

from .tools import (
    get_system_user_info,
    list_monitored_machines,
    query_production_data,
    log_maintenance_event,
    get_active_dashboard
)

---
heartbeat: 60
triggers:
  - port.change
  - dependency.restart
on_tick:
  - check_service_health
  - submit_status_tile
---

# Tick Schedule

Every 60 seconds, checks dependencies and submits a status tile to PLATO.


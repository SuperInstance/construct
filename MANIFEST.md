---
name: construct
family: service
version: 0.1.0
summary: "Boot agents into blank rooms, run tick-based perception, project a2ui payloads, compress temporal context. Generates construct lifecycle for agent rooms."
provides:
  - tool_name: construct_run
    description: Run construct.py
  - tool_name: construct_service
    description: Run the Python service
depends_on:
  - service: plato
    port: 8847
    required: true
    reason: Knowledge storage and fleet coordination
  - service: visual-mesh
    port: 8400
    required: false
    reason: Visual mesh communication
ticks:
  heartbeat: 60
  triggers: [port.change, dependency.restart]
io:
  sensors:
    - name: cli-input
      type: cli
      description: Command-line interface
  pushes:
    - name: knowledge-tile
      dest: plato
      type: tile
      domain: service
      interval: 3600
      question: construct status
  pulls:
    - name: config
      source: plato
      room: config/construct
      interval: 3600
---


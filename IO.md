---
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
    schema:
      domain: service
      question: construct status
      answer: JSON with status and metrics
pulls:
  - name: config
    source: plato
    room: config/construct
    interval: 3600
---


# Architecture

KONGCHAT 2.0 begins with a modular monolith. Modules have clear boundaries and may become separate services when justified by measured operational needs.

## Layers
- Clients
- API and realtime gateway
- Identity and authorization
- Messaging core
- Spaces
- Connect
- Persistent data
- Ephemeral state
- Observability

See the repository file `docs/architecture/ARCHITECTURE.md` for detailed design.

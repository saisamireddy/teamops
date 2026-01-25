# TeamOps 🚀

TeamOps is a backend-focused team collaboration and task management platform
designed with production-grade architecture and security principles.

The project emphasizes:
- clean domain modeling
- strict access control
- auditability
- real-time, authorized communication between users

The frontend is intentionally minimal; the primary focus is building
robust backend infrastructure similar to real-world internal tools.

---

##  Architecture
The following diagram illustrates the  architecture of TeamOps
![TeamOps Architecture](docs/architecture.png)
## Architecture Highlights

- **Django + PostgresSQL** backend
- **JWT-based authentication** (REST & WebSockets share the same auth system)
- **Role-aware, object-level access control**
- **Queryset-level data isolation**
- **Soft delete with controlled visibility**
- **Audit logging with field-level diffs**
- **ASGI-based real-time communication using Django Channels and Redis**
- **Strict Git workflow with feature branches and PR-based merges**

## Real-Time Features (WebSockets)

TeamOps supports real-time updates using **Django Channels**, **ASGI**, and **Redis**.

### Authentication & Authorization
- WebSocket connections require **JWT authentication**
- Anonymous connections are rejected at handshake
- `scope["user"]` behaves the same as `request.user` in REST APIs

### Project-Based Isolation
- Each project has its own WebSocket group
- Only project members can connect and receive events
- Cross-project data leakage is strictly prevented

### Real-Time Task Events
Task lifecycle events are broadcast in real time to authorized project members:
- Task creation
- Task updates
- Soft deletion
- Restore events

All real-time events are **server-authoritative** and emitted only from backend
domain events — clients cannot publish arbitrary messages.

## Project Status

This project is actively under development.

Recent milestones:
- Production-grade audit logging
- JWT-authenticated WebSockets
- Project-scoped real-time communication
- Real-time task event broadcasting

Upcoming work includes:
- Event reliability & delivery guarantees
- Fine-grained real-time permissions
- Activity feeds and live dashboards


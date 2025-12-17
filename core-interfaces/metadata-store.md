# Metadata Store Interface

Interface contract for structured metadata and relational data storage.

## Interface ID
`metadata-store`

## Version
`v1`

## Description
Provides structured data storage, querying, and transaction support for application metadata.

---

## Required Capabilities

### Connection
| Operation | Description |
| :--- | :--- |
| `connect` | Establish database connection |
| `disconnect` | Close connection |
| `health` | Check database availability |

### Query Operations
| Operation | Description |
| :--- | :--- |
| `execute` | Execute raw SQL query |
| `query` | Execute SELECT and return results |
| `insert` | Insert record(s) |
| `update` | Update record(s) |
| `delete` | Delete record(s) |

### Transaction Support
| Operation | Description |
| :--- | :--- |
| `begin` | Start transaction |
| `commit` | Commit transaction |
| `rollback` | Rollback transaction |

---

## Connection String Format
```
postgresql://user:password@host:port/database
```

## Health Endpoint
Direct connection test via `SELECT 1`

---

## Implementations
- `postgresql` - PostgreSQL database (default)

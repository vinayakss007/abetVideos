# ADR-001: JSON File Storage for User Data

**Date:** 2026-06-02

## Status
Accepted

## Context
The application needs to persist user accounts, user settings, and video history. Options considered: JSON files, SQLite, PostgreSQL.

## Decision
Use flat JSON files with `fcntl.flock` for thread-safe read/write.

## Rationale
- Zero external dependencies (no database server, no ORM)
- Files are human-readable and debuggable
- The data volume is tiny (single-user/tiny-team, <100 history entries)
- `fcntl.flock` prevents concurrent write corruption even with multiple workers

## Consequences
- Positive: Simple deployment, no database to maintain
- Positive: Easy to inspect/modify data manually
- Negative: Doesn't scale to multi-user or high-write scenarios
- Negative: No query capabilities (must read entire file)
- Mitigation: An ADR to migrate to SQLite/PostgreSQL when needed (see ADR-002)

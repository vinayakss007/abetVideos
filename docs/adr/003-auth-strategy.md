# ADR-003: JWT Authentication with httpOnly Cookies

**Date:** 2026-06-02

## Status
Accepted

## Context
The application needs user authentication. Options: JWT in localStorage, JWT in httpOnly cookies, session-based auth.

## Decision
Use JWT tokens stored in httpOnly cookies (set by the backend). The frontend never reads the raw token.

## Rationale
- httpOnly cookies are not accessible via JavaScript, preventing XSS token theft
- JWT allows stateless verification (no DB lookup on each request)
- Backend auto-generates a strong JWT secret on first startup (stored in `.jwt_secret`)
- Rate limiting at login prevents brute-force attacks
- 7-day token expiry with automatic cookie handling

## Consequences
- Positive: More secure than localStorage (immune to XSS token theft)
- Positive: Simpler frontend code (no manual token management)
- Negative: Requires CSRF protection consideration (samesite=lax mitigates this)
- Negative: Cookie-based auth doesn't work across different origins without `withCredentials`

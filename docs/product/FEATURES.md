# KONGCHAT 2.0 Feature Specification

This document defines the product scope and intended feature behavior.
It is not a claim that every feature has been implemented.

## Status vocabulary

- **Implemented:** exists in code and has verifiable behavior
- **Tested:** covered by automated or documented reproducible tests
- **In progress:** actively being developed
- **Planned:** accepted scope, not implemented
- **Research:** feasibility or design exploration
- **Deferred:** intentionally not prioritized

## KONGCHAT Core

### Identity and Account
- Account registration
- Authentication
- Session management
- Profile
- Account lifecycle
- Password recovery
- Account deletion

### Conversations
- Direct conversations
- Conversation listing
- Message history
- Message delivery state
- Pagination
- Conversation metadata

### Messaging
- Send and receive text messages
- Server-side validation
- Message identifiers
- Timestamps
- Persistence
- Retry and reconnect behavior
- Duplicate handling
- Message ordering considerations

### Realtime
- WebSocket connection
- Authentication of realtime sessions
- Heartbeats
- Reconnection
- Connection lifecycle
- Error handling
- Rate limiting

### Presence
- Online/offline state
- Last-seen policy
- Privacy settings
- Presence expiry

## KONGCHAT Spaces

### Groups
- Group creation
- Membership
- Join and leave
- Member listing
- Group metadata

### Channels
- Channel creation
- Channel membership
- Message history
- Channel visibility

### Roles and Permissions
- Role definitions
- Permission assignment
- Membership authorization
- Moderation actions
- Auditability for privileged actions

### Moderation
- Reporting
- Muting
- Blocking
- Removal
- Rate limiting
- Abuse response

## KONGCHAT CLI

- Secure authentication
- Terminal-based conversation list
- Message send and receive
- Connection status
- Reconnection
- Command help
- Configuration management
- Secure token storage appropriate to the operating system

CLI must use the same documented protocol and authorization rules as supported
other clients.

## KONGCHAT Connect

- Versioned API
- API authentication and authorization
- Bot identities
- Webhooks
- Event definitions
- Integration management
- Developer documentation
- SDK design

## Cross-Cutting Requirements

- Input validation
- Authorization
- Error consistency
- Logging without secrets
- Abuse prevention
- Rate limits
- Pagination
- Accessibility
- Localization readiness
- Secure configuration
- Observability
- Data retention policy
- Backup and restore strategy
- Migration policy

## Deferred / Requires Separate Evaluation

- Voice and video calls
- End-to-end encryption
- Federated messaging
- Large-scale distributed architecture
- Mobile applications
- AI features
- Payment or financial features

These must not be advertised as available unless implemented, tested,
and documented. E2EE in particular requires threat modeling, key lifecycle
design, protocol review, and independent security scrutiny.

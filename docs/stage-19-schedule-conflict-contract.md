# Stage 19A — Temporal Scheduling & Conflict Contract

Status: design contract; no calendar integration or automatic rescheduling is implemented by this document.

## Goal

Make the planner's time-related decisions explicit and deterministic before adding more scheduling behavior. Preserve the current safety-first rule: an infeasible weekly target must never cause a workout to be placed outside a user's configured availability.

## Canonical concepts

- **Availability window**: a period when the user can perform a normal strength/gym session. It is a constraint, not a booked event.
- **Reserved sport session**: a user-configured sport session on a canonical weekday, optionally with a start/end time. It is a planned session, not a free window.
- **Planned training session**: the single workout assigned to a weekday by the current weekly planner.
- **External calendar event**: not currently modeled. Do not imply that the app detects work, school, travel, or third-party calendar conflicts.

All clock times are local wall-clock HH:MM values. V1 windows must have start earlier than end; overnight windows are unsupported. For interval comparisons, use half-open intervals [start, end) so an event ending at 18:00 does not overlap one starting at 18:00.

## Rules that must remain true

1. **Availability is a hard constraint.** A normal gym session is eligible only on a selected day. If that day has a valid availability window, its duration must be at least the configured required session duration.
2. **No invented availability.** If the user's explicit availability leaves fewer eligible days than the weekly target, return a smaller feasible plan rather than adding sessions on unavailable days.
3. **Sport precedence.** On a configured sport day with available sport drills, schedule the sport session instead of a normal gym session. Do not schedule two planned sessions on one weekday in V1.
4. **Separate meanings.** A gym availability window overlapping a reserved sport window is not, by itself, a calendar conflict: the former means "can train here"; the latter means "sport session is scheduled here." The sport reservation takes precedence for that day.
5. **Malformed constraints fail closed.** Invalid or unreadable time-window data must not make an otherwise ineligible gym day eligible. Do not silently normalize impossible intervals.
6. **Determinism.** Identical profile, assessment, availability, and sport schedule inputs must produce identical scheduling decisions, excluding generated timestamps.
7. **Explain infeasibility.** Future implementation should expose why the requested weekly target could not be met (e.g. unavailable weekday, window shorter than required duration, sport session occupying the day), without fabricating missing facts.
8. **User isolation.** Availability, sport reservations, diagnostics, and resulting plans must be derived only from the authenticated user's records.
9. **Staleness.** A change to any scheduling constraint that affects plan generation must invalidate the existing plan's provenance using the existing stale-plan mechanism.
10. **No hidden autonomy.** V1 does not automatically move, delete, or re-time a user-configured sport session. Do not describe this as automatic rescheduling.

## Conflict categories for future implementation

- `unavailable_day`: a proposed normal session is outside selected availability.
- `insufficient_window`: a valid availability window is shorter than the required session duration.
- `sport_reserved`: the weekday is occupied by the configured sport session; the normal gym session must not also be scheduled.
- `overlapping_events`: two actual scheduled event intervals overlap. This category must only be emitted when both intervals represent booked/planned events; an availability interval is not itself an event.
- `invalid_constraint`: persisted or submitted scheduling data cannot be safely interpreted.

Conflict records should be deterministic and machine-readable, and should identify the affected canonical weekday/date plus a stable reason code. Do not include secrets or another user's data. If the system has insufficient information to determine a conflict, report insufficient information rather than asserting no conflict.

## Scope boundaries

Included in Stage 19:
- formalize and test the scheduling contract;
- make current planner decisions and infeasible targets observable;
- maintain deterministic planning, hard availability constraints, and user isolation.

Not included until separately designed:
- external calendar integration;
- timezone database / daylight-saving-aware event storage;
- overnight or cross-midnight sessions;
- arbitrary multi-event calendar scheduling;
- automatic rescheduling, notifications, or edits to third-party calendars.

## Acceptance criteria

- Tests cover exact interval boundary behavior, invalid/overnight intervals, sport precedence, insufficient windows, infeasible weekly targets, determinism, stale-plan invalidation, and cross-user isolation.
- No test or UI wording claims that external calendar conflicts are detected.
- Existing main regression and clean-database Alembic checks pass.
- The legacy regression job remains informational and is reported separately.

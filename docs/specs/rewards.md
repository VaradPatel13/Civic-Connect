# Rewards Specification

> This document defines the rewards and gamification system for CivicConnect.
>
> It serves as the authoritative specification for point earning, redemption, and citizen engagement incentives.

---

# Overview

The rewards system incentivizes civic engagement through a points-based mechanism.

Citizens earn points for submitting, validating, and resolving reports, encouraging active participation in maintaining Pune's civic infrastructure.

---

# Objectives

The rewards system must provide

- Fair and transparent point allocation
- Consistent point accounting
- Multiple redemption pathways
- Community leaderboard engagement
- Anniversary recognition
- Achievement acknowledgment

---

# Reward Principles

The rewards system operates on these principles:

- **Equity**: All citizens receive equal opportunity to earn points
- **Transparency**: Point earning rules are clear and published
- **Immediate**: Points awarded within seconds of qualifying action
- **Accurate**: Point calculations verified by backend validation
- **Reversible**: Points deducted for invalid submissions
- **Auditable**: All point transactions recorded permanently

---

# Reward Events

Points are awarded for citizen actions

| Event | Points | Description |
|-------|--------|-------------|
| Report submission | 10 | First-time submission OR duplicate check passed |
| Report verified | 5 | AI and/or human validation confirms authenticity |
| Report resolved | 20 | Marked as resolved by department |
| Comment added | 2 | Meaningful comment on own report |
| Photo added | 3 | Valid photo supplement to report |
| Monthly active | 100 | Minimum 5 reports submitted in month |

---

# Point Rules

### Earning Rules

Points awarded when:

- Report passes validation
- Report moves to next lifecycle stage
- Citizen adds valuable contribution

### Deduction Rules

Points deducted for:

- Spam detection confirmed
- False report confirmed
- Malicious content confirmed

### Maintenance Rules

- Points never expire
- Points transfer prohibited
- Points can be lost through abuse

---

# Reward Lifecycle

```
Registration

↓

Profile Setup

↓

Report Submitted (+10 points)

↓

Report Verified (+5 points)

↓

Department Assigned

↓

Work Started

↓

Report Resolved (+20 points)
OR
Report Rejected (-5 points)

↓

Points Redeemed or Saved
```

---

# Redemption Process

Redemption requires:

- Minimum 100 points available
- Valid redemption request
- Email/SMS confirmation
- Points deducted on confirmation

---

# Validation Rules

### Point Validation

Before awarding points:

- Citizen account must be active
- Report must pass fraud checks
- Action must occur in valid timeframe
- No prior reward for same event

### Anti-Gaming Checks

System validates:

- Report spacing (minimum 5 minutes between submissions)
- Location verification (no duplicate submissions from same location)
- Content similarity (no duplicate reports)
- Photo authenticity scores

---

# Abuse Prevention

The system prevents abuse through:

### Rate Limiting

- Maximum 10 reports per hour per citizen
- SMS verification required for >5 reports/day
- IP address monitoring

### Behavioral Analysis

- Anomaly detection on submission patterns
- Photo quality scoring
- Language consistency checks

### Penalties

- First offense: Warning
- Second offense: 7-day suspension
- Third offense: Permanent ban

---

# Audit Requirements

Every reward transaction records:

- Transaction ID
- Citizen ID
- Report ID (if applicable)
- Points change amount
- Reason code
- Agent/system that made change
- Timestamp
- Previous balance
- New balance

Audit records are immutable.

---

# API Endpoints

```
GET    /rewards/balance

GET    /rewards/history

POST   /rewards/redeem

GET    /rewards/leaderboard

GET    /achievements

POST   /notifications/remind-rewards
```

---

# Performance Requirements

Operation | Target
----------|--------
Point calculation | < 50 ms
Leaderboard generation | < 1 s for top 100
Balance query | < 20 ms
Redemption processing | < 200 ms

---

# Testing Requirements

The rewards system requires:

- Unit tests for point calculation logic
- Integration tests for redemption flows
- Audit trail verification tests
- Leaderboard accuracy tests
- Anti-gaming effectiveness tests
- API endpoint tests

---

# Future Enhancements

Planned improvements:

- Tiered rewards (Bronze/Silver/Gold status)
- Social rewards (refer-a-friend bonuses)
- Charity donation partnerships
- Seasonal campaigns
- Group challenge rewards
- Real-world merchandise store
- Sponsor reward programs

---

# References

- [Agent Pipeline](../specs/AGENT.md) - Agent decisions affect reward eligibility
- [Reports](../specs/reports.md) - Report lifecycle determines reward events
- [User System](../specs/users.md) - Citizen profiles track reward balances


# Permission Matrix

This document describes the permission patterns used in the agentic RAG demo.

## Users and Departments

| User | Department | Department Access |
|------|-----------|------------------|
| alice | engineering | All 15 engineering documents |
| bob | sales | All 10 sales documents |
| hr_manager | hr | All 10 HR documents |
| finance_manager | finance | All 10 finance documents |

## Permission Patterns

### 1. Department-Based Access (Primary Pattern)

All department members can view documents in their department:

- **Engineering** (15 docs): alice can access all
  - architecture: 5 docs
  - guide: 5 docs
  - memo: 3 docs
  - spec: 2 docs

- **Sales** (10 docs): bob can access all
  - proposal: 4 docs
  - guide: 3 docs
  - playbook: 2 docs
  - report: 1 doc

- **HR** (10 docs): hr_manager can access all
  - policy: 4 docs
  - guide: 3 docs
  - handbook: 2 docs
  - memo: 1 doc

- **Finance** (10 docs): finance_manager can access all
  - report: 4 docs
  - policy: 3 docs
  - analysis: 2 docs
  - memo: 1 doc

### 2. Cross-Department Documents

Some documents are accessible to multiple departments for collaboration:

| Document ID | Primary Department | Also Accessible To | Reason |
|------------|-------------------|-------------------|---------|
| engineering-architecture-001 | engineering | sales | Technical sales teams need architecture knowledge |
| sales-guide-005 | sales | engineering | Engineering needs product positioning info |
| hr-policy-001 | hr | finance | Finance needs HR policies for budget planning |

### 3. Individual User Exceptions

Specific users get special access outside their department:

| User | Additional Access | Reason |
|------|------------------|--------|
| alice (engineering) | sales-proposal-001 | Technical input needed for sales proposal |
| finance_manager | hr-policy-002 | Compensation policy access for budget planning |
| bob (sales) | engineering-guide-006 | Technical documentation for sales enablement |

### 4. Public Documents

All users can access public documents:

- public-handbook-001
- public-handbook-002
- public-handbook-003
- public-policy-004
- public-policy-005

All 4 users (alice, bob, hr_manager, finance_manager) have viewer permission.

## Testing Permissions

Use the verification script to test permissions:

```bash
python3 scripts/verify_permissions.py
```

This will verify:
- Department-based access works correctly
- Cross-department documents are accessible
- Individual exceptions are granted
- Public documents are universally accessible
- Access denials work as expected

## Document Distribution

Total: 50 documents across 5 departments

| Department | Count | Categories |
|-----------|-------|-----------|
| Engineering | 15 | architecture (5), guide (5), memo (3), spec (2) |
| Sales | 10 | proposal (4), guide (3), playbook (2), report (1) |
| HR | 10 | policy (4), guide (3), handbook (2), memo (1) |
| Finance | 10 | report (4), policy (3), analysis (2), memo (1) |
| Public | 5 | handbook (3), policy (2) |

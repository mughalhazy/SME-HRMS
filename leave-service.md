# leave-service implementation

This repository now includes `leave_service.py`, a canonical leave-service domain implementation aligned with the HRMS docs.

## Implemented operations

- create leave request
- patch leave request (including cancellation)
- submit leave request
- approve leave request
- reject leave request
- get leave request by id
- list leave requests with filters and cursor pagination

## Security + policy behavior

- CAP-LEV-001 lifecycle access for create/read/update/submit
- CAP-LEV-002 decision access for approve/reject
- manager team scoping + employee self scoping
- overlap validation against submitted/approved requests
- workflow transitions: `Draft -> Submitted -> Approved/Rejected` and cancellation rules
- event log emission:
  - `LeaveRequestSubmitted`
  - `LeaveRequestApproved`
  - `LeaveRequestRejected`
  - `LeaveRequestCancelled`

## Testing

```bash
pytest -q
```

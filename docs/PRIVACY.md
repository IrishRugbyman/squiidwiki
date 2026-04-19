# SquiidWiki — Data Handling Policy

## What This Database Contains

SquiidWiki is an internal research tool that catalogs information about gang activity, including:

- **Nicknames and legal names** of individuals believed to be gang-affiliated
- **Biographical details**: approximate dates of birth/death, incarceration status, known associates
- **Incident records**: shootings, murders, and other violent events with participant roles and outcomes
- **Social network data**: set affiliations, alliances, and enemy relationships
- **Source citations**: news articles, court documents, and other references

All data is scoped to a **Universe** (metro area). Each universe is independently access-controlled.

## Who Can Access This Data

Access requires authentication. Three roles exist:

| Role | Can Read | Can Write | Can Delete | Can Manage Users |
|------|----------|-----------|------------|-----------------|
| Viewer | ✅ | ❌ | ❌ | ❌ |
| Editor | ✅ | ✅ | ❌ | ❌ |
| Admin | ✅ | ✅ | ✅ | ✅ |

Per-universe access can be granted independently — a user may be an Editor in one universe and a Viewer in another.

## Data Accuracy and Sourcing

- Every claim should be tied to a **Source** record with a reliability rating (HIGH / MEDIUM / LOW / UNVERIFIED).
- Unverified data must be treated as unconfirmed until corroborated.
- The `verified` flag on Incident records indicates editor review, not legal adjudication.

## Retention and Deletion

- Records can be deleted by Admins. Deletions are recorded in the audit log.
- The audit log itself is retained indefinitely and should not be purged without explicit data governance review.
- Backups retain deleted records for the backup retention window (see `docs/CONTRIBUTING.md`).

## Takedown Requests

If a subject of this database requests removal of their information:

1. An Admin must review the request for legitimacy.
2. If granted: delete the Member record and associated incidents/sources where the member is the primary subject.
3. Record the takedown in the audit log with a note referencing the request.
4. Purge backups within the retention window if legally required.

## Legal Considerations

- This tool is intended for **lawful research and journalism** purposes only.
- Data must not be used to facilitate harassment, stalking, or extortion.
- Do not store information obtained through illegal interception or in violation of applicable wiretapping laws.
- Consult legal counsel before sharing data with law enforcement or third parties.

## Access Logging

All write operations (create, update, delete) are logged to the `audit_log` table with:
- The acting user's ID and timestamp
- The entity type and ID affected
- A JSON diff of what changed

Read access is not individually logged (query volume makes this impractical), but authentication events are.

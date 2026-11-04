# SquiidWiki — API Reference

Full interactive docs are available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

All endpoints are under `/api/v1/` and require a `Bearer` token unless noted.

---

## Auth

### `POST /api/v1/auth/register`
Create a new user account (returns 409 if email already exists).
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "researcher@example.com", "password": "secret123"}'
```

### `POST /api/v1/auth/login`
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "researcher@example.com", "password": "secret123"}'
# → {"access_token": "eyJ...", "token_type": "bearer"}
```

### `GET /api/v1/auth/me`
Returns the current user's profile.

### `POST /api/v1/auth/refresh`
Rotates the refresh token (sent as an httpOnly cookie) and returns a new access token.

### `POST /api/v1/auth/logout`
Clears the refresh token cookie.

---

## Common Patterns

All list endpoints accept `universe_id` (required), `offset` (default 0), and `limit` (default 50).
Member and incident lists use cursor pagination: pass `cursor` from the previous response's `next_cursor`.

**Authentication header:**
```
Authorization: Bearer <access_token>
```

---

## Universes

```
GET    /api/v1/universes/              List universes
POST   /api/v1/universes/              Create universe (Admin only)
GET    /api/v1/universes/{id}          Get universe
PATCH  /api/v1/universes/{id}          Update universe (Admin only)
DELETE /api/v1/universes/{id}          Delete universe (Admin only)
```

**Create:**
```bash
curl -X POST http://localhost:8000/api/v1/universes/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Metro Detroit", "slug": "metro-detroit"}'
```

---

## Municipalities

```
GET    /api/v1/municipalities/?universe_id=  List
POST   /api/v1/municipalities/               Create
GET    /api/v1/municipalities/{id}?universe_id=  Get
PATCH  /api/v1/municipalities/{id}?universe_id=  Update
DELETE /api/v1/municipalities/{id}?universe_id=  Delete (Admin)
GET    /api/v1/municipalities/search?universe_id=&q=  Search by name or alias
GET    /api/v1/municipalities/geojson?universe_id=&parent_id=&kind=  FeatureCollection; `kind` (DISTRICT | NEIGHBORHOOD) narrows a parent's children to one layer
```

---

## Sets

```
GET    /api/v1/sets/?universe_id=            List
POST   /api/v1/sets/                         Create
GET    /api/v1/sets/{id}?universe_id=        Get (includes friend_ids, enemy_ids)
PATCH  /api/v1/sets/{id}?universe_id=        Update
DELETE /api/v1/sets/{id}?universe_id=        Delete (Admin)
GET    /api/v1/sets/search?universe_id=&q=   Trigram search
GET    /api/v1/sets/{id}/stats?universe_id=  Aggregated stats
POST   /api/v1/sets/{id}/relationships?universe_id=  Add friend/enemy
DELETE /api/v1/sets/{id}/relationships/{target_id}?universe_id=  Remove relationship
```

**Add relationship:**
```bash
curl -X POST "http://localhost:8000/api/v1/sets/$SET_ID/relationships?universe_id=$UNIVERSE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target_id": "OTHER-SET-UUID", "type": "ENEMY"}'
```

---

## Alliances

```
GET    /api/v1/alliances/?universe_id=          List
POST   /api/v1/alliances/                       Create
GET    /api/v1/alliances/{id}?universe_id=      Get (includes set_ids)
PATCH  /api/v1/alliances/{id}?universe_id=      Update
DELETE /api/v1/alliances/{id}?universe_id=      Delete (Admin)
GET    /api/v1/alliances/search?universe_id=&q= Trigram search
```

---

## Members

```
GET    /api/v1/members/?universe_id=             Cursor-paginated list
POST   /api/v1/members/                          Create
GET    /api/v1/members/{id}?universe_id=         Get (includes citations)
PATCH  /api/v1/members/{id}?universe_id=         Update
DELETE /api/v1/members/{id}?universe_id=         Delete (Admin)
GET    /api/v1/members/search?universe_id=&q=    Substring, then trigram near-misses, on nickname/legal_name/aliases
GET    /api/v1/members/similar?universe_id=&name=[&exclude_id=&threshold=0.5&limit=10]  Possible duplicates with scores (0..1)
GET    /api/v1/members/{id}/stats?universe_id=   Kill/shooting stats
```

**Create with FuzzyDate:**
```bash
curl -X POST http://localhost:8000/api/v1/members/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "universe_id": "UNIVERSE-UUID",
    "nickname": "Ghost",
    "status": "FREE",
    "dob": {"year": 1998, "precision": "Y", "approx": true}
  }'
```

---

## Incidents

```
GET    /api/v1/incidents/?universe_id=           Cursor-paginated list
POST   /api/v1/incidents/                        Create (with participants)
GET    /api/v1/incidents/{id}?universe_id=       Get (includes participants, citations)
PATCH  /api/v1/incidents/{id}?universe_id=       Update
DELETE /api/v1/incidents/{id}?universe_id=       Delete (Admin)
GET    /api/v1/incidents/search?universe_id=&q=  Search
```

**Create with participants:**
```bash
curl -X POST http://localhost:8000/api/v1/incidents/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "universe_id": "UNIVERSE-UUID",
    "type": "SHOOTING",
    "date": {"year": 2023, "month": 7, "precision": "YM", "approx": false},
    "location_text": "7 Mile & Gratiot, Detroit",
    "participants": [
      {"member_id": "SHOOTER-UUID", "role": "SHOOTER", "outcome": "UNHARMED"},
      {"member_id": "VICTIM-UUID",  "role": "VICTIM",  "outcome": "INJURED"}
    ]
  }'
```

---

## Sources

A source is a document, page or record; a citation is one record citing it,
with where in it (`locator`), the words (`quote`) and what it supports (`note`).
Every record's detail response carries `citations: CitationRead[]` (member,
incident, set, alliance, court case, municipality, business). There is no
`source_ids` field on any record.

```
GET    /api/v1/sources/?universe_id=&q=&kind=&reliability=&publication=&uncited=&sort=&order=&offset=&limit=
                                              {items, total, facets{kind, reliability}}; &format=csv for all rows
POST   /api/v1/sources/                       Create; 409 duplicate_url / lookup_source (body: existing_id)
GET    /api/v1/sources/search?universe_id=&q= Ranked over title, publication, URL, then trigram near-misses on the title; a pasted URL pins its match
GET    /api/v1/sources/lookup?universe_id=&url=
                                              {exact, lookup{source, suggested_locator}, same_host}
GET    /api/v1/sources/{id}?universe_id=      With counts per record type
GET    /api/v1/sources/{id}/citations?universe_id=&entity_type=&offset=&limit=
                                              Paged records citing it, each an EntityRef
GET    /api/v1/sources/{id}/custody-ids?universe_id=
PATCH  /api/v1/sources/{id}?universe_id=      Update
PATCH  /api/v1/sources/bulk?universe_id=      {ids, reliability?, kind?}
POST   /api/v1/sources/{id}/merge?universe_id= {into_id} (Admin)
DELETE /api/v1/sources/{id}?universe_id=&force=
                                              Admin; 409 source_in_use with counts unless force
GET    /api/v1/search/text?universe_id=&q=[&types=member|set|alliance|incident|source&limit=20]  Full-text over bios, narratives, source notes
```

## Citations

```
GET    /api/v1/citations/?universe_id=&entity_type=&entity_id=
POST   /api/v1/citations/?universe_id=        {source_id, entity_type, entity_id, locator?, quote?, note?, accessed_at?}
                                              409 citation_exists (body: citation_id)
POST   /api/v1/citations/batch?universe_id=   {items[], on_conflict: skip|update}; all or nothing
PATCH  /api/v1/citations/{id}?universe_id=    locator, quote, note, accessed_at, source_id
PUT    /api/v1/citations/order?universe_id=   {entity_type, entity_id, ids[]}: every citation once
DELETE /api/v1/citations/{id}?universe_id=
```

Municipality citations are read and written in prod whatever the DB mode.

Errors raised as `ApiError` carry a stable `code` beside `detail`, plus extras.

## Error Responses

All errors follow this envelope:
```json
{"detail": "Human-readable error message"}
```

| Status | Meaning |
|--------|---------|
| 400 | Validation error |
| 401 | Missing or invalid auth token |
| 403 | Insufficient role |
| 404 | Entity not found (or wrong universe) |
| 409 | Conflict (duplicate slug, relationship already exists) |
| 422 | Pydantic schema validation failure |

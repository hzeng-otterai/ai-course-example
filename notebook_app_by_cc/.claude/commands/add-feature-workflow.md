> **CRITICAL: Follow this workflow for every feature implementation or refinement. Do not skip or reorder steps.**

You are implementing or refining a feature for the GreatNotes app (Django REST Framework backend + React 19 frontend). Work through the steps below in order, pausing for explicit approval before editing any code.

---

## Step 1 — Confirm context

Before anything else, verify:
- Current git branch (`git branch --show-current`)
- Working directory (confirm you are in `notebook_app_by_cc/`)
- Any uncommitted changes (`git status`)

Report these findings to the user. If there are uncommitted changes, ask whether to proceed or stash first.

---

## Step 2 — Understand the requirement

Restate the feature request in your own words in 2–3 sentences. Call out any ambiguities or edge cases you see. Ask the user to confirm or correct your understanding before continuing.

---

## Step 3 — Identify affected areas

Map out every file likely to change, grouped by layer:

| Layer | Files |
|---|---|
| DB schema | `backend/notebooks/models.py`, new migration |
| Backend | serializers, views, permissions, urls |
| Frontend | components, API modules, context, routes |
| Tests | `backend/notebooks/tests.py`, frontend test files |

Flag any cross-cutting concerns (auth, permissions, React Query cache keys, TipTap content shape).

---

## Step 4 — Produce a plan and get approval

Write a numbered implementation plan. For each step include:
- What file changes and why
- Any new model fields or migrations needed
- API contract changes (new endpoints, modified request/response shape)
- Frontend data-flow changes (new query keys, mutation invalidations)

**Do not edit any files until the user explicitly approves this plan.**

---

## Step 5 — Implement in layer order

Work strictly in this sequence to avoid import errors and broken intermediate states:

1. **DB schema first** — update `models.py`, then run `python manage.py makemigrations` and `python manage.py migrate`
2. **Backend** — serializers → permissions → views → urls (in that dependency order)
3. **Frontend** — API modules (`api/`) → context/hooks → components → routes

After each layer, briefly confirm to the user what was changed before moving to the next.

Ownership and auto-save rules to respect:
- `Notebook.user` is set once at create time (`perform_create`) and never reassigned
- All views that touch notebooks or pages must use the two-layer pattern: `get_queryset` filtered by `user=request.user` **and** `IsNotebookOwner` / `IsPageOwner` in `permission_classes`
- Auto-save in `PageEditor.jsx` uses a 1 s `useRef` debounce; page-switch resets content with `setContent(newContent, false)` to suppress spurious saves

---

## Step 6 — Update tests and verify behavior

- Add or update tests in `backend/notebooks/tests.py` covering the new or changed endpoints
- Run the backend test suite: `cd backend && python manage.py test`
- If frontend components changed, note any test files that need updating
- Start both servers and manually verify the golden path for the new feature

Report pass/fail results. Do not mark the task complete until tests pass.

---

## Step 7 — Summarise changes

Produce a concise summary:

```
Branch: <branch-name>
Files changed: <count>

Backend
  - <file>: <what changed>

Frontend
  - <file>: <what changed>

Migrations
  - <migration file name>

Tests
  - <what was added/updated>

Open questions / follow-up items
  - <any deferred edge cases>
```

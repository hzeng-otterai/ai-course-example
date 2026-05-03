# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (Django)
```bash
cd backend
python manage.py runserver        # dev server on http://localhost:8000
python manage.py migrate          # apply migrations (first-time setup)
python manage.py makemigrations   # after changing models
python manage.py test             # run tests
python manage.py createsuperuser  # create admin user
python manage.py shell            # Django REPL
```

### Frontend (React + Vite)
```bash
cd frontend
npm run dev      # dev server on http://localhost:5173
npm run build    # production build
npm run preview  # preview production build
npm run lint     # ESLint
```

## Architecture

Full-stack notebook app: Django REST Framework backend + React 19 SPA frontend.

### Backend (`backend/`)

Single Django app `notebooks` handles all logic. Key files:

- `config/settings.py` — JWT config (60-min access, 7-day refresh with rotation), CORS allowed for `localhost:5173`, SQLite by default
- `config/urls.py` — mounts `notebooks/urls.py` at root
- `notebooks/models.py` — three models: `Notebook` (FK→User), `Page` (FK→Notebook, content stored as JSONField for TipTap state), `ShareLink` (UUID token, FK→Page)
- `notebooks/views.py` — function-based auth views (register, me) + DRF generic class-based views for resources
- `notebooks/serializers.py` — separate list vs. detail serializers (list excludes page content); `share_token` is a computed `SerializerMethodField`
- `notebooks/permissions.py` — `IsNotebookOwner` and `IsPageOwner` enforce object-level ownership

**Ownership conventions:**

Ownership is anchored at `Notebook.user` (FK → `auth.User`), set once in `perform_create` and never reassigned. The full ownership chain is `ShareLink → Page → Notebook → User`.

Views enforce ownership at two layers:
1. `get_queryset` filters to `user=request.user` so cross-user lookups return 404, not 403
2. Detail views also apply `IsNotebookOwner` / `IsPageOwner` as a second check on the resolved object

`PageListCreateView` and `page_share` skip the permission class and instead call `get_object_or_404(Notebook, pk=..., user=request.user)` inline — same effect, just shorter.

The shared-page endpoint (`/api/shared/<token>/`) is `AllowAny` by design; it serves a read-only snapshot via `SharedPageSerializer` and never exposes the owner's identity.

When adding new views that touch notebooks or pages, follow the same two-layer pattern: filter in `get_queryset` **and** add the relevant permission class to `permission_classes`.

**URL structure:**
```
/api/auth/register/
/api/auth/login/
/api/auth/token/refresh/
/api/auth/me/
/api/notebooks/                        # list/create
/api/notebooks/<id>/                   # retrieve/update/delete
/api/notebooks/<notebook_pk>/pages/    # list/create pages
/api/pages/<id>/                       # retrieve/update/delete page
/api/pages/<id>/share/                 # POST create / DELETE revoke share link
/api/shared/<token>/                   # public read-only (AllowAny)
```

### Frontend (`frontend/src/`)

- `main.jsx` — wraps app in `AuthProvider`, `QueryClientProvider`, `BrowserRouter`
- `App.jsx` — route definitions; `ProtectedRoute` redirects to `/login` if unauthenticated
- `contexts/AuthContext.jsx` — global auth state; stores JWT access/refresh tokens in `localStorage`
- `api/client.js` — Axios instance with interceptors: adds `Authorization: Bearer` header on every request; on 401, queues requests and attempts token refresh; on refresh failure, clears storage and redirects to `/login`
- `api/auth.js`, `api/notebooks.js`, `api/pages.js` — thin API method modules
- `components/PageEditor.jsx` — TipTap rich text editor with debounced auto-save (see conventions below)
- `components/AutoSaveIndicator.jsx` — displays save state driven by `saveStatus` prop
- `components/ShareModal.jsx` — creates/revokes `ShareLink`; parent invalidates queries on close

**Data flow:** Vite proxies `/api/*` → `http://localhost:8000` in dev. React Query manages server state with keys like `['notebook', id]` and `['page', id]`; mutations invalidate relevant queries on success.

**Auto-save conventions (`PageEditor.jsx`):**

Auto-save is a plain `useRef` debounce — no React Query mutation, no `useMutation`. The flow:

1. TipTap's `onUpdate` fires on every editor change, clears the pending timer, and starts a new 1000 ms timer.
2. After 1 s of inactivity the timer calls `save(editor.getJSON())`, which PATCHes `/api/pages/<id>/` with `{ content }`.
3. `saveStatus` state drives `AutoSaveIndicator`: `null` (idle) → `'saving'` → `'saved'` (auto-clears after 2 s) or `'error'`.

Page-switch behaviour: a `useEffect` keyed on `page.id` resets editor content via `editor.commands.setContent(newContent, false)`. The `false` flag suppresses the `onUpdate` event, preventing a spurious save on page load.

Cleanup: a second `useEffect` returns `() => clearTimeout(saveTimer.current)` to cancel any pending save on unmount.

When modifying auto-save logic, preserve the debounce-on-every-keystroke + suppress-on-load pattern. The 1 s delay is intentional — frequent POSTing on each keystroke is unnecessary given TipTap's in-memory state.

### Auth Flow

1. Login/register → backend returns `{access, refresh, user}`; stored in `localStorage`
2. All requests include `Authorization: Bearer {access}` via Axios request interceptor
3. On 401: interceptor POSTs to `/api/auth/token/refresh/`; backend rotates both tokens (`ROTATE_REFRESH_TOKENS=True`); queued requests retry with new token
4. On refresh failure: logout, redirect to `/login`

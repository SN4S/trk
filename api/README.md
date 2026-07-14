# XproSupport API

A FastAPI-powered REST backend for the XproSupport ticket management system. It handles authentication, support tickets, agents (users), groups, folders, reply threads, and topic themes.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115+ |
| Language | Python 3.11+ |
| ORM | SQLAlchemy 2.0 (async) |
| Database | MySQL (via `aiomysql`) |
| Migrations | Alembic 1.13+ |
| Auth | JWT (PyJWT) + bcrypt + HttpOnly refresh cookies |
| Validation | Pydantic 2.7+ |
| Settings | pydantic-settings 2.4+ |

---

## Project Structure

```
api/
├── alembic/                    # Alembic migration environment
│   └── versions/
│       └── 2026-07-08_initial_migration.py
├── seeder/
│   └── addadmin.py             # One-off script to seed an admin user
├── src/
│   ├── auth/                   # Authentication & user management
│   │   ├── config.py           # AuthConfig (JWT_SECRET, REFRESH_TOKEN_KEY, …)
│   │   ├── constants.py        # ErrorCode StrEnum
│   │   ├── dependencies.py     # parse_jwt_data, get_current_user, CurrentUser
│   │   ├── exceptions.py       # InvalidCredentials, InvalidToken, …
│   │   ├── models.py           # User, RefreshToken ORM models
│   │   ├── router.py           # /auth endpoints
│   │   ├── schemas.py          # LoginRequest, RegisterRequest, UserOut, …
│   │   ├── service.py          # register_user, authenticate_user, token rotation
│   │   └── utils.py            # bcrypt, JWT encode/decode, token helpers
│   ├── folders/                # Folder management (per-user)
│   │   ├── exceptions.py
│   │   ├── models.py           # Folder, FolderGroup ORM models
│   │   ├── router.py           # /folders endpoints + group link/unlink
│   │   ├── schema.py           # FolderCreate, FolderOut, FolderGroupAdd, …
│   │   └── service.py
│   ├── groups/                 # Telegram groups (admin-managed)
│   │   ├── exceptions.py
│   │   ├── models.py           # Group ORM model
│   │   ├── router.py           # /groups endpoints
│   │   ├── schemas.py          # GroupCreate, GroupOut, GroupUpdate
│   │   └── service.py
│   ├── tickets/                # Support tickets
│   │   ├── exceptions.py
│   │   ├── models.py           # Ticket ORM model, TicketStatus enum
│   │   ├── router.py           # /tickets endpoints
│   │   ├── schemas.py          # TicketCreate, TicketOut, TicketUpdate
│   │   └── service.py
│   ├── replies/                # Ticket replies (chat messages)
│   │   ├── exceptions.py
│   │   ├── models.py           # Reply ORM model
│   │   ├── router.py           # /tickets/{ticket_id}/replies endpoints
│   │   ├── schemas.py          # ReplyCreate, ReplyOut
│   │   └── service.py
│   ├── themes/                 # Ticket topic themes / categories
│   │   ├── exceptions.py
│   │   ├── models.py           # Theme ORM model
│   │   ├── router.py           # /themes endpoints
│   │   ├── schemas.py          # ThemeCreate, ThemeOut, ThemeUpdate
│   │   └── service.py
│   ├── config.py               # Global Settings (DATABASE_URL)
│   ├── database.py             # Async engine, SessionFactory, Base
│   ├── models.py               # (shared model base — extendable)
│   └── main.py                 # FastAPI app, CORS middleware, router wiring
├── alembic.ini
└── requirments.txt
```

---

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirments.txt
```

### 2. Configure environment variables

Create a `.env` file at the project root (`api/.env`):

```env
# Database (MySQL via asyncmy/aiomysql)
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/xprosupport

# JWT settings (AUTH_ prefix)
AUTH_JWT_SECRET=your-super-secret-key-here
AUTH_JWT_ALG=HS256
AUTH_JWT_EXP_MINUTES=15

# Refresh token settings
AUTH_REFRESH_TOKEN_KEY=your-refresh-token-signing-key
AUTH_REFRESH_TOKEN_EXP=30d    # timedelta string, default 30 days
AUTH_SECURE_COOKIES=true      # set false for local HTTP dev

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:3000
```

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. Seed an admin user (optional)

```bash
python -m seeder.addadmin
```

This creates a user with username `admin` and password `changeme`. **Change the password immediately.**

### 5. Start the development server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs are available at: http://localhost:8000/docs

---

## API Reference

All endpoints except `/auth/login` and `/auth/refresh` require a valid `Authorization: Bearer <access_token>` header.

### Authentication — `/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | ✅ Required (admin only) | Create a new agent account |
| `POST` | `/auth/login` | ❌ Public | Login → returns access token + sets refresh cookie |
| `POST` | `/auth/refresh` | ❌ (cookie) | Rotate refresh token → new access token |
| `POST` | `/auth/logout` | ❌ (cookie) | Revoke refresh token, clear cookie |
| `GET`  | `/auth/me` | ✅ Required | Return the currently authenticated user |

**Login request body:**
```json
{ "username": "admin", "password": "changeme" }
```

**Login response:**
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

The refresh token is stored in an `HttpOnly` cookie (`refresh_token`) scoped to `/auth`.

---

### Groups — `/groups`

Telegram groups that receive tickets.

| Method | Path | Description |
|--------|------|-------------|
| `GET`    | `/groups/`           | List groups (searchable) |
| `POST`   | `/groups/`           | Create a group |
| `GET`    | `/groups/{id}`       | Get a group by ID |
| `PATCH`  | `/groups/{id}`       | Update a group |
| `DELETE` | `/groups/{id}`       | Delete a group |

**Query parameters for `GET /groups/`:**

| Param | Type | Description |
|-------|------|-------------|
| `search` | `string` | Case-insensitive substring match on group name |

**Create/update body:**
```json
{ "name": "Support Group Alpha", "tg_group_id": -1001234567890 }
```

---

### Themes — `/themes`

Topic categories for tickets (e.g., "Billing", "Technical").

| Method | Path | Description |
|--------|------|-------------|
| `GET`    | `/themes/`       | List all themes |
| `POST`   | `/themes/`       | Create a theme |
| `GET`    | `/themes/{id}`   | Get a theme by ID |
| `PATCH`  | `/themes/{id}`   | Update a theme |
| `DELETE` | `/themes/{id}`   | Delete a theme |

---

### Folders — `/folders`

Personal folders that group Telegram groups together, scoped per authenticated user.

| Method | Path | Description |
|--------|------|-------------|
| `GET`    | `/folders/`                        | List my folders (with nested groups) |
| `POST`   | `/folders/`                        | Create a folder |
| `GET`    | `/folders/{id}`                    | Get a folder by ID |
| `PATCH`  | `/folders/{id}`                    | Rename a folder |
| `DELETE` | `/folders/{id}`                    | Delete a folder |
| `POST`   | `/folders/{id}/groups`             | Add a group to a folder |
| `DELETE` | `/folders/{id}/groups/{group_id}`  | Remove a group from a folder |

**Create body:**
```json
{ "name": "My Folder" }
```

**Add group body:**
```json
{ "group_id": 3 }
```

---

### Tickets — `/tickets`

Support tickets created (typically by a Telegram bot) and managed by agents.

| Method | Path | Description |
|--------|------|-------------|
| `GET`    | `/tickets/`       | List tickets (filterable + searchable) |
| `POST`   | `/tickets/`       | Create a ticket |
| `GET`    | `/tickets/{id}`   | Get a ticket by ID |
| `PATCH`  | `/tickets/{id}`   | Update ticket (status, theme, group) |
| `DELETE` | `/tickets/{id}`   | Delete a ticket |

**Query parameters for `GET /tickets/`:**

| Param | Type | Description |
|-------|------|-------------|
| `group_id` | `int` | Filter by Telegram group ID |
| `status` | `open` \| `pending` \| `closed` | Filter by status |
| `theme_id` | `int` | Filter by theme ID |
| `search` | `string` | Search across `ticket_num`, `message`, and theme `name` (SQL `ILIKE`) |

> All params are optional and combinable. Example:  
> `GET /tickets/?group_id=3&status=open&search=billing`

**Create body:**
```json
{
  "ticket_num": "TKT-001",
  "theme_id": 1,
  "group_id": 2,
  "soc_user_id": 987654321,
  "message": "User's initial message text"
}
```

**Update body (all fields optional):**
```json
{ "status": "closed", "theme_id": 2 }
```

**Ticket statuses:** `open` → `pending` → `closed`

---

### Replies — `/tickets/{ticket_id}/replies`

Chat-style reply thread for a specific ticket.

| Method | Path | Description |
|--------|------|-------------|
| `GET`    | `/tickets/{ticket_id}/replies/`             | List replies (searchable) |
| `POST`   | `/tickets/{ticket_id}/replies/`             | Post a reply |
| `DELETE` | `/tickets/{ticket_id}/replies/{reply_id}`   | Delete a reply |

**Query parameters for `GET /tickets/{id}/replies/`:**

| Param | Type | Description |
|-------|------|-------------|
| `search` | `string` | Case-insensitive search in reply message body |

**Create body:**
```json
{
  "message": "We are looking into this issue.",
  "is_support": true
}
```

`is_support: true` → message sent by a support agent.  
`is_support: false` → message from the customer (e.g. relayed by the bot).

---

## Data Model

```
User ──< Folder >──< FolderGroup >── Group ──< Ticket >── Theme
                                                │
                                                └──< Reply >── User
```

- A **User** (agent) owns many **Folders**.
- A **Folder** contains many **Groups** via the `FolderGroup` join table.
- A **Group** (Telegram group) holds many **Tickets**.
- Each **Ticket** belongs to a **Theme** and a **Group**, and has many **Replies**.
- A **Reply** is optionally linked to the **User** (agent) who wrote it.

---

## Error Responses

All errors follow FastAPI's standard `HTTPException` format:

```json
{ "detail": "<error_code_string>" }
```

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `invalid_credentials` | 401 | Wrong username or password |
| `invalid_token` | 401 | JWT is malformed or missing |
| `token_expired` | 401 | Access token has expired |
| `inactive_user` | 403 | Account is disabled |
| `username_taken` | 409 | Username already in use |
| `folder_not_found` | 404 | No such folder (or not yours) |
| `group_not_found` | 404 | No such group |
| `ticket_not_found` | 404 | No such ticket |
| `reply_not_found` | 404 | No such reply |
| `theme_not_found` | 404 | No such theme |
| `group_already_in_folder` | 409 | Group is already linked to this folder |
| `group_not_in_folder` | 404 | Group is not linked to this folder |

---

## Development Notes

- **CORS**: Origins are controlled by the `CORS_ORIGINS` env variable (comma-separated list). Default: `http://localhost:3000`.
- **Migrations**: Use `alembic revision --autogenerate -m "<description>"` to generate new migrations. File names follow the `YYYY-MM-DD_<slug>.py` convention.
- **Auth flow**: Access tokens expire in 15 minutes (configurable). The refresh token (30-day cookie) rotates on every use. Reusing a revoked token triggers full session revocation (theft detection).
- **Register is admin-only**: The `/auth/register` endpoint requires an authenticated user. Use the seeder to create the first admin, then register more users through the API.

# xGentic

Enterprise multi-agent platform for deploying and managing AI agents across organizational hierarchies with multi-provider support, environment-based deployments, and enterprise integrations.

## Project Structure

```
xGentic/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── api/               # API routes (agents, auth, hierarchy, environments, campaigns, etc.)
│   │   ├── core/              # Config, security, auth, permissions, rate limiting
│   │   ├── db/                # Database session, Redis client
│   │   ├── middleware/        # Request tracing, security headers
│   │   ├── models/            # SQLAlchemy models (user, agent, organization, hierarchy, environment)
│   │   └── services/          # Business logic & integrations
│   │       ├── tools/         # Agent tools (ServiceNow, Jira, Salesforce, etc.)
│   │       ├── providers/     # AI providers (Azure AI Foundry, AWS Bedrock, Google Vertex)
│   │       └── telephony/     # Telephony providers (Telnyx, Twilio, Vonage)
│   ├── migrations/versions/   # Alembic database migrations
│   └── tests/                 # Backend tests
├── frontend/                   # Next.js 15 React frontend
│   ├── src/
│   │   ├── app/dashboard/     # Dashboard pages (agents, hierarchy, environments, campaigns, etc.)
│   │   ├── app/embed/         # Embeddable agent widget (voice + chat)
│   │   ├── components/ui/     # shadcn/ui components
│   │   ├── hooks/             # Custom React hooks
│   │   └── lib/               # Utilities, stores, API clients
│   └── public/                # Static assets
└── docker-compose.yml         # PostgreSQL 17 + Redis 7
```

## Architecture

- **Org Hierarchy**: Organization > Unit > Department > Project > Workspace (5-level)
- **Agent Types**: Voice, Chat, Email, Document/Workflow
- **Environments**: Development, QA, Staging, Production, Sandbox
- **SSO**: Azure AD, Okta, SAML
- **No billing/Stripe** - internal enterprise platform

## Organization Rules

**Backend:**
- API routes → `app/api/`, one file per resource
- Business logic → `app/services/`, organized by domain
- Models → `app/models/`, one model per file
- Tools → `app/services/tools/`, one class per integration
- Providers → `app/services/providers/`, one module per AI provider
- Telephony → `app/services/telephony/`, one module per telephony provider

**Frontend:**
- Pages → `src/app/dashboard/`, using Next.js App Router
- Components → `src/components/`, reusable UI elements
- Lib → `src/lib/`, utilities, types, stores, API clients
- One component per file, co-locate related files

## Code Quality - Zero Tolerance

### Backend:
```bash
cd backend
uv run ruff check app tests --fix        # Lint + auto-fix
uv run ruff format app tests             # Format
uv run mypy app                          # Type check (strict)
```

### Frontend:
```bash
cd frontend
npm run check                            # eslint + tsc + prettier
npm run lint:fix && npm run format       # Auto-fix
```

### Server Checks:
```bash
cd backend && uv run uvicorn app.main:app --reload   # Check runtime warnings
cd frontend && npm run dev                            # Check compilation warnings
```

**Fix ALL errors/warnings before continuing!**

## Key Commands

- `/check` - Run all quality checks, auto-fix issues
- `/commit` - Run checks, commit with AI message, push

## Tech Stack

**AI Providers**: Azure AI Foundry (primary), AWS Bedrock (stub), Google Vertex (stub)
**Backend**: FastAPI, PostgreSQL 17 (pgvector), Redis 7, SQLAlchemy 2.0, Python 3.12+, uv
**Frontend**: Next.js 15, React 19, TypeScript 5.7, Tailwind, shadcn/ui
**Telephony**: Telnyx, Twilio, Vonage
**Enterprise Integrations**: ServiceNow, Jira, Salesforce, Confluence, Microsoft Teams, Outlook, SharePoint, PagerDuty, Dynamics 365, Power Automate, SAP

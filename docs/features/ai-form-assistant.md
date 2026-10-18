# AI form assistant (Groq)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Live in code (2026-10-18); production answers from help text until `GROQ_API_KEY` is set on Fly |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-18 |
| **Where**    | `core/assistant.py` (endpoint `/admin/assistant/`), `templates/admin/change_form.html`, `core/static/core/assistant.js`; Groq API (`openai/gpt-oss-20b`) |
| **Cost**     | $0 (Groq free plan) |
| **Depends on** | [admin-ui.md](admin-ui.md), [authentication-and-roles.md](authentication-and-roles.md) |

## What
An "Ask about this form" panel on every admin add and change page. It answers "what does this field mean / how do I fill this in" for the field you last clicked into.

It's grounded in the real form, built for the current user (`get_form`, `get_readonly_fields`, `get_fieldsets`, inlines included). The prompt gets:
- each field's label, help text and required/read-only flag;
- static model choices;
- for tickets, the workflow moves, the reply-before-resolve rule, the Lead-only close/reopen rule and the SLA table.

**What never reaches the prompt:**
- Ticket and customer data, and foreign-key options (those would be real records).
- Fields a role can't see. An Agent never gets a prompt for the Agent form, so WIP caps stay out.

## Why
- **Groq:** free tier, OpenAI-compatible API, no data retention by default. It's called with the stdlib (`urllib`), so no SDK dependency.
- **The admin never breaks.** On missing config, a timeout (8 s), a 429 or any other error, the panel answers with the field's own help text and choices, and the HTTP status stays 200.

**Rejected:**
- **Gemini free tier:** its terms allow **only Paid Services** for apps serving users in the EEA, UK or Switzerland (the reviewers are in Estonia), and free-tier prompts may be read by human reviewers (verified 2026-10-15, ai.google.dev/gemini-api/terms).
- **A chain of providers, or an LLM SDK:** chatbot-framework over-engineering. The provider is an env-var swap.
- **Streaming:** under WSGI it ties up a gunicorn worker per open stream.
- **A global daily cap:** the per-user hourly cap plus Groq's own free-plan limits are enough for two reviewers.

## How it's set up
1. https://console.groq.com: sign up, then **API Keys** → create a key.
2. Run `fly secrets set GROQ_API_KEY=… -a aleksei-ticket-tracker`. `LLM_BASE_URL` and `LLM_MODEL` are already in `fly.toml [env]`.
3. Locally: put the key in `.env` (`GROQ_API_KEY=`; leave it blank to test the fallback).

Tests: `tests/test_assistant.py` covers:
- the prompt contents (metadata and rules in, ticket data out);
- read-only marking for Agents;
- Agent access to Lead-only forms and other agents' tickets refused;
- the fallback on timeout, 429 and missing config;
- question scrubbing and the length cap;
- the rate limit;
- staff-only access with CSRF;
- the widget being present.

The leak sweep in `tests/test_tickets.py` also asks the assistant as an Agent.

## Who owns what
- **Groq account:** Aleksei.
- **API key:** Fly secrets and the password manager.

## Gotchas
- **The question is cleaned before sending:** capped at 500 characters, control characters dropped, and emails and phone numbers replaced with `[email]` and `[phone]`. The reply is shown with `textContent`, never as HTML.
- **CSRF:** the widget sends `X-CSRFToken`. The endpoint is wrapped in `admin_view`, so it's staff-only with CSRF on.
- **Groq's edge refuses urllib's default `User-Agent`,** so the request sends its own.
- **`/admin/assistant/` must come before `admin.site.urls`** in `config/urls.py`, or the admin's catch-all swallows it.
- **Rate limit:** 20 questions per user per hour, counted in the default cache. `shortcut:` that cache is per process, so with two gunicorn workers the real cap is up to 40. Use a shared cache if that matters.
- **Timeout:** `shortcut:` the 8 s timeout is per socket read, not total.

## Open items
- [ ] Set `GROQ_API_KEY` on Fly (the key is in the password manager since 2026-10-15). Until then, production shows the help-text fallback.
- [ ] Confirm the Groq free-plan limits in the console (the docs page shows only Developer plan limits).

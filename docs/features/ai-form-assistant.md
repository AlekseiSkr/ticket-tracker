# AI form assistant (Groq)

|              |                                            |
|--------------|--------------------------------------------|
| **Status**   | Planned (Phase 3) |
| **Owner**    | Aleksei (GitHub: AlekseiSkr) |
| **Created**  | 2026-10-15 |
| **Updated**  | 2026-10-15 |
| **Where**    | Groq API (`openai/gpt-oss-20b`); admin change-form widget; endpoint under `/admin/` |
| **Cost**     | $0 (Groq free plan) |
| **Depends on** | [admin-ui.md](admin-ui.md), [authentication-and-roles.md](authentication-and-roles.md) |

## What
A small chat panel on admin edit pages that answers "what does this field mean / how do I
fill this in". It's grounded in the real form: label, help_text, choices and required flag,
taken from `ModelAdmin.get_form(request, obj)`, plus the ticket workflow rules and the SLA
table. Because the form is built for the current user, an Agent's prompt never contains
fields the Agent can't see.

## Why
- **Groq:** free tier, OpenAI-compatible API, no data retention by default.
- **Fallback:** if the call fails, times out (8 s) or is rate-limited, the panel shows the
  field's own help text, so the admin never breaks.

**Rejected:**
- **Gemini free tier:** its terms allow **only Paid Services** for apps serving users in the
  EEA, UK or Switzerland (reviewers are in Estonia), and free-tier prompts may be read by
  human reviewers (verified 2026-10-15, ai.google.dev/gemini-api/terms).
- **A chain of several providers:** that's chatbot-framework over-engineering. The provider
  is an env var swap.
- **Streaming:** under WSGI it ties up a gunicorn worker per open stream.

## How it's set up
1. https://console.groq.com: sign up, then **API Keys** → create a key.
2. `fly secrets set GROQ_API_KEY=…`. Set `LLM_BASE_URL=https://api.groq.com/openai/v1` and
   `LLM_MODEL=openai/gpt-oss-20b` in `fly.toml [env]`.
3. Check the real free limits at console.groq.com → Settings → Limits (target ≥ 1K
   requests/day).

## Who owns what
- **Groq account:** Aleksei.
- **API key:** Fly secrets + password manager.

## Gotchas
- **Only field metadata is sent, never ticket or customer data.** Emails and phone numbers
  are stripped from the user's question before sending (GDPR).
- **Input and output limits:** questions are capped at 500 characters, and the reply is
  rendered as text, never HTML.
- **Rate limits:** 20 requests/hour per user and 800/day overall, stored in the DB cache.
- **CSRF:** the widget sends `X-CSRFToken`, and the endpoint keeps CSRF protection on.

## Open items
- [ ] Confirm the Groq free-plan limits in the console (the docs page shows only Developer
  plan limits).

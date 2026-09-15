# frontend — dashboard UI

## Today: white-label overlay

`whitelabel/index.html` is a drop-in replacement for the Strix viewer's
`static/index.html`. Loaded over the existing viewer, it:

- rebrands **Strix → SoldierIQ Cyber** (title, header, toasts) via a MutationObserver;
- removes every `strix.ai` link + blocks navigation/`window.open` to them;
- hides all cloud/enterprise/upsell UI ("Run a pentest in Cloud", "Run in the cloud",
  "Try Enterprise", cloud/team nav, feedback link);
- hides the email one-time-code form (the server-side unblock patch in
  `../backend/patches/unblock_history.py` makes it unnecessary anyway).

It is applied to the running viewer by `../backend/scripts/apply_whitelabel.sh`
(local) and by the root `Dockerfile` (image build).

## Next: a custom Next.js dashboard

The plan is to replace the overlay with a real **Next.js** app here that consumes
the viewer's REST API directly (see `../backend/README.md` for the endpoints:
`/api/run`, `/api/runs`, `/api/transcript`, `/api/vulnerabilities`, `/api/report`).
That gives full control over branding, layout, and merging in SoldierIQ **SA data**
(TAK / knowledge base) alongside the pentest view — without patching a compiled bundle.

When that exists, scaffold it in this folder (e.g. `frontend/app/`), point it at the
backend API base URL via an env var, and update the root `Dockerfile` (or add a
second service) to build and serve it.

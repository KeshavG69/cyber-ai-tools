# Security Penetration Test Report

**Generated:** 2026-09-11 20:04:16 UTC

# Executive Summary

# Executive Summary

An authorized black-box security assessment of the **OWASP Juice Shop v20.2.0** instance at `http://host.docker.internal:3001` identified **18 confirmed vulnerabilities**, each validated with a working proof-of-concept: **3 critical, 2 high, and 13 medium**.

**Overall risk posture: Critical.** The application can be fully compromised by an unauthenticated attacker through multiple independent paths, and every authenticated user can access or manipulate other users' data at will.

**Key findings**

- **Unauthenticated full administrative compromise** via two independent paths: mass assignment of `role:"admin"` at registration (`POST /api/Users`) and acceptance of unsigned `alg:none` JWTs — either yields a valid admin session with no credentials.
- **Unauthenticated SQL injection** on the login endpoint (`POST /rest/user/login`) logs in as the administrator and returns its password hash; a UNION-based injection on product search dumps all 28 users' credentials.
- **Systemic broken access control**: any customer can read, hijack, or check out other users' baskets, modify or delete other users' saved delivery addresses (with ownership reassignment enabling delivery interception), list the full user directory with emails and last-login IPs, and read all users' private complaints.
- **Money-manipulation primitives**: negative basket quantities generate negative-total orders that *credit* the paying wallet, and the wallet top-up endpoint accepts arbitrary amounts — together an unlimited store-credit mint.
- **Further validated issues**: reflected DOM XSS via the search parameter, SSRF with full response disclosure via profile-image URL fetch, open redirect via substring allowlist bypass, non-expiring JWTs, user enumeration, and credential exposure in URL query strings.

**Business impact.** In a production deployment of this codebase, the critical findings alone would expose all customer data, order history, and payment-related records, and grant full administrative control without any prior knowledge or credentials. The chained path (mass assignment → admin JWT → full user directory → SQLi credential dump) demonstrates total compromise end to end. As this is a deliberately vulnerable training instance with seeded demo data, the findings are rated on the demonstrated consequence class of each vulnerability.

**Remediation theme.** The single highest-leverage fix is enforcing server-side authorization and input parameterization consistently: deny-by-default field binding (whitelist registration fields), strict JWT algorithm allowlisting with expiry, parameterized SQL, and object-ownership checks on every ID-bearing route.

# Methodology

# Methodology

Conducted as a **gray-box-biased black-box assessment** (no source code; API structure inferred from the SPA bundle and Swagger UI) against the platform-authorized target `http://host.docker.internal:3001`, aligned with the **OWASP Top 10 (2021)** and **OWASP WSTG** methodology.

**Scope:** All application surfaces of the Juice Shop v20.2.0 deployment — REST API (`/rest/*`), Sequelize JSON API (`/api/*`), Angular SPA, exposed file directories (`/ftp`, `/3d`), LLM chatbot (`/rest/chat`), web3/NFT endpoints, and Prometheus metrics.

**Phases**

1. **Reconnaissance and attack-surface mapping** — endpoint extraction from the Angular bundle (~90 endpoints), technology fingerprinting (Node/Express, Sequelize/SQLite, Angular), authentication model documentation (RS256 JWTs, customer/admin/deluxe roles), exposed directory and config-endpoint enumeration, and test-account provisioning.
2. **Threat model derivation** — trust boundaries (unauthenticated user → customer → deluxe → admin) documented before testing and shared across all specialists.
3. **Parallel specialist testing** — dedicated specialists for SQL injection, broken access control/IDOR, authentication/JWT, XSS, SSRF/open redirect, business logic/race conditions, security misconfiguration, and LLM/chatbot security.
4. **Validation discipline** — every reported finding carries a working proof-of-concept executed against the live target (Python scripts, captured HTTP exchanges, browser-executed XSS evidence, inbound SSRF callback capture), a counterevidence pass, and honest CVSS calibration. Two-identity testing was used to prove cross-user (IDOR) impact; negative controls were used where applicable (e.g., invalid RS256 signatures correctly rejected while `alg:none` tokens were accepted).
5. **Coverage recording** — every assessed surface was recorded with an explicit outcome (reported / ruled out with named control / needs follow-up), including surfaces verified as safe (e.g., payment-card IDOR ruled out by ownership checks, feedback-comment XSS held by server-side sanitization, warehouse inventory tampering blocked by a server-side guard).

**Limitations.** The LLM chatbot could not be dynamically tested: the application's model backend (Ollama at `127.0.0.1:11434`) was unreachable from the app container, severing every prompt-injection test path at the provider. Stored-XSS via product description and the admin-account password-reset chain were narrowed but not fully landed within the engagement budget; these are listed as open items.

# Technical Analysis

# Technical Analysis

**Severity model:** CVSS v3.1 scores computed from the demonstrated attack, not the theoretical worst case. Critical = unauthenticated total compromise; High = cross-tenant/cross-user data access or database-wide disclosure; Medium = constrained-by-authentication or single-surface issues with concrete demonstrated impact.

**Critical findings**

1. **Mass assignment at registration** (CVSS 9.4) — `POST /api/Users` binds the client-supplied `role` field; registering with `role:"admin"` mints a genuine administrator account, verified with server-side admin actions. Root cause: un whitelisted model binding.
2. **`alg:none` JWT acceptance** (CVSS 9.4) — the backend accepts unsigned tokens; a forged token with an arbitrary identity (including admin) receives full authorization. Negative control confirmed valid RS256 signature verification is bypassed only by the algorithm-confusion path. Root cause: missing algorithm allowlist in token verification.
3. **SQL injection on login** (CVSS 9.1) — the `email` parameter is interpolated into a raw query; `' OR 1=1--` returns the administrator's session and password hash. Root cause: string-concatenated SQL.

**High findings**

4. **UNION-based SQL injection on product search** (CVSS 7.5) — `GET /rest/products/search?q=` concatenates into raw SQL; all 28 users' emails and password hashes dumped unauthenticated.
5. **Address-write IDOR** (CVSS 7.1) — `PUT/DELETE /api/Addresss/:id` performs no ownership check; the update additionally reassigns the record to the attacker, enabling delivery interception of other users' orders.

**Medium findings (13)** — cross-user basket read/checkout/basket-item manipulation (vuln-0004/0005/0009), full user-directory disclosure (vuln-0007), all-users complaint disclosure (vuln-0008), user enumeration with security-question disclosure (vuln-0003), password change via GET query string with hash disclosure (vuln-0010), non-expiring JWTs with no lifetime validation (vuln-0011), reflected DOM XSS via `bypassSecurityTrustHtml` on the search parameter (vuln-0013), SSRF with response disclosure via server-side fetch of the profile-image URL and persistence of the fetched body (vuln-0014), substring-based open-redirect allowlist bypass via userinfo-credential embedding (vuln-0012), negative-quantity orders that credit the paying wallet (vuln-0016), and unrestricted wallet top-up amounts (vuln-0018).

**Validated attack chains**

- **Chain A — unauthenticated full compromise:** mass assignment (vuln-0001) or `alg:none` forgery (vuln-0002) → admin JWT → full user directory (vuln-0007) → combined with search SQLi (vuln-0017) yields every user's credentials. No password, no interaction, entirely unauthenticated entry.
- **Chain B — financial fraud:** wallet top-up (vuln-0018) or negative-quantity wallet crediting (vuln-0016) provides unlimited funds; basket IDOR (vuln-0005) and address IDOR (vuln-0006) allow redirecting or hijacking other users' deliveries.
- **Chain C — session permanence:** non-expiring tokens (vuln-0011) mean any token theft (e.g., via the DOM XSS vuln-0013 or open redirect vuln-0012) is permanent.

**Systemic root causes:** (1) no server-side authorization layer — object ownership is trusted to the client or not checked at all; (2) unvalidated client input bound directly to privileged fields and SQL; (3) legacy cryptographic/JWT practices (MD5 hashes, unsigned-token acceptance, missing expiry). These three themes account for 16 of the 18 findings.

**Areas verified as safe (negative results):** payment-card IDOR (`/api/Cards` ownership checks present), admin role enforcement on order-history/delivery-status endpoints (403s), feedback-comment stored XSS (server-side sanitize-html allowlist held against 20+ bypass attempts), product-review XSS (safe Angular text interpolation), coupon abuse with expired codes (rejected server-side), and warehouse inventory tampering (blocked by a server-side guard). Exposed `/rest/admin/application-configuration` was verified to contain no secrets (informational only).

**Open items / follow-up**

- LLM chatbot security (prompt injection, tool-call abuse, output handling): dynamically untestable — the app's Ollama backend at `127.0.0.1:11434` was unreachable; `/rest/chat` accepts attacker-supplied `system`-role messages unauthenticated, a ready injection primitive once the backend is restored. Re-test after fixing the deployment.
- Stored XSS via product description (`PUT /api/Products/:id` with customer JWT — the authz gap itself is confirmed): no executing payload landed within budget; `<img onerror>` forms untested on that sink.
- Local file read via the data-erasure `layout` parameter (confirmed ENOENT path disclosure, content PoC incomplete).
- Password-reset takeover of `admin@juice-sh.op` (security-answer hash recovered; offline cracking inconclusive — the account is already trivially compromised via Chains A/B).
- Exposed legacy dependency manifest (sanitize-html 1.4.2, express-jwt 0.1.3, sequelize ~4): pinned-version CVE cross-check not completed within budget; flagged for SCA follow-up.

# Recommendations

# Recommendations

**Immediate (critical exposure — fix before any redeployment)**

1. **Close both admin-compromise paths**: whitelist registration fields server-side (never bind `role` from client input) and enforce a strict JWT algorithm allowlist (RS256 only) with signature verification that hard-rejects `alg:none` and unsigned tokens. *(vuln-0001, vuln-0002)*
2. **Parameterize all SQL**: replace string interpolation with parameterized/ORM queries on the login and search endpoints. *(vuln-0015, vuln-0017)*
3. **Add object-ownership checks to every ID-bearing route**, deny-by-default: baskets, basket items, checkout, addresses, complaints, and the user directory must verify the authenticated principal owns (or is authorized for) the referenced object before any read or write. *(vuln-0004–0009)*

**Short-term**

4. **JWT lifecycle**: add mandatory `exp` claims with server-side lifetime validation and rotate all existing tokens. *(vuln-0011)*
5. **Wallet and order validation**: enforce positive, server-computed amounts and quantities — reject negative values on `PUT /api/BasketItems/:id`, recompute totals server-side at checkout, and bind wallet deposits to a real payment confirmation rather than a client-supplied amount. *(vuln-0016, vuln-0018)*
6. **SSRF and redirect hardening**: allowlist destinations by exact parsed-origin match (no substring checks) on `/redirect`; on the profile-image URL fetch, validate scheme (https only), resolve and block private/loopback/link-local IP ranges, and never persist the fetched response as a downloadable asset. *(vuln-0012, vuln-0014)*
7. **XSS sink removal**: remove the `bypassSecurityTrustHtml` call on the search-results path and render user input through Angular's default text interpolation. *(vuln-0013)*
8. **Account hygiene**: return generic responses on the security-question endpoint to prevent enumeration; move password change to a POST body (never query strings) and stop returning password hashes in API responses; store passwords with a salted adaptive hash (bcrypt/argon2) rather than unsalted MD5/SHA-256. *(vuln-0003, vuln-0010)*

**Medium-term**

9. **Session and token design**: stop embedding the full user record (password hash, TOTP secret) inside the JWT payload; carry only minimal claims (id, role, expiry).
10. **Automated regression gates**: add authorization tests (two-identity IDOR cases), SQLi tests, and business-invariant tests (positive totals, positive quantities, server-computed wallet mutations) to CI, and consider deploying these checks with an API fuzzer (e.g., ZAP/nuclei custom templates) against staging.
11. **Dependency modernization**: the exposed legacy manifest reveals severely outdated packages (sanitize-html 1.4.2, express-jwt 0.1.3, sequelize ~4); schedule a dependency upgrade program with SCA gating.

**Retest and validation.** After remediation, re-run the PoC scripts from each finding's report (all are self-contained) to confirm: no admin role can be minted at registration, `alg:none` tokens are rejected, injection payloads fail on login/search, two-identity IDOR tests return 403/404, negative quantities and arbitrary wallet deposits are rejected, the SSRF callback never arrives, and the search XSS no longer executes.


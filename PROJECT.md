# Project: homeandrecipe-cloaker Modernization & Refactoring

## Architecture
- **Target Repository**: `c:\Users\mouni\Desktop\my-cloakers`
- **Stack**: Node.js (v24 native test runner), Express 5 backend server (`server.js`), Cloudflare Workers edge runtime (`src/index.js`), Cloudflare D1 SQL database, Vanilla HTML5/Tailwind/Lucide UI (`public/index.html`).
- **Core Objectives**: Eliminate bugs, security vulnerabilities (SQL injection, XSS, token leakage), schema mismatches, and runtime errors while upgrading performance (in-memory caching, non-blocking Worker I/O, distinct visitor counting) and accessibility (WCAG 2.2 AA).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Legacy File Removal | Permanently remove 33 files in `scratch/`, `last cloaking.js`, `last cloaking - Copie.js`, `worker-single-file.js`, `src/themes/cloak.js`, and empty `src/themes/` dir | M1 | ORIGINAL_REQUEST §R1 |
| 2 | Secret Scrubbing | Remove hardcoded `cfoat_...` Cloudflare token from `dashboard-config.json`, sanitize hardcoded account/DB IDs, enforce environment/UI config | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Git & .gitignore Hygiene | Create `.gitignore` covering `node_modules/`, `.wrangler/`, `.env*`, `*.log`, untrack `node_modules` from git index cache | M1 | ORIGINAL_REQUEST §R1 |
| 4 | Campaign Schema Normalization | Deduplicate IDs in `dashboard-campaigns.json`, standardize fields `{ id, name, sourceDomain, safeUrl, targetDomain, moneyUrl, status, createdAt }` | M1 | ORIGINAL_REQUEST §R1 |
| 5 | D1 Analytics SQLi Parameterization | Parameterize `/api/analytics/simulate` queries using `(?1, ?2, datetime('now'), ?3)` with array bindings | M2 | ORIGINAL_REQUEST §R2 |
| 6 | Token Precedence Enforce | User-configured API tokens in `dashboard-config.json` strictly take priority over Wrangler defaults | M2 | ORIGINAL_REQUEST §R2 |
| 7 | In-Memory Caching & Async I/O | Replace per-request synchronous `fs.readFileSync`/`writeFileSync` with in-memory cache backed by asynchronous disk writes | M2 | ORIGINAL_REQUEST §R2 |
| 8 | Worker Distinct Visitor Counting | Update visit queries in `src/index.js` and `buildWorkerCode` to use `COUNT(DISTINCT visitor_hash)` for 24h gate | M2 | ORIGINAL_REQUEST §R2 |
| 9 | Non-Blocking Worker Logging | Offload D1 log inserts in Worker via `ctx.waitUntil()` to avoid blocking request response | M2 | ORIGINAL_REQUEST §R2 |
| 10 | Safe Redirect URL Stringification | Sanitize redirect URLs via `JSON.stringify().replace(/</g, '\\u003c')` to prevent script breakout XSS | M2 | ORIGINAL_REQUEST §R2 |
| 11 | Wrangler Config Bindings | Add `[[d1_databases]]` binding for `DB` and daily cron `[triggers]` to `wrangler.toml` | M2 | ORIGINAL_REQUEST §R2 |
| 12 | WCAG 2.2 AA Card Accessibility | Convert method selection and trigger cards to accessible buttons/radiogroups (`role="radiogroup"`, `role="radio"`, `tabindex="0"`, `aria-checked`, keyboard handlers) | M3 | ORIGINAL_REQUEST §R3 |
| 13 | Form Input Label Association | Add explicit `<label for="...">` to all 11 inputs and accessible labels to selects in `public/index.html` | M3 | ORIGINAL_REQUEST §R3 |
| 14 | Accessible Settings Modal | Add `role="dialog"`, `aria-modal="true"`, and keyboard `Escape` handler to settings modal | M3 | ORIGINAL_REQUEST §R3 |
| 15 | Visibility-Aware Polling | Pause analytics polling when `document.hidden` is true, resume upon tab focus/visibilitychange | M3 | ORIGINAL_REQUEST §R3 |
| 16 | Campaign Card Fallback & Deletion | Fix `undefined` display in campaign cards, add delete button wired to `DELETE /api/campaigns/:id` | M3 | ORIGINAL_REQUEST §R3 |
| 17 | Dynamic Threshold Sync & Copy Polish | Sync threshold counts across cards and buttons, eliminate duplicate text | M3 | ORIGINAL_REQUEST §R3 |
| 18 | Regression Test Suite Pass | Maintain 100% pass rate across existing 31 tests in `test/*.test.js` | M4 | ORIGINAL_REQUEST §R4 |
| 19 | New Automated Security & A11y Tests | Add automated tests verifying SQLi prevention, token precedence, campaign upsert normalization, Worker distinct count query logic, and HTML accessibility attributes | M4 | ORIGINAL_REQUEST §R4 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Repo Hygiene, Secrets & Schema | Features 1, 2, 3, 4 | none | DONE |
| M2 | Backend & Worker Security & Performance | Features 5, 6, 7, 8, 9, 10, 11 | M1 | DONE |
| M3 | Frontend Simplification & WCAG 2.2 AA | Features 12, 13, 14, 15, 16, 17 | M1, M2 | DONE |
| M4 | Automated Verification Suite & Adversarial QA | Features 18, 19 | M1, M2, M3 | DONE |

## Interface Contracts

### Backend ↔ Frontend Campaign Schema Contract
```typescript
interface CampaignRecord {
  id: string;               // Unique slug (e.g., "homeandrecipe-com-cloaker")
  name: string;             // Display name (e.g., "Home and Recipe Cloaker")
  sourceDomain: string;     // Clean origin host without protocol (e.g., "homeandrecipe.com")
  safeUrl: string;          // Full safe URL (e.g., "https://homeandrecipe.com")
  targetDomain: string;     // Full offer redirect URL or target domain
  moneyUrl: string;         // Target offer redirect URL (synonym with targetDomain)
  workerName: string;       // Cloudflare worker service name
  activationMethod: 'trigger' | 'visitor_threshold';
  triggerCondition: 'scroll' | 'click' | 'both';
  scrollPct: number;        // e.g., 15
  thresholdCount: number;   // e.g., 8
  routes: string[];         // e.g., ["homeandrecipe.com/*", "www.homeandrecipe.com/*"]
  status: 'active' | 'inactive';
  createdAt: string;        // ISO 8601
  deployedAt?: string;      // ISO 8601
}
```

### Backend ↔ D1 Database Contract
```sql
-- D1 Table Schema
CREATE TABLE IF NOT EXISTS url_human_visits (
  post_path TEXT NOT NULL,
  visitor_hash TEXT NOT NULL,
  visited_at TEXT NOT NULL,
  country TEXT DEFAULT 'US'
);
CREATE INDEX IF NOT EXISTS idx_visits_path_time ON url_human_visits (post_path, visited_at);
```
- Query 24h distinct count:
  `SELECT COUNT(DISTINCT visitor_hash) as cnt FROM url_human_visits WHERE post_path = ?1 AND visited_at >= datetime('now', '-24 hours')`
- Insert visit (asynchronous via `ctx.waitUntil`):
  `INSERT INTO url_human_visits (post_path, visitor_hash, visited_at, country) VALUES (?1, ?2, datetime('now'), ?3)`
- Simulate visits (parameterized batch):
  `INSERT INTO url_human_visits (post_path, visitor_hash, visited_at, country) VALUES (?, ?, datetime('now'), ?), ...` with flat params array.

## Code Layout
- `c:\Users\mouni\Desktop\my-cloakers\`
  - `server.js`: Express dashboard backend, API endpoints, worker code builder
  - `src/index.js`: Cloudflare Workers edge runtime entrypoint
  - `public/index.html`: Dashboard UI, styling, and client script
  - `wrangler.toml`: Cloudflare Workers deployment config & D1/cron bindings
  - `.gitignore`: Git ignore definitions
  - `dashboard-config.json`: Local dashboard runtime configuration (scrubbed of secrets)
  - `dashboard-campaigns.json`: Local campaigns record store (normalized, deduplicated)
  - `test/`:
    - `endpoints.test.js`: Core route and API tests
    - `health.test.js`: Health & uptime tests
    - `server.test.js`: Cloaking logic & bot detection tests
    - `startup.test.js`: Server lifecycle tests
    - `modernization.test.js`: New automated tests for R1-R4



"github": {
    "token": "YOUR_GITHUB_TOKEN",
    "owner": "annadeco",
    "repo": "annadeco.github.io",
    "branch": "main",
    "is_org": true,
    "base_path": ""
  },
  "cloudflare": {
    "api_token": "YOUR_CLOUDFLARE_API_TOKEN",
    "account_id": "YOUR_CLOUDFLARE_ACCOUNT_ID",
    "project_name": "gardenhomejdhd",
    "deployment_type": "workers_assets",
    "custom_domain": "",
    "compatibility_date": "2024-11-01",
    "worker_dir": "my-worker",
    "account_subdomain": "laurainsley01"
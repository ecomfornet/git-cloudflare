# Multi-Project Management System & Step 1 Organization Decoupling Walkthrough

**Architecture Milestone**: Milestone P1–P5 Final Walkthrough & Verification Guide  
**Project**: pSEO Static Site Generator & Cloudflare Edge / GitHub Pages Multi-Cloud Hub  
**Status**: **100% Complete & Verified** (144/144 Automated Tests Passing, Gate Ensemble Unanimous Sign-Off)  
**Live Target Edge Destination**: [`http://localhost:8080`](http://localhost:8080) (Status: **HTTP 200 OK**)

---

## 1. Executive Summary

This release resolves the two core challenges requested by the user:
1. **Multi-Project System with Empty Category Isolation**:
   - Previously, all scraped and ingested posts from all websites were lumped into a single monolithic manifest (`pseo_manifest.json`), permanently filling the Categories filter dropdown with 16 old categories (`Landscaping Ideas1`, `minimal bedroom design ideas`, `Bedroom Inspo`, etc.).
   - Users can now click **`+ New Project`** directly in the top command bar. Any newly created project begins with an isolated manifest (`scraped_data/<project_id>/manifest.json`) with **0 posts and an empty category list**. Categories from old projects never contaminate the new project!
   - Users can seamlessly switch between projects using the new **Project Selector** dropdown in the header.
2. **Step 1 Decoupling of Cloudflare Worker Name & GitHub Organization**:
   - In Step 1 (**01 Ingest**), the dashboard now provides dedicated, independent inputs for **Cloudflare Worker Name** (e.g., `gardenhomejdhd`) and **GitHub Organization / User** (e.g., `annadeco`).
   - The backend build engine (`resolve_project_output_dir` and `SiteBuilder`) strictly routes Cloudflare builds to `dist/<cf_worker>` with Cloudflare base URLs, and GitHub builds to `dist/<gh_owner>` with GitHub base URLs.
   - When Cloudflare and GitHub have different names, **there is zero collision, zero base URL cross-contamination, and zero organization check error**.
   - Fixed `/api/github/check-org` to test both `/orgs/{name}` and `/users/{name}`, allowing personal GitHub user accounts (like `annadeco`) to verify successfully.

---

## 2. Key Code Changes

### A. Backend Architecture & Data Models
- **`app/models.py`**:
  - Added `ProjectItem` dataclass representing a project profile (id, name, platform, cf_project_name, cf_custom_domain, gh_owner, gh_repo, sitemap_url, theme, manifest_path, output_dir).
  - Added `Manifest.create_empty(project_id)` to initialize brand-new catalogs with empty posts and empty categories.
- **`app/config.py`**:
  - Added `active_project: str = "stylesdays"` and `projects: dict[str, dict]` to `AppConfig` with full serialization in `to_dict` and `from_dict`.
- **`app/dashboard/server.py`**:
  - Implemented `DashboardManager._init_projects()`, `list_projects()`, `create_project()`, and `switch_project()`.
  - Added REST API routes:
    - `GET /api/projects`: Lists all projects and their post/category counts.
    - `POST /api/projects`: Creates an isolated new project with an empty catalog.
    - `POST /api/projects/switch`: Swaps the active project and hot-reloads its isolated manifest.
  - Updated `resolve_project_output_dir()`: When target is Cloudflare, strictly uses `cf.project_name` (`gardenhomejdhd`), never falling back to `gh.owner` (`annadeco`).
  - Updated `run_build()`: Resolves base URL according to the target cloud and active platform, preventing URL mixing.
  - Updated `/api/github/check-org`: Automatically falls back to `/users/{name}` if `/orgs/{name}` returns 404, allowing user accounts to verify as active GitHub entities.
- **`app/generator/site_builder.py`**:
  - Decoupled `base_url` resolution so Cloudflare worker projects never adopt GitHub Pages root domains when both platforms are configured.

### B. Frontend Dashboard UI & Real-Time Sync
- **`app/dashboard/static/index.html`**:
  - Added a compact **Project Selector** (`#selectActiveProject`) and **`+ New Project`** button (`#btnNewProject`) to the sticky top command bar.
  - Added the **Create New Project Modal** (`#modalNewProject`) with fields for Project Name, Deployment Platform, Cloudflare Worker Name, Custom Domain, GitHub Organization, GitHub Repo, and Sitemap URL.
  - Enhanced Step 1 (**01 Ingest**) with independent inputs for Cloudflare (`#cfgCfProjectName`, `#cfgCfCustomDomain`) and GitHub (`#cfgStep1GithubOwner`, `#cfgStep1GithubRepo`).
- **`app/dashboard/static/app.js`**:
  - Implemented `loadProjects()`, `switchProject()`, `handleCreateNewProject()`, and modal listeners.
  - Guaranteed empty category reset: when switching to a project with 0 posts, `#postCategoryFilter` is reset to strictly `<option value="">All Categories</option>`.
  - Implemented two-way live synchronization between Step 1 GitHub inputs and Settings modal inputs.

---

## 3. Verification & Test Results

### 1. New Dedicated Automated Test Suite (`Tier 9`)
```powershell
python run_tests.py --tier 9
```
**Results**:
- `test_create_new_project_has_empty_categories`: **PASS** (Asserts newly created project starts with 0 posts and 0 categories in memory and on disk).
- `test_project_switching_isolates_manifests`: **PASS** (Asserts switching from `stylesdays` with 152 posts to `clean-site` loads 0 posts/0 categories, and switching back restores all 152 posts).
- `test_resolve_project_output_dir_independence`: **PASS** (Asserts Cloudflare resolves to `dist/gardenhomejdhd` and GitHub resolves to `dist/annadeco` without collisions).
- `test_site_builder_base_url_decoupling`: **PASS** (Asserts Cloudflare worker URLs are not corrupted by GitHub owner name).
- `test_list_projects_reports_active_status`: **PASS** (Asserts correct project list metadata and active flags).
- `test_legacy_project_loads_existing_categories`: **PASS** (Asserts backward compatibility with existing data).

### 2. Full Regression Suite Execution
```powershell
python run_tests.py --tier 1 2 3 5 6 7 8 9
```
```
==================================================================================================
                               TEST EXECUTION SUMMARY TABLE
==================================================================================================
 Tier     Description                                    Total  Pass  Fail   Err  Skip    Time  Status
--------------------------------------------------------------------------------------------------
 Tier 1   Unit Tests (Models, Routing, SEO Schemas, R...    29    29     0     0     0   0.01s  PASS  
 Tier 2   Integration (WP REST, Sitemaps, Diffing, Im...    22    22     0     0     0   3.65s  PASS  
 Tier 3   SEO & Static (JSON-LD Graph, OpenGraph, Pin...    19    19     0     0     0   0.00s  PASS  
 Tier 5   Adversarial Stress Suite (Ingestion, Diff, ...    29    29     0     0     0   5.16s  PASS  
 Tier 6   WebP Image Optimization & Core Web Vitals (...     9     9     0     0     0   1.33s  PASS  
 Tier 7   Cloudflare Workers & Pages Deployment Engin...    19    19     0     0     0   7.64s  PASS  
 Tier 8   Full-Content Scraper, Multi-Domain Folders ...    11    11     0     0     0   3.12s  PASS  
 Tier 9   Multi-Project System, Empty Category Catalo...     6     6     0     0     0   0.10s  PASS  
--------------------------------------------------------------------------------------------------
 TOTAL    All Selected Tiers Combined                      144   144     0     0     0  21.00s  PASS (100.0%)
==================================================================================================
[SUCCESS] All test suites completed successfully with 0 failures!
```

---

## 4. User Manual & How to Use

1. **Creating a New Project with Empty Categories**:
   - Open the dashboard at `http://localhost:8080`.
   - In the top command bar, click **`+ New Project`**.
   - Enter your new project name (e.g. `Luxury Villas`), select your deployment platform, and click **`Create & Activate Project`**.
   - Navigate to **03 Catalog**: the Category filter dropdown is clean (only "All Categories"), and the table is empty with 0 posts.
2. **Switching Between Projects**:
   - Select any project from the **`📁 Project`** dropdown in the header to hot-swap to that project's catalog and configuration.
3. **Using Step 1 with Different Cloudflare and GitHub Names**:
   - In **01 Ingest**, you will see both the **Cloudflare Worker Name** and **GitHub Organization / User** fields.
   - Enter your Cloudflare worker name (e.g. `gardenhomejdhd`) and GitHub organization/username (e.g. `annadeco`).
   - Both operate independently without any naming conflicts or validation errors.


---

## 3. GitHub Org & Repo Decoupling to Step 1 with API Account Detection (Milestones O1–O5)

### A. Motivation & Architecture
Previously, the global **Settings modal** (`⚙️ Settings`) contained fields for GitHub Organization and Repository Name, mixing global platform credentials (Personal Access Token `PAT`) with project-specific repository routing.

In this update:
1. **Clean Settings Modal (`⚙️ Settings`)**:
   - Organization and Repository Name inputs and buttons were completely removed from Settings.
   - Settings is now exclusively dedicated to **Global Platform Credentials**:
     - Personal Access Token (`PAT: repo, admin:org`) with show/hide eye toggle and status badge.
     - Default Branch (`main`).
     - Subpath Prefix (`/subpath`).
     - "⚡ Test Token & Detect Orgs" button.
     - "💾 Save GitHub Settings" button.
2. **Step 1 (Content Ingestion) Target Configuration**:
   - The GitHub configuration card in Step 1 now features:
     - **Detected Organization / User Dropdown (`#cfgStep1GithubAccount`)**: Automatically queries `/api/github/orgs` using the saved token in Settings, presenting all detected accounts (`🏢 annadeco (Organization)`, `👤 ecomfornet (User)`).
     - **Refresh Button (`🔄`)**: Re-queries the GitHub API on demand.
     - **Organization Handle Input (`#cfgStep1GithubOwner`)**: Automatically populated from the dropdown, with manual override support.
     - **Repository Name Input (`#cfgStep1GithubRepo`)**: Directly input and editable by the user.
     - **Root Domain Mode Toggle (`#cfgStep1AutoRootOrg`)**: Automatically syncs `<org>.github.io` repository naming.
     - **Inline Action Buttons**: **`🏢 Verify Org`** and **`🚀 Create Repo`** directly inside Step 1, displaying real-time feedback banners with zero need to open the Settings modal.
     - **Live Target Link**: Dynamically updates target URL preview (`https://annadeco.github.io/`).
3. **Backend API**:
   - `GET /api/github/orgs` detects accounts using `self.manager.config.github.token`.
   - `update_config_from_dict()` non-destructively preserves project-specific `owner` and `repo` when saving from Settings, and updates active project metadata when updated from Step 1.

---

## 4. Verification & Validation Results

### A. Automated Test Suite (146/146 PASS - 100%)
```text
==================================================================================================
                               TEST EXECUTION SUMMARY TABLE
==================================================================================================
 Tier     Description                                    Total  Pass  Fail   Err  Skip    Time  Status
--------------------------------------------------------------------------------------------------
 Tier 1   Unit Tests (Models, Routing, SEO Schemas, R...    29    29     0     0     0   0.01s  PASS  
 Tier 2   Integration (WP REST, Sitemaps, Diffing, Im...    22    22     0     0     0   3.76s  PASS  
 Tier 3   SEO & Static (JSON-LD Graph, OpenGraph, Pin...    19    19     0     0     0   0.00s  PASS  
 Tier 5   Adversarial Stress Suite (Ingestion, Diff, ...    29    29     0     0     0   6.25s  PASS  
 Tier 6   WebP Image Optimization & Core Web Vitals (...     9     9     0     0     0   1.85s  PASS  
 Tier 7   Cloudflare Workers & Pages Deployment Engin...    19    19     0     0     0   8.64s  PASS  
 Tier 8   Full-Content Scraper, Multi-Domain Folders ...    11    11     0     0     0   3.75s  PASS  
 Tier 9   Multi-Project System, Empty Category Catalo...     8     8     0     0     0   0.15s  PASS  
--------------------------------------------------------------------------------------------------
 TOTAL    All Selected Tiers Combined                      146   146     0     0     0  24.41s  PASS (100.0%)
==================================================================================================

[SUCCESS] All test suites completed successfully with 0 failures!
```

### B. Live Browser Verification via Playwright
1. **Settings Modal**:
   - Verified only Token, Branch, and Subpath are present.
   - Verified Organization and Repo inputs are completely absent.
2. **Step 1 Ingest**:
   - Verified detected organization dropdown automatically populated with 3 accounts (`👤 ecomfornet (User)`, `🏢 heros-githob-io (Organization)`, `🏢 annadeco (Organization)`).
   - Selecting an account updates organization and repository name.
   - Clicked `🏢 Verify Org`: successfully displayed verified active status banner (`✅ Organization 'annadeco' is verified and active on GitHub! Plan: free`).
   - Verified 0 JavaScript runtime errors in browser console.


---

## 7. Model 1 · Kinfolk Journal (`editorial-warm`) Aesthetic & Interactivity Refinement

**Milestones K1–K4 Verification Summary**:
- **Front Cover Hero Image**: Now dynamically pulls the featured image (`local_image_path` or `image_url`), title, excerpt, and target link directly from the latest ingested article (`posts[0]`), ensuring the front page always showcases the freshest content.
- **Excised Metadata & Badges**:
  - Removed `"Featured Cover Story"` badge.
  - Removed `"schedule 8 Min Read"` time chip.
  - Removed `"Volume 48 • Autumn/Winter"` volume label.
  - Removed top notice bar `"The Spatial Journal • Vol. XII"` badge.
  - Removed top notice bar `"auto_stories {total_posts} Guides Published"` counter.
  - Centered the publication dispatch subtitle cleanly.
- **Topic Silos & Categories**:
  - Completely removed slug indicators (`/bedroom-inspo/`, `/fire-pits/`, `/patio-design/`, `/gazebos-pergolas/`, etc.) from all category cards.
  - Retained only the clean, elegant category title (`Bedroom Inspo Guides`, `Fire Pits & Hearths`, etc.) and the curated guide count.
- **All Published Guides Grid**:
  - Made both the thumbnail image and title clickable anchor links pointing to the article URL (`<a href="{link}">...</a>`).
  - Removed the monospace slug preview (`{web_path_val}`) from the card body.

### Visual Verification

````carousel
![Refined Kinfolk Hero](file:///C:/Users/mouni/.gemini/antigravity/brain/c74d76e0-2737-467a-9b30-b696007f0f5f/kinfolk_hero_refined.png)
<!-- slide -->
![Topic Silos & Published Guides Grid](file:///C:/Users/mouni/.gemini/antigravity/brain/c74d76e0-2737-467a-9b30-b696007f0f5f/kinfolk_silos_and_guides.png)
````


---

## 8. Live Template Preview Dual-View (Homepage Hub & Article Guide)

**Milestones H1–H4 Verification Summary**:
- **Root Cause Identified**: The dashboard preview engine previously only invoked `render_post(...)`, rendering an individual article page when users clicked `👁️ Preview` on **Model 1 · Kinfolk Journal**, hiding the refined Magazine Homepage Hub (`render_stitch_editorial_hub`).
- **Dual-View Modal Header**:
  - Added interactive view toggle buttons directly to the template preview modal: `[🏛️ Front / Hub | 📄 Article Guide]`.
  - Clicking `👁️ Preview` on **Model 1 · Kinfolk Journal** in Step 2 now defaults directly to the **Front / Homepage Hub** view, dynamically showcasing the user's latest ingested article (`New Ingested Guide`), the clean Topic Silos with zero slugs, and clickable guide cards.
  - Clicking `📄 Article Guide` toggles instantly to the single article layout.
- **Step 4 Live Preview Integration**:
  - Added `🏛️ Front / Homepage Hub (Model 1 Kinfolk Journal)` as the top choice in `#previewPostSelect`.
  - Added a dedicated `🏛️ Model 1: Kinfolk Homepage Hub` quick switcher button.

### Visual Verification

![Modal Template Preview - Kinfolk Journal Front Hub](file:///C:/Users/mouni/.gemini/antigravity/brain/c74d76e0-2737-467a-9b30-b696007f0f5f/modal_template_preview_hub.png)


---

## 9. The Nordroom Scandinavian Design System & Default Theme (Template 2)

**Milestones N1–N4 Verification Summary**:
- **Design Inspiration**: Seeded the acclaimed minimalist aesthetic and spatial storytelling of **The Nordroom** ([thenordroom.com](https://www.thenordroom.com/)) into **Template 2** (`nordic-studio`).
- **Elevation to Default Theme**:
  - `BuildConfig.theme`: Defaulted to `"nordic-studio"` across `app/config.py`, `pseo_config.json`, and `pseo_config.example.json`.
  - In Step 2 of the Dashboard, **Model 2 · The Nordroom** is now selected by default with a dedicated `⭐ Default Theme` badge.
- **The Nordroom Homepage Hub (`render_nordic_studio_hub`)**:
  - **Centered Masthead**: Elegant uppercase tracking-widest branding (`THE NORDROOM`) flanked by room categories (`LIVING ROOM`, `BEDROOM`, `KITCHEN`, `BATHROOM`, `GARDEN & OUTDOOR`, `SMALL SPACES`, `COLOR TRENDS`).
  - **Dynamic Cover Story**: Pulls dynamically from the latest ingested article (`posts[0]`) with 16:9 / 3:2 photography, teak category kicker, 40px serif headline (`Cormorant Garamond`), 2-line architectural lede, and byline `By Rachel • 4 Min Read`. Both image and title are clickable links!
  - **Curated Room Taxonomy**: 6 clean room showcases with curated guide counts (**zero ugly raw slugs**).
  - **3-Column Scandinavian Feed**: Clean 4:3 cards with hover scale, teak kicker, serif titles, short excerpts, and `Read Tour →` links.
  - **Newsletter Dispatch**: Clean linen subscription box for weekly Scandinavian home tours.
  - **4-Column Footer**: Curated room tours, design styles, and social/copyright links.
- **The Nordroom Single Article Guide (`render_nordic_studio_layout`)**:
  - **Header & Footer Continuity**: Shares the exact same The Nordroom masthead, room navigation, and 4-column footer.
  - **Centered 740px Reading Pane**: Max-width strictly constrained to `740px` for optimal legibility and reading comfort.
  - **Post Meta & Headline**: Clean category kicker (`CATEGORY • 5 MIN READ • UPDATED 2026`), high-impact `Cormorant Garamond` serif headline, 2-line italic lede, author byline (`By Rachel` or configured author) with circular monogram avatar, and `📌 Save to Pinterest` button.
  - **Hero Photography**: 16:10 rounded image with photo credit caption.
  - **Zero Robotic Filler**: 100% removal of artificial checklist boxes (e.g. `Step 1: Draft floor plan...`).
  - **Prose Elegance**: 18px body font (`Plus Jakarta Sans`), 1.8 line height, and classic drop cap on the first paragraph.
  - **Related Guides Grid**: 3 clean Scandinavian post cards with clickable images and titles (zero slugs).

### Visual Verification

````carousel
![The Nordroom Homepage Hub](file:///C:/Users/mouni/.gemini/antigravity/brain/c74d76e0-2737-467a-9b30-b696007f0f5f/thenordroom_hub_preview.png)
<!-- slide -->
![The Nordroom Single Article Guide](file:///C:/Users/mouni/.gemini/antigravity/brain/c74d76e0-2737-467a-9b30-b696007f0f5f/thenordroom_article_preview.png)
````


---

## 10. Production Static Site & pSEO Architecture across All 3 Templates + Model 3 Styleire Magazine Replacement

**Milestones S1–S4 Verification Summary**:
- **Reference Architecture Forensic Analysis**: Audited `C:\Users\mouni\Desktop\github cloudlare\static-site` (82 directories, 78 HTML pages, 128 optimized JPGs, Tailwind v4 consolidated bundle, and multi-schema JSON-LD structured data).
- **Universal 3-Template pSEO System**:
  - **URL & Directory Routing (`pseo_nested_silo`)**:
    - Articles: `/blog/<slug>/index.html` (clean URL: `/blog/<slug>/`)
    - Category Silos: `/category/<category_slug>/index.html` (clean URL: `/category/<category_slug>/`)
    - E-E-A-T Author Page: `/author/sophia-bennett/index.html` (clean URL: `/author/sophia-bennett/`)
    - HTML Sitemap Directory: `/sitemap/index.html` (clean URL: `/sitemap/`)
    - 9 Legal/Trust Compliance Pages: `/about/`, `/contact/`, `/editorial-policy/`, `/fact-checking-policy/`, `/privacy-policy/`, `/cookie-policy/`, `/terms/`, `/disclaimer/`, `/copyright/`
    - Technical SEO Assets: `/robots.txt`, `/sitemap.xml` (with priorities 1.0, 0.8, 0.6, 0.5, 0.4), `/ads.txt` (IAB Tech Lab spec 1.1)
  - **3-Tier Multi-Schema JSON-LD**:
    - **Schema 1: `@type: "Article"`**: headline, description, images, ISO publish/modified dates, Person author with profile URL, and Organization publisher with logo.
    - **Schema 2: `@type: "FAQPage"`**: mainEntity array of Question and Answer matching the visible on-page FAQ accordion.
    - **Schema 3: `@type: "BreadcrumbList"`**: `Home` -> `Category` -> `Article Title`.
    - **Homepage Schema**: `@type: "WebSite"` with publisher Organization.
    - **Author Schema**: `@type: "Person"` with jobTitle, bio, credentials, and image.
  - **Universal Support**: Works seamlessly across **all 3 templates** (`editorial-warm` [Kinfolk], `nordic-studio` [The Nordroom], and `pinterest-mag` / `styleire` [Styleire]).

- **Replaced Template 3 with Styleire Editorial Magazine (`render_styleire_layout` & `render_styleire_hub`)**:
  - **Modern Editorial Aesthetic**: Replaced the previous rudimentary pinboard with the exact Styleire layout from `static-site`.
  - **Sticky Blurred Masthead**: Clean backdrop-blur header with bold serif brand logo, category links (`Living Room`, `Bedroom`, `Kitchen & Dining`, `Outdoor Spaces`, `DIY & Craft`, `Seasonal & Trends`), and mobile horizontal scroll bar.
  - **Single Post Reading Architecture (`render_styleire_layout`)**:
    - 768px (`max-w-3xl`) centered container.
    - Breadcrumbs `<nav aria-label="Breadcrumb">` (`Home / Category / Article Title`).
    - Uppercase category kicker (`text-xs font-semibold uppercase tracking-widest text-stone-500`).
    - Serif H1 headline (`font-serif text-4xl font-bold leading-tight md:text-5xl`).
    - Byline with clickable author profile link (`By Sophia Bennett • May 20, 2026 • 5 min read`).
    - Hero image with hover-activated Pinterest Save pill (`📌 Save`).
    - Clean prose typography (`prose prose-stone`).
    - **Key Takeaways Box**: Styled callout (`rounded-xl border border-stone-200 bg-stone-50 p-6`) with bullet points.
    - **Interactive FAQ Accordion**: Expandable `<details>` cards matching the `@type: "FAQPage"` schema.
    - **Rich E-E-A-T Author Card**: 96x96 circular avatar, "Written by" kicker, name linking to author profile, credentials ("Senior Home Decor Editor & Interior Stylist"), and bio.
    - **Related Reading Grid**: 3-column cards with aspect 3:2 photography, category kicker, serif title, clamp excerpt, date, and reading time.
    - **4-Column Trust Footer**: Brand summary, Explore categories, 10 Company & Legal links, and copyright notice.
  - **Homepage Hub Layout (`render_styleire_hub`)**:
    - Large featured cover story (`posts[0]`) with 16:10 photo, category kicker, title, excerpt, and byline.
    - Curated Room Silos grid with 6 rooms and guide counts.
    - Latest Published Guides 3-column grid.
    - Newsletter dispatch banner.
    - Full legal footer with links to all 9 trust pages and HTML sitemap.
- **Dashboard Enhancements**:
  - Step 2 Model 3 updated to **Model 3 · Styleire Magazine** (Editorial & Trust Suite).
  - Step 2 Route Architecture updated with dedicated **pSEO Silo (Styleire)** card and option.
  - Modal Live Preview updated with seamless switching between Styleire Front Hub and Article Guide.

### Visual Verification

````carousel
![Styleire Magazine Homepage Hub](file:///C:/Users/mouni/.gemini/antigravity/brain/c74d76e0-2737-467a-9b30-b696007f0f5f/styleire_modal_hub_preview.png)
<!-- slide -->
![Styleire Magazine Single Article Guide](file:///C:/Users/mouni/.gemini/antigravity/brain/c74d76e0-2737-467a-9b30-b696007f0f5f/styleire_modal_article_preview.png)
````

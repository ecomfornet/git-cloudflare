---
name: stitch
description: >-
  Generate and manage UI designs, frontend code, mobile/desktop screens, design systems,
  and visual variants using Google Stitch (stitch.withgoogle.com). Use this skill when the
  user asks to design interfaces, generate screens from text, modify screens, or via the /stitch slash command.
---

# Google Stitch UI Design & Prototyping Skill

This skill integrates **Google Stitch** (`https://stitch.withgoogle.com`) directly into Antigravity via the **Stitch MCP Server** (`https://stitch.googleapis.com/mcp`).

It allows you to generate complete mobile and desktop UI designs, interactive screens, frontend code, design variations, and design systems from natural language prompts.

---

## When to Use This Skill

- When the user types `/stitch` in the chat.
- When creating, listing, inspecting, or deleting Stitch projects.
- When generating new UI screens for web, tablet, or mobile applications from text prompts.
- When generating design variations or editing existing screen layouts.
- When managing or applying design systems and design tokens (`DESIGN.md`).
- When downloading and integrating generated HTML/CSS/React components into local codebases.

---

## Available Stitch MCP Tools

| Tool | Purpose | Key Arguments |
|---|---|---|
| `list_projects` | Lists all accessible Stitch projects | `filter` (`"view=owned"` or `"view=shared"`) |
| `create_project` | Creates a new Stitch design project | `title` |
| `get_project` | Fetches project metadata and screens | `projectId` |
| `delete_project` | Deletes a Stitch project | `projectId` |
| `generate_screen_from_text` | Generates a new UI screen from a prompt | `projectId`, `prompt`, `deviceType` (`MOBILE`, `DESKTOP`, `TABLET`), `modelId` |
| `get_screen` | Retrieves screen details, layout & code | `projectId`, `screenId` |
| `list_screens` | Lists all screens in a project | `projectId` |
| `edit_screens` | Modifies existing screens with instructions | `projectId`, `edits` |
| `generate_variants` | Creates visual design alternatives | `projectId`, `screenId`, `prompt`, `variantCount` |
| `download_file` | Downloads screen assets and code | `projectId`, `screenId`, `fileType` |
| `list_design_systems` | Lists available design systems | `projectId` |
| `create_design_system` | Creates custom design system tokens | `projectId`, `designSystem` |
| `apply_design_system` | Applies design tokens to screens | `projectId`, `designSystemId`, `screenIds` |
| `upload_design_md` | Uploads a Markdown design system spec | `projectId`, `content` |

---

## Core Workflows

### 1. Generating a New Screen
1. Check existing projects with `list_projects` or create one with `create_project(title="App Name")`.
2. Generate screen:
   ```json
   {
     "projectId": "<project_id>",
     "prompt": "Modern luxury Scandinavian furniture eCommerce product page with sticky bottom buy bar, high-res photography gallery, customer reviews, and minimalist typography.",
     "deviceType": "DESKTOP"
   }
   ```
3. If generation takes time, do not retry immediately. Retrieve the result using `get_screen(projectId=..., screenId=...)`.

### 2. Generating Design Variants
To explore alternative layouts or aesthetics:
```json
{
  "projectId": "<project_id>",
  "screenId": "<screen_id>",
  "prompt": "Dark mode editorial magazine layout with high contrast accents",
  "variantCount": 3
}
```

### 3. Downloading Code & Assets
Retrieve the generated frontend code and assets using `download_file` and place them directly into your workspace.

# Categories, Jekyll, and Entry Specification Reference

Exact inventory of `gh-pages` site files, contribution formatting rules, and the `19` awesome-list categories from commit `ae5cf0a`.

## Repository & Jekyll Files (`gh-pages`)

| File | Role | Configuration / Notes |
| :--- | :--- | :--- |
| `_config.yml` | Jekyll settings | `title: Awesome MySQL`, `markdown: kramdown`, `exclude: ["README.md", "tests/"]` |
| `_layouts/default.html` | HTML page template | Loads relative `css/normalize.css`, `css/syntax.css`, `css/solo.css` |
| `_includes/head.html`, `scripts.html` | Empty extension hooks | Placeholder HTML includes (`0` bytes) |
| `404.html` | Error page | `layout: default`, outputs `Page Not Found.` |
| `index.md` | Jekyll site root | Uses `layout: default`; links `docs/index.md`, `CONTRIBUTING.md`, `LICENSE.md` |
| `README.md` | Repository root overview | Excluded by Jekyll; holds Mermaid diagram, curated highlights, test command |
| `CONTRIBUTING.md` | Contribution rules | Upstream PR guide (`blob/master/index.md` upstream link retained) |
| `LICENSE.md` | Dual license | CC-BY-SA-4.0 for content; MIT for `solo` CSS/layout by Shu Uesugi |

## Entry Format Rules (`CONTRIBUTING.md`)

| Rule | Specification |
| :--- | :--- |
| Entry syntax | `[item](link) - description.` (lowercase description start, single link) |
| Sorting | Alphabetical order under `utf8_general_ci` |
| Software criteria | FSF-recognized open-source license, production-tested, actively maintained |
| Disallowed items | Proprietary software, commercial trials, docs-only pages, slides, videos, single SQL snippets |
| Language | English only |

## Archived Categories Matrix (`ae5cf0a:index.md`)

| Group | Categories |
| :--- | :--- |
| **Software** (`15`) | `Analysis`, `Backup`, `Benchmarking`, `ChatOps`, `Configuration`, `Connectors`, `Deployment`, `Development`, `GUI`, `HA`, `Proxy`, `Replication`, `Schema`, `Security`, `Server`, `Sharding`, `Toolkits` (`17` subsections) |
| **Resources** (`4`) | `Conferences`, `e-books`, `Media`, `Newsletters` |

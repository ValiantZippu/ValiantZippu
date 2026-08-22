# Developer Notes — Terminal Profile System

This repository is a small profile-dashboard system. `README.md` is the
**interface**; the scripts and generated SVGs are the **data layer**.

```text
README.md                              ← public-facing terminal interface (hand-written)
scripts/generate_profile.py            ← fetches live GitHub data, renders SVGs
assets/generated/                      ← machine-written SVG assets (do not hand-edit)
.github/workflows/update-profile.yml   ← daily regeneration + auto-commit
```

## Running the generator locally

Requires Python 3.10+ (stdlib only — no pip installs).

```bash
# Optional but recommended: a token raises the rate limit and unlocks
# commit/PR/issue counts via GraphQL. Any token with public read access works.
export GH_TOKEN=ghp_xxx

python scripts/generate_profile.py
```

The script is **idempotent**: running it twice without upstream data changes
writes nothing (byte-identical output). It prints `[generate] wrote ...` only
for files that actually changed.

Without a token the script still works: repo/star/fork/follower counts come
from the unauthenticated REST API and the contribution calendar falls back to
scraping the public contributions page. Values that cannot be verified are
rendered as `--`. Nothing is ever invented.

## How GitHub Actions updates the profile

`.github/workflows/update-profile.yml` runs daily (and on demand via
*Run workflow*):

1. checks out the repo,
2. runs `scripts/generate_profile.py` with the built-in `GITHUB_TOKEN`,
3. commits any changed files under `assets/generated/` and pushes.

If nothing changed, no commit is made. The workflow needs `contents: write`
permission (already set in the file).

## Generated files

| File | Content |
|---|---|
| `header.svg` | Terminal boot window: identity, status line |
| `about.svg` | `identity.dat` + BUILDING / LEARNING / EXPLORING focus columns (static config) |
| `stats.svg` | One continuous panel: metric tiles + heatmap + weekly activity graph |
| `detailed.svg` | Commits / PRs / issues / total contributions + ranked language bars |
| `repo_<Name>.svg` | One clickable project card per indexed repository |
| `toolkit.svg` | Toolkit inventory (static config) |
| `contact_<label>.svg` | Clickable contact cards (GitHub / Email / Portfolio), linked in the README |
| `footer.svg` | `session.log` closing panel (static config) |
| `label_*.svg` | Thin command-line section labels (static) |

Data sources, in priority order:

- **REST v3** — user profile, repositories, per-repo languages.
- **GraphQL** — `contributionsCollection`: commit/PR/issue counts and the
  contribution calendar.
- **Fallback scrape** — day tooltips from
  `github.com/users/<user>/contributions` when GraphQL is unavailable.

## Adding another repository

Two cases:

1. **Repository already exists on GitHub** — it appears automatically once it
   is among your most recently pushed non-fork repos (up to `MAX_CARDS`).
   Descriptions, language tags, stars and forks are pulled from the API.
   **Note:** the clickable link for each card is hand-written in `README.md` —
   if a repo lives under an organization or has a non-standard URL, update the
   `<a href>` wrapping its card there.

2. **Pin or pre-announce a repository** — add an entry to the `FEATURED` list
   at the top of `scripts/generate_profile.py`:

   ```python
   FEATURED = [
       {"name": "Kaiteyo"},
       {"name": "Isekaiyo", "status": "PLANNED",
        "description": "Interactive fiction platform"},
       {"name": "NewRepo", "tags": ["RUST", "CLI"]},   # optional overrides
   ]
   ```

   Featured entries always render first. A name that has no repository yet
   renders as a dimmed `[ PLANNED ]` card linking to the future URL.

Then re-run the generator locally or let the workflow pick it up within a day.

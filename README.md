# AWS CLF-C02 Prep

Study notes for the **AWS Certified Cloud Practitioner (CLF-C02)** exam, organized by exam domain.

## Domains

| # | Domain | Notes |
|---|--------|-------|
| 1 | Cloud Concepts | 24 |
| 2 | Global Infrastructure | 10 |
| 3 | Billing, Pricing & Support | 37 |
| 4 | AWS Services | 161 |

## Website

A static site is generated from Markdown source files using `build.py`. The built site is served from the repo root.

### Build

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 build.py
```

### Serve locally

```bash
python3 -m http.server 8000
```

## Source

Notes are written in Markdown with YAML frontmatter under `1_Concepts/`, `2_Global_Infrastructure/`, `3_Billing_And_Support/`, and `4_Services/`.

The build script converts wikilinks (`[[Page Name]]`), highlights (`==text==`), and embeds AWS service icons on matching pages.

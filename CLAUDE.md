# MetLife Pet Insurance Plugin

Claude Code plugin for interacting with MetLife Pet Insurance claims API and drafting claim appeals.

## Setup

Set your bearer token (get it from browser DevTools on mypets.metlife.com):
```bash
export METLIFE_BEARER_TOKEN="<your token>"
```

## Skills

### `/metlife-pets` — API Interaction
Query the MetLife Pet Insurance API:
- `/metlife-pets list claims for policy 3508770 pet 1536515`
- `/metlife-pets get claim 3357541 for pet 1`
- `/metlife-pets list documents for claim 3357541 policy 3508770 pet 1536515`
- `/metlife-pets get policy packet for policy 3508770`

### `/appeal-claim` — Claim Appeal Drafting
Gathers evidence, analyzes EOBs against policy terms, and drafts a formal appeal letter:
- `/appeal-claim policy 3508770 pet 1536515 claim 3357541`

Workflow: fetch claim + EOBs + policy → analyze denial reasons → cross-reference policy → draft appeal letter with cited policy sections.

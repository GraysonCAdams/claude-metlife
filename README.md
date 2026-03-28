# metlife-pet-insurance

A [Claude Code plugin](https://github.com/anthropics/claude-plugins-official) for interacting with the MetLife Pet Insurance claims API and drafting formal claim appeals.

## Features

- **`/metlife-pets`** — Query claims, download EOBs, fetch policy documents
- **`/appeal-claim`** — Automated appeal workflow: gathers all evidence, analyzes denial reasons against your policy, and drafts a formal appeal letter

## Installation

```bash
claude plugin add GraysonCAdams/claude-metlife
```

## Setup

You need a bearer token from your authenticated mypets.metlife.com session:

1. Log in to [mypets.metlife.com](https://mypets.metlife.com)
2. Open browser DevTools → Network tab
3. Copy the `authorization: Bearer ...` header from any API request
4. Set it in your shell:

```bash
export METLIFE_BEARER_TOKEN="<your token>"
```

> Tokens expire periodically. If you get 401 errors, grab a fresh one.

## Usage

### Query the API

```
/metlife-pets list claims for policy 3508770 pet 1536515
/metlife-pets get claim 3357541 for pet 1
/metlife-pets list documents for claim 3357541 policy 3508770 pet 1536515
/metlife-pets get policy packet for policy 3508770
```

### Appeal a Denied Claim

```
/appeal-claim policy 3508770 pet 1536515 claim 3357541
```

The appeal skill will:
1. Fetch claim details, claims history, all EOB documents, and your policy packet
2. Read and analyze every document
3. Identify the denial/underpayment basis from the EOB
4. Cross-reference against your actual policy terms
5. Draft a formal appeal letter citing specific policy sections
6. Flag the 90-day appeal deadline and recommend attachments

## No Secrets

This repo contains no tokens, credentials, or personal data. The bearer token is read from the `METLIFE_BEARER_TOKEN` environment variable at runtime.

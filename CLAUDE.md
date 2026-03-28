# MetLife Pet Insurance CLI Tool

Custom slash command for interacting with MetLife Pet Insurance claims API via Claude Code.

## Setup

Set your bearer token (get it from browser DevTools on mypets.metlife.com):
```bash
export METLIFE_BEARER_TOKEN="<your token>"
```

## Usage

Run `/metlife-pets` followed by what you want to do:
- `/metlife-pets list claims for policy 3508770 pet 1536515`
- `/metlife-pets get claim 3357541 for pet 1`
- `/metlife-pets list documents for claim 3357541 policy 3508770 pet 1536515`
- `/metlife-pets download document <filePath> from claim 3357541 policy 3508770 pet 1536515`

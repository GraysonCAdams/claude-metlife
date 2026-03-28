---
name: metlife-pets
description: This skill should be used when the user asks to query MetLife Pet Insurance, check pet insurance claims, list claims, get claim details, download EOBs, download policy documents, or interact with the mypets.metlife.com API.
argument-hint: "<action> [policy <policyId>] [pet <petId>] [claim <claimId>]"
---

# MetLife Pet Insurance API

You are a helper for interacting with the MetLife Pet Insurance API. Use the bearer token from the environment variable `METLIFE_BEARER_TOKEN`.

## Configuration

- **Claims Base URL:** `https://api.metlife.com/metlife/production/api/pet-services/pingv2/cl/v1`
- **Policy Base URL:** `https://api.metlife.com/metlife/production/api/pet-services/pingv2/p/v1`
- **Required Headers** (include on every request):
  ```
  authorization: Bearer $METLIFE_BEARER_TOKEN
  x-ibm-client-id: 634dc387-c737-4a6a-86ef-f49056e30898
  x-app-version: 4.5.1
  origin: https://mypets.metlife.com
  referer: https://mypets.metlife.com/
  accept: */*
  cache-control: no-cache, no-store
  ```

## Available Endpoints

### 1. List All Claims
```
GET {Claims Base}/claim/all?petId={petId}&policyId={policyId}
```
Lists all claims for a given pet and policy. Both `petId` and `policyId` are required.

### 2. Get Claim Details
```
GET {Claims Base}/claim/{claimSourceId}/{claimId}
```
Gets detailed information about a specific claim. **Important:** The first path parameter is `claimSourceId` (typically `1`), NOT the `petId`. The `claimSourceId` comes from the claim list response.

### 3. List Claim Documents
```
GET {Claims Base}/document-details?policyId={policyId}&claimId={claimId}&petId={petId}
```
Lists all documents (EOBs, etc.) associated with a specific claim.

### 4. Download Document (Submitted Docs: invoices, SOAP notes, etc.)
```
GET {Claims Base}/document-details?policyId={policyId}&claimId={claimId}&petId={petId}&isBlobRequest=true&filePath={filePath}&claimDocumentType=2
```
Downloads submitted documents (invoices, SOAP notes, misc files). The `filePath` comes from the `docDetails` array in the document list response. Use `claimDocumentType=2` for submitted documents.

**Important:** The response JSON will contain the file as a base64-encoded string. You must decode it and save it. Example:
```bash
# Pipe the API response through jq to extract the base64 data, then decode
curl -s '...' | python3 -c "import sys,json,base64; data=json.load(sys.stdin); [open('output.pdf','wb').write(base64.b64decode(d['document'])) for d in (data.get('model',{}).get('docDetails',None) or []) if d.get('document')]"
```

### 4b. Download EOB
```
GET {Claims Base}/document-details?policyId={policyId}&claimId={claimId}&petId={petId}&isBlobRequest=true&filePath={filePath}&claimDocumentType=1
```
Downloads the Explanation of Benefits. The `filePath` comes from the `eobDetails` array in the document list response (the `eobFilePath` field). Use `claimDocumentType=1` for EOBs.

**Important:** The EOB PDF is returned as a base64-encoded string in the `eobDocument` field of the first item in `eobDetails`. Decode and save it:
```bash
curl -s '...' | python3 -c "import sys,json,base64; data=json.load(sys.stdin); eob=data.get('model',{}).get('eobDetails',None); [open('eob.pdf','wb').write(base64.b64decode(e['eobDocument'])) for e in (eob or []) if e.get('eobDocument')]"
```

### 5. Get Policy Packet
```
GET {Policy Base}/policy/{policyId}/policyPacket
```
Downloads the full policy document/packet PDF for a given policy.

## Local Cache

All API responses and downloaded documents are cached in `.metlife-cache/` in the working directory. This prevents redundant API calls across conversations.

### Cache structure:
```
.metlife-cache/
├── claims/
│   ├── {policyId}_{petId}_all.json          # All claims list
│   └── {petId}_{claimId}.json               # Individual claim details
├── documents/
│   ├── {policyId}_{claimId}_{petId}_list.json  # Document list
│   └── {policyId}_{claimId}_{petId}/           # Downloaded files
│       └── {filename}.pdf
└── policies/
    └── {policyId}_packet.pdf                # Policy packet
```

### Cache rules:
1. **Before any API call**, check if the cached file exists. If it does, read from cache instead.
2. **After any successful API call**, write the response to the cache location.
3. **For JSON responses**, save the raw JSON.
4. **For PDF/binary downloads**, save the file directly.
5. To force a refresh, the user can say "refresh" or "re-fetch" and you should bypass the cache for that request and overwrite the cached file.
6. **Create the directories** as needed using `mkdir -p`.

## Instructions

1. **Always check** that `METLIFE_BEARER_TOKEN` is set before making requests. If not set, tell the user: `export METLIFE_BEARER_TOKEN="<token from mypets.metlife.com DevTools>"`
2. **Check cache first** before making any API call. Read from `.metlife-cache/` if the file exists.
3. **Use curl** via the Bash tool to make API calls with all required headers. Cache every response.
4. **Parse JSON responses** and present data in a readable format (tables, summaries).
5. **For document/PDF downloads**, save to the cache directory and tell the user the path.
6. If a request returns 401, tell the user their token has expired and they need a new one from the mypets.metlife.com browser session.

### curl template:
```bash
curl -s 'https://api.metlife.com/metlife/production/api/pet-services/pingv2/cl/v1/{endpoint}' \
  -H 'accept: */*' \
  -H "authorization: Bearer $METLIFE_BEARER_TOKEN" \
  -H 'cache-control: no-cache, no-store' \
  -H 'origin: https://mypets.metlife.com' \
  -H 'referer: https://mypets.metlife.com/' \
  -H 'x-app-version: 4.5.1' \
  -H 'x-ibm-client-id: 634dc387-c737-4a6a-86ef-f49056e30898'
```

## First-Run Sync

When the user first starts a conversation and provides their policy ID and pet ID(s), or when the user says "sync" or "fetch everything", run a full sync:

1. **Fetch all claims** for each pet/policy combo. Cache the response.
2. **For each claim**, fetch claim details. Cache each one.
3. **For each claim**, fetch the document list. Cache it.
4. **Download every document** (EOBs, etc.) from every claim. Cache them all.
5. **Download the policy packet**. Cache it.
6. Run all independent fetches in parallel where possible.
7. Tell the user what was fetched and cached when done.

After sync, all future reads come from cache. No more API calls unless the user asks to refresh.

$ARGUMENTS

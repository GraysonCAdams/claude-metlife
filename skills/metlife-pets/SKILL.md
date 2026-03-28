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

## Token Refresh

The bearer token expires quickly (minutes). Use the refresh token mechanism to keep the session alive automatically.

**Environment variables:**
- `METLIFE_BEARER_TOKEN` — the current access token (set by user initially, then auto-refreshed)
- `METLIFE_REFRESH_TOKEN` — the refresh token (set by user initially)

### Refresh endpoint
```
POST https://apis.metlife.com/external/pet-services/authentication/v2/refreshToken_v2
```

### Refresh headers
**Important:** The refresh endpoint requires `session-id` and `transaction-id` headers. Generate a timestamp-based ID.
```
accept: */*
cache-control: no-cache, no-store
channel-id: PetMobile
content-type: application/json
is-ping-token: true
ocp-apim-subscription-key: 979fd0c2ea204f1095d7faa8154c39b0
origin: https://mypets.metlife.com
referer: https://mypets.metlife.com/
session-id: {timestamp}cls
transaction-id: {timestamp}cls
x-app-version: 4.5.1
```

### Refresh body
Send the refresh token as a JSON string (quoted):
```bash
SESSION_ID="$(date +%s%3N)cls"
RESPONSE=$(curl -s 'https://apis.metlife.com/external/pet-services/authentication/v2/refreshToken_v2' \
  -H 'accept: */*' \
  -H 'cache-control: no-cache, no-store' \
  -H 'channel-id: PetMobile' \
  -H 'content-type: application/json' \
  -H 'is-ping-token: true' \
  -H 'ocp-apim-subscription-key: 979fd0c2ea204f1095d7faa8154c39b0' \
  -H 'origin: https://mypets.metlife.com' \
  -H 'referer: https://mypets.metlife.com/' \
  -H "session-id: $SESSION_ID" \
  -H "transaction-id: $SESSION_ID" \
  -H 'x-app-version: 4.5.1' \
  --data-raw "\"$METLIFE_REFRESH_TOKEN\"")
```

The response contains `access_token` and a new `refresh_token`. Update BOTH env vars:
```bash
export METLIFE_BEARER_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
NEW_REFRESH=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('refresh_token',''))" 2>/dev/null)
[ -n "$NEW_REFRESH" ] && export METLIFE_REFRESH_TOKEN="$NEW_REFRESH"
```

### Auto-refresh on 401
**Before starting any multi-step operation** (like a full sync), proactively refresh the token to avoid mid-operation expiry. When any API call returns a 401 response (`"Token is not active"` or `"Unauthorized"`):
1. Call the refresh endpoint to get a new access token
2. Update `METLIFE_BEARER_TOKEN` with the new token
3. Retry the failed request
4. If refresh also fails, tell the user to provide fresh tokens

### Helper script
At the start of any session that will make API calls, create a helper script at `.metlife-cache/refresh.sh` that other commands can source:
```bash
#!/bin/bash
refresh_token() {
  local SESSION_ID="$(date +%s%3N)cls"
  local RESPONSE
  RESPONSE=$(curl -s 'https://apis.metlife.com/external/pet-services/authentication/v2/refreshToken_v2' \
    -H 'accept: */*' \
    -H 'cache-control: no-cache, no-store' \
    -H 'channel-id: PetMobile' \
    -H 'content-type: application/json' \
    -H 'is-ping-token: true' \
    -H 'ocp-apim-subscription-key: 979fd0c2ea204f1095d7faa8154c39b0' \
    -H 'origin: https://mypets.metlife.com' \
    -H 'referer: https://mypets.metlife.com/' \
    -H "session-id: $SESSION_ID" \
    -H "transaction-id: $SESSION_ID" \
    -H 'x-app-version: 4.5.1' \
    --data-raw "\"$METLIFE_REFRESH_TOKEN\"" 2>/dev/null)
  local NEW_TOKEN
  NEW_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
  local NEW_REFRESH
  NEW_REFRESH=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('refresh_token',''))" 2>/dev/null)
  if [ -n "$NEW_TOKEN" ] && [ "$NEW_TOKEN" != "None" ]; then
    export METLIFE_BEARER_TOKEN="$NEW_TOKEN"
    [ -n "$NEW_REFRESH" ] && export METLIFE_REFRESH_TOKEN="$NEW_REFRESH"
    echo "Token refreshed successfully"
    return 0
  else
    echo "Token refresh failed"
    return 1
  fi
}

metlife_api() {
  local RESPONSE
  RESPONSE=$(curl -s "$@" \
    -H 'accept: */*' \
    -H "authorization: Bearer $METLIFE_BEARER_TOKEN" \
    -H 'cache-control: no-cache, no-store' \
    -H 'origin: https://mypets.metlife.com' \
    -H 'referer: https://mypets.metlife.com/' \
    -H 'x-app-version: 4.5.1' \
    -H 'x-ibm-client-id: 634dc387-c737-4a6a-86ef-f49056e30898')
  if echo "$RESPONSE" | grep -q '"401"\|"Unauthorized"\|"Token is not active"'; then
    refresh_token && RESPONSE=$(curl -s "$@" \
      -H 'accept: */*' \
      -H "authorization: Bearer $METLIFE_BEARER_TOKEN" \
      -H 'cache-control: no-cache, no-store' \
      -H 'origin: https://mypets.metlife.com' \
      -H 'referer: https://mypets.metlife.com/' \
      -H 'x-app-version: 4.5.1' \
      -H 'x-ibm-client-id: 634dc387-c737-4a6a-86ef-f49056e30898')
  fi
  echo "$RESPONSE"
}
```

## Instructions

1. **Always check** that `METLIFE_BEARER_TOKEN` and `METLIFE_REFRESH_TOKEN` are set before making requests. If not set, tell the user:
   - `export METLIFE_BEARER_TOKEN="<token from mypets.metlife.com DevTools>"` (the `authorization` Bearer token from any API request)
   - `export METLIFE_REFRESH_TOKEN="<refresh token>"` (from the refreshToken_v2 request body in DevTools)
2. **Proactively refresh the token** before starting any multi-step operation (sync, appeal analysis, etc.) to minimize mid-operation failures.
3. **Check cache first** before making any API call. Read from `.metlife-cache/` if the file exists.
4. **Use curl** via the Bash tool to make API calls with all required headers. Cache every response.
5. **Parse JSON responses** and present data in a readable format (tables, summaries).
6. **For document/PDF downloads**, save to the cache directory and tell the user the path.
7. **On 401 responses**, automatically refresh the token and retry. If refresh fails, tell the user their session has expired and they need to log in again at mypets.metlife.com and provide fresh tokens.

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

---
name: metlife-pets
description: This skill should be used when the user asks to query MetLife Pet Insurance, check pet insurance claims, list claims, get claim details, download EOBs, download policy documents, or interact with the mypets.metlife.com API.
argument-hint: <action> [policy <policyId>] [pet <petId>] [claim <claimId>]
allowed-tools: [Bash, Read, Glob, Write]
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
GET {Claims Base}/claim/{petId}/{claimId}
```
Gets detailed information about a specific claim.

### 3. List Claim Documents
```
GET {Claims Base}/document-details?policyId={policyId}&claimId={claimId}&petId={petId}
```
Lists all documents (EOBs, etc.) associated with a specific claim.

### 4. Download Document
```
GET {Claims Base}/document-details?policyId={policyId}&claimId={claimId}&petId={petId}&isBlobRequest=true&filePath={filePath}&claimDocumentType={claimDocumentType}
```
Downloads the actual document file (PDF, etc). The `filePath` and `claimDocumentType` values come from the document list response.

### 5. Get Policy Packet
```
GET {Policy Base}/policy/{policyId}/policyPacket
```
Downloads the full policy document/packet PDF for a given policy.

## Instructions

1. **Always check** that `METLIFE_BEARER_TOKEN` is set before making requests. If not set, tell the user: `export METLIFE_BEARER_TOKEN="<token from mypets.metlife.com DevTools>"`
2. **Use curl** via the Bash tool to make API calls with all required headers.
3. **Parse JSON responses** and present data in a readable format (tables, summaries).
4. **For document/PDF downloads**, save the file to the current directory and tell the user the path.
5. If a request returns 401, tell the user their token has expired and they need a new one from the mypets.metlife.com browser session.

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

$ARGUMENTS

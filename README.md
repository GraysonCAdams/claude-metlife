# MetLife Pet Insurance Plugin for Claude Code

A [Claude Code plugin](https://github.com/anthropics/claude-plugins-official) that lets you query the MetLife Pet Insurance claims API and build evidence-based appeals for denied or underpaid claims.

## What It Does

### `/metlife-pets` - API Access
Query your MetLife pet insurance account directly from Claude:
- List all claims for a pet/policy
- Get detailed claim information
- List and download EOB documents
- Download your full policy packet

### `/appeal-claim` - Adversarial Claim Appeal
A rigorous appeal workflow that does real underwriting analysis before writing anything. It will **refuse to draft a losing appeal** and tell you honestly when a denial is correct.

**How it works:**

1. Fetches your claim details, EOBs, claims history, and policy packet
2. Reads every document and extracts denial reasons, amounts, dates
3. Cross-references the denial against your actual policy terms
4. Runs a **3-agent adversarial simulation**:
   - **Policyholder Advocate** builds the strongest case for appeal
   - **MetLife Claims Reviewer** defends the denial using policy language
   - **Independent Judge** evaluates both sides neutrally
5. Only drafts a letter if the case survives adversarial review
6. Produces a plain-English appeal letter (not AI-sounding, not legalistic)
7. Includes submission instructions, deadlines, and recommended attachments

The appeal letter follows MetLife's required format: your name, pet's name, claim identification, and explanation with supporting evidence. It cites specific policy sections and does the reimbursement math.

## Installation

```bash
claude plugin add GraysonCAdams/claude-metlife
```

## Setup

You need a bearer token from your authenticated mypets.metlife.com session:

1. Log in to [mypets.metlife.com](https://mypets.metlife.com)
2. Open browser DevTools (F12) and go to the Network tab
3. Click around in the app, then find any API request to `api.metlife.com`
4. Copy the value from the `authorization: Bearer ...` header
5. Set it in your environment:

```bash
export METLIFE_BEARER_TOKEN="<your token>"
```

Tokens expire periodically. If you get 401 errors, grab a fresh one.

## Usage

Once installed, just open a conversation and talk normally. No commands needed. Examples:

- "Hey, can you check on my claims?"
- "My claim for Peaches got denied, what happened?"
- "Can you look into whether I should appeal this?"
- "What does my policy cover for diagnostics?"
- "Pull up the EOB for claim 3357541"

The plugin understands the context and will ask for any IDs it needs (policy, pet, claim). It will walk you through everything conversationally.

### Slash commands (optional)

If you prefer explicit commands, these are also available:

```
/metlife-pets list claims for policy <policyId> pet <petId>
/metlife-pets get claim <claimId> for pet <petId>
/metlife-pets list documents for claim <claimId> policy <policyId> pet <petId>
/metlife-pets get policy packet for policy <policyId>
/appeal-claim policy <policyId> pet <petId> claim <claimId>
```

## How the Appeal Process Works

Per MetLife policy (PET21-01-V):

- You have **90 days** from the claim decision to submit a written appeal
- MetLife acknowledges receipt within **5 business days**
- Final decision within **45 days** (extendable if they need more info)
- If denied on first appeal, you can request an **external review within 30 days** by an independent veterinarian
- External review decision comes within **10 days**

The plugin knows all of this and will flag deadlines for you.

## No Secrets

This repo contains no tokens, credentials, or personal data. The bearer token is read from the `METLIFE_BEARER_TOKEN` environment variable at runtime. Source curl captures with tokens are gitignored.

## License

MIT

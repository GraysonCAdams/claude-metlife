---
name: appeal-claim
description: This skill should be used when the user asks to appeal a MetLife pet insurance claim, dispute a denial, challenge an underpayment, draft an appeal letter, review an EOB for appeal grounds, or fight a pet insurance claim decision.
argument-hint: [policy <policyId>] [pet <petId>] [claim <claimId>]
allowed-tools: [Bash, Read, Glob, Write, Agent]
---

# MetLife Pet Insurance Claim Appeal

You are an expert assistant for drafting appeals of denied or underpaid MetLife pet insurance claims. You gather all evidence from the API, analyze denial reasons against policy terms, and draft a formal written appeal.

## Appeals Process (from MetLife Policy PET21-01-V)

Per the policy language, the appeals process works as follows:

### First-Level Appeal
- Must be submitted **in Writing within 90 days** after receiving the initial claim determination.
- Submit to the **address indicated on the claim form**.
- The appeal **must include**:
  1. Your name
  2. The name of your pet
  3. Identification of the claim denial you are appealing
  4. An explanation of why you believe the denial was incorrect
- You may also submit written comments, documents, records, or other information relating to the claim.
- MetLife will **acknowledge receipt within 5 business days**.
- MetLife will provide a **final decision within 45 days** of receiving the written appeal.
- If MetLife needs more information, they may take up to an **extra 45 days**. The clock pauses while they wait for your response.
- **You must respond to info requests within 45 days** or the appeal will be denied.
- If denied on appeal, MetLife will send a final written decision stating the reason and referencing specific policy provisions.
- You may request, at no charge, copies of all documents, records, and information relevant to your claim.

### External Review (Second Level)
- If you disagree with the first appeal decision, you may request an **external review within 30 days** of the first appeal decision date.
- An **impartial Veterinarian** (independent of MetLife and not part of your pet's vet team) will conduct the review.
- MetLife will provide the external review decision **within 10 days** of receiving the independent veterinarian's report.

### Complaints
- To complain to MetLife directly: **Metropolitan General Insurance Company, 700 Quaker Lane, Warwick, RI 02886**
- You may also file a complaint with your state's Department of Insurance.

### Key Policy Definitions Relevant to Appeals
- **Pre-Existing Condition**: Prior to Continuous Coverage start (or during a Waiting Period), a vet provided medical advice, the pet received diagnosis/care/treatment, or the pet displayed signs or symptoms consistent with the illness or injury.
- **Medically Necessary**: Consistent with symptoms/diagnosis, accepted as good veterinary practice standards, not for convenience, and consistent with proper level of services that can be safely provided.
- **Covered Charge**: Charges for services described in "What We Cover" incurred while the pet is insured.
- **Written/Writing**: A record on or transmitted by paper or electronic media acceptable to MetLife and consistent with applicable law.

## API Configuration

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
- If any call returns 401, stop and tell the user to refresh their token.

### curl template:
```bash
curl -s '{BASE_URL}/{endpoint}' \
  -H 'accept: */*' \
  -H "authorization: Bearer $METLIFE_BEARER_TOKEN" \
  -H 'cache-control: no-cache, no-store' \
  -H 'origin: https://mypets.metlife.com' \
  -H 'referer: https://mypets.metlife.com/' \
  -H 'x-app-version: 4.5.1' \
  -H 'x-ibm-client-id: 634dc387-c737-4a6a-86ef-f49056e30898'
```

## Appeal Workflow

Follow these steps **in order** when the user asks to appeal a claim.

### Step 1: Gather All Evidence

Ask the user for `policyId`, `petId`, and `claimId` if not provided. Then fetch all of the following — run independent calls in parallel:

1. **Claim details** — `GET {Claims Base}/claim/{petId}/{claimId}`
2. **Full claims history** — `GET {Claims Base}/claim/all?petId={petId}&policyId={policyId}`
3. **Claim documents (EOBs)** — `GET {Claims Base}/document-details?policyId={policyId}&claimId={claimId}&petId={petId}`
4. **Policy packet** — `GET {Policy Base}/policy/{policyId}/policyPacket`

### Step 2: Download and Read Every Document

1. From the document list response, download **each EOB** using `isBlobRequest=true&filePath={filePath}&claimDocumentType={claimDocumentType}`. Save as PDFs locally.
2. Save the policy packet PDF locally.
3. **Read every downloaded PDF** using the Read tool. Do not skip any. A missed detail could be the key to the appeal.

### Step 3: Extract Denial / Underpayment Details

From the EOB(s), extract and record:
- Denial codes / reason codes and their descriptions
- Amounts: billed, allowed, paid, and member responsibility
- Service dates and procedure descriptions
- Any specific exclusions, limitations, or conditions cited as the basis

### Step 4: Cross-Reference Against the Policy

From the policy packet, find and analyze:
- **Coverage terms** for the denied services — is this type of treatment covered?
- **Exclusions and limitations** — does the cited exclusion actually apply to this situation?
- **Waiting periods** — have they been satisfied based on policy effective date vs. date of service?
- **Benefit schedule** — verify the reimbursement percentage, deductible, and annual limit calculations
- **Pre-existing condition definition** — if cited, does the condition actually meet the policy's definition?
- **Appeals section** — confirm the deadline, process, and where to send it

### Step 5: Build the Appeal Argument

Identify the strongest argument(s) by analyzing the gap between the denial reason and actual policy terms:

| Argument Type | When to Use |
|---|---|
| **Misapplied exclusion** | The exclusion cited doesn't match the actual condition or treatment |
| **Pre-existing condition dispute** | Condition developed after policy effective date + waiting period; build a timeline |
| **Medical necessity** | Treatment was standard veterinary care for the diagnosis |
| **Calculation error** | Reimbursement math doesn't match the benefit schedule (wrong %, deductible, limit) |
| **Coding error** | Wrong diagnosis or procedure code was applied to the claim |
| **Waiting period satisfied** | Condition first presented after all applicable waiting periods elapsed |
| **Continuation of covered condition** | A previously approved condition was suddenly excluded on a follow-up claim |

Be honest: if the denial appears valid after thorough analysis, tell the user and explain why.

### Step 6: Draft the Appeal Letter

Write a formal appeal letter. Per policy, it **must** include: (1) your name, (2) your pet's name, (3) identification of the claim denial being appealed, and (4) an explanation of why you believe the denial was incorrect. You may also include written comments, documents, records, or other supporting information. Use this structure:

---

**[Today's Date]**

MetLife Pet Insurance / Metropolitan General Insurance Company
[Address from the claim form — check the EOB or claim form for the correct mailing address]

**Re: Formal Appeal of Claim [Claim ID]**
Policy Number: [Policy ID]
Pet Name: [from claim data]
Date(s) of Service: [from EOB]

Dear MetLife Pet Insurance Appeals Department,

I am writing to formally appeal the [denial/underpayment] of Claim [ID], as detailed in the Explanation of Benefits dated [EOB date]. This appeal is submitted within the 90-day appeal window.

**Summary of Claim**
[Brief factual summary: the visit, diagnosis, treatment performed, and amount billed.]

**Basis for the Claim Decision**
[Quote the exact denial/reduction reason from the EOB — code and description.]

**Why This Decision Is Incorrect**
[Systematically address the denial reason. Cite specific policy sections by name/number/page. Include dates, amounts, and facts that contradict the denial basis. This is the core of the appeal — be thorough and specific.]

**Supporting Policy Language**
[Direct quotes from the policy packet that support coverage, with section references. If the exclusion was misapplied, quote both the exclusion AND the coverage term to show the conflict.]

**Timeline of Events** *(if applicable — especially for pre-existing condition disputes)*
[Chronological list: policy effective date → waiting period end → first symptom → diagnosis → treatment. Show that the condition is not pre-existing per the policy definition.]

**Requested Resolution**
[State exactly what you're asking for: full reimbursement of $X, recalculation per benefit schedule, etc. Show the math if relevant.]

I respectfully request a full review of this claim and reversal of the [denial/underpayment]. I have included [list any attached documents] for your reference. Please contact me if additional information is needed.

Sincerely,
[Policyholder Name]
[Phone / Email]

---

### Step 7: Present to the User

1. **Findings summary**: what was denied, why, and the strength of the appeal argument
2. **The full draft letter** — save it as `appeal-claim-{claimId}.md` and display it
3. **Appeal deadline**: calculate the 90-day deadline from the EOB date and flag if it's approaching
4. **Recommended attachments**: list documents the user should gather (vet records, invoices, prior approval letters, etc.)
5. **How to submit**: provide the following instructions:

---

**How to Submit Your Appeal:**

1. **Find the submission address** on your claim form or EOB. The policy states the appeal must be sent to "the address indicated on the claim form."
2. **Submit in Writing** — per policy, "Written" means paper or electronic media acceptable to MetLife. Options:
   - **Mail** to the address on the claim form
   - **Call 866-937-7387** to confirm electronic submission options
3. **Include with your letter:**
   - The appeal letter itself (all 4 required elements: your name, pet name, claim ID, explanation)
   - Copies of relevant vet records and itemized invoices
   - Any additional supporting documents referenced in your letter
4. **Keep copies** of everything you send.
5. **Expect acknowledgment** within 5 business days of receipt.
6. **Expect a decision** within 45 days (may be extended if they request more info — you'll have 45 days to respond).
7. **If denied again**, you have **30 days** from the appeal decision to request an **external review** by an independent veterinarian. MetLife will provide the external review decision within 10 days.
8. **To file a complaint** with MetLife directly: Metropolitan General Insurance Company, 700 Quaker Lane, Warwick, RI 02886. You may also contact your state's Department of Insurance.

---

$ARGUMENTS

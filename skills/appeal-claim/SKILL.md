---
name: appeal-claim
description: This skill should be used when the user asks to appeal a MetLife pet insurance claim, dispute a denial, challenge an underpayment, draft an appeal letter, review an EOB for appeal grounds, or fight a pet insurance claim decision.
argument-hint: [policy <policyId>] [pet <petId>] [claim <claimId>]
allowed-tools: [Bash, Read, Glob, Write, Agent]
---

# MetLife Pet Insurance Claim Appeal

You are an expert assistant for evaluating and, when warranted, drafting appeals of denied or underpaid MetLife pet insurance claims. Your primary job is honest analysis. You are NOT an automatic appeal generator. You must do real underwriting work first and only draft an appeal if the evidence actually supports one.

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

### Step 5b: Adversarial Simulation — DO NOT SKIP

**This step is mandatory. You must complete it before deciding whether to draft a letter.**

After Steps 3-5, you have the denial details, the policy language, and candidate arguments. Now you must stress-test the case by running an adversarial simulation using three background agents. Launch all three in parallel using the Agent tool.

**Prepare a briefing document** before launching agents. Write it to a temp file (e.g., `appeal-briefing-{claimId}.tmp.md`) containing:
- The denial reason (exact text from EOB)
- The candidate appeal arguments from Step 5
- All relevant policy sections (quoted verbatim with section names/page numbers)
- Key dates: policy effective date, waiting period end, date of service, date of first symptoms
- Dollar amounts: billed, allowed, paid, member responsibility
- Any other facts from the claim data and vet records

Then launch these three agents **in parallel**, each given the briefing file to read:

---

**Agent 1: Policyholder Advocate**

```
You represent the policyholder appealing a denied pet insurance claim. Read the briefing file at [path]. Your job is to build the strongest possible case for why the denial is wrong. Argue from the policy language. Find every angle. Be specific, cite sections, quote the policy. If an argument is weak, say so, but still present it. Write your argument as a structured brief with each point numbered. End with your honest confidence level (0-100%) that this appeal would succeed.
```

**Agent 2: MetLife Claims Reviewer**

```
You are a MetLife pet insurance claims reviewer defending the denial of a claim. Read the briefing file at [path]. Your job is to argue why the denial is correct and should be upheld on appeal. Use the policy language to support the denial. Anticipate every argument the policyholder might make and explain why each one fails. Be thorough. Look for pre-existing condition evidence, exclusion applicability, waiting period issues, and any policy language that supports the original decision. If you find any argument from the policyholder that you genuinely cannot counter, admit it. Write your defense as a structured brief with each point numbered. End with your honest confidence level (0-100%) that MetLife would successfully defend this denial.
```

**Agent 3: Independent Review Judge**

```
You are a neutral insurance dispute mediator evaluating a pet insurance claim appeal. Read the briefing file at [path]. Your job is to evaluate the case from both sides without bias. For each potential argument, assess: (a) does the policy language clearly support the policyholder or the insurer? (b) is the language ambiguous? (c) what would a reasonable reading conclude? Consider regulatory norms: in insurance disputes, ambiguous policy language is typically construed in favor of the insured. Write your assessment as a structured evaluation of each argument. End with:
- Overall ruling: "Appeal should succeed" / "Appeal should fail" / "Could go either way"
- Confidence: 0-100%
- Key vulnerability for each side (what could sink their case)
```

---

**After all three agents return**, synthesize their findings:

1. Read all three briefs carefully.
2. Identify where the Advocate and Reviewer agree (these are settled points, don't waste time on them).
3. Focus on where they disagree. The Judge's assessment of these disputed points is the tiebreaker.
4. Note any argument the MetLife Reviewer could not counter (these are your strongest appeal points).
5. Note any argument the Advocate admitted was weak (drop these or deprioritize them).

**Then make the final determination.** Rate the appeal as:

- **Strong**: The Advocate wins on the core arguments, the Reviewer has no strong counter, and the Judge sides with the policyholder. Proceed to draft.
- **Moderate**: The Advocate has solid arguments on some points but the Reviewer lands real hits on others. The Judge says it could go either way or leans policyholder. Proceed to draft, but be transparent about vulnerabilities.
- **Weak**: The Reviewer's defense is mostly sound but there's one angle worth trying. Tell the user honestly: "This is a long shot. Here's the one argument that has some merit, and here's what MetLife will say back."
- **Not viable**: The Reviewer wins. The policy supports the denial. The Judge agrees. **Do not draft an appeal letter.**

**When the assessment is Weak or Not viable, you must:**
1. Tell the user directly: "I ran this through adversarial review and I don't think this appeal will succeed. Here's why."
2. Show the user the key points from the MetLife Reviewer's brief that are hard to counter.
3. Quote the specific policy language that works against them.
4. If there's any angle at all (even a long shot), mention it, but be honest about the odds.
5. Do NOT draft an appeal letter just because the user asked. A losing appeal wastes their time and the 90-day window. Being honest now is more valuable.
6. If the user still insists after seeing the analysis, you can draft one, but include a private disclaimer (not in the letter) about expected outcome and which arguments MetLife will use to deny it again.

**When the assessment is Strong or Moderate:**
Proceed to Step 6. Incorporate the strongest arguments identified by the simulation. Avoid or minimize arguments the MetLife Reviewer successfully countered. In the findings summary (Step 7), include the key vulnerabilities identified by the Judge.

Clean up the temp briefing file after the simulation completes.

### Step 6: Draft the Appeal Letter (only if assessment is Strong or Moderate)

Write a formal appeal letter. Per policy, it **must** include: (1) your name, (2) your pet's name, (3) identification of the claim denial being appealed, and (4) an explanation of why you believe the denial was incorrect. You may also include written comments, documents, records, or other supporting information.

#### Writing Tone and Style Rules

The letter must read like a real person wrote it — a pet owner who is frustrated but composed. Follow these rules strictly:

**DO NOT:**
- Use em dashes (—). Use commas, periods, or "and" instead.
- Use emojis anywhere in the letter.
- Use filler phrases like "I hope this letter finds you well", "I would like to take this opportunity", "It is worth noting that", "I want to emphasize", "In light of the foregoing".
- Use "furthermore", "moreover", "additionally", "consequently", "thus", "hence", "therefore" to start sentences. Just start the next sentence.
- Use "I am reaching out", "I am writing to express", or similar throat-clearing.
- Use bullet points in the body paragraphs. Use normal prose paragraphs instead. Bullet points are only OK in a short list of attached documents at the end.
- Bold or italicize words for emphasis in the body. Let the facts speak.
- Use the word "utilize" (say "use"). Don't say "prior to" (say "before"). Don't say "in order to" (say "to").
- Write in a legalistic or corporate tone. This is a letter from a person, not a law firm.
- Use exclamation marks.

**DO:**
- Write in plain, direct English. Short sentences are fine. Vary sentence length naturally.
- Be specific and factual. Name dates, dollar amounts, policy section titles, and quote the policy where it helps.
- Sound like someone who has read their policy carefully and knows the denial doesn't add up.
- Be firm but not aggressive. The tone is: "I've reviewed this, the denial doesn't match the policy, here's why, please fix it."
- Use "I" naturally. This is a first-person letter.
- Keep paragraphs short (3-5 sentences max).
- Use simple transitions: "The EOB states...", "However, my policy says...", "The treatment happened on..."
- Format the letter like a normal typed letter you'd print and mail. Left-aligned, standard paragraphs, no fancy formatting.

Use this structure:

---

**[Today's Date]**

MetLife Pet Insurance / Metropolitan General Insurance Company
[Address from the claim form — check the EOB or claim form for the correct mailing address]

**Re: Formal Appeal of Claim [Claim ID]**
Policy Number: [Policy ID]
Pet Name: [from claim data]
Date(s) of Service: [from EOB]

To Whom It May Concern,

I'm appealing the [denial/underpayment] of Claim [ID]. The Explanation of Benefits I received on [EOB date] states [quote the denial reason]. After reviewing my policy, I believe this determination is incorrect.

[1-2 paragraphs: what happened. Plain facts. "On [date], I took [pet name] to [vet] for [reason]. The vet diagnosed [condition] and performed [treatment]. The total charge was $X."]

[1-2 paragraphs: why the denial is wrong. "The EOB cites [specific reason]. However, my policy's [section name] states [quote relevant language]. This treatment falls under [coverage category] because [reason]." Be direct and cite the policy.]

[If applicable, 1 paragraph on timeline: "My policy took effect on [date]. The waiting period for illness was [X] days, ending on [date]. [Pet name] first showed symptoms on [date], which was [X] days/months after coverage began. This does not meet the policy's definition of a Pre-Existing Condition."]

[1 paragraph: the math, if relevant. "Per my policy, covered charges are reimbursed at [X]% after a $[X] deductible. The correct reimbursement should be: ($[billed] - $[deductible]) x [X]% = $[amount]. The EOB shows a payment of $[paid], which is $[difference] less than what the policy provides."]

Based on the above, I'm asking that you [reverse the denial and reimburse $X / recalculate the reimbursement to $X].

I've included [list: copies of vet records, itemized invoice, etc.] with this letter. Please let me know if you need anything else.

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

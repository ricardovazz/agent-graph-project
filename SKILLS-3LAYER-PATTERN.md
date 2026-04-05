# 3-Layer Skills Pattern for Multi-Agent Systems

## The Problem

When combining skills with multi-agent architectures, a critical question arises:

> "Who should have the skills - the supervisor or the subagents?"

**Answer: BOTH, but with different purposes and a 3-layer split.**

---

## The 3-Layer Split

| Layer | Owned By | Contains |
|-------|----------|----------|
| **Capability Catalog** | Supervisor | Agent names, domain summaries, delegation rules, I/O contracts |
| **Process Skill** | Supervisor + participating agents (role-specific) | Same business process viewed from each role: orchestration for supervisor, execution steps for workers |
| **Specialist Skill** | Specialist only | API/tool instructions, failure modes, parameter guidance, reference docs |

---

## How It Works: Complete Example

### Scenario: Monthly CRM Report

```
User: "Generate the monthly CRM report"
```

### STEP 1: Supervisor Sees Capability Catalog (Always in Context)

The supervisor's system prompt includes:

```xml
<skills_system>
Available Skills:
<skill>
  <name>crm-report-process</name>
  <description>Monthly CRM report workflow. Orchestrates data extraction, analysis, and report writing.</description>
  <tags>business-process, orchestration, crm</tags>
  <delegates_to>api-specialist, analyst, writer</delegates_to>
  <input_contract>{period: string, format: string}</input_contract>
  <output_contract>{report: markdown, data: json}</output_contract>
</skill>
</skills_system>
```

**Supervisor thinks**: "This matches `crm-report-process`"

---

### STEP 2: Supervisor Loads Process Skill (Orchestration View)

**Tool call**: `load_skill("crm-report-process")`

**Returns**:
```json
{
  "skill_name": "crm-report-process",
  "role": "supervisor",
  "instructions": "# CRM Report Process - Supervisor View\n\n## Workflow\n1. Extract data → delegate to api-specialist\n2. Analyze trends → delegate to analyst\n3. Write report → delegate to writer\n\n## I/O Contracts\n- Input: {period, format}\n- Output: {report, data}"
}
```

**Supervisor now knows**:
- This is a 3-step workflow
- Which subagents to delegate to
- What inputs/outputs to expect

---

### STEP 3: Supervisor Delegates to api-specialist

**Tool call**:
```python
start_job(
    agent_name="api-specialist",
    task="extract_crm_data",
    params={
        "period": "monthly",
        "date": "2024-01"
    },
    expected_output=["contacts", "deals", "revenue"]
)
```

**Returns**: `"Job started: job_abc123"`

---

### STEP 4: api-specialist Loads Process Skill (Execution View)

**Tool call**: `load_skill("crm-report-process")`

**Returns** (different view!):
```json
{
  "skill_name": "crm-report-process",
  "role": "api-specialist",
  "instructions": "# CRM Report Process - API Specialist View\n\n## Your Role\nExtract CRM data for the specified period.\n\n## Required Actions\n1. Call GET /contacts?created_after={date}\n2. Call GET /deals?closed_after={date}\n3. Call GET /revenue?period={period}\n\n## Expected Output\n{\n  \"contacts\": [...],\n  \"deals\": [...],\n  \"revenue\": [...]\n}"
}
```

**api-specialist now knows**:
- What endpoints to call
- What parameters to use
- What format to return

---

### STEP 5: api-specialist Loads Specialist Skill

**Tool call**: `load_skill("api-integration")`

**Returns**:
```json
{
  "skill_name": "api-integration",
  "instructions": "# API Integration Skill\n\n## Authentication\nBase URL: https://api.crm.example.com/v1\nAuth: Bearer token\n\n## Endpoints\nGET /contacts - Extract contact data\nGET /deals - Extract deal data\nGET /revenue - Extract revenue metrics\n\n## Error Handling\n- 429: Wait 60s, retry\n- 500: Retry once, then fail\n- 401: Check token"
}
```

**api-specialist now knows**:
- How to authenticate
- Exact API parameters
- Rate limiting strategy
- Error recovery procedures

---

### STEP 6: api-specialist Executes & Returns

**Executes**:
1. Calls `GET /contacts?created_after=2024-01-01`
2. Calls `GET /deals?closed_after=2024-01-01`
3. Calls `GET /revenue?period=monthly`
4. Returns structured data per contract

**Job completes with**:
```json
{
  "contacts": [...],
  "deals": [...],
  "revenue": {...}
}
```

---

### STEP 7-9: Workflow Continues

Supervisor gets result → delegates to analyst → analyst loads skills → analyzes → returns

Supervisor gets result → delegates to writer → writer loads skills → writes report → returns

---

### STEP 10: Supervisor Returns Final Result

```
Here's your monthly CRM report:

EXECUTIVE SUMMARY
=================
• 45 new customers acquired (+15% vs last month)
• 23 deals closed worth $125,000
• Average deal size increased 8%

[Full report...]
```

---

## The Key Insight

**Same business process, DIFFERENT views per role:**

```
crm-report-process (Supervisor view):
  "Orchestrate 3 agents in sequence"

crm-report-process (api-specialist view):
  "Extract data from these 3 endpoints"

crm-report-process (analyst view):
  "Analyze trends in provided dataset"

crm-report-process (writer view):
  "Format insights into executive report"
```

This keeps shared understanding aligned **WITHOUT** collapsing into one giant prompt!

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        SUPERVISOR AGENT                          │
│                                                                   │
│  Layer 1: Capability Catalog (always in context)                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • api-specialist: API integration, data extraction      │    │
│  │ • analyst: Statistical analysis, visualization          │    │
│  │ • writer: Report writing, documentation                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  Layer 2: Process Skills (loaded on-demand)                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ crm-report-process (orchestration view)                 │    │
│  │ - Knows workflow steps                                  │    │
│  │ - Knows delegation rules                                │    │
│  │ - Knows I/O contracts                                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  Tools: start_job, check_status, get_result                      │
└───────────────────────┬─────────────────────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐
│api-specialist│ │ analyst  │ │  writer  │
│              │ │          │ │          │
│Layer 2:      │ │Layer 2:  │ │Layer 2:  │
│crm-report    │ │crm-report│ │crm-report│
│(exec view)   │ │(exec view)│ │(exec view)│
│              │ │          │ │          │
│Layer 3:      │ │Layer 3:  │ │Layer 3:  │
│api-integr.   │ │data-     │ │report-   │
│              │ │analysis  │ │writing   │
│              │ │          │ │          │
│Tools:        │ │Tools:    │ │Tools:    │
│• HTTP calls  │ │• pandas  │ │• docs    │
│• DB queries  │ │• matplotlib│• templates│
└──────────────┘ └──────────┘ └──────────┘
```

---

## Skill File Structure

### Layer 1: Capability Catalog

```markdown
---
name: subagent-capabilities
description: Catalog of available subagents and their capabilities
tags:
  - catalog
  - orchestration
---

# Subagent Capabilities

## api-specialist
- **Domain**: API integration, data extraction
- **Skills**: api-integration, data-extraction
- **I/O Contract**: 
  - Input: {endpoints: [], params: {}}
  - Output: {data: dict}

## analyst
- **Domain**: Statistical analysis, visualization
- **Skills**: data-analysis, visualization
- **I/O Contract**:
  - Input: {data: dict, questions: []}
  - Output: {insights: [], charts: []}

## writer
- **Domain**: Report writing, documentation
- **Skills**: report-writing, documentation
- **I/O Contract**:
  - Input: {insights: [], format: string}
  - Output: {report: markdown}
```

### Layer 2: Process Skill (Supervisor View)

```markdown
---
name: crm-report-process
description: Monthly CRM report workflow
tags:
  - business-process
  - orchestration
delegates_to:
  - api-specialist
  - analyst
  - writer
---

# CRM Report Process - Supervisor View

## Workflow
1. Extract data → delegate to api-specialist
2. Analyze trends → delegate to analyst
3. Write report → delegate to writer

## I/O Contracts
- Input: {period: string, format: string}
- Output: {report: markdown, data: json}

## Delegation Rules
- Always follow 3-step sequence
- Pass outputs between steps
- If step fails, inform user and suggest alternatives
```

### Layer 2: Process Skill (Worker View - api-specialist)

```markdown
---
name: crm-report-process
description: Monthly CRM report workflow - data extraction role
tags:
  - business-process
  - execution
role: api-specialist
---

# CRM Report Process - API Specialist View

## Your Role
Extract CRM data for the specified period.

## Required Actions
1. Call GET /contacts?created_after={date}
2. Call GET /deals?closed_after={date}
3. Call GET /revenue?period={period}

## Expected Output
{
  "contacts": [...],
  "deals": [...],
  "revenue": [...]
}
```

### Layer 3: Specialist Skill

```markdown
---
name: api-integration
description: CRM API integration specialist
tags:
  - api
  - integration
  - data-extraction
---

# API Integration Skill

## Authentication
Base URL: https://api.crm.example.com/v1
Auth: Bearer token (from CRM_API_TOKEN env var)

## Endpoints

### GET /contacts
Extract customer contact data.

**Parameters:**
- `created_after`: Filter by creation date
- `status`: Filter by status (active, inactive, lead)
- `limit`: Max results (default 100, max 1000)

## Rate Limiting
- Limit: 100 requests per minute
- Strategy: If 429 received, wait 60 seconds and retry

## Error Handling
| Status | Action |
|--------|--------|
| 401 | Check API token |
| 429 | Wait 60s, retry |
| 500 | Retry once, then fail |
```

---

## Decision Matrix

| Question | Answer | Layer |
|----------|--------|-------|
| Is this about WHAT subagents exist? | Capability Catalog | Layer 1 |
| Is this about WHEN to delegate? | Process Skill (Supervisor) | Layer 2 |
| Is this about HOW to execute? | Process Skill (Worker) | Layer 2 |
| Is this about API/tool details? | Specialist Skill | Layer 3 |
| Is this about I/O contracts? | Capability Catalog + Process | Layer 1-2 |
| Is this about error recovery? | Specialist Skill | Layer 3 |

---

## Benefits of 3-Layer Split

1. **Separation of Concerns**
   - Supervisor knows orchestration, not implementation
   - Workers know implementation, not overall workflow
   - Clean boundaries prevent knowledge leakage

2. **Progressive Disclosure at Every Level**
   - Layer 1: Always visible (~100 words)
   - Layer 2: Loaded when process matches (~500 words)
   - Layer 3: Loaded for execution details (~1000-2000 words)

3. **Shared Understanding Without Bloat**
   - Same process name across agents
   - Different views per role
   - No need to duplicate workflow knowledge

4. **Scales to Many Agents**
   - Add agents by adding to catalog
   - Add processes by adding process skills
   - Each agent only loads what it needs

5. **Team Independence**
   - Process owners define workflows
   - Specialists own implementation
   - Changes isolated to relevant layer

---

## Implementation Checklist

- [ ] Create `skills/capabilities/` for Layer 1
- [ ] Create `skills/orchestration/` for Layer 2 (supervisor view)
- [ ] Create `skills/<agent>/` for Layer 2 (worker view) + Layer 3
- [ ] Update supervisor to load capability catalog
- [ ] Update subagents to load their own skills
- [ ] Define I/O contracts for each subagent
- [ ] Test delegation flow end-to-end

---
name: research-then-write
description: Research a topic thoroughly, then create written content based on findings. Use when user asks to research and write about something.
tags:
  - business-process
  - orchestration
  - multi-step
delegates_to:
  - research
  - writing
---

# Research → Write Process (Supervisor View)

## Your Role: Orchestrator

You coordinate two subagents in sequence to produce researched content.

## Workflow

### Step 1: Research
**Delegate to**: `research`
**Task**: Research the topic thoroughly
**Input Contract**: `{topic: string, scope: string, depth: "detailed"}`
**Expected Output**: `{summary, key_findings, sources, confidence}`

### Step 2: Write
**Delegate to**: `writing`
**Task**: Create content based on research findings
**Input Contract**: `{topic: string, audience: string, tone: string, format: string, research_findings: object}`
**Expected Output**: `{content, word_count, tone, structure}`

## Delegation Instructions

**For Research Step**:
```
Research this topic: {topic}
Scope: {scope}
Depth: detailed
Focus on: key findings, credible sources, current information
```

**For Writing Step**:
```
Write {format} about: {topic}
Audience: {audience}
Tone: {tone}
Use these research findings: {research_output}
Structure with clear headings and actionable insights
```

## Stop Conditions

- Both steps complete successfully → Return final content
- Research fails → Inform user, ask if they want to proceed with writing anyway
- Writing fails → Return research findings with formatting notes

## Escalation Rules

- If research is inconclusive: Note limitations, suggest manual research
- If writing doesn't match requirements: Request revision with specific feedback
- If user requests changes: Iterate on writing step only (research is complete)

## Example

**User**: "Research and write an article about the benefits of remote work"

**You**:
1. Delegate to research: "Research benefits of remote work, scope: comprehensive, depth: detailed"
2. Get research output
3. Delegate to writing: "Write an article about remote work benefits, audience: professionals, tone: informative, format: article"
4. Return final article

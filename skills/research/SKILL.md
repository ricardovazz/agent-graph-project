---
name: research
description: Expert research specialist. Finds, analyzes, and summarizes information from various sources. Use for fact-finding, data gathering, and knowledge synthesis tasks.
tags:
  - research
  - analysis
  - information
  - synthesis
---

# Research Skill

## When to Use

- User asks for information on a topic, event, or concept
- User needs factual data, statistics, or historical context
- User wants a summary of research on a subject
- User needs to understand a complex topic from multiple angles
- Fact-checking or verification tasks

## Instructions

### Research Methodology

1. **Clarify the scope**: Identify what specific information is needed
2. **Search systematically**: Use available tools to find relevant information
3. **Evaluate sources**: Prioritize authoritative, recent, and relevant sources
4. **Synthesize findings**: Combine information from multiple sources coherently
5. **Cite appropriately**: Reference where information came from
6. **Acknowledge uncertainty**: Be clear about what is known vs. speculative

### Output Format

When presenting research findings:

```
## Topic: [Subject]

### Key Findings
- [Finding 1] - [Source/Context]
- [Finding 2] - [Source/Context]

### Background
[Relevant context and history]

### Current State
[Latest developments or status]

### Sources & Notes
[Methodology, limitations, and source quality]
```

### Quality Guidelines

- **Accuracy**: Verify facts across multiple sources when possible
- **Recency**: Note when information might be outdated
- **Balance**: Present multiple perspectives on controversial topics
- **Depth**: Go beyond surface-level; provide meaningful detail
- **Relevance**: Stay focused on what the user actually needs

## Examples

**User**: "What are the latest developments in quantum computing?"

**Approach**: 
1. Load this skill via `load_skill("research")`
2. Apply research methodology
3. Present findings in structured format
4. Note knowledge cutoff limitations

## When NOT to Use

- Simple greetings or casual conversation
- Tasks better suited for creative writing (use `writing` skill instead)
- Code generation tasks (use `code-generation` skill instead)

---
name: subagent-capabilities
description: Catalog of available subagents, their domains, skills, and I/O contracts. Use to understand what each subagent can do and when to delegate.
tags:
  - catalog
  - orchestration
  - capabilities
  - delegation
---

# Subagent Capabilities Catalog

## Overview

This catalog defines all available subagents, their capabilities, and the contracts for delegation.

## Available Subagents

### research

**Domain**: Research, fact-finding, information synthesis

**Skills**:
- `research`: Research methodology, source evaluation, synthesis

**I/O Contract**:
- **Input**: `{topic: string, scope: string, depth: "brief" | "detailed"}`
- **Output**: `{summary: string, key_findings: string[], sources: string[], confidence: string}`

**When to Delegate**:
- User asks for information on a topic, event, or concept
- User needs factual data, statistics, or historical context
- User wants a summary of research on a subject
- Fact-checking or verification tasks

**Quality Expectations**:
- Accuracy: Verify facts across multiple sources
- Recency: Note when information might be outdated
- Balance: Present multiple perspectives on controversial topics
- Depth: Go beyond surface-level; provide meaningful detail

---

### writing

**Domain**: Content creation, documentation, marketing copy, editing

**Skills**:
- `writing`: Content creation methodology, tone adaptation, structured writing

**I/O Contract**:
- **Input**: `{topic: string, audience: string, tone: string, format: string, length: string}`
- **Output**: `{content: string, word_count: number, tone: string, structure: string}`

**When to Delegate**:
- Creating articles, blog posts, or documentation
- Writing marketing copy, emails, or communications
- Editing or improving existing content
- Generating creative content (stories, scripts, poems)

**Quality Expectations**:
- Clear purpose and audience alignment
- Logical structure and flow
- Appropriate tone and language level
- No grammatical errors or typos
- Actionable or memorable conclusion

---

### code-generation

**Domain**: Software development, debugging, code review, architecture

**Skills**:
- `code-generation`: Multi-language coding, best practices, design patterns, testing

**I/O Contract**:
- **Input**: `{language: string, task: string, requirements: string[], constraints: string[]}`
- **Output**: `{code: string, language: string, explanation: string, usage: string, tests: string}`

**When to Delegate**:
- Writing new code or scripts in any programming language
- Debugging or fixing existing code
- Code review and improvement suggestions
- Explaining how code works
- Refactoring or optimizing code

**Quality Expectations**:
- Correctness: Code works as intended
- Readability: Others can understand it
- Performance: No obvious bottlenecks
- Security: Input validation, no hardcoded secrets
- Maintainability: Easy to modify and extend

---

## Delegation Rules

1. **Match task to subagent domain** - Choose the subagent whose skills align with the task
2. **Provide clear input contract** - Specify exactly what the subagent should do
3. **Expect structured output** - Each subagent returns data per its contract
4. **Handle failures gracefully** - If a subagent fails, inform user and suggest alternatives
5. **Chain subagents when needed** - Complex tasks may require multiple subagents in sequence

## Multi-Subagent Workflows

For tasks requiring multiple subagents:

1. **Research → Writing**: Research a topic, then write an article
2. **Research → Code-generation**: Research best practices, then implement
3. **Code-generation → Writing**: Generate code, then write documentation

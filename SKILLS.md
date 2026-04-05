# Skills Pattern Implementation

This project implements the **LangChain Skills Pattern** for progressive disclosure of domain expertise in AI agents.

## Overview

The skills pattern allows agents to load specialized capabilities **on-demand** rather than stuffing all knowledge into the system prompt upfront. This enables:

- ✅ **Scalability**: Add dozens of skills without context bloat
- ✅ **Progressive Disclosure**: Load knowledge only when needed
- ✅ **Team Independence**: Different teams can develop skills separately
- ✅ **Lightweight Composition**: Simpler than full sub-agents

## Architecture

### Three-Tier Progressive Disclosure

```
Tier 1: Skill Descriptions (~100 words) → Always in system prompt
         ↓
Tier 2: Full SKILL.md Instructions (~500-2000 words) → Loaded via load_skill()
         ↓
Tier 3: Reference Documents → Loaded via read_skill_file()
```

### Directory Structure

```
skills/
├── research/
│   └── SKILL.md              # Research specialist skill
├── writing/
│   └── SKILL.md              # Content creation skill
└── code-generation/
    └── SKILL.md              # Software development skill
    └── references/           # Optional reference documents
        └── python-patterns.md

src/
├── skills.py                 # SkillStore, SkillMetadata, ParsedSkill
├── skill_tools.py            # load_skill() and read_skill_file() tools
├── prompts.py                # System prompt template
└── agent_graph.py            # Main agent graph with skills integration
```

## Skill Format

Each skill is a directory containing:

### SKILL.md Format

```markdown
---
name: my-skill-name
description: A brief description shown in the catalog
tags:
  - tag1
  - tag2
---

# Skill Title

## When to Use
Describe scenarios where this skill applies.

## Instructions
Step-by-step guidance for the skill.

## Examples
Show the skill in action.

## When NOT to Use
Describe when to skip this skill.
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier (kebab-case recommended) |
| `description` | Yes | Brief summary for the skill catalog |
| `tags` | No | Keywords for categorization |

## Core Components

### 1. SkillStore (`src/skills.py`)

Manages skill discovery, metadata caching, and lazy loading:

```python
from src.skills import SkillStore

store = SkillStore("skills/")
store.scan()  # Discover all SKILL.md files

# Get lightweight catalog for system prompt
catalog = store.get_skill_catalog()

# Load full skill content on-demand
parsed = store.load("research")
print(parsed.content)  # Full markdown body
print(parsed.metadata.description)  # Description from frontmatter
```

### 2. Skill Tools (`src/skill_tools.py`)

Two tools exposed to the LLM:

- **`load_skill(skill_name)`**: Returns full SKILL.md content + available files
- **`read_skill_file(skill_name, filename)`**: Returns supporting file content

```python
from src.skill_tools import create_skill_tools

tools = create_skill_tools(store)
# Returns: [load_skill, read_skill_file]
```

### 3. System Prompt (`src/prompts.py`)

Template with placeholders for skill catalog:

```python
from src.prompts import SYSTEM_PROMPT

prompt = SYSTEM_PROMPT.format(
    current_time=datetime.now().isoformat(),
    skill_catalog=store.get_skill_catalog()
)
```

### 4. Agent Graph (`src/agent_graph.py`)

Integrates skills with the existing Three-tool pattern:

```python
# Combine skill tools with job tools
all_tools = [start_job, check_status, get_result] + skill_tools

# Create agent with skills
agent = create_agent(
    model=get_llm(),
    tools=all_tools,
    system_prompt=SYSTEM_PROMPT.format(...)
)
```

## Usage Examples

### Example 1: Research Task

```python
from langchain_core.messages import HumanMessage
from src.agent_graph import app

result = await app.ainvoke({
    "messages": [HumanMessage(
        content="Research and summarize the benefits of microservices architecture"
    )]
})
```

**Expected behavior**:
1. Agent sees skill catalog in system prompt
2. Agent recognizes this matches `research` skill
3. Agent calls `load_skill("research")`
4. Agent applies research methodology from SKILL.md
5. Agent presents findings in structured format

### Example 2: Code Generation

```python
result = await app.ainvoke({
    "messages": [HumanMessage(
        content="Write a Python function to validate email addresses"
    )]
})
```

**Expected behavior**:
1. Agent loads `code-generation` skill
2. Agent follows coding guidelines from SKILL.md
3. Agent returns well-documented code with examples

### Example 3: Multi-Skill Task

```python
result = await app.ainvoke({
    "messages": [HumanMessage(
        content="Research best practices for API authentication, then write documentation about it"
    )]
})
```

**Expected behavior**:
1. Agent loads `research` skill first
2. Agent gathers information
3. Agent loads `writing` skill for documentation
4. Agent produces structured documentation

## Adding New Skills

1. Create a new directory under `skills/`:
   ```bash
   mkdir skills/my-new-skill
   ```

2. Add a `SKILL.md` file:
   ```markdown
   ---
   name: my-new-skill
   description: What this skill does
   tags:
     - category
     - domain
   ---
   
   # My New Skill
   
   ## When to Use
   ...
   
   ## Instructions
   ...
   ```

3. (Optional) Add reference documents:
   ```
   skills/my-new-skill/
   ├── SKILL.md
   └── references/
       ├── guide.md
       └── examples.md
   ```

4. Restart the agent - skills are auto-discovered on startup

## Best Practices

### 1. Keep Skills Focused
- Each skill should cover a specific domain or capability
- Avoid overlapping responsibilities between skills
- Use clear, distinct descriptions

### 2. Write Actionable Instructions
- Include concrete "When to Use" and "When NOT to Use" sections
- Provide examples of typical usage
- Document common pitfalls

### 3. Use Progressive Disclosure Effectively
- Keep descriptions concise but informative (~50 words)
- Put detailed instructions in the SKILL.md body
- Move reference material to supporting files

### 4. Organize Hierarchically for Large Knowledge Bases
```
skills/
├── data-science/
│   ├── SKILL.md              # Overview + sub-skills list
│   └── sub-skills/
│       ├── pandas/
│       │   └── SKILL.md
│       └── visualization/
│           └── SKILL.md
```

### 5. Enable Team Independence
- Structure skills so different teams can own them
- Use consistent format but allow content freedom
- Version skills independently

## Performance Considerations

### Context Window Usage

| Approach | Context Usage | Scalability |
|----------|---------------|-------------|
| **All skills in prompt** | 10,000+ tokens | Poor (5-10 skills max) |
| **Skills pattern** | ~500 tokens for catalog | Excellent (50+ skills) |

### Loading Latency

- **Scan**: ~10-50ms (metadata only, cached)
- **Load skill**: ~5-20ms (file read, cached after first load)
- **Read reference**: ~1-5ms (on-demand)

## Testing

Run the test suite:

```bash
python test_skills.py
```

This will:
1. Test skill store initialization
2. Verify skill catalog generation
3. Test skill loading
4. Run the agent with different skill-triggering queries

## References

- [LangChain Skills Pattern Documentation](https://docs.langchain.com/oss/python/langchain/multi-agent/skills)
- [LangChain Skills Repository](https://github.com/langchain-ai/langchain-skills)
- [Stop Stuffing Your System Prompt (Article)](https://pessini.medium.com/stop-stuffing-your-system-prompt-build-scalable-agent-skills-in-langgraph-a9856378e8f6)
- [LangGraph Skills Agent (Reference Implementation)](https://github.com/pessini/langgraph-skills-agent)

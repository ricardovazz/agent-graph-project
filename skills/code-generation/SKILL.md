---
name: code-generation
description: Expert software developer and code specialist. Generates, reviews, debugs, and explains code across multiple programming languages and frameworks.
tags:
  - programming
  - development
  - debugging
  - code-review
---

# Code Generation Skill

## When to Use

- Writing new code or scripts in any programming language
- Debugging or fixing existing code
- Code review and improvement suggestions
- Explaining how code works
- Refactoring or optimizing code
- Writing tests for existing code
- Architecture and design pattern guidance

## Instructions

### Code Generation Process

1. **Understand requirements**: What should the code do? What are the constraints?
2. **Choose the right approach**: Language, framework, patterns, and architecture
3. **Write clean code**: Follow best practices and conventions for the language
4. **Add documentation**: Docstrings, comments for complex logic, type hints
5. **Consider edge cases**: Error handling, validation, boundary conditions
6. **Test mentally**: Walk through the code to verify correctness

### Language-Specific Guidelines

#### Python
- Use type hints for function signatures
- Follow PEP 8 style guidelines
- Prefer list comprehensions and built-in functions
- Use `dataclasses` for structured data
- Add docstrings with Args/Returns sections

#### JavaScript/TypeScript
- Use `const` and `let`, avoid `var`
- Add TypeScript types where applicable
- Use async/await for asynchronous operations
- Prefer arrow functions for callbacks
- Handle errors with try/catch blocks

#### General Best Practices
- Write self-documenting code with clear variable/function names
- Keep functions small and focused (single responsibility)
- Use meaningful error messages
- Avoid magic numbers; use named constants
- Include examples of how to use the code

### Output Format

When providing code:

````
[Language]: Python/JavaScript/etc.

```[language]
# Code here with comments
```

**Explanation**:
- [Key design decisions]
- [How to use this code]
- [Any limitations or assumptions]
````

### Code Review Checklist

When reviewing or improving code:
- [ ] Correctness: Does it work as intended?
- [ ] Readability: Can others understand it?
- [ ] Performance: Any obvious bottlenecks?
- [ ] Security: Input validation, no hardcoded secrets
- [ ] Maintainability: Easy to modify and extend?
- [ ] Testing: Can it be tested? Are edge cases covered?

## Examples

**User**: "Write a Python function to validate email addresses"

**Approach**:
1. Load this skill via `load_skill("code-generation")`
2. Choose regex approach with `re` module
3. Add type hints and docstring
4. Include usage examples
5. Explain the pattern

## When NOT to Use

- Pure research without code needs (use `research` skill instead)
- Content writing or documentation (use `writing` skill instead)
- General conversation or simple greetings

## Reference Documents

- `references/python-patterns.md` — Common Python design patterns
- `references/testing-guide.md` — Testing best practices

# LangGraph Project

This is a starter LangGraph project with examples.

## Setup

1. Ensure Python 3.10+ is installed.
2. Activate the virtual environment: `venv\Scripts\activate`
3. Install dependencies: `pip install -e .`
4. Run the examples below.

## Examples

### Basic Counter Graph
Run: `python src/main.py`

A simple state graph that increments and decrements a counter.

### Agent Graph with Orchestrator
Run: `python src/agent_graph.py`

A graph with an orchestrator that delegates tasks to a worker agent. Each has system prompts and follows LangChain best practices.

## What it does

- **Counter Example**: Demonstrates basic LangGraph state management.
- **Agent Graph**: Shows agent orchestration with system prompts, tools, and conditional routing.
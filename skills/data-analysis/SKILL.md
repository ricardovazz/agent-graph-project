---
name: data-analysis
description: Expert data analyst. Analyzes datasets, creates visualizations, and extracts insights from structured data using Python libraries like pandas, matplotlib, and numpy.
tags:
  - data
  - analysis
  - visualization
  - python
  - statistics
---

# Data Analysis Skill

## When to Use

- User asks to analyze a dataset or CSV file
- User needs statistics, trends, or patterns identified
- User wants charts, graphs, or visualizations
- User needs data cleaning or transformation
- User asks for insights from numerical or tabular data

## Instructions

### Analysis Workflow

1. **Understand the data**: What columns? What's the goal?
2. **Load and inspect**: Check shape, types, missing values
3. **Clean if needed**: Handle nulls, duplicates, outliers
4. **Analyze**: Calculate statistics, find patterns
5. **Visualize**: Create appropriate charts
6. **Explain insights**: What does the data tell us?

### Python Libraries to Use

- **pandas**: Data manipulation and analysis
- **matplotlib/seaborn**: Visualization
- **numpy**: Numerical operations
- **scipy**: Statistical tests

### Output Format

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('data.csv')

# Analysis steps
print(df.describe())
print(df.info())

# Visualization
df.plot(kind='bar')
plt.show()
```

### Visualization Guidelines

- Use bar charts for categorical comparisons
- Use line charts for time series
- Use scatter plots for correlations
- Use histograms for distributions
- Always label axes and add titles

## Examples

**User**: "Analyze this sales data and show me monthly trends"

**Approach**:
1. Load this skill via `load_skill("data-analysis")`
2. Parse the data
3. Group by month
4. Create line chart
5. Explain trends

## When NOT to Use

- Simple calculations (do directly)
- Non-data research tasks (use `research` skill)
- Code without data focus (use `code-generation` skill)

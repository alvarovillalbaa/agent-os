# System Prompt Instructions Architecture

**Comprehensive guide for designing, implementing, and maintaining AI agent system prompts across the Cloush platform.**

This document serves as the authoritative reference for creating effective system prompt instructions—combining theoretical foundations from leading AI labs (Anthropic, OpenAI, Cursor) with practical implementation patterns specific to our platform architecture.

---

## Table of Contents

1. [Introduction & Scope](#1-introduction--scope)
2. [Architectural Integration](#2-architectural-integration)
3. [Theoretical Foundations](#3-theoretical-foundations)
4. [Instruction Anatomy](#4-instruction-anatomy)
5. [Implementation Patterns](#5-implementation-patterns)
6. [Optimization Guidelines](#6-optimization-guidelines)
7. [Advanced Techniques](#7-advanced-techniques)
8. [Quality Assurance](#8-quality-assurance)
9. [Advanced Platform-Specific Patterns](#9-advanced-platform-specific-patterns)
10. [Prompt Structure Reference](#10-prompt-structure-reference)
11. [Examples & Templates](#11-examples--templates)
12. [Maintenance & Evolution](#12-maintenance--evolution)

---

## 1. Introduction & Scope

### 1.1 Purpose

This guide defines **how system prompt instructions should be structured, written, and maintained** across the Cloush platform. It covers:

- **What instructions are**: The system prompts that define AI agent identity, behavior, capabilities, and constraints
- **Why they matter**: Instructions are the primary mechanism for controlling AI agent behavior and output quality
- **Who uses this guide**: Engineers, AI specialists, and product teams creating or modifying agent instructions
- **When to apply**: During initial agent design, optimization cycles, debugging, and feature additions

### 1.2 Relationship to Other Documentation

| Document | Focus | Use When |
|----------|-------|----------|
| **This guide** (`messages-instructions-architecture.md`) | How to design and write system prompts | Creating/optimizing agent instructions |
| **`messages/instructions/README.md`** | Package structure, versioning, access patterns | Implementing instructions in codebase |
| **`.cursor/rules/build-ai-instructions.mdc`** | Meta-patterns and prompt engineering techniques | Iterating on instruction quality |
| **`.cursor/rules/ai_agent_tool_calls.mdc`** | Tool function descriptions and contracts | Defining agent capabilities |

**Key Distinction**: This guide focuses on **system instructions** (who the AI is, how it thinks). Tool descriptions define **what actions are available** (function parameters, returns, errors).

### 1.3 Scope Boundaries

**In Scope**:
- System prompt structure and hierarchy
- Instruction content design principles
- Platform integration patterns
- Quality metrics and evaluation
- Version management strategies

**Out of Scope**:
- Tool function implementations (see tool development docs)
- Agent runtime orchestration (see `services/agents/` docs)
- Frontend UI/UX patterns
- Infrastructure deployment

---

## 2. Architectural Integration

### 2.1 Platform Architecture Overview

System prompt instructions integrate with the broader Cloush platform architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    Platform Stack                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ API Views    │  │ Services     │  │ Tasks        │ │
│  │ (DRF)        │  │ (Business    │  │ (Celery)     │ │
│  │              │  │  Logic)      │  │              │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │         │
│         └──────────────────┼──────────────────┘         │
│                            │                            │
│                   ┌────────▼────────┐                   │
│                   │ instruction_     │                   │
│                   │ service          │                   │
│                   │ (Centralized)    │                   │
│                   └────────┬────────┘                   │
│                            │                            │
│         ┌──────────────────┼──────────────────┐         │
│         │                  │                  │         │
│    ┌────▼────┐       ┌────▼────┐       ┌────▼────┐    │
│    │ Agents  │       │Middleware│      │Functions│    │
│    │ /assista│       │ /router │       │/selectio│    │
│    │ nt/     │       │         │       │n/       │    │
│    └─────────┘       └─────────┘       └─────────┘    │
│                                                         │
│    ┌─────────────────────────────────────────────┐    │
│    │ Shared Components (root-level)              │    │
│    ├─────────────────────────────────────────────┤    │
│    │ guardrails/ | formatting/ | capabilities/   │    │
│    │ tool_descriptions/ | intelligence/          │    │
│    └─────────────────────────────────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Package Architecture

All system prompts live under `messages/instructions/` with **version-driven packages**:

```
messages/instructions/
├── agents/                 # Agent-specific instructions
│   ├── assistant/
│   │   ├── CHANGELOG.md
│   │   ├── v1/
│   │   │   ├── instruction.j2    # Jinja2 template
│   │   │   ├── values.py         # Fixed text blocks (UPPERCASE)
│   │   │   ├── composables.py    # Assembly functions
│   │   │   └── meta.yaml         # Metadata
│   │   └── v2/ (latest)
│   ├── cdo/
│   └── candidates/
├── middleware/             # Processing pipeline instructions
│   ├── router/
│   ├── analysis/
│   └── context_compression/
├── functions/              # Canvas function instructions
│   ├── selection/
│   ├── document/
│   └── heatmap/
├── guardrails/             # Shared: safety constraints (root-level)
├── formatting/             # Shared: response formatting (root-level)
├── capabilities/           # Shared: operating principles (root-level)
├── tool_descriptions/      # Shared: tool contracts (root-level)
├── intelligence/           # Shared: dynamic prompt generation (root-level)
└── instruction_service.py  # Centralized access API
```

**Key Principles**:
- **Version IS Instruction**: Highest numbered version directory is current/active
- **Complete Snapshots**: Each version is immutable and self-contained
- **Centralized Access**: Always use `instruction_service`, never direct imports
- **Root-level Shared**: No `shared/` folder; root placement means shared

### 2.3 Centralized Access Pattern

**✅ CORRECT** - Single entry point for all instruction access:

```python
from messages.instruction_service import render_prompt, get_instruction_composables

# Agent instructions
agent_prompt = render_prompt("agents/assistant", **context_vars)

# Middleware instructions
middleware_prompt = render_prompt("middleware/analysis", 
                                 CONTENT_TYPE=content_type,
                                 ANALYSIS_DEPTH=depth)

# Function instructions
function_prompt = render_prompt("functions/selection",
                               FUNCTION_GUARDRAIL=guardrails)

# Access composables
guardrails = get_instruction_composables("guardrails", "v2")
```

**❌ INCORRECT** - Direct imports bypass centralized control:

```python
# Don't do this
from messages.instructions.agents.assistant.v2.values import OPERATING_PRINCIPLES
from messages.instructions.guardrails.v2.composables import compose_base_guardrail
```

**Benefits of Centralized Access**:
- **Version Safety**: Registry-based resolution prevents version drift
- **Consistency**: Same interface across all platform layers
- **Testability**: Service-level mocking for tests
- **Migration Safety**: Gradual updates without breaking changes
- **Performance**: Centralized caching and optimization

---

## 3. Theoretical Foundations

Understanding how language models process instructions is critical for effective prompt design.

### 3.1 Model Weighting

Language models assign different levels of importance to prompt sections based on **position, repetition, formatting, and examples**.

#### 3.1.1 Position in Prompt (Start > End > Middle)

**Beginning** (Maximum Attention):
- Place **Identity/Role** in opening lines
- Define **Mission** statement early
- Establish **Core Principles** upfront

**End** (Secondary Reinforcement):
- Reiterate **Critical Guardrails**
- Final **Output Format** specifications
- **Closing Behavioral Cues**

**Middle** (Most Likely Deprioritized):
- Avoid placing critical instructions here
- Use for **supporting details** and **reference material**
- **Examples** and **context data** can go here

**Example**:
```python
# ✅ GOOD: Critical identity at start
You are an HR expert designed to serve HR professionals within organizations.
Your mission is to resolve user asks by orchestrating the system's capabilities.

{{OPERATING_PRINCIPLES}}  # Core behavior
{{CAPABILITIES}}          # What you can do
{{EXAMPLES}}              # Supporting material (middle)
{{GUARDRAILS}}            # Final reinforcement (end)
```

```python
# ❌ BAD: Identity buried in middle
{{CAPABILITIES}}          # Capabilities first
{{EXAMPLES}}
You are an HR expert...   # Identity lost in middle
{{GUARDRAILS}}
```

#### 3.1.2 Repetition and Reinforcement

**Strategic Repetition**:
- Reinforce essential ideas **1-2 times** at strategic locations (start/end)
- Use **slightly different phrasing** to avoid verbatim copying

**Avoid Over-Anchoring**:
- Excessive repetition causes model to ignore nuance
- Don't repeat the same phrase >3 times

**Example**:
```python
# ✅ GOOD: Strategic reinforcement
# At start:
Your mission is to provide accurate data analysis based on verified sources.

# In capabilities:
When analyzing data, always validate sources and cite references.

# At end (guardrails):
Critical: Use only verified data from authorized sources. Never fabricate.

# Three different phrasings, same core principle
```

#### 3.1.3 Formatting and Emphasis

**Emphasis Signals** (use selectively):
- **Bold** (`**text**`): Most important concepts
- *Italics* (`*text*`): Secondary emphasis
- CAPITALIZATION: Critical constraints (use sparingly)
- Strong cue words: `MUST`, `ALWAYS`, `NEVER`, `ONLY`

**When to Use Emphasis**:
- Security-critical constraints: **Never expose user emails**
- Data integrity rules: **ALWAYS validate input before processing**
- Behavioral boundaries: *Respond in the same language as the query*

**Avoid Over-Emphasis**:
```python
# ❌ BAD: Everything emphasized loses meaning
**ALWAYS** use **ONLY** verified **DATA** from **AUTHORIZED** sources and **NEVER** fabricate **INFORMATION**.

# ✅ GOOD: Selective emphasis
Use only verified data from authorized sources. **Never fabricate information.**
```

#### 3.1.4 Example Power and Bias

Examples carry **disproportionate weight**—models replicate tone, structure, and logic.

**Managing Example Bias**:
- Provide **3-5 diverse examples** covering different scenarios
- Vary **structure, tone, and length**
- Include explicit disclaimer: *"These examples are for reference only. Adapt to each situation."*

**Example**:
```xml
<examples>
  <example>
    Input: "Show me skills for John Doe"
    Output: [Structured skills list with proficiency scores]
  </example>
  <example>
    Input: "Who has Python experience?"
    Output: [Employee list filtered by Python, sorted by proficiency]
  </example>
  <example>
    Input: "Compare Alice and Bob's skills"
    Output: [Comparison table highlighting skill gaps]
  </example>
</examples>

Note: These examples demonstrate different output structures. Adapt format to each specific request.
```

### 3.2 Scope and Determinism

**Scope** is the single most important factor affecting agent behavior—it defines the variability of inputs and outputs.

#### 3.2.1 Input Scope

**Narrow Input Scope** (Low Variability):
- Specific use cases with predictable inputs
- Example: "Evaluate candidate skills against job requirements"
- **When to use**: Specialized agents, middleware processors

**Wide Input Scope** (High Variability):
- Open-ended queries across multiple domains
- Example: "Answer any HR-related question"
- **When to use**: General-purpose agents, conversational assistants

#### 3.2.2 Output Scope

**Narrow Output Scope** (High Determinism):
- Structured, predictable outputs (JSON schemas, specific formats)
- Example: `{"skill_name": "Python", "level": 85}`
- **When to use**: Data processing, API integrations, structured artifacts

**Wide Output Scope** (Low Determinism):
- Open-ended, creative outputs (recommendations, strategic advice)
- Example: "Based on the analysis, here are three strategic options..."
- **When to use**: Research agents, strategic planning, ideation

#### 3.2.3 Scope Selection Matrix

| Input Scope | Output Scope | Use Case | Example Agent |
|-------------|--------------|----------|---------------|
| Narrow | Narrow | Data transformation | Middleware router |
| Narrow | Wide | Specialized analysis | Skills analyzer |
| Wide | Narrow | General data retrieval | Search agent |
| Wide | Wide | Conversational assistant | Main assistant |

**Most common in Cloush**: **Wide-enough input scope + Narrow-to-medium output scope**

### 3.3 Context Optimization

When prompts contain extensive information (>2000 tokens), models struggle to distinguish instructions from context.

#### 3.3.1 Content Delineation with XML

Use **XML tags** to mark logical boundaries:

```xml
<context>
{{COMPANY_DATA}}
{{INDUSTRY_STANDARDS}}
{{REFERENCE_DOCUMENTS}}
</context>

<instructions>
Your mission is to analyze the provided context and generate insights.

Follow these steps:
1. Validate data sources
2. Identify patterns
3. Generate recommendations
</instructions>

<examples>
  <example>
    Input: "Analyze employee retention trends"
    Output: [Analysis with data-backed recommendations]
  </example>
</examples>
```

**When to Use XML**:
- Prompts >2000 tokens
- Multiple content types (data + instructions + examples)
- Need to handle content that might contain Markdown

**Best Practices**:
- Use consistent tag names: `<context>`, `<instructions>`, `<examples>`
- Nest logically: `<examples><example>...</example></examples>`
- Keep tags descriptive: `<context>` not `<c>`

### 3.4 Intelligence Balancing

**Core Principle**: The intelligence required by the AI model is **inversely proportional** to the intelligence provided in the prompt.

#### 3.4.1 Lazy Prompts (High AI Intelligence Required)

**Vague, under-specified prompts force the model to**:
1. Interpret unclear intent
2. Fill in missing context
3. Make assumptions

**Result**: Increased error rate, inconsistent behavior

**Example**:
```python
# ❌ BAD: Lazy prompt
"Help with hiring"

# Model must guess:
# - Help with what aspect of hiring?
# - What role? What criteria?
# - What output format?
# - What data to use?
```

#### 3.4.2 Intelligent Prompts (Low AI Intelligence Required)

**Clear, detailed prompts allow the model to focus on**:
1. Executing the task correctly
2. Producing high-quality outputs

**Result**: Better performance, fewer failures

**Example**:
```python
# ✅ GOOD: Intelligent prompt
"Evaluate these 5 candidates against the Senior Engineer job requirements. Focus on:
- Python skills (5+ years experience)
- System design experience (demonstrated in projects)
- Team leadership (direct reports or mentorship)

For each candidate, provide:
1. Skill match score (0-100)
2. Key strengths (3 bullet points)
3. Potential concerns (if any)
4. Hiring recommendation (Strong Yes / Yes / Maybe / No)"
```

#### 3.4.3 Literacy Consideration

**AI interprets instructions literally**—no reading between the lines.

**Key Implications**:
- When providing sample phrases, models may use them **verbatim**
- Instruct to **vary language** as needed
- Ambiguous language creates **unpredictable behavior**

**Example**:
```python
# ❌ BAD: Model will copy phrases exactly
When rejecting candidates, say: "Thank you for your interest, but we've decided to move forward with other candidates."

# ✅ GOOD: Instruct to vary
When rejecting candidates, provide a professional, empathetic response. Vary your language for each candidate—avoid templated phrases. Acknowledge their time investment and wish them well in their job search.
```

### 3.5 Reusability Strategies

Minimize total number of instructions and their length through **strategic reuse patterns**.

#### 3.5.1 Variables (Dynamic Parameter Injection)

**When to use**: Content is mostly fixed but needs configurable parameters

**Pattern**: `{{PARAMETER_NAME}}` placeholders replaced at runtime

**Benefits**:
- Single instruction template
- Runtime flexibility
- Easy to maintain

**Selection Criteria**: **20-50% variability**

**Example**:
```jinja2
You are analyzing {{CONTENT_TYPE}} content with {{FIDELITY_LEVEL}} fidelity.

Your compression ratio target is {{COMPRESSION_RATIO}} (e.g., 0.5 = 50% reduction).
```

#### 3.5.2 Composable Modules (Building Block Assembly)

**When to use**: Content has clear functional boundaries that can be mixed/matched

**Pattern**: `BASE_MODULE + SPECIALIZED_MODULE + GUARDRAILS`

**Benefits**:
- Modular composition
- Easier maintenance
- Clear separation of concerns

**Selection Criteria**: **50-80% variability**

**Example**:
```python
# composables.py
def compose_agent_capabilities():
    return (
        BASE_CAPABILITIES +
        DATA_CAPABILITIES +
        CANVAS_CAPABILITIES +
        OPERATING_CAPABILITIES
    )

# instruction.py
INSTRUCTION = (
    IDENTITY +
    MISSION +
    compose_agent_capabilities() +
    FORMATTING +
    GUARDRAILS
)
```

#### 3.5.3 Message-Based Specificity (Dynamic Strategy Selection)

**When to use**: Strategy should be determined by input content rather than fixed instructions

**Pattern**: Analyze message content to select optimal processing approach

**Benefits**:
- Maximum flexibility
- Input-driven adaptation
- Reduced instruction complexity

**Selection Criteria**: **>80% variability**

**Example**:
```python
def select_compression_strategy(message_content):
    """Determine compression strategy based on message content."""
    if "compress to 1000 tokens" in message_content:
        return TOKEN_BUDGET_COMPRESSION
    elif "technical content" in message_content:
        return TECHNICAL_PRESERVATION
    elif "research sources" in message_content:
        return RESEARCH_SYNTHESIS
    else:
        return STANDARD_COMPRESSION
```

#### 3.5.4 Selection Criteria Summary

| Variability | Strategy | Implementation |
|-------------|----------|----------------|
| <20% | Fixed instructions | No variables/composables needed |
| 20-50% | Variables | Jinja2 templates with `{{PLACEHOLDERS}}` |
| 50-80% | Composables | Modular functions with `+` operators |
| >80% | Message-based | Dynamic selection based on input analysis |

### 3.6 Chain Prompting

Multi-step tasks benefit from **breaking down into sequential subtasks** with clear handoffs.

**When to Chain**:
- Complex tasks requiring multiple transformations
- Document analysis with citations
- Iterative content creation
- Research synthesis

**How to Chain**:
1. **Identify subtasks**: Break into distinct, sequential steps
2. **Structure with XML**: Use tags for clear handoffs
3. **Single-task goals**: Each subtask has one clear objective
4. **Iterate**: Refine based on performance

**Example**:
```xml
<step_1>
Analyze the provided documents and extract key themes.
Output: List of 5-7 themes with supporting evidence.
</step_1>

<step_2>
For each theme from step_1, identify contradictions or gaps in the evidence.
Output: Table of themes with assessment of evidence quality.
</step_2>

<step_3>
Synthesize findings into a coherent analysis with recommendations.
Output: 3-paragraph summary with 3 actionable recommendations.
</step_3>
```

**Thinking Out Loud**:
- Models improve accuracy when asked to **"think step by step"**
- Explicit reasoning reduces errors in math, logic, analysis
- **Caution**: Thinking only counts when it's output—can't think silently then respond

---

## 4. Instruction Anatomy

AI agent instructions follow a **hierarchical structure** from broad to specific:

**Identity → Mission → Goals → Responsibilities → Tasks → Functions**

This cascade is **mandatory and internally consistent**, but **not all levels are required for every agent**. The hierarchy must be complete up to the deepest level used (e.g., if you define Tasks, you must have Responsibilities, Goals, and Mission).

### 4.1 Identity / Role

**Purpose**: Define who the AI is—its domain expertise, specialization, and creation context.

**Placement**: Opening sentence (maximum model weighting)

**Structure**:
```
You are [ROLE] created by [CREATOR]. [Domain expertise and specialization].
```

**Best Practices**:
- Be specific about domain expertise
- Avoid vague descriptors like "helpful assistant"
- Link role to platform context ("designed to serve HR professionals")

**Examples from Codebase**:
```python
# General assistant
You are an HR expert designed to serve HR professionals within organizations.

# Specialized agent
You are the Skills Analyzer, an AI specialist in workforce competency assessment and talent mapping.

# Middleware processor
You are a content routing system designed to classify and direct user requests to appropriate processing pipelines.
```

**When to Include**:
- ✅ All conversational agents
- ✅ Specialized domain agents (CDO, Skills, Research)
- ⚠️ Optional for simple middleware processors
- ❌ Not needed for pure data transformations

### 4.2 Mission

**Purpose**: Define core purpose statement and overarching objective—the "why" of the agent's existence.

**Placement**: Immediately after Identity

**Structure**:
```
Your mission is to [PRIMARY OBJECTIVE] so [STAKEHOLDER] can [DESIRED OUTCOME].
```

**Best Practices**:
- One sentence, action-oriented
- Clearly state **who benefits** and **how**
- Link **means** (what agent does) to **ends** (value delivered)
- Avoid buzzwords—be concrete and specific

**Examples from Codebase**:
```python
# General assistant
Your mission is to resolve user asks by orchestrating the system's capabilities—coordinating specialized agents, components, and data management to deliver value.

# Hiring workflow agent
Your mission is to execute and orchestrate end-to-end hiring workflows so HR professionals complete key tasks faster with higher quality and less manual effort across sourcing, screening, scheduling, interview operations, offers, and onboarding.

# Skills agent
Your mission is to make skills visible, comparable, and actionable so HR professionals can understand current skills, define talent needs, and analyze the significance of skills to drive decisions on upskilling, redeployment, hiring, and workforce planning.

# Research agent
Your mission is to find, fuse, analyze, and explain hard-to-get information across internal data and external integrations so HR professionals can make correct, timely decisions by reducing uncertainty through verified facts, synthesized insights, and quantified confidence.
```

**When to Include**:
- ✅ All agents with significant autonomy
- ✅ Agents orchestrating multiple capabilities
- ⚠️ Optional for simple function-specific agents
- ❌ Not needed for pure formatters or validators

### 4.3 Goals

**Purpose**: Specify **measurable success outcomes** and primary value delivered.

**Placement**: After Mission statement

**Structure**:
```
Your goals are to:
- [Measurable outcome 1]
- [Measurable outcome 2]
- [Measurable outcome 3]
```

**Best Practices**:
- Use **action verbs** (enable, optimize, automate, identify, synthesize)
- Make outcomes **measurable** when possible
- Limit to **3-5 key goals** to maintain focus
- Align with Mission statement

**Examples from Codebase**:
```python
# General assistant goals
Your goals are to enable HR professionals to:
- Optimize talent management through data-driven insights
- Make informed decisions about employees and candidates
- Automate repetitive HR workflow tasks

# Research agent goals (objectives format)
# Objectives
- **Find**: Locate, extract, and normalize relevant data from internal systems and external sources
- **Validate**: Cross-check claims, quantify data quality, resolve contradictions, document assumptions
- **Analyze**: Compute effect sizes, trends, base rates, and deltas; test alternative explanations
- **Synthesize**: Deliver minimum sufficient explanation and recommended next steps, with citations
```

**When to Include**:
- ✅ Agents with broad scope requiring focus
- ✅ Agents with multiple capabilities needing prioritization
- ⚠️ Optional for single-purpose agents
- ❌ Not needed for simple transformations

### 4.4 Responsibilities

**Purpose**: Clarify **accountability scope** and **operational boundaries**—what the agent is responsible for and what it should escalate.

**Placement**: Embedded within Operating Principles or as standalone section

**Structure**:
```
# Responsibilities

You are accountable for:
- [Accountability item 1]
- [Accountability item 2]

You must escalate when:
- [Escalation condition 1]
- [Escalation condition 2]

You are NOT responsible for:
- [Out-of-scope item 1]
- [Out-of-scope item 2]
```

**Best Practices**:
- Define what agent **is accountable for**
- Specify **operational scope** (what's in/out of scope)
- Clarify **decision-making authority**
- Set boundaries for when to **escalate**

**Examples from Codebase**:
```python
# Operating Principles (embedded responsibilities)
Keep going until the user ask is completely resolved, before ending your workflow task. Only terminate your workflow task when you are sure that the problem is solved and the desired outcome is provided, or when you've exhausted all available tool combinations without achieving the desired outcome.

Be proactive in addressing user needs, as users can always reject, modify or accept proposed actions, solutions, decisions and/or changes.

# Explicit responsibility boundaries
You are responsible for:
- Data retrieval and validation
- Insight generation and recommendations
- Tool orchestration and error recovery

You must escalate to specialized agents when:
- Complex data transformations are required
- Legal or compliance review is needed
- User explicitly requests human intervention

You are NOT responsible for:
- Final decision-making (users decide)
- Data persistence without confirmation
- Modifying permissions or access control
```

**When to Include**:
- ✅ Agents with autonomous decision-making
- ✅ Agents coordinating multiple tools/subagents
- ⚠️ Optional for agents with narrow scope
- ❌ Not needed for pure data processors

### 4.5 Tasks

**Purpose**: Describe **concrete work units** the AI must perform—the "what" at an operational level.

**Placement**: Within Capabilities section or as standalone section

**Structure**:
```
## [Task Category]

- **[Task Name]**: [Description of what the task accomplishes]
- **[Task Name]**: [Description of what the task accomplishes]
```

**Best Practices**:
- Group related tasks into **logical categories**
- Use **descriptive task names**
- Provide enough detail for execution without **over-prescribing**
- Link tasks to **capabilities**

**Examples from Codebase**:
```python
## Data Management

- **Cross-Source Validation**: When data seems incomplete or unavailable in one source, progress to other sources before concluding information is unavailable.
- **Progressive Discovery**: Start with general searches to see what's available, then get more specific based on what you find.
- **Context Preservation**: Consider previous retrieval results throughout the process.

## Canvas Components

Components are specialized tools that generate structured outputs—visualizations, documents, analyses, and strategic artifacts—beyond standard conversational responses.

**Component Implementation**: Create components when users directly request them or when user asks require the specialized capabilities described in component functionalities.
```

**When to Include**:
- ✅ Agents with multiple distinct capabilities
- ✅ Complex workflows requiring task breakdown
- ⚠️ Optional for simple single-purpose agents
- ❌ Not needed when capabilities are self-explanatory

### 4.6 Functions

**Purpose**: Outline **structured steps or logic** for task execution—the "how" with detailed procedural guidance.

**Placement**: Within Tasks section or as standalone process documentation

**Structure**:
```
## [Function/Process Name]

1. **[Step 1]**: [Action and criteria]
2. **[Step 2]**: [Action and criteria]
3. **[Step 3]**: [Action and criteria]
```

**Best Practices**:
- Provide **step-by-step execution logic** when helpful
- Use **numbered lists** for sequential processes
- Include **decision points** and branching logic
- Balance **specificity with flexibility**

**Examples from Codebase**:
```python
## Retrieval Strategy (7-step process)

1. **Plan** the minimal evidence needed to answer the User Ask
2. **List** candidate sources; select those with highest expected signal-to-noise
3. **Fetch** in parallel when independent; otherwise sequence by dependency
4. **Validate** via cross-source checks; reconcile conflicts (state reasoning)
5. **Quantify**: Compute baselines, deltas, confidence, and uncertainty bounds
6. **Synthesize**: Compress to essentials; include trade-offs and next steps
7. **Cite**: Attach sources to each non-trivial claim

## Component Guidelines

**Component Implementation**: create components when users directly request them or when user asks require the specialized capabilities described in component functionalities. Evaluate each user ask based on functional requirements, user intent, and complexity signals to determine whether component-level processing is needed.
```

**When to Include**:
- ✅ Complex multi-step processes
- ✅ Tasks requiring specific execution order
- ✅ Processes with decision trees or branching
- ⚠️ Optional when tasks are straightforward
- ❌ Not needed for simple atomic operations

### 4.7 Hierarchy Decision Matrix

Use this matrix to determine which levels to include:

| Agent Type | Identity | Mission | Goals | Responsibilities | Tasks | Functions |
|------------|----------|---------|-------|------------------|-------|-----------|
| **General Assistant** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **Specialized Agent** (CDO, Skills) | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| **Research Agent** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Middleware Processor** | ⚠️ | ⚠️ | ❌ | ⚠️ | ✅ | ⚠️ |
| **Function Agent** (Canvas) | ⚠️ | ⚠️ | ❌ | ❌ | ✅ | ⚠️ |
| **Data Transformer** | ❌ | ❌ | ❌ | ❌ | ⚠️ | ⚠️ |

**Legend**:
- ✅ **Required**: Essential for this agent type
- ⚠️ **Optional**: Include if it adds clarity or control
- ❌ **Not Needed**: Skip to reduce instruction length

---

## 5. Implementation Patterns

### 5.1 Template Architecture

The platform uses **Jinja2 templates** for modular, reusable instructions.

#### 5.1.1 Basic Template Pattern

**File**: `instruction.j2`

```jinja2
You are an HR expert designed to serve HR professionals within organizations.

Your mission is to resolve user asks by orchestrating the system's capabilities.

{{OPERATING_PRINCIPLES}}

{{AGENT_CAPABILITIES}}

{{BASE_FORMATTING}}

{{CONVERSATIONAL_GUARDRAIL}}
```

**Benefits**:
- **DRY Principle**: Define common patterns once, reuse across agents
- **Consistency**: All agents follow same core patterns
- **Maintainability**: Update shared logic in one place
- **Customization**: Override or extend base patterns per agent

#### 5.1.2 Variable Sources

Variables come from two sources:

**1. Fixed Text Blocks** (`values.py`):
```python
# values.py - UPPERCASE constants
OPERATING_PRINCIPLES = """
# Operating Principles

Keep going until the user ask is completely resolved...
"""

AGENT_GUARDRAIL = """
# Guardrails

Use only verified data from available sources...
"""
```

**2. Runtime Variables** (call site):
```python
from messages.instruction_service import render_prompt

agent_prompt = render_prompt("agents/assistant",
                            USER_NAME=user.full_name,
                            COMPANY_NAME=company.name,
                            USER_ROLE=user.role,
                            CONVERSATION_HISTORY=history)
```

#### 5.1.3 Composable Functions

**File**: `composables.py`

```python
def compose_agent_capabilities():
    """Assemble complete agent capabilities from modules."""
    return (
        BASE_CAPABILITIES +
        "\n\n" +
        DATA_CAPABILITIES +
        "\n\n" +
        CANVAS_CAPABILITIES +
        "\n\n" +
        OPERATING_CAPABILITIES
    )

def compose_agent_guardrail():
    """Assemble agent-specific guardrails."""
    return (
        OPERATION_GUARDRAILS +
        "\n\n" +
        BEHAVIOR_GUARDRAILS
    )
```

**Usage in Template**:
```jinja2
{{compose_agent_capabilities()}}

{{compose_agent_guardrail()}}
```

**When to Use Composables**:
- Modular assembly of instruction blocks
- Conditional inclusion of sections
- Complex composition logic
- Reusable patterns across multiple agents

### 5.2 Operating Principles

Defines **how the agent thinks and behaves** during execution.

**Key Patterns**:
- **Clear Communication**: Explain progress naturally without verbosity
- **Task Persistence**: Keep going until user ask is resolved
- **Proactive Action-Taking**: Users can always reject/modify/accept
- **Intelligent Tool Orchestration**: Parallel execution when possible
- **Adaptive Error Recovery**: Retry with adjusted parameters
- **Specialized Agent Coordination**: Handoff when expertise needed

**Example**:
```python
OPERATING_PRINCIPLES = """
# Operating Principles

## Task Completion

Keep going until the user ask is completely resolved, before ending your workflow task. Only terminate when:
- Problem is solved and desired outcome is provided, OR
- You've exhausted all available tool combinations without achieving the outcome

## Proactive Behavior

Be proactive in addressing user needs—users can always reject, modify, or accept proposed actions, solutions, decisions, and changes.

## Tool Orchestration

- **Parallel Execution**: Use tools in parallel when tasks are independent
- **Sequential Dependencies**: Execute in sequence when outputs depend on previous steps
- **Error Recovery**: Retry with adjusted parameters (up to 2 attempts)
- **Alternative Strategies**: Try alternative tools if primary approach fails

## Agent Coordination

Transfer to specialized agents when their expertise better serves the user's needs. Provide complete context during handoffs.
"""
```

**When to Include**:
- ✅ All autonomous agents
- ✅ Agents with tool orchestration
- ⚠️ Optional for simple function agents
- ❌ Not needed for pure data processors

### 5.3 Capabilities Modules

Modular system defining **what the agent can do**—composable building blocks.

**Standard Modules**:
- **BASE_CAPABILITIES**: Core interaction patterns
- **DATA_CAPABILITIES**: Data retrieval, creation, update
- **CANVAS_CAPABILITIES**: Artifact generation (documents, charts, diagrams)
- **OPERATING_CAPABILITIES**: Tool usage, agent coordination

**Example**:
```python
# capabilities/v2/values.py

BASE_CAPABILITIES = """
## Core Capabilities

- **Conversational Interaction**: Engage in natural dialogue with users
- **Context Awareness**: Maintain conversation context across turns
- **Adaptive Responses**: Adjust tone and detail based on query complexity
"""

DATA_CAPABILITIES = """
## Data Management

- **Retrieval**: Search, list, and read data from multiple sources
- **Creation**: Create new records with validation
- **Update**: Modify existing records with proper authorization
- **Cross-Source Validation**: Verify data across multiple sources
"""

CANVAS_CAPABILITIES = """
## Canvas Components

Components are specialized tools that generate structured outputs:
- **Documents**: Job descriptions, emails, reports
- **Visualizations**: Charts, heatmaps, diagrams
- **Analyses**: Data analysis, comparisons, insights
"""

# composables.py
def compose_agent_capabilities():
    return (
        BASE_CAPABILITIES +
        "\n\n" +
        DATA_CAPABILITIES +
        "\n\n" +
        CANVAS_CAPABILITIES +
        "\n\n" +
        OPERATING_CAPABILITIES
    )
```

**Benefits**:
- **Reusability**: Define once, use across agents
- **Flexible Composition**: Mix and match modules
- **Maintainability**: Update modules independently
- **Clear Separation**: Each module has single responsibility

### 5.4 Guardrails

Two-dimensional safety framework governing **data handling** and **interaction behavior**.

**Guardrail Dimensions**:

**1. Operation Guardrails** (Data Integrity):
- Prevent information fabrication
- Ensure transparency about limitations
- Handle missing data gracefully
- Validate sources before using

**2. Behavior Guardrails** (Interaction Patterns):
- Respond in user's language
- Adapt tone to query complexity
- Handle sensitive topics appropriately
- Evaluate claims critically

**Example**:
```python
# guardrails/v2/values.py

OPERATION_GUARDRAILS = """
# Operation Guardrails

## Data Integrity

- Use only verified data from available sources
- If data is incomplete, return partial results with clear indication of missing fields
- **Never fabricate or infer data** that isn't explicitly available
- Flag assumptions with (assumption) label

## Source Validation

- Cross-check claims through multiple sources
- Document source quality and recency
- Prioritize primary sources over aggregated sources
- Cite sources for all non-trivial claims
"""

BEHAVIOR_GUARDRAILS = """
# Behavior Guardrails

## Language Matching

Respond in the same language as the user query. If user asks in Spanish, respond in Spanish.

## Response Adaptation

- Simple questions: Brief, direct answers
- Complex questions: Comprehensive, detailed analysis
- Technical queries: Use domain-specific terminology
- General queries: Use accessible language

## Sensitive Topics

Handle sensitive HR topics (terminations, compensation, performance issues) with appropriate professional tone and confidentiality awareness.
"""

# composables.py
def compose_agent_guardrail():
    return OPERATION_GUARDRAILS + "\n\n" + BEHAVIOR_GUARDRAILS
```

**Layering Strategy** (general → specific):
1. **Platform-wide guardrails**: Apply to all agents
2. **Agent-type guardrails**: Apply to agent categories (conversational, middleware)
3. **Agent-specific guardrails**: Apply to individual agents

### 5.5 Formatting

Guidelines ensuring **consistent, professional response output**.

**Core Principles**:
- **Adapt to Request**: Match format to user's specific request
- **Default to Prose**: Use prose for readability unless structure required
- **Strategic Markdown**: Use markdown for clarity (headers, lists, emphasis)
- **Specialized Formats**: Cards for metrics/objects, tables for comparisons

**Example**:
```python
# formatting/v2/values.py

BASE_FORMATTING = """
# Response Formatting

## Default Format

Use prose format for most responses—natural, flowing text that's easy to read and scan.

## When to Use Structured Formats

- **Lists**: When presenting multiple discrete items
- **Tables**: When comparing data across dimensions
- **Cards**: When displaying metrics or object summaries
- **Code blocks**: When showing JSON, SQL, or technical examples

## Markdown Usage

- Use headers (##, ###) to organize long responses
- Use **bold** for key terms or important concepts
- Use bullet points for clarity, not as default
- Keep formatting clean and minimal
"""

CONVERSATIONAL_FORMATTING = """
# Conversational Formatting

## Tone

- Professional but approachable
- Clear and direct
- Avoid jargon unless domain-specific
- No flattery ("That's a great question...")

## Length Adaptation

- Very simple questions: 1-2 sentence answers
- Standard questions: 1-2 paragraph answers
- Complex questions: Multi-paragraph detailed responses
- Open-ended questions: Comprehensive analysis
"""
```

### 5.6 Domain Frameworks

Some agents require **specialized taxonomies, scales, or frameworks** for their domain.

**When to Include Domain Frameworks**:
- ✅ Agent requires specialized domain knowledge to function
- ✅ Framework improves consistency and quality of outputs
- ✅ Industry-standard taxonomies or scales exist
- ✅ Complex domain logic needs explicit codification
- ❌ Generic knowledge already possessed by base model
- ❌ Framework would over-constrain agent behavior

**Example 1: Skills Agent KSAC Framework**:
```python
KSAC_FRAMEWORK = """
# Skill Framework & Taxonomy

## KSAC Components

### Competence (C)
Broad, outcome-driven, cross-functional domains requiring blended abilities.
**Examples**: Data Analysis, Project Management, Leadership

### Skill (S)
Task-focused, actionable, measurable, transferable capabilities independent of tools.
**Examples**: Data Cleaning, Coding, Negotiation

### Knowledge (K)
Theoretical foundations, methodologies, regulatory frameworks enabling execution.
**Examples**: Data Protection Regulations, ML Model Evaluation Techniques

### Attitude (A)
Mindsets, beliefs, values, dispositions toward work, people, and challenges.
**Examples**: Growth Mindset, Resilience, Customer Orientation

## Classification Guidelines

When classifying skills:
1. Start with the most specific category (K/S/A)
2. If multiple skills cluster around an outcome, consider Competence
3. Technical know-how = Skill, not Knowledge
4. Theoretical understanding = Knowledge
5. Behavioral traits = Attitude
"""
```

**Example 2: Research Agent Priority Hierarchy**:
```python
RESEARCH_PRIORITIES = """
# Priority Hierarchy

When conducting research, prioritize in this order:

1. **Truthfulness & Precision** - Accuracy and reproducibility over speed
2. **Evidence Quality** - Primary sources, proper methodology
3. **Relevance to User Ask** - Direct alignment with question
4. **Completeness** - Coverage of key perspectives
5. **Speed** - Efficiency without sacrificing quality

## Evidence Quality Rubric (score 1–5)

**Authority** (1=blog, 5=primary source):
- Primary/official sources > aggregated sources > blogs

**Recency** (1=outdated, 5=current):
- Timestamped content covering the right time period

**Method** (1=opaque, 5=rigorous):
- Transparent methodology, stated sample size, reproducible

**Independence** (1=circular, 5=independent):
- Not circularly citing the same origin

**Relevance** (1=tangential, 5=precise match):
- Matches the precise question or segment being answered
"""
```

---

## 6. Optimization Guidelines

### 6.1 Simple and Clear

**The most important prompting technique**: Write clear, detailed instructions that leave **no room for ambiguity**.

**Best Practices**:
- Use direct, unambiguous language
- Break down multi-step instructions into simpler steps
- Avoid jargon unless domain-specific and necessary
- State exactly what you want—models interpret literally

**Examples**:

❌ **Vague**:
```python
"Help with hiring"
```

✅ **Clear**:
```python
"Evaluate these 5 candidates against the Senior Engineer job requirements focusing on Python skills, system design experience, and team leadership"
```

❌ **Ambiguous**:
```python
"Make it better"
```

✅ **Specific**:
```python
"Increase proficiency scores for candidates who have 5+ years of experience in the skill by 10 points, capped at maximum of 95"
```

### 6.2 Generalization (Heuristics over Rigid Rules)

Use **flexible heuristics** that provide guiding principles rather than rigid rules for specific situations.

**Benefits**:
- **Scalability**: Works across different domains without rewriting
- **Robustness**: Less prone to catastrophic failures when conditions change
- **Intelligent Adaptation**: Allows sophisticated behavior without rigidity

**Pattern**:

❌ **Rigid Rule**:
```python
If candidate has Python experience AND degree in CS AND 5+ years experience, set score to 75.
If candidate has Python experience AND degree in CS AND 3-4 years experience, set score to 60.
If candidate has Python experience AND no degree AND 5+ years experience, set score to 65.
[... 50 more specific rules]
```

✅ **Heuristic**:
```python
Assess Python proficiency (0-100) based on:
- Depth and recency of experience (weight recent higher)
- Project complexity and demonstrable impact
- Formal education and certifications
- Code quality evidence and peer validation

Use critical judgment rather than rigid formulas.
```

**Abstraction over Specification**:

Frame instructions around **domain behavior understanding** rather than enumerating specific actions.

❌ **Specific Rule**:
```python
When disqualifying candidates, send feedback emails notifying them of disqualification.
```

✅ **Abstract Principle**:
```python
Understand natural HR workflow behaviors and patterns. Pay attention to user intent and tool call descriptions that indicate related actions and natural follow-through steps in the process.
```

**Why This Matters**:
- **Extensibility**: Adding new tools doesn't require instruction changes
- **Emergent Behavior**: Agent discovers appropriate actions through domain understanding
- **Reduced Maintenance**: Instructions remain stable as capabilities expand

### 6.3 Input Analysis (Why over What)

Don't just name or describe inputs—**explain why they matter and how the model should treat them**.

**Pattern**:

❌ **What only**:
```python
You will receive candidate data including name, email, skills, experience.
```

✅ **What + Why**:
```python
You will receive candidate data including:
- **Name & email**: Use for identification and communication context only; never expose in public outputs
- **Skills list**: Core evaluation criteria—assess depth, recency, and validation level
- **Experience**: Weight recent experience higher; look for progression and impact
```

**Benefits**:
- Model understands intent behind each input
- Reduces misuse or misinterpretation of data
- Enables intelligent handling of edge cases

### 6.4 Reasoning Steps (Chain of Thought)

For complex tasks, giving models space to think dramatically improves performance.

**When to Use**:
- Math or logic problems
- Multi-step analysis
- Research synthesis
- Complex decision-making

**How to Implement**:
```python
First, think carefully step by step about what data is needed to answer the query. Then, identify the most reliable sources. Then, validate findings through cross-referencing. Finally, synthesize into minimum sufficient explanation.
```

**Caution**: Thinking only counts when it's output. Can't ask to "think silently" then respond.

**Alternative Phrasing**:
- "Think step by step before responding"
- "Explain your reasoning for each decision"
- "Walk through your analysis process"
- "Show your work before final answer"

### 6.5 Avoid Contradictions

Contradictions and ambiguities degrade performance. Advanced reasoning models follow instructions with extreme precision, making contradictions especially harmful.

**Resolution Strategies**:

**Priority Hierarchies**:
```python
In case of conflict between speed and accuracy, **always prioritize accuracy**.

When data quality is uncertain, clearly state assumptions rather than fabricating.
```

**Contextual Exceptions**:
```python
General rule: Verify credentials before proceeding.
Exception: In time-sensitive situations, proceed with available data and flag for later verification.
```

**Execution Order**:
```python
Processing sequence:
1. Validate inputs
2. Retrieve data
3. Analyze and synthesize
4. Generate response
5. Apply guardrails
```

### 6.6 Formatting (XML and Markdown)

Help models understand logical boundaries using **Markdown** for structure and **XML** for content boundaries.

**Markdown for Structure**:
```markdown
# Main Section

## Subsection

### Details

- Key point 1
- Key point 2
```

**XML for Content Boundaries**:
```xml
<context>
Background information, supporting documents, reference data
</context>

<instructions>
Task-specific rules and requirements
</instructions>

<examples>
  <example>
    Input: "Show me skills for John Doe"
    Output: [Skills list with proficiency scores]
  </example>
</examples>
```

**When to Use XML**:
- Delineating content sections (context, examples, data)
- Defining metadata about content
- Creating super-structured, high-performance prompts
- Handling content that might contain Markdown

**Best Practices**:
- Use consistent tag names across instructions
- Nest tags logically
- Keep tags descriptive (`<context>` not `<c>`)

### 6.7 Output Specifications

Clearly define what the model should produce.

**Content Requirements**:
```python
Your response must include:
1. Analysis summary (2-3 paragraphs)
2. Top 3 recommendations with rationale
3. Risk assessment for each recommendation
4. Next steps with timeline
```

**Format Specification**:
```json
{
  "employee_name": "Full name of employee",
  "department": "Department name",
  "skills": [
    {
      "skill_name": "Name of skill",
      "level": 75  // 0-100 scale
    }
  ],
  "hire_date": "YYYY-MM-DD",
  "is_active": true  // boolean
}
```

**Edge Cases**:
```python
Edge case handling:
- If no candidates match criteria, return empty array with explanation in "insights" field
- If data is incomplete, include partial results and flag missing data
- If confidence is low (<60%), include disclaimer in response
```

### 6.8 Sampling (Few-Shot Examples)

Examples are powerful but require careful use to avoid over-rigidity.

**Crafting Effective Examples**:
- **Relevant**: Mirror actual use cases
- **Diverse**: Cover edge cases and variations
- **Clear**: Wrapped in `<example>` tags

**Reducing Example Bias**:
- Expand number of examples (3-5 minimum)
- Explicitly state examples are reference only
- Vary structure, tone, length across examples
- Include disclaimer: "These examples are for reference only. Each output should be unique and adapted to the specific situation."

**Example**:
```xml
<examples>
  <example>
    Input: "Show skills for John"
    Output: [Detailed skills list with proficiency scores]
  </example>
  <example>
    Input: "Who has Python skills?"
    Output: [Employee list filtered by Python, sorted by proficiency]
  </example>
  <example>
    Input: "Compare Alice and Bob's skills"
    Output: [Comparison table with skill gaps highlighted]
  </example>
</examples>

Note: These examples are for reference only. Adapt format and content to each specific request.
```

---

## 7. Advanced Techniques

### 7.1 System Resiliency

Build **error handling** and **graceful degradation** into instructions.

**Error Handling**:
```python
When tool calls fail:
1. Retry with adjusted parameters (up to 2 times)
2. Try alternative tool with similar functionality
3. If all attempts fail, explain limitation clearly to user
4. Never fabricate data to mask failures
```

**Graceful Degradation**:
```python
If complete data is unavailable:
- Return partial results with clear indication of what's missing
- Explain what additional data would improve response
- Provide best-effort answer based on available information
- Flag assumptions made due to data gaps
```

### 7.2 Avoid Negative Phrasing

Focus on what the AI **should do** rather than what it **should not do**.

❌ **Negative**:
```python
Don't fabricate information. Don't make assumptions. Don't provide incomplete answers.
```

✅ **Positive**:
```python
Use only verified data from available sources. Clearly label any assumptions made. Provide complete answers or explain what information is missing.
```

**Why It Matters**:
- Positive framing is clearer and more actionable
- Models respond better to affirmative instructions
- Reduces ambiguity about desired behavior

### 7.3 Conversational Models

Special considerations for agents engaged in multi-turn conversations.

**User Isn't Always Right**:
```python
Critically evaluate any theories, claims, and ideas presented rather than automatically agreeing. Prioritize truthfulness and accuracy over agreeability.

If users claim you've made a mistake, think through the issue carefully before acknowledging, since users sometimes make errors themselves.
```

**Response Length Adaptation**:
```python
Give concise responses to very simple questions, but provide thorough responses to complex and open-ended questions.
```

**No Flattery**:
```python
Never start responses by saying a question or idea was "good," "great," "fascinating," or any other positive adjective. Skip the flattery and respond directly.
```

**Direct Answers**:
```python
If you cannot or will not help with something, do not explain why or what it could lead to, since this comes across as preachy. Keep response to 1-2 concise sentences.
```

### 7.4 Spatiality Awareness

AI lacks inherent understanding of positional or temporal references.

**Avoid Spatial References**:
- ❌ "As mentioned above"
- ❌ "The previous section"
- ❌ "Below you'll find"
- ❌ "Refer to the earlier example"

**Use Direct References**:
- ✅ "In the Data Management section"
- ✅ "The Search → List → Read pattern"
- ✅ "Using the KSAC framework"
- ✅ "As stated in the mission statement"

### 7.5 Terminology Consistency

Use the same terms for the same concepts throughout instructions.

**Establish Glossary Early**:
```python
# Terminology
- **candidate** (not applicant, job seeker, prospect)
- **HR professional** (not user, admin, recruiter)
- **job details** (not job description)
- **organization** (not company, firm)
- **User Ask** (not query, request, prompt)
```

**Enforce Throughout**:
- Don't alternate between synonyms
- Capitalize key terms consistently
- Define domain-specific terms once
- Reference glossary in behavior guidelines

---

## 8. Quality Assurance

### 8.1 Pre-Deployment Checklist

Use this checklist before deploying or updating agent instructions.

#### Structure & Completeness

- [ ] **Identity/Role** clearly stated in opening sentence
- [ ] **Mission** defines core purpose and value delivered in one sentence
- [ ] **Goals** specify 3-5 measurable success outcomes
- [ ] **Responsibilities** clarify accountability scope and boundaries
- [ ] **Operating Principles** specify tool orchestration, parallel execution, retry logic
- [ ] **Capabilities** comprehensively cover required domains

#### Guardrails & Safety

- [ ] **Operation guardrails** prevent fabrication, enforce language matching, handle missing data
- [ ] **Behavior guardrails** address sensitive topics, define transparency requirements
- [ ] **Input guardrails** (if applicable) validate requests for relevance, safety, compliance
- [ ] **Output guardrails** (if applicable) prevent PII leakage, ensure brand safety
- [ ] **Error handling** defined for tool failures, missing data, edge cases

#### Formatting & Response Guidelines

- [ ] **Response format** specified (prose-first, markdown structure, specialized formats)
- [ ] **Citation format** defined if sources/references required
- [ ] **Output structure** clarified (JSON schema, report sections, visualization types)
- [ ] **Tone and style** appropriate for target audience and use case

#### Quality & Maintainability

- [ ] **No contradictions** or ambiguous instructions present
- [ ] **Terminology consistent** throughout (same terms for same concepts)
- [ ] **Reusable variables** used for common patterns (`{{PLACEHOLDER}}`)
- [ ] **Examples provided** for complex behaviors (if applicable)
- [ ] **Priority hierarchies** defined for conflicting requirements
- [ ] **Execution order** clear for multi-step processes
- [ ] **Domain frameworks** included if specialized knowledge required

#### Optimization

- [ ] **Model weighting** considered (critical items at start/end)
- [ ] **Scope clearly defined** (input and output variability)
- [ ] **XML tags** used for content boundaries where helpful
- [ ] **Reasoning steps** included for complex tasks
- [ ] **Positive phrasing** used instead of negative
- [ ] **Spatial references** avoided (no "above/below/previous")

### 8.2 Common Anti-Patterns

#### 8.2.1 Over-Prescriptive Rules

❌ **Problem**: Rigid rules that don't adapt to context

```python
If candidate has Python experience AND degree in CS AND 5+ years experience, set score to 75.
[... 50 more specific rules]
```

✅ **Solution**: Flexible heuristics

```python
Assess Python proficiency holistically based on depth and recency of experience, project complexity, education, and code quality evidence.
```

#### 8.2.2 Contradictory Instructions

❌ **Problem**: Conflicting requirements without resolution

```python
Always provide comprehensive, detailed analysis.
Keep responses brief and concise.
```

✅ **Solution**: Clear priority hierarchies

```python
Response length should match query complexity:
- Simple questions: Brief, direct answers
- Complex questions: Comprehensive, detailed analysis
```

#### 8.2.3 Positional References

❌ **Problem**: AI can't interpret spatial relationships

```python
As mentioned above in the previous section...
```

✅ **Solution**: Direct, explicit references

```python
As defined in the Mission statement...
Using the KSAC framework...
```

#### 8.2.4 Inconsistent Terminology

❌ **Problem**: Alternating between synonyms

```python
Evaluate the candidate's skills...
Assess the applicant's competencies...
Review the job seeker's capabilities...
```

✅ **Solution**: Establish and enforce glossary

```python
# Terminology
- candidate (consistent usage)
- skills (consistent usage)

Evaluate the candidate's skills...
```

#### 8.2.5 Over-Use of Examples

❌ **Problem**: Too many or too similar examples cause rigidity

```xml
<examples>
  <example>Response in this exact format...</example>
  <example>Response in this exact format...</example>
  [... 10 more identical examples]
</examples>
```

✅ **Solution**: Diverse, focused examples with disclaimer

```xml
<examples>
  <example>Input: "Show skills for John" Output: [Detailed skills list]</example>
  <example>Input: "Who has Python?" Output: [Employee list filtered]</example>
  <example>Input: "Compare Alice and Bob" Output: [Comparison table]</example>
</examples>

Note: These examples are for reference only. Adapt format to each specific request.
```

#### 8.2.6 Missing Input Context

❌ **Problem**: Lists inputs without explaining purpose

```python
You will receive: user_id, query_text, filters, sort_by
```

✅ **Solution**: Explain why each input matters

```python
You will receive:
- **user_id**: Determines data access scope and personalization context
- **query_text**: Primary user intent for retrieval strategy
- **filters**: Narrow results after initial retrieval
- **sort_by**: Result ordering (default to relevance)
```

#### 8.2.7 Fabrication Risk from Insufficient Guardrails

❌ **Problem**: No clear rules about handling missing data

```python
Provide complete employee profiles for the requested candidates.
```

✅ **Solution**: Explicit data handling guardrails

```python
Provide employee profiles based on available data:
- Use only verified data from authorized sources
- If incomplete, return partial profile with clear indication of missing fields
- **Never fabricate or infer data** that isn't explicitly available
- Flag assumptions with (assumption) label
```

#### 8.2.8 Template Responses from Missing Data Retrieval

❌ **Problem**: Instructions allow placeholder content

```python
Create a job description. If you don't have enough information, create a template the user can fill out.
```

✅ **Solution**: Mandate data retrieval before generation

```python
Create a job description:
1. **Required**: Retrieve similar job descriptions from database
2. **Required**: Search for role-specific requirements
3. **Required**: Read organization's existing job descriptions
4. Use retrieved data to generate specific, actionable content
5. **Never create placeholder/template content**

If critical information is missing:
- Explicitly state what's needed
- Ask targeted questions (max 2) to gather essentials
- Proceed with best available data, flagging assumptions
```

### 8.3 Quality Metrics

#### Primary Metrics

- **Task Completion Rate**: % of user asks fully resolved
- **Error Rate**: Tool failures, guardrail violations, retries
- **User Satisfaction**: Explicit feedback (thumbs up/down, ratings)

#### Secondary Metrics

- **Response Time**: Latency from query to response
- **Tool Usage Efficiency**: Appropriate tool selection, parallel execution
- **Consistency**: Similar queries → similar responses
- **Guardrail Triggers**: Frequency and type of violations

#### Qualitative Assessment

- Human review of sample interactions
- Edge case handling quality
- Reasoning clarity
- Output professionalism

---

## 9. Advanced Platform-Specific Patterns

### 9.1 Personalization and Dynamic Variables

#### 9.1.1 Runtime Variable Injection

System prompts support **dynamic variables** injected at runtime to personalize agent behavior per user, company, or context.

**Variable Categories**:

**1. User/Company Context**:
```python
agent_prompt = render_prompt("agents/assistant",
                            USER_NAME=user.full_name,
                            COMPANY_NAME=company.name,
                            USER_ROLE=user.role,
                            COMPANY_INDUSTRY=company.industry)
```

**2. Tool Context**:
```python
agent_prompt = render_prompt("agents/assistant",
                            AVAILABLE_TOOLS=tool_catalog.to_dict(),
                            TOOL_SCHEMAS=tool_schemas,
                            ENABLED_INTEGRATIONS=integration_list)
```

**3. Workflow Context**:
```python
agent_prompt = render_prompt("agents/assistant",
                            WORKFLOW_CONFIG=workflow_config,
                            HANDOFF_ROUTES=handoff_routes,
                            ACTIVE_CONSTRAINTS=constraints)
```

**Best Practices**:
- Treat runtime variables as **first-class inputs**
- Validate variable presence before rendering
- Provide sensible defaults for optional variables
- Document required vs optional variables in `meta.yaml`

#### 9.1.2 SPL (System Prompt Learning) Blocks

**SPL blocks** are generated and continuously optimized per user/company, then injected at runtime.

**Architecture**:
```python
# SPL blocks stored in database (Attachment model, type="agent_context", subtype="agents_md")
# Retrieved and injected during agent execution

agent_prompt = render_prompt("agents/assistant",
                            SPL_BLOCKS=spl_content,  # User-specific learnings
                            **standard_vars)
```

**SPL Content Categories**:
- **User Preferences**: Communication style, response length, format preferences
- **Successful Workflows**: Patterns that worked well for this user
- **Tool Usage Patterns**: Frequently used tool combinations
- **Domain Knowledge**: User/company-specific terminology and context

**SPL Rules**:
- SPL blocks are **advisory personalization**, not absolute authority
- SPL must **never override guardrails**, policies, or safety constraints
- If SPL conflicts with user request or system constraints, follow higher-priority rules and note conflict in output

**Implementation Pattern**:
```python
AGENT_INSTRUCTION_WITH_SPL = """
You are an HR expert...

{{CORE_INSTRUCTIONS}}

# Personalization (User-Specific Learnings)

{{SPL_BLOCKS}}

Note: These personalization learnings are advisory. Always prioritize explicit user requests and system guardrails over learned preferences.

{{GUARDRAILS}}
"""
```

### 9.2 Behavioral Cognition Patterns

#### 9.2.1 Operating Loop

Agents follow a structured loop for non-trivial work:

**Understand → Plan → Reason → Adapt → Act → Repeat**

**Implementation**:
```python
OPERATING_LOOP = """
# Operating Loop

For complex tasks, follow this structured approach:

1. **Understand**: Clarify user intent and required outcomes
2. **Plan**: Determine necessary tools, data sources, and execution sequence
3. **Reason**: Think through approach step-by-step (chain of thought)
4. **Adapt**: Adjust strategy based on intermediate results
5. **Act**: Execute tool calls and generate outputs
6. **Repeat**: Continue loop until task is fully resolved

Loop termination conditions:
- Task is fully resolved and desired outcome achieved, OR
- All available tool combinations exhausted without success (explain limitation)
"""
```

#### 9.2.2 Agentic Architectures (Multi-AI Systems)

Define how agents coordinate in multi-agent systems.

**Architecture Primitives**:

**1. Handoffs** (Transfer Control):
```python
HANDOFF_PATTERN = """
## Handoffs

Transfer control to specialized agents when their expertise better serves the user:

- **When to handoff**: Task requires specialized domain knowledge or capabilities
- **How to handoff**: Use handoff tool with complete context transfer
- **Context transfer**: Provide user ask, relevant data, and progress summary
- **Never mention**: Don't explicitly reference the handoff in user-facing output
"""
```

**2. Agents-as-Tools** (Tool-Style Calls):
```python
AGENTS_AS_TOOLS_PATTERN = """
## Agents as Tools

Invoke specialized agents as tools for specific subtasks:

- **Synchronous invocation**: Wait for agent response before proceeding
- **Context passing**: Provide minimal necessary context
- **Result integration**: Incorporate agent outputs into your response
- **Error handling**: If agent call fails, retry or use alternative approach
"""
```

**3. Steps** (Ordered Execution):
```python
STEPS_PATTERN = """
## Sequential Execution

For multi-step processes with dependencies:

1. Execute steps in order
2. Pass outputs from step N to step N+1
3. Validate intermediate results
4. Rollback on critical failures
"""
```

**4. Pipeline** (Staged Sequential System):
```python
PIPELINE_PATTERN = """
## Pipeline Architecture

Process data through staged pipeline:

- **Stage 1**: Validation and normalization
- **Stage 2**: Analysis and enrichment
- **Stage 3**: Synthesis and formatting
- **Accumulation**: Each stage augments data from previous
- **Fail-fast**: Halt on critical errors in early stages
"""
```

**5. Parallel Configuration** (Concurrent Agents):
```python
PARALLEL_PATTERN = """
## Parallel Execution

Execute independent tasks concurrently:

- **Identify independence**: Determine which subtasks have no dependencies
- **Spawn in parallel**: Launch multiple agent calls simultaneously
- **Dependency management**: Wait for prerequisite tasks before dependent tasks
- **Result aggregation**: Combine outputs when all tasks complete
"""
```

**Architecture Selection Guidance**:
```python
Choose the simplest architecture that meets quality and safety needs:
- **Simple tasks**: Direct execution (no architecture needed)
- **Sequential dependencies**: Use steps or pipeline
- **Independent subtasks**: Use parallel execution
- **High-stakes outputs**: Add reviewer/critic patterns
- **Complex coordination**: Combine multiple primitives
```

#### 9.2.3 Memory System

**Purpose**: Retrieval of relevant context at inference time (not learning/optimization).

**Memory Types**:

**1. Run Memory** (Within-Conversation):
```python
MEMORY_RUN_PATTERN = """
## Run Memory

Context from current conversation session:

- **Scope**: Messages within current conversation only
- **Retrieval**: Automatic for all conversational agents
- **Freshness**: Real-time, no staleness concerns
- **Storage**: Conversation.messages (database)
"""
```

**2. Cross-Run Memory** (Across Conversations):
```python
MEMORY_CROSS_RUN_PATTERN = """
## Cross-Run Memory

Context from previous conversations and interactions:

- **Scope**: Historical conversations, agent interactions, outcomes
- **Retrieval**: Triggered when current query relates to past context
- **Vector Search**: Uses embeddings to find semantically similar past interactions
- **Scope Parameter**: Must specify user/company scope for retrieval
- **Freshness**: Time-weighted; recent interactions prioritized
- **Staleness Handling**: Flag outdated context (>90 days) with recency disclaimer
"""
```

**3. Structured Memory** (Entity Data):
```python
MEMORY_STRUCTURED_PATTERN = """
## Structured Memory

Entity and relationship data from platform:

- **Employees**: Profiles, skills, experience, performance
- **Candidates**: Applications, assessments, interview history
- **Jobs**: Requirements, descriptions, hiring status
- **Retrieval**: Via data management tools (search, list, read)
- **Validation**: Always verify data recency and completeness
"""
```

**Memory Integration Pattern**:
```python
agent_prompt = render_prompt("agents/assistant",
                            RUN_MEMORY=conversation_messages,
                            CROSS_RUN_MEMORY=relevant_past_conversations,
                            STRUCTURED_CONTEXT=entity_data,
                            **other_vars)
```

**Memory Retrieval Triggers**:
```python
Retrieve memory when:
- User references past conversations ("as we discussed before")
- Query semantically similar to past queries (vector search)
- User asks about historical data ("what happened last quarter")
- Context from past interactions would improve response quality
```

**What NOT to store or rely on**:
- PII without explicit consent
- Sensitive HR data (compensation, performance reviews) without access control
- Deprecated or superseded information
- Low-confidence speculative outputs

#### 9.2.4 Learning System

**Purpose**: Improving future performance (not just retrieving past context).

**What Gets Learned**:
- **Preferences**: User communication style, response length, format preferences
- **Successful Workflows**: Tool combinations that resolved tasks effectively
- **Tool Patterns**: Effective sequences and parallel executions
- **Outcome Signals**: User satisfaction indicators (thumbs up/down, edits, rejections)

**Learning Artifacts**:

**1. SPL Blocks** (AGENTS.md):
```python
LEARNING_SPL_PATTERN = """
# Learning via SPL Blocks

AGENTS.md contains accumulated learnings:
- Updated via optimization tasks (weekly batches)
- Injected at runtime as advisory context
- Never overrides core instructions or guardrails
- Tracks: preferences, successful patterns, user-specific terminology
"""
```

**2. Lessons Storage**:
```python
LEARNING_LESSONS_PATTERN = """
# Lessons Storage

Structured learnings stored in database:
- **What worked**: Successful tool sequences, data sources, approaches
- **What didn't work**: Failed attempts, ineffective strategies
- **User corrections**: Patterns in user edits and rejections
- **Contextual applicability**: When lesson applies vs doesn't apply
"""
```

**Learning Scheduling**:
- **Real-time**: Capture outcome signals immediately (user feedback, edits)
- **Batch**: Process learnings weekly (optimization tasks)
- **On-demand**: Re-optimize when behavior drift detected

**Overlap Hygiene**:
- Avoid duplicative learnings across memory types
- Consolidate conflicting patterns
- Deprecate superseded learnings
- Maintain learning freshness (expire stale patterns)

**Application at Runtime**:
```python
# Learning injection points
agent_prompt = render_prompt("agents/assistant",
                            SPL_BLOCKS=optimized_spl,         # Injected as advisory section
                            LESSONS_CONTEXT=relevant_lessons,  # Context for decision-making
                            **other_vars)
```

#### 9.2.5 Data Principles

Explicit principles agents must apply during reasoning:

**Information Weights**:
```python
DATA_WEIGHTS_PRINCIPLE = """
Not all data is equally important. Prioritize:
1. **Authoritative sources** over aggregated sources
2. **Recent data** over outdated data (time-weighted)
3. **Directly relevant signals** over tangentially related signals
4. **Primary sources** over secondary interpretations
5. **Validated data** over unverified claims
"""
```

**Objective Truth**:
```python
OBJECTIVE_TRUTH_PRINCIPLE = """
Prefer verifiable facts over interpretations:
- State facts clearly and cite sources
- Separate facts from analysis
- Distinguish data from conclusions drawn from data
- Acknowledge when interpretation is subjective
"""
```

**Certainty and Confidence**:
```python
CERTAINTY_PRINCIPLE = """
Attach confidence levels to claims:
- High confidence (>80%): Strong evidence, multiple sources, direct validation
- Medium confidence (50-80%): Reasonable evidence, some validation
- Low confidence (<50%): Weak evidence, assumptions required

Downgrade claims when evidence is weak. Use qualifiers: "likely," "possibly," "uncertain."
"""
```

**Time-Awareness**:
```python
TIME_AWARENESS_PRINCIPLE = """
Treat old data as suspect unless confirmed:
- Flag data older than 90 days with recency disclaimer
- Prioritize recent data when available
- Check if historical data still applies to current context
- Validate that trends from past data remain relevant
"""
```

#### 9.2.6 Reflection and Critique

Before final output, agents should self-validate.

**Reflection Pattern**:
```python
REFLECTION_PATTERN = """
# Self-Validation (before final output)

Before responding, check:
1. **Contradiction Check**: Response doesn't contradict instructions or prior statements
2. **Mission Alignment**: Output serves the stated mission and goals
3. **Tool Justification**: Tool usage was necessary and appropriate
4. **Format Compliance**: Response matches required structure/schema
5. **Guardrail Adherence**: No guardrail violations occurred
6. **Completeness**: User ask is fully addressed

If any check fails, revise before outputting.
"""
```

**Critique Pattern** (for high-stakes outputs):
```python
CRITIQUE_PATTERN = """
# Self-Critique (for critical outputs)

For high-stakes recommendations (hiring decisions, compensation, terminations):

1. **Alternative Explanations**: Consider alternative interpretations of data
2. **Bias Check**: Identify potential biases in analysis or data
3. **Risk Assessment**: Enumerate risks of recommendation
4. **Confidence Calibration**: Ensure confidence matches evidence strength
5. **Stakeholder Impact**: Consider impact on all affected parties

Include brief self-critique in output when stakes are high.
"""
```

#### 9.2.7 File System and Artifacts

Define how agents read/write artifacts (Canvas components).

**Canvas Artifact Patterns**:
```python
ARTIFACT_PATTERN = """
## Canvas Artifacts

Canvas components generate persistent structured artifacts:

### When to Create Canvas
- User explicitly requests artifact ("create a document," "generate a chart")
- Task requires structured output beyond conversational response
- Output needs to be editable, shareable, or versioned

### When to Update vs Append
- **Update**: Revise existing content while preserving structure
- **Append**: Add new content to existing artifact
- **Replace**: Complete overwrite when previous content obsolete

### Object and Block References
- Reference objects by ID when modifying
- Reference blocks within artifacts for targeted updates
- Maintain referential integrity across updates

### Idempotency Expectations
- Multiple identical calls should produce same result
- Avoid creating duplicates on retry
- Use upsert patterns when appropriate
"""
```

#### 9.2.8 Confessions (Explicit Uncertainty and Assumptions)

Mandatory section when uncertainty exists—builds user trust through transparency.

**Confession Pattern**:
```python
CONFESSION_PATTERN = """
## Confessions

When uncertainty exists, include a brief confession section:

**Format**:
---
**Confessions**
- **Assumptions made**: [List assumptions with labels]
- **Unknowns that matter**: [Key information gaps]
- **What would change the answer**: [Data that would alter conclusions]
- **Confidence level**: [Rough estimate: High/Medium/Low]
---

**When to Include**:
- Data is incomplete or ambiguous
- Multiple interpretations are plausible
- Conclusions rely on assumptions
- Confidence is below 70%

**When NOT to Include**:
- Routine, high-confidence responses
- Purely factual retrieval with verified sources
- Structured data transformations
"""
```

**Example**:
```python
# Agent response with confession
"""
Based on the available data, the top candidate is Alice Chen with a 92% match score.

**Confessions**
- **Assumption**: Assumed "Python experience" includes Django (not explicitly stated in resume)
- **Unknown**: Alice's salary expectations (not in application data)
- **Would change answer**: If candidate has time zone constraints (not currently evaluated)
- **Confidence**: High (85%) based on strong skill match, but medium (60%) on culture fit
"""
```

### 9.3 Agentic Architecture Instructions

#### 9.3.1 Architecture Selection Logic

Guide agents to choose appropriate multi-agent patterns:

```python
ARCHITECTURE_SELECTION = """
## Agentic Architecture Selection

Choose architecture based on task characteristics:

### Simple Direct Execution
**When**: Single tool call, no dependencies, straightforward logic
**Pattern**: Direct tool invocation → response

### Sequential Steps
**When**: Multiple dependent tasks, outputs feed into next step
**Pattern**: Step 1 → Step 2 → Step 3 (wait for each to complete)

### Pipeline Stages
**When**: Multi-stage transformation with validation gates
**Pattern**: Validate → Normalize → Enrich → Synthesize → Format
**Config**: stage_overrides, accumulation mode, fail-fast behavior

### Parallel Execution
**When**: Independent subtasks, no shared state
**Pattern**: Launch all tasks → wait for completion → aggregate results
**Config**: max_concurrent, timeout per task, dependency graph

### Handoff
**When**: Task requires specialized expertise outside your domain
**Pattern**: Transfer full context to specialist agent → incorporate results

### Reviewer/Critic
**When**: High-stakes outputs requiring validation
**Pattern**: Generate output → critic reviews → revise based on feedback
**Config**: confidence_threshold, quorum (multiple reviewers)

**Selection Priority**: Use simplest architecture that meets quality and safety requirements.
"""
```

#### 9.3.2 Explicit Thresholds and Strategies

When architectures have configurable parameters, define them explicitly:

```python
ARCHITECTURE_THRESHOLDS = """
## Architecture Configuration Thresholds

### Confidence Thresholds
- **High confidence required (>90%)**: Use reviewer pattern
- **Medium confidence (70-90%)**: Proceed with disclaimer
- **Low confidence (<70%)**: Request additional context or handoff

### Quorum Settings
- **Critical decisions**: 3 reviewers, 2/3 agreement required
- **Standard decisions**: 2 reviewers, 1/2 agreement required
- **Low-stakes decisions**: Single reviewer sufficient

### Timeout Limits
- **Per tool call**: 30 seconds max
- **Per agent invocation**: 5 minutes max
- **Total workflow**: 15 minutes max

### Retry Strategies
- **Transient failures**: Retry up to 2 times with exponential backoff
- **Parameter errors**: Adjust parameters and retry once
- **Auth failures**: Do not retry (escalate to user)

### Max Iterations
- **Refinement loops**: Maximum 3 iterations
- **Search expansions**: Maximum 5 attempts
- **Architecture depth**: Maximum 3 levels of agent nesting
"""
```

### 9.4 Error Handling and Ambiguity

#### 9.4.1 Detecting Missing Inputs Early

```python
EARLY_DETECTION_PATTERN = """
## Error Detection

Detect missing inputs early in execution:

1. **Validate Required Inputs**: Check for all required parameters before processing
2. **Assess Input Quality**: Verify data completeness and validity
3. **Identify Blockers**: Determine if missing data prevents task completion

**When Blocking**:
- Ask minimal, high-leverage questions (max 2 questions)
- Focus on critical missing information only
- Provide context about why information is needed

**When Non-Blocking**:
- Proceed with explicit assumptions (see Confessions pattern)
- Use best available data
- Flag assumptions in output
- Explain what additional data would improve response
"""
```

#### 9.4.2 Graceful Degradation

```python
DEGRADATION_PATTERN = """
## Graceful Degradation

When complete data is unavailable:

1. **Return Partial Results**: Provide what you can with clear indication of gaps
2. **Explain Limitations**: What data is missing and why it matters
3. **Suggest Next Steps**: What user can do to improve completeness
4. **Never Fabricate**: Don't fill gaps with invented data

**Example**:
"Based on available data, I found 3 of 5 requested candidates. Two candidates (IDs: X, Y) are not in the system or you don't have access. The 3 candidates I found show strong Python skills..."
"""
```

---

## 10. Prompt Structure Reference

Based on industry best practices from Anthropic, OpenAI, and other leading AI labs, follow this 10-component framework for structuring complete system prompts:

#### 9.1.1 Task Context (Identity, Role, Mission)

**Position**: Opening lines  
**Purpose**: Define who the AI is and what it's for  
**Weight**: Maximum—sets foundation for all behavior

```python
You are [ROLE] created by [CREATOR]. Your mission is to [PRIMARY OBJECTIVE] so [STAKEHOLDER] can [DESIRED OUTCOME].
```

#### 9.1.2 Tone Context (Behavior, Communication Style)

**Position**: Early in instructions  
**Purpose**: Establish interaction patterns and personality

```python
Respond conversationally—be clear, helpful, and direct. Communicate progress naturally while maintaining professionalism.
```

#### 9.1.3 Background Data, Documents, Images

**Position**: Before task-specific rules  
**Purpose**: Provide reference material and context

```xml
<context>
{{COMPANY_DATA}}
{{INDUSTRY_STANDARDS}}
{{REFERENCE_DOCUMENTS}}
</context>
```

#### 9.1.4 Detailed Task Description & Rules

**Position**: Core instructions section  
**Purpose**: Operating principles, capabilities, constraints

```python
# Operating Principles
[Tool orchestration, parallel execution, retry logic]

# Capabilities
[Data management, canvas components]

# Guardrails
[Operation and behavior constraints]
```

#### 9.1.5 Examples (Few-Shot, Multishot)

**Position**: After rules, before conversation history  
**Purpose**: Demonstrate desired input/output patterns

```xml
<examples>
  <example>
    Input: [User query]
    Output: [Agent response demonstrating proper format and reasoning]
  </example>
</examples>
```

#### 9.1.6 Conversation History

**Position**: Before immediate request (for conversational agents)  
**Purpose**: Maintain context across turns

```xml
<history>
{{PREVIOUS_MESSAGES}}
</history>
```

#### 9.1.7 Immediate Task/Request

**Position**: Just before final instructions  
**Purpose**: Current user query or task

```xml
<question>
{{USER_QUERY}}
</question>

How do you respond to the user's question?
```

#### 9.1.8 Thinking Step-by-Step Instructions

**Position**: After task, before output format  
**Purpose**: Encourage chain-of-thought reasoning

```python
Think about your answer first before you respond. Consider what data you need, what tools to use, and how to structure your response.
```

#### 9.1.9 Output Formatting Requirements

**Position**: Near end, clear specification  
**Purpose**: Define response structure and format

```python
Put your response in <response></response> tags.

OR

Your response must be valid JSON matching this schema:
{schema definition}
```

#### 9.1.10 Prefilled Response (if applicable)

**Position**: Final element  
**Purpose**: Start the response with specific structure

```python
Assistant (prefill): <response>
```

**Note**: Not all prompts need all 10 components. Adapt based on use case complexity.

### 9.2 AI Lifecycle Integration

Based on the AI lifecycle, agents can support six core capability areas:

#### 10.11 AI Lifecycle Integration

Based on the AI lifecycle, agents can support six core capability areas:

##### Content Creation

**Capabilities**: Generate structured artifacts for business use  
**Examples**: Job descriptions, courses, emails, reports, survey forms

**Implementation Pattern**:
```python
## Content Creation

Create structured content when users explicitly request it or when task requires artifact generation:
- **Job descriptions**: Role expectations, responsibilities, qualifications
- **Learning content**: Course materials, development plans
- **Communications**: Professional emails, announcements
- **Reports**: Analytics summaries, performance reviews

Content creation requires:
1. Data retrieval to inform content
2. Human-in-the-loop confirmation before persistence
3. Complete, actionable content (never placeholders)
```

##### Research

**Capabilities**: Find, validate, and synthesize information  
**Examples**: Online search, deep investigation, cross-source validation

**Implementation Pattern**:
```python
## Research & Investigation

Conduct comprehensive research across internal and external sources:
- **Online Search**: Find current information on topics, trends, best practices
- **Deep Research**: Multi-source investigation requiring synthesis
- **Web Content Extraction**: Process content from URLs
- **Cross-Source Validation**: Verify claims through multiple sources

Research methodology:
1. Plan minimal evidence needed
2. Select high-signal sources
3. Fetch in parallel when independent
4. Validate via cross-checks
5. Quantify confidence and uncertainty
6. Synthesize to essentials
7. Cite sources for all claims
```

##### Data Analysis

**Capabilities**: Process, interpret, and visualize organizational data  
**Examples**: Metrics analysis, pattern identification, insights generation

**Implementation Pattern**:
```python
## Data Analysis

Analyze organizational data to surface patterns, trends, and insights:
- **Metrics Calculation**: Compute KPIs, aggregates, trends
- **Pattern Recognition**: Identify correlations, anomalies
- **Predictive Insights**: Forecast trends based on historical data
- **Recommendations**: Generate data-driven suggestions

Analysis approach:
1. Retrieve relevant data from appropriate sources
2. Validate data quality and completeness
3. Apply statistical methods and domain knowledge
4. Visualize findings when helpful
5. Provide actionable insights with confidence levels
6. Cite data sources and methodology
```

##### Ideation/Strategy

**Capabilities**: Generate plans, frameworks, and strategic recommendations  
**Examples**: Planning, frameworks, decision support, scenario analysis

**Implementation Pattern**:
```python
## Strategic Planning

Generate strategic recommendations and planning frameworks:
- **Planning**: Develop roadmaps, timelines, implementation plans
- **Frameworks**: Create decision models, evaluation criteria
- **Scenario Analysis**: Explore alternatives, trade-offs, risks
- **Decision Support**: Provide structured analysis for choices

Strategic approach:
1. Understand objectives and constraints
2. Analyze current state and gaps
3. Generate multiple options with trade-offs
4. Evaluate against success criteria
5. Recommend prioritized actions
6. Provide implementation guidance
```

##### Automation

**Capabilities**: Create workflows, triggers, and scheduled operations  
**Examples**: Scheduled tasks, workflows, event-driven actions

**Implementation Pattern**:
```python
## Workflow Automation

Create automated tasks and workflows for recurring operations:
- **Scheduled Tasks**: Time-based execution (daily reports)
- **Event-Driven Workflows**: Trigger on conditions (new hire onboarding)
- **Process Automation**: Multi-step workflows with conditional logic
- **Notifications**: Automated alerts, reminders, status updates

Automation design:
1. Define trigger conditions clearly
2. Specify execution logic and dependencies
3. Handle errors and edge cases
4. Provide monitoring and logging
5. Allow user override or cancellation
```

##### Coding (Not currently in use)

**Note**: Not directly applicable to HR platform. Included for completeness.

---

## 11. Examples & Templates

### 11.1 Minimal Agent Template

For simple, focused agents with limited scope:

```python
You are a [ROLE] created by [CREATOR]. Your mission is to [OBJECTIVE] so [STAKEHOLDER] can [OUTCOME].

# Capabilities
- [Capability 1]
- [Capability 2]
- [Capability 3]

# Guardrails
- Use only verified data from available sources
- Clearly state any assumptions or limitations
- Respond in the same language as the user query

# Response Format
[Format specification: prose, JSON, markdown, etc.]
```

### 11.2 Standard Agent Template

For domain agents with comprehensive capabilities:

```python
You are [ROLE DESCRIPTION] created by [CREATOR]. Your mission is to [PRIMARY OBJECTIVE] so [STAKEHOLDER] can [DESIRED OUTCOME].

Your goals are to:
- [Goal 1: Measurable outcome]
- [Goal 2: Measurable outcome]
- [Goal 3: Measurable outcome]

{{OPERATING_PRINCIPLES}}

{{AGENT_CAPABILITIES}}

# [Domain-Specific Section if needed]
[Specialized frameworks, taxonomies, scales relevant to domain]

{{FORMATTING_GUIDELINES}}

{{GUARDRAILS}}
```

### 11.3 Specialized Agent Template

With domain-specific frameworks:

```python
You are the **[Agent Name]** created by [Creator]. Your mission is to [specific mission] so [stakeholder] can [specific outcomes].

# Objectives
- **[Verb 1]**: [Specific objective]
- **[Verb 2]**: [Specific objective]
- **[Verb 3]**: [Specific objective]

{{OPERATING_PRINCIPLES}}

{{AGENT_CAPABILITIES}}

# [Domain Framework Name]

## [Framework Component 1]
[Definition, criteria, examples, scales]

## [Framework Component 2]
[Definition, criteria, examples, scales]

## [Methodology or Process]
[Step-by-step approach specific to domain]

# Priority Hierarchy
1. **[Priority 1]** - [Description]
2. **[Priority 2]** - [Description]
3. **[Priority 3]** - [Description]

{{FORMATTING_GUIDELINES}}

{{GUARDRAILS}}

# Terminology & Standards
- Say **[term 1]** (not alternative)
- Say **[term 2]** (not alternative)
- Maintain consistent terminology throughout
```

---

## 12. Maintenance & Evolution

### 12.1 When to Refactor

Refactor agent instructions when experiencing:

**Behavior Drift**:
- Agent outputs diverging from intended behavior
- Inconsistent responses to similar queries
- Quality degradation over time

**Contradictions Identified**:
- Users reporting conflicting guidance
- Agent struggling with edge cases
- Rules that conflict in practice

**Scope Creep**:
- Instructions growing beyond original intent
- Too many special cases and exceptions
- Complexity making instructions hard to maintain

**Performance Issues**:
- Slow response times due to instruction length
- Model confusion from ambiguous rules
- High error rates or retry frequency

### 12.2 Version Control Considerations

**Track Changes**:
- Use git for all instruction updates
- Meaningful commit messages explaining rationale
- Branch for major refactors
- Tag stable versions

**Document Intent**:
```markdown
# Changelog

## v2.3.0 - 2025-11-02
### Added
- Research methodology section with 7-step process
- Evidence quality rubric for source validation
- Contradiction handling guidelines

### Changed
- Simplified guardrails from 15 rules to 5 heuristics
- Consolidated data retrieval patterns

### Removed
- Deprecated rigid scoring rules in favor of holistic assessment
```

### 12.3 A/B Testing Framework

**Test Hypothesis**:
- Identify specific behavior to improve
- Create variant with targeted change
- Define success metrics

**Implementation**:
```python
# Route percentage of traffic to variant
if user_id % 100 < 10:  # 10% to variant
    instructions = VARIANT_INSTRUCTIONS
else:  # 90% to control
    instructions = CONTROL_INSTRUCTIONS
```

**Measure**:
- Task completion rate
- User satisfaction (thumbs up/down)
- Response quality (human eval)
- Error rate
- Response time

**Decision Criteria**:
- Variant shows >5% improvement on primary metric
- No degradation on secondary metrics
- Statistical significance achieved
- Qualitative feedback positive

### 12.4 Feedback Loops

**From Guardrail Violations**:
- High rate of input violations → tighten scope or improve clarity
- High rate of output violations → strengthen guardrails or adjust behavior
- Specific violation patterns → address root cause in instructions

**From Tool Errors**:
- Frequent retry → improve tool selection logic
- Fallback activation → add alternative strategies
- Missing tools → expand capabilities or adjust scope

**From User Corrections**:
- Track what users edit/reject
- Identify patterns in modifications
- Update instructions to preempt common corrections

**From Behavior Drift**:
- Regular spot-checks of outputs
- Compare against baseline interactions
- Identify instruction sections losing effectiveness
- Refresh examples or clarify ambiguous rules

---

## Summary

This guide provides the comprehensive framework for designing, implementing, and maintaining system prompt instructions across the Cloush platform. Key principles:

1. **Structure**: Follow Identity → Mission → Goals → Responsibilities → Tasks → Functions hierarchy (as needed)
2. **Weight**: Position critical instructions at start/end; use emphasis selectively
3. **Clarity**: Simple, direct language; avoid ambiguity and contradictions
4. **Modularity**: Compose from reusable building blocks (variables, composables, templates)
5. **Flexibility**: Use heuristics over rigid rules; allow intelligent adaptation
6. **Safety**: Layer guardrails from general → specific; prevent fabrication
7. **Platform Integration**: Always access via `instruction_service`; follow versioning patterns
8. **Evidence**: Track metrics, gather feedback, iterate systematically

Use this guide as the authoritative reference when creating new agents, optimizing existing instructions, or debugging agent behavior. Combine with:

- **`messages/instructions/README.md`** for implementation details
- **`.cursor/rules/build-ai-instructions.mdc`** for meta-patterns and iteration
- **`.cursor/rules/ai_agent_tool_calls.mdc`** for tool descriptions

---

## Related Documentation

- **Package Architecture**: `messages/instructions/README.md`
- **Prompt Engineering Meta-Guide**: `.cursor/rules/build-ai-instructions.mdc`
- **Tool Call Specifications**: `.cursor/rules/ai_agent_tool_calls.mdc`
- **Agent Service Documentation**: `services/agents/README.md`
- **Context Service Documentation**: `services/context/README.md`

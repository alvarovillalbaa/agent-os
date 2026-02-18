# Messages Instructions Architecture

This directory contains the instruction packages for the Cloush platform, organized according to the **Package Architecture** for versioned, composable system prompts.

**📖 Comprehensive Guide**: `docs/cookbook/messages-instructions-architecture.md` — For detailed guidance on designing system prompt instructions, including theoretical foundations, instruction anatomy, optimization guidelines, quality checklists, and best practices from leading AI labs.

**This README focuses on**: Package structure, versioning, centralized access patterns, and platform integration.

## Architecture Overview

The instruction system is built on a **registry-based package architecture** where:

- **Version IS Instruction**: The highest numbered version directory (`v1/`, `v2/`, `v3/`, etc.) contains the current/active instruction
- **Complete Snapshots**: Each version directory contains the complete, immutable snapshot of template + values + composables
- **Centralized Access**: All instructions are accessed through `messages.instruction_service`, never through direct imports
- **Composable Design**: Instructions combine **values** (fixed text), **templates** (`.j2` with interleaved placeholders), and **composables** (Python assembly)

### Terminology

| Term | Definition |
|------|------------|
| **Value** | A Python string constant (UPPERCASE) in `values.py` — fixed instruction text. |
| **Template** | A `.j2` file with `{{ PLACEHOLDER }}` slots filled at render time (from values or runtime). |
| **Composable** | A Python function in `composables.py` that assembles text by concatenating values and other composables. |
| **Runtime variable** | Data injected at call site (user name, company data, etc.) — never stored under `messages/instructions/`. |

**Values vs runtime variables:** Instruction text is defined as Python variables; the file holding fixed blocks is `values.py` (canonical). Runtime variables are passed as `**ctx` to `render_prompt()`.

## Directory Structure

Root-level directories are **shared** across everything under `messages/instructions/`. No `shared/` folder is required — placement at root means shared.

```
messages/instructions/
├── guardrails/              # Shared: safety and behavioral constraints
├── formatting/              # Shared: response formatting (base, document, conversational variants)
├── capabilities/            # Shared: operating principles, base + data + canvas capabilities
├── intelligence/            # Shared: dynamic prompt generation
├── tool_descriptions/       # Shared: tool contracts
├── agents/                  # Agent-specific instructions
│   ├── assistant/
│   ├── candidates/
│   ├── cdo/
│   └── ...
├── middleware/              # Processing pipeline instructions
│   ├── router/
│   ├── analysis/
│   └── ...
├── functions/               # Canvas function instructions
├── loops/                   # Conversation loop instructions
├── evals/                   # Evaluation system instructions
├── canvas/                  # Canvas/chart visualization
├── artifacts/               # Artifact instructions
├── online/                  # Root-level: online search and research (migrated from shared/online)
└── instruction_renderer.py  # Core rendering engine
```

## Package Structure

Each instruction package follows this structure:

```
instruction_name/
├── CHANGELOG.md              # Version history and changes
├── v1/                       # Version 1 (immutable snapshot)
│   ├── instruction.j2        # Jinja2 template (if variables used)
│   ├── instruction.py        # Python composition (if no variables)
│   ├── values.py             # Fixed text blocks (UPPERCASE constants; was variables.py)
│   ├── composables.py        # Composition functions (+ operators)
│   └── meta.yaml             # Metadata (inputs, dependencies)
├── v2/                       # Version 2 (current version)
│   ├── instruction.j2
│   ├── values.py
│   ├── composables.py
│   └── meta.yaml
└── ...
```

## File Types and Usage

### Template Files (`.j2`)
- **Purpose**: Instructions that interpolate dynamic variables using Jinja2
- **When to use**: When content needs to be customized with runtime variables
- **Example**: Agent instructions that vary based on user context

### Composition Files (`.py`)
- **Purpose**: Instructions built through Python string concatenation
- **When to use**: For static instructions or when composition logic is needed
- **Example**: Guardrails, formatting rules, static capability descriptions

### Values Files (`values.py`)
- **Purpose**: Fixed text blocks (UPPERCASE constants) — the atoms of instructions. Used for template interpolation and composition.
- **Convention**: UPPERCASE names; file is `values.py` (canonical; `variables.py` supported as fallback).
- **Rule**: Values may import from other packages' `values.py` or `composables.py`; must not import from their own `composables.py` (avoids circular imports).
- **Example**: `OPERATING_PRINCIPLES`, `AGENT_CAPABILITIES`, `AGENT_GUARDRAIL` (pre-composed from guardrails composable).

### Composables Files (`composables.py`)
- **Purpose**: Functions that assemble instruction text by concatenating values and other composables (structural assembly; no Jinja2 required).
- **Pattern**: Return strings built from `values.py` and other composables; use for e.g. `BASE_GUARDRAIL + FUNCTION_GUARDRAIL + CONVERSATIONAL_GUARDRAIL`.
- **Example**: `compose_base_guardrail()`, `compose_agent_guardrail()`

## Centralized Platform Access

**CRITICAL ARCHITECTURE REQUIREMENT**: All system prompt instructions must be accessed through `messages.instruction_service`, never through direct imports or scattered calls. This ensures consistency, version safety, and maintainability across the platform.

### Single Entry Point Pattern

```python
# ✅ CORRECT: All instruction access goes through instruction_service
from messages.instruction_service import render_prompt, get_instruction_composables

# Get any instruction from anywhere in the platform
agent_prompt = render_prompt("agents/assistant", **variables)
guardrails = get_instruction_composables("guardrails", "v2")
```

```python
# ❌ WRONG: Direct imports from instruction files
from messages.instructions.agents.assistant.v3.values import OPERATING_PRINCIPLES
from messages.instructions.guardrails.v2.composables import compose_base_guardrail

# ❌ WRONG: Scattered render_prompt calls throughout codebase
from messages.instructions.instruction_renderer import render_instruction
prompt = render_instruction("agents/assistant/v3/instruction.j2", **ctx)
```

### Platform-Wide Implementation

Every service, view, and component across Cloush uses the **same centralized access pattern**:

#### 🤖 **Agent Services**
```python
# services/agents/builder.py
from messages.instruction_service import render_prompt

def build_agent_prompt(self, agent_name, **context):
    return render_prompt(f"agents/{agent_name}", **context)
```

#### 🔧 **Middleware Services**
```python
# services/middleware/functions/selection_service.py
from messages.instruction_service import render_prompt, get_instruction_composables

def execute_selection(self, objects_payload, **params):
    guardrails = get_instruction_composables("guardrails", "v2")
    system_prompt = render_prompt("functions/selection",
                                FUNCTION_GUARDRAIL=guardrails.compose_function_guardrail(),
                                **params)
```

#### 🌐 **API Views**
```python
# content/views.py or api/views.py
from messages.instruction_service import render_prompt

def process_content(request, content_id):
    system_prompt = render_prompt("middleware/analysis",
                                CONTENT_TYPE=request.data.get('type'),
                                ANALYSIS_DEPTH=request.data.get('depth', 'standard'))
```

#### ⚙️ **Background Tasks**
```python
# services/tasks/ modules
from messages.instruction_service import render_prompt

@global_celery_task(bind=True)
def process_evaluation_task(self, evaluation_id, **kwargs):
    system_prompt = render_prompt("evals/performance", **kwargs)
```

### Instruction Categories Available

#### 🤖 **Agents** (`agents/`)
- **Assistant** (`agents/assistant`): General-purpose conversational assistant
- **CDO** (`agents/cdo`): Chief Data Officer for data analysis and insights
- **Candidates** (`agents/candidates`): Candidate management and evaluation

#### 🔧 **Middleware** (`middleware/`)
- **Router** (`middleware/router`): Request routing and classification logic
- **Analysis** (`middleware/analysis`): Data analysis and processing instructions
- **Context Compression** (`middleware/context_compression`): Content summarization

#### 🎨 **Canvas Functions** (`functions/`)
- **Selection** (`functions/selection`): Object selection and filtering
- **Document** (`functions/document`): Document generation and analysis
- **Heatmap** (`functions/heatmap`): Data visualization instructions

#### 📊 **Charts & Visualization** (`charts/`)
- **Chart Generation**: Instructions for creating various chart types
- **Graph Analysis**: Network and relationship visualization

#### 🔄 **Conversation Loops** (`loops/`)
- **Loop Control**: Managing conversation state and transitions
- **Context Preservation**: Maintaining conversation coherence

#### 📈 **Evaluations** (`evals/`)
- **Performance Evaluation**: Agent and system performance metrics
- **Quality Assessment**: Content and output evaluation criteria

#### 🔒 **Root-level shared components**
- **Guardrails** (`guardrails/`): Safety constraints and behavioral boundaries
- **Formatting** (`formatting/`): Response formatting and import-format schemas
- **Capabilities** (`capabilities/`): Operating principles and agent-specific capabilities
- **Tool Descriptions** (`tool_descriptions/`): Agent tool contract definitions
- **Intelligence** (`intelligence/`): Dynamic prompt generation functions
- **Online** (`online/`): Online search and research instructions

### Platform Integration Benefits

**Consistency**: Every component uses the same `instruction_service` interface
**Version Safety**: Registry-based resolution prevents version drift
**Maintainability**: Instruction loading logic changes in one place
**Testing**: Instruction access can be mocked at the service level
**Migration Safety**: Gradual migration from legacy paths without breaking changes

### Implementation Across Platform Layers

All layers follow the **same centralized pattern** - import from `messages.instruction_service` and use registry identifiers:

#### **API Layer** (Views)
```python
from messages.instruction_service import render_prompt

def process_content(request, content_id):
    system_prompt = render_prompt("middleware/analysis",
                                CONTENT_TYPE=request.data.get('type'),
                                ANALYSIS_DEPTH=request.data.get('depth', 'standard'))
```

#### **Service Layer** (Business Logic)
```python
from messages.instruction_service import render_prompt

def build_agent_prompt(self, agent_name, **context):
    return render_prompt(f"agents/{agent_name}",
                        AGENT_SKILLS=self._get_agent_skills(agent_name),
                        SYSTEM_BLOCKS=self._get_system_blocks(),
                        **context)
```

#### **Middleware Layer** (Processing Pipelines)
```python
from messages.instruction_service import render_prompt, get_instruction_composables

def execute_selection(self, objects_payload, **params):
    guardrails = get_instruction_composables("guardrails", "v2")
    return render_prompt("functions/selection",
                        FUNCTION_GUARDRAIL=guardrails.compose_function_guardrail(),
                        **params)
```

#### **Background Tasks** (Celery)
```python
from messages.instruction_service import render_prompt

@global_celery_task(bind=True)
def process_evaluation_task(self, evaluation_id, **kwargs):
    return render_prompt("evals/performance", **kwargs)
```

### Variable Context Patterns

All variable access goes through the centralized `instruction_service`:

#### **Agent-Specific Variables**
Used when instructions need customization per agent instance:
```python
from messages.instruction_service import render_prompt

agent_prompt = render_prompt("agents/assistant",
                           USER_COMPANY=company.name,
                           USER_ROLE=request.user.role,
                           AGENT_CAPABILITIES=agent_config.capabilities,
                           CONVERSATION_HISTORY=recent_messages)
```

#### **Shared Variables**
Used for common functionality across multiple agents:
```python
from messages.instruction_service import render_prompt

base_prompt = render_prompt("agents/assistant", **agent_vars)
guardrails_prompt = render_prompt("guardrails")  # or get_instruction_composables("guardrails", "v2")
final_prompt = base_prompt + "\n\n" + guardrails_prompt
```

#### **Runtime Variables**
Used for dynamic content that changes per request:
```python
from messages.instruction_service import render_prompt

function_prompt = render_prompt("functions/document",
                              DOCUMENT_TYPE=user_selection.type,
                              OUTPUT_FORMAT=user_selection.format,
                              CONTENT_LENGTH=user_selection.length)
```

### Error Handling and Fallbacks

All error handling goes through the centralized `instruction_service`:

#### **Graceful Degradation**
```python
from messages.instruction_service import render_prompt

try:
    system_prompt = render_prompt("agents/assistant", **variables)
except (FileNotFoundError, ValueError) as e:
    logger.warning(f"Failed to render agent instructions: {e}")
    system_prompt = self._get_fallback_instructions(agent_name)
```

#### **Version Pinning for Stability**
```python
from messages.instruction_service import render_prompt

# Pin to specific versions for production stability
production_prompt = render_prompt("agents/assistant", version="v2", **vars)
staging_prompt = render_prompt("agents/assistant", version="v3", **vars)  # Latest for testing
```

#### **Validation and Sanitization**
```python
from messages.instruction_service import render_prompt, get_instruction_variables

required_vars = get_instruction_variables("agents/assistant")
missing_vars = [var for var in required_vars if var not in provided_vars]
if missing_vars:
    raise ValueError(f"Missing required variables: {missing_vars}")

system_prompt = render_prompt("agents/assistant", **provided_vars)
```

### Composition Patterns

All composition access goes through the centralized `instruction_service`:

#### **Base + Extensions** (Most Common)
```python
from messages.instruction_service import render_prompt

base_instruction = render_prompt("capabilities")
specialized_instruction = render_prompt("agents/cdo")
final_prompt = base_instruction + "\n\n" + specialized_instruction
```

#### **Main + Guardrails** (Security-Critical)
```python
from messages.instruction_service import render_prompt

main_instruction = render_prompt("middleware/router", **variables)
guardrails = render_prompt("guardrails")
final_prompt = main_instruction + "\n\n" + guardrails
```

#### **Template + Variables** (Dynamic Content)
```python
from messages.instruction_service import render_prompt

prompt = render_prompt("functions/heatmap",
                     DATA_SCHEMA=json.dumps(schema),
                     VISUALIZATION_TYPE=chart_type,
                     USER_PREFERENCES=user_settings)
```

### Performance and Monitoring

All performance optimizations go through the centralized `instruction_service`:

#### **Caching Strategy**
```python
from django.core.cache import cache
from messages.instruction_service import render_prompt

def get_cached_instruction(instruction_id, **variables):
    cache_key = f"instruction:{instruction_id}:{hash(str(variables))}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    prompt = render_prompt(instruction_id, **variables)
    cache.set(cache_key, prompt, timeout=3600)  # 1 hour
    return prompt
```

#### **Usage Metrics and Monitoring**
```python
from services.system.logs_service import PerformanceLogger
from messages.instruction_service import render_prompt

def render_with_metrics(instruction_id, **variables):
    with PerformanceLogger(__name__, f"render_{instruction_id}", "instruction_rendering"):
        prompt = render_prompt(instruction_id, **variables)

    logger.info(f"Rendered instruction: {instruction_id}, length: {len(prompt)}")
    return prompt
```

#### **Memory Management**
```python
from messages.instruction_service import render_prompt

def render_large_instruction(instruction_id, chunk_size=4096, **variables):
    """Render large instructions in chunks to manage memory."""
    full_prompt = render_prompt(instruction_id, **variables)
    for i in range(0, len(full_prompt), chunk_size):
        yield full_prompt[i:i + chunk_size]
```

### Accessing Instructions

**✅ Correct: Centralized access through service**
```python
from messages.instruction_service import render_prompt

# Get latest version
prompt = render_prompt("agents/assistant", **variables)

# Get specific version
prompt = render_prompt("agents/assistant", version="v2", **variables)

# Access composables directly
from messages.instruction_service import get_instruction_composables
composables = get_instruction_composables("tool_descriptions")
```

**❌ Incorrect: Direct imports**
```python
# Don't do this - breaks encapsulation
from messages.instructions.agents.assistant.v2.values import OPERATING_PRINCIPLES
from messages.instructions.guardrails.v2.composables import compose_base_guardrail
```

### Composition Patterns

**Variables + Template (Most Powerful)**
```python
# variables.py
BASE_INSTRUCTIONS = "..."
AGENT_SPECIFIC = "..."

# instruction.j2
{{BASE_INSTRUCTIONS}}
{{AGENT_SPECIFIC}}
{{variable_content}}
```

**Composition Only (Static)**
```python
# composables.py
def compose_instruction():
    return BASE_INSTRUCTIONS + "\n\n" + GUARDRAILS

# instruction.py
INSTRUCTION = compose_instruction()
```

**Hybrid Approach**
```python
# Use composables to build structure, variables for content
base_instruction = compose_base_structure()
final_prompt = render_template("instruction.j2", {"base": base_instruction, **variables})
```

## Variable Placement Strategy

**Agent-Specific Variables**: Stored in individual agent packages
- `messages/instructions/agents/assistant/v2/values.py`
- Used only by that specific agent

**Shared Variables**: Stored in `shared/` packages
- `messages/instructions/capabilities/v2/values.py`
- Imported by multiple agents and middleware

**Cross-Agent Shared**: Variables used by multiple agents
- Consider placing at `agents/` level if shared across many agents
- Or use shared packages for better organization

## Registry System

Instructions are registered in `messages/registry.yaml`:

```yaml
- id: agents/assistant
  path: instructions/agents/assistant
  latest: v2
  inputs:
    - OPERATING_PRINCIPLES
    - AGENT_CAPABILITIES
```

The registry enables:
- **Discovery**: Find available instructions
- **Version Resolution**: Automatic latest version detection
- **Validation**: Ensure paths and metadata are correct
- **Migration**: Gradual updates without breaking changes

## Version Management

### Creating New Versions

1. **Create new version directory**: `mkdir v3/`
2. **Copy complete snapshot**: Copy all files from `v2/` to `v3/`
3. **Update content**: Modify instruction files as needed
4. **Update registry**: Change `latest: v3` in `registry.yaml`
5. **Update CHANGELOG**: Document changes in `CHANGELOG.md`

### Version Compatibility

- **Historical Fidelity**: Old versions remain unchanged
- **Breaking Changes**: Require new version numbers
- **Shared Dependencies**: Versioned to prevent silent changes

## Shared Components

The `shared/` directory contains reusable components:

- **`base_capabilities/`**: Core agent operating principles and capabilities
- **`formatting/`**: Output formatting and presentation rules
- **`guardrails/`**: Safety constraints and behavioral boundaries
- **`intelligence/`**: Dynamic prompt generation functions
- **`tool_descriptions/`**: Agent tool contract definitions

## Best Practices

### 1. Version Early, Version Often
- Create new versions for any meaningful change
- Don't accumulate changes in a single version
- Use semantic versioning principles

### 2. Prefer Composition Over Templates
- Use `.py` files for static content
- Reserve `.j2` templates for dynamic content
- Combine both when needed (hybrid approach)

### 3. Centralize Access
- Always use `instruction_service` for access
- Avoid direct imports from instruction packages
- Keep business logic out of instruction files

### 4. Test Thoroughly
- Test instruction rendering with various inputs
- Validate template syntax and variable interpolation
- Ensure composables produce expected output

### 5. Document Changes
- Maintain detailed `CHANGELOG.md` files
- Include rationale for significant changes
- Reference related issues/PRs

## Migration from Legacy Systems

The instruction system has been migrated from scattered legacy locations:

- **`messages/preprompts/`** → `shared/intelligence/`
- **`messages/tool_descriptions/`** → `shared/tool_descriptions/`
- **Direct template files** → Versioned package structure

Legacy imports are gradually being updated to use the centralized service.

## Development Workflow

1. **Identify need**: Determine if new instruction or version is required
2. **Check registry**: See if instruction already exists
3. **Create/update package**: Follow package structure guidelines
4. **Update registry**: Register new instructions or versions
5. **Test integration**: Verify in actual usage contexts
6. **Update documentation**: Maintain accurate CHANGELOG and registry

## Troubleshooting

### Common Issues

**"Template not found"**
- Check registry entry exists
- Verify path is correct in registry
- Ensure version directory exists

**"Variable not defined"**
- Check `values.py` (or `variables.py`) contains required UPPERCASE constants
- Verify template syntax (`{{VARIABLE_NAME}}`)
- Test with `render_prompt()` directly

**"Composable not found"**
- Check `composables.py` exists and exports functions
- Verify function signatures match usage
- Test composable functions individually

### Debug Tools

```python
# Test instruction rendering
from messages.instruction_service import render_prompt
result = render_prompt("agents/assistant", debug=True)

# Check registry
from messages.instruction_service import _load_registry
registry = _load_registry()
print(registry.keys())
```

## Contributing

When adding new instructions:

1. Follow the package structure exactly
2. Include comprehensive `CHANGELOG.md`
3. Add registry entry with accurate metadata
4. Test rendering with various inputs
5. Update this README if patterns change

## Platform Integration Summary

The instruction system is a **central nervous system** for AI functionality across Cloush, accessed through a **single entry point**:

### **Single Source of Truth**
```python
# Every component imports from the same place
from messages.instruction_service import render_prompt, get_instruction_composables

# Same interface everywhere: API views, services, background tasks
agent_prompt = render_prompt("agents/assistant", **vars)
guardrails = get_instruction_composables("guardrails")
```

### **6 Instruction Categories**
- 🤖 **Agents**: Specialized AI assistants (assistant, cdo, candidates)
- 🔧 **Middleware**: Processing pipelines (router, analysis, context_compression)
- 🎨 **Functions**: Canvas tools (selection, document, heatmap)
- 📊 **Charts**: Visualization instructions
- 🔄 **Loops**: Conversation management
- 📈 **Evaluations**: Assessment and scoring
- 🔒 **Root-level shared**: guardrails, formatting, capabilities, online, tool_descriptions, intelligence

### **Key Architecture Benefits**
- **Consistency**: Every component uses `instruction_service` interface
- **Version Safety**: Registry-based resolution prevents version drift
- **Maintainability**: Instruction loading changes in one place
- **Testing**: Centralized access enables service-level mocking
- **Migration Safety**: Gradual migration from legacy paths
- **Security**: Guardrails always appended with override authority

## Related Documentation

- `docs/reports/messages_rearchitecture.md` - Detailed architecture rationale
- `docs/reports/messages_current_state_analysis.md` - Migration progress and gaps
- `messages/registry.yaml` - Complete instruction registry
- `messages/instruction_service.py` - Service API documentation
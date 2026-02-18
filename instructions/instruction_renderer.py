# instruction_renderer.py - Instruction Rendering and Composition
# Handles both Jinja2 template rendering and Python-based composition patterns
# New versioning: latest version IS the instruction (no separate "current" files)

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

logger = logging.getLogger(__name__)

# Base directory for instructions
INSTRUCTIONS_DIR = Path(__file__).parent

# Configure Jinja to load from the instructions directory
env = Environment(
    loader=FileSystemLoader(str(INSTRUCTIONS_DIR)),
    undefined=StrictUndefined,     # blow up if any var is missing
    autoescape=False,              # we don't HTML-escape LLM prompts
)


def _load_instruction_variables(instruction_path: str, version: Optional[str] = None) -> Dict[str, Any]:
    """Load values (fixed text blocks) from an instruction's values.py or variables.py file.

    Prefers values.py (canonical name for fixed instruction text); falls back to variables.py.

    Args:
        instruction_path: Relative path to instruction directory (e.g., "agents/assistant")
        version: Optional version string (e.g., "v2") or None for latest

    Returns:
        Dict of UPPERCASE constants from the instruction's values.py (or variables.py)
    """
    # Determine the correct path to values.py / variables.py (prefer values.py)
    if version:
        version_dir = INSTRUCTIONS_DIR / instruction_path / version
    else:
        instruction_dir = INSTRUCTIONS_DIR / instruction_path
        if not instruction_dir.exists():
            return {}
        version_dirs = [d for d in instruction_dir.iterdir() if d.is_dir() and d.name.startswith('v')]
        if not version_dirs:
            version_dir = instruction_dir
        else:
            version_dir = max(version_dirs, key=lambda d: int(d.name[1:]))

    values_path = version_dir / "values.py"
    variables_path = version_dir / "variables.py"
    if values_path.exists():
        version_path = values_path
    elif variables_path.exists():
        version_path = variables_path
    else:
        return {}

    try:
        # Import the variables module
        import importlib.util
        # Convert instruction path to valid module name by replacing slashes with underscores
        module_name = instruction_path.replace('/', '_') + '_variables'
        spec = importlib.util.spec_from_file_location(module_name, version_path)
        if spec and spec.loader:
            variables_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(variables_module)

            # Get all uppercase variables (convention for template variables)
            vars_dict = {}
            for attr_name in dir(variables_module):
                if not attr_name.startswith('_') and attr_name.isupper():
                    vars_dict[attr_name] = getattr(variables_module, attr_name)

            return vars_dict
    except Exception as e:
        error_msg = str(e)
        # Skip warnings for expected import issues in dynamic loading context
        if "attempted relative import" not in error_msg and "No module named" not in error_msg:
            logger.warning(f"Failed to load variables from {version_path}: {e}")

    return {}


def _load_instruction_composables_module(instruction_path: str, version: Optional[str] = None):
    """Load composables module directly for accessing constants and functions.

    Prefers import via package path so relative imports (e.g. from .values) resolve.
    Falls back to file-based load when the package is not importable.

    Args:
        instruction_path: Relative path to instruction directory (e.g., "tool_descriptions", "guardrails")
        version: Optional version string or None for latest

    Returns:
        Module object containing composables, or None if not found
    """
    import importlib

    # Resolve version directory
    if version:
        version_name = version
    else:
        instruction_dir = INSTRUCTIONS_DIR / instruction_path
        if not instruction_dir.exists():
            return None
        version_dirs = [d for d in instruction_dir.iterdir() if d.is_dir() and d.name.startswith('v')]
        if not version_dirs:
            return None
        version_name = max(version_dirs, key=lambda d: int(d.name[1:])).name

    composables_path = INSTRUCTIONS_DIR / instruction_path / version_name / "composables.py"
    if not composables_path.exists():
        return None

    # Prefer package import so relative imports (from .values) work
    package_path = "messages.instructions." + instruction_path.replace("/", ".") + "." + version_name + ".composables"
    try:
        return importlib.import_module(package_path)
    except Exception:
        pass

    # Fallback: load from file (relative imports in the module may fail)
    try:
        import importlib.util
        module_name = instruction_path.replace("/", "_") + "_composables"
        spec = importlib.util.spec_from_file_location(module_name, composables_path)
        if spec and spec.loader:
            composables_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(composables_module)
            return composables_module
    except Exception as e:
        error_msg = str(e)
        if "attempted relative import" not in error_msg and "No module named" not in error_msg:
            logger.warning(f"Failed to load composables module from {composables_path}: {e}")

    return None


def _load_instruction_composables(instruction_path: str, version: Optional[str] = None) -> Dict[str, Any]:
    """Load composables from an instruction's composables.py file.

    Args:
        instruction_path: Relative path to instruction directory (e.g., "agents/assistant")
        version: Optional version string or None for latest

    Returns:
        Dict of composable functions from the instruction's composables.py
    """
    # Determine the correct path to composables.py
    if version:
        composables_path = INSTRUCTIONS_DIR / instruction_path / version / "composables.py"
    else:
        # Find latest version directory
        instruction_dir = INSTRUCTIONS_DIR / instruction_path
        if instruction_dir.exists():
            version_dirs = [d for d in instruction_dir.iterdir() if d.is_dir() and d.name.startswith('v')]
            if version_dirs:
                latest_version = max(version_dirs, key=lambda d: int(d.name[1:]))
                composables_path = latest_version / "composables.py"
            else:
                composables_path = instruction_dir / "composables.py"  # fallback
        else:
            return {}

    if not composables_path.exists():
        return {}

    try:
        # Import the composables module
        import importlib.util
        # Convert instruction path to valid module name by replacing slashes with underscores
        module_name = instruction_path.replace('/', '_') + '_composables'
        spec = importlib.util.spec_from_file_location(module_name, composables_path)
        if spec and spec.loader:
            composables_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(composables_module)

            # Get all callable functions (composable functions)
            composables_dict = {}
            for attr_name in dir(composables_module):
                attr_value = getattr(composables_module, attr_name)
                if not attr_name.startswith('_') and callable(attr_value):
                    composables_dict[attr_name] = attr_value

            return composables_dict
    except Exception as e:
        error_msg = str(e)
        # Skip warnings for expected import issues in dynamic loading context
        if "attempted relative import" not in error_msg and "No module named" not in error_msg:
            logger.warning(f"Failed to load composables from {composables_path}: {e}")

    return {}


def render_template_instruction(
    instruction_path: str,
    version: Optional[str] = None,
    **context_vars
) -> str:
    """Render a Jinja2 template-based instruction.

    Args:
        instruction_path: Relative path to instruction directory (e.g., "agents/assistant")
        version: Optional version string (e.g., "v2") or None for latest
        **context_vars: Variables to pass to template

    Returns:
        Rendered instruction string

    Raises:
        FileNotFoundError: If template not found
        ValueError: If instruction path is invalid
    """
    if not instruction_path or not isinstance(instruction_path, str):
        raise ValueError("Instruction path must be a non-empty string")

    # Determine template path
    if version:
        template_path = f"{instruction_path}/{version}/instruction.j2"
    else:
        # Find latest version with template
        instruction_dir = INSTRUCTIONS_DIR / instruction_path
        if instruction_dir.exists():
            version_dirs = [d for d in instruction_dir.iterdir() if d.is_dir() and d.name.startswith('v')]
            version_dirs.sort(key=lambda d: int(d.name[1:]), reverse=True)  # highest first

            for version_dir in version_dirs:
                template_path_candidate = f"{instruction_path}/{version_dir.name}/instruction.j2"
                full_path = INSTRUCTIONS_DIR / template_path_candidate
                if full_path.exists():
                    template_path = template_path_candidate
                    break
            else:
                raise FileNotFoundError(f"No template found in any version of {instruction_path}")
        else:
            raise FileNotFoundError(f"Instruction directory not found: {instruction_path}")

    try:
        template = env.get_template(template_path)
        # Load instruction values from values.py (or variables.py)
        instruction_vars = _load_instruction_variables(instruction_path, version)
        # Merge with user-provided context (user context takes precedence)
        merged_context = {**instruction_vars, **context_vars}
        return template.render(**merged_context).strip()
    except Exception as e:
        logger.error(f"Failed to render template {template_path}: {e}")
        raise


def compose_python_instruction(
    instruction_path: str,
    version: Optional[str] = None,
    **context_vars
) -> str:
    """Compose a Python-based instruction using composables.

    Args:
        instruction_path: Relative path to instruction directory (e.g., "middleware/router")
        version: Optional version string or None for latest
        **context_vars: Variables to pass to composables

    Returns:
        Composed instruction string

    Raises:
        FileNotFoundError: If instruction not found
        ValueError: If instruction path is invalid
    """
    if not instruction_path or not isinstance(instruction_path, str):
        raise ValueError("Instruction path must be a non-empty string")

    # Load composables
    composables = _load_instruction_composables(instruction_path, version)

    if not composables:
        raise FileNotFoundError(f"No composables found for instruction: {instruction_path}")

    # Try to find a main composition function
    main_composer = composables.get('compose_instruction') or composables.get('build_instruction')

    if main_composer:
        try:
            return main_composer(**context_vars).strip()
        except Exception as e:
            logger.error(f"Failed to compose instruction {instruction_path}: {e}")
            raise
    else:
        # Fallback: try to load from instruction.py file
        instruction_py_path = INSTRUCTIONS_DIR / instruction_path
        if version:
            instruction_py_path = instruction_py_path / version / "instruction.py"
        else:
            # Find latest version with instruction.py
            if instruction_py_path.exists():
                version_dirs = [d for d in instruction_py_path.iterdir() if d.is_dir() and d.name.startswith('v')]
                version_dirs.sort(key=lambda d: int(d.name[1:]), reverse=True)  # highest first

                for version_dir in version_dirs:
                    candidate_path = version_dir / "instruction.py"
                    if candidate_path.exists():
                        instruction_py_path = candidate_path
                        break
                else:
                    raise FileNotFoundError(f"No instruction.py found in any version of {instruction_path}")

        if not instruction_py_path.exists():
            raise FileNotFoundError(f"Instruction file not found: {instruction_py_path}")

        try:
            # Convert instruction path to valid module name by replacing slashes with underscores
            module_name = instruction_path.replace('/', '_') + '_instruction'
            spec = importlib.util.spec_from_file_location(module_name, instruction_py_path)
            if spec and spec.loader:
                instruction_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(instruction_module)

                # Look for INSTRUCTION constant or compose_instruction function
                if hasattr(instruction_module, 'INSTRUCTION'):
                    return str(getattr(instruction_module, 'INSTRUCTION')).strip()
                elif hasattr(instruction_module, 'compose_instruction'):
                    composer = getattr(instruction_module, 'compose_instruction')
                    return composer(**context_vars).strip()
        except Exception as e:
            logger.error(f"Failed to load instruction.py from {instruction_py_path}: {e}")
            raise

    raise FileNotFoundError(f"No valid composition method found for instruction: {instruction_path}")


def compose_markdown_instruction(
    instruction_path: str,
    version: Optional[str] = None,
    **context_vars
) -> str:
    """Load a static markdown-based instruction.

    Args:
        instruction_path: Relative path to instruction directory (e.g., "guardrails")
        version: Optional version string or None for latest
        **context_vars: Ignored for markdown instructions (for API compatibility)

    Returns:
        Markdown instruction content

    Raises:
        FileNotFoundError: If instruction not found
    """
    if not instruction_path or not isinstance(instruction_path, str):
        raise ValueError("Instruction path must be a non-empty string")

    # Determine instruction.md path
    if version:
        instruction_md_path = INSTRUCTIONS_DIR / instruction_path / version / "instruction.md"
    else:
        # Find latest version with instruction.md
        instruction_dir = INSTRUCTIONS_DIR / instruction_path
        if instruction_dir.exists():
            version_dirs = [d for d in instruction_dir.iterdir() if d.is_dir() and d.name.startswith('v')]
            version_dirs.sort(key=lambda d: int(d.name[1:]), reverse=True)  # highest first

            for version_dir in version_dirs:
                candidate_path = version_dir / "instruction.md"
                if candidate_path.exists():
                    instruction_md_path = candidate_path
                    break
            else:
                raise FileNotFoundError(f"No instruction.md found in any version of {instruction_path}")

    if not instruction_md_path.exists():
        raise FileNotFoundError(f"Markdown instruction not found: {instruction_md_path}")

    try:
        with open(instruction_md_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"Failed to load markdown instruction from {instruction_md_path}: {e}")
        raise


def render_instruction(
    instruction_path: str,
    version: Optional[str] = None,
    **context_vars
) -> str:
    """Render or compose an instruction based on its type.

    Automatically detects whether to use template rendering (.j2), Python composition (.py),
    or static markdown (.md) based on available files in the latest version.

    Args:
        instruction_path: Relative path to instruction directory (e.g., "agents/assistant")
        version: Optional version string or None for latest
        **context_vars: Variables to pass to template or composables

    Returns:
        Rendered or composed instruction string

    Raises:
        FileNotFoundError: If no valid instruction found
    """
    # Determine base path for checking files
    if version:
        base_path = INSTRUCTIONS_DIR / instruction_path / version
    else:
        # Find latest version directory
        instruction_dir = INSTRUCTIONS_DIR / instruction_path
        if instruction_dir.exists():
            version_dirs = [d for d in instruction_dir.iterdir() if d.is_dir() and d.name.startswith('v')]
            if version_dirs:
                latest_version = max(version_dirs, key=lambda d: int(d.name[1:]))
                base_path = latest_version
            else:
                raise FileNotFoundError(f"No version directories found in {instruction_path}")
        else:
            raise FileNotFoundError(f"Instruction directory not found: {instruction_path}")

    # Check for different instruction types in priority order
    if (base_path / "instruction.j2").exists():
        return render_template_instruction(instruction_path, version, **context_vars)
    elif (base_path / "instruction.py").exists() or (base_path / "composables.py").exists():
        return compose_python_instruction(instruction_path, version, **context_vars)
    elif (base_path / "instruction.md").exists():
        return compose_markdown_instruction(instruction_path, version, **context_vars)
    else:
        raise FileNotFoundError(f"No valid instruction found in: {base_path}")


# Backward compatibility alias
render_prompt = render_instruction
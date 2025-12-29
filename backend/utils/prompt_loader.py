"""
Prompt Loader Utility
Handles loading and formatting of markdown prompt templates.

Features:
- LRU caching for efficient prompt loading
- Template variable substitution
- Singleton pattern for global access
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache


# Get the prompts directory path
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class PromptLoader:
    """
    Loads and manages prompt templates from markdown files.

    Usage:
        loader = PromptLoader()
        prompt = loader.load("consultant_system")
        formatted = loader.format("consultant_system", name="John", amount=1000)
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize the PromptLoader.

        Args:
            prompts_dir: Optional custom path to prompts directory
        """
        self.prompts_dir = prompts_dir if prompts_dir is not None else PROMPTS_DIR
        self._cache: Dict[str, str] = {}

    def load(self, prompt_name: str, use_cache: bool = True) -> str:
        """
        Load a prompt template from the prompts directory.

        Args:
            prompt_name: Name of the prompt file (without .md extension)
            use_cache: Whether to use cached version if available

        Returns:
            The prompt content as a string

        Raises:
            FileNotFoundError: If the prompt file doesn't exist
        """
        # Check cache first
        if use_cache and prompt_name in self._cache:
            return self._cache[prompt_name]

        prompt_path = self.prompts_dir / f"{prompt_name}.md"

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Store in cache
        self._cache[prompt_name] = content

        return content

    def format(self, prompt_name: str, **kwargs: Any) -> str:
        """
        Load and format a prompt template with the given variables.

        Uses {{variable}} syntax for placeholders.

        Args:
            prompt_name: Name of the prompt file (without .md extension)
            **kwargs: Variables to substitute in the template

        Returns:
            The formatted prompt string
        """
        template = self.load(prompt_name)

        # Use double curly brace syntax: {{variable}}
        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"  # Creates {{key}}
            template = template.replace(placeholder, str(value))

        return template

    def format_with_defaults(
        self,
        prompt_name: str,
        defaults: Dict[str, Any],
        **kwargs: Any
    ) -> str:
        """
        Load and format a prompt with default values and overrides.

        Args:
            prompt_name: Name of the prompt file
            defaults: Default values for template variables
            **kwargs: Override values (take precedence over defaults)

        Returns:
            The formatted prompt string
        """
        # Merge defaults with overrides
        merged = {**defaults, **kwargs}
        return self.format(prompt_name, **merged)

    def clear_cache(self) -> None:
        """Clear the prompt cache."""
        self._cache.clear()

    def reload(self, prompt_name: str) -> str:
        """
        Force reload a prompt from disk, bypassing cache.

        Args:
            prompt_name: Name of the prompt file

        Returns:
            The prompt content
        """
        if prompt_name in self._cache:
            del self._cache[prompt_name]
        return self.load(prompt_name, use_cache=False)

    def list_prompts(self) -> List[str]:
        """
        List all available prompt files.

        Returns:
            List of prompt names (without .md extension)
        """
        if not self.prompts_dir.exists():
            return []

        return [f.stem for f in self.prompts_dir.glob("*.md")]

    def exists(self, prompt_name: str) -> bool:
        """
        Check if a prompt file exists.

        Args:
            prompt_name: Name of the prompt file

        Returns:
            True if the prompt exists, False otherwise
        """
        prompt_path = self.prompts_dir / f"{prompt_name}.md"
        return prompt_path.exists()

    def get_prompts_dir(self) -> Path:
        """Get the prompts directory path."""
        return self.prompts_dir


# Singleton instance
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """
    Get or create the singleton PromptLoader instance.

    Returns:
        The global PromptLoader instance
    """
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader


# Convenience functions for direct use

@lru_cache(maxsize=32)
def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from the prompts directory.

    This is a cached convenience function.

    Args:
        prompt_name: Name of the prompt file (without .md extension)

    Returns:
        The prompt content as a string

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    prompt_path = PROMPTS_DIR / f"{prompt_name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def format_prompt(prompt_name: str, **kwargs: Any) -> str:
    """
    Load and format a prompt template with the given variables.

    Args:
        prompt_name: Name of the prompt file (without .md extension)
        **kwargs: Variables to substitute in the template

    Returns:
        The formatted prompt string
    """
    template = load_prompt(prompt_name)

    # Use double curly brace syntax: {{variable}}
    for key, value in kwargs.items():
        placeholder = f"{{{{{key}}}}}"  # Creates {{key}}
        template = template.replace(placeholder, str(value))

    return template


def clear_prompt_cache() -> None:
    """Clear both the function cache and the singleton cache."""
    load_prompt.cache_clear()
    loader = get_prompt_loader()
    loader.clear_cache()


def list_available_prompts() -> List[str]:
    """
    List all available prompt files.

    Returns:
        List of prompt names
    """
    if not PROMPTS_DIR.exists():
        return []

    return [f.stem for f in PROMPTS_DIR.glob("*.md")]

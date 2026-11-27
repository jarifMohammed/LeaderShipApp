from pathlib import Path
from typing import Any, Dict, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape


class PromptLoader:
    """Lightweight Jinja2 prompt template loader and renderer."""

    def __init__(self, template_dir: Optional[str] = None):
        if template_dir is None:
            template_dir = str(Path(__file__).parent / "templates")
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, **kwargs: Any) -> str:
        """Renders a Jinja2 prompt template with the provided context."""
        template = self.env.get_template(template_name)
        return template.render(**kwargs)


_prompt_loader_instance: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    global _prompt_loader_instance
    if _prompt_loader_instance is None:
        _prompt_loader_instance = PromptLoader()
    return _prompt_loader_instance


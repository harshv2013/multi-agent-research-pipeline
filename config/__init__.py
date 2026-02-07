"""
Configuration package for multi-agent system.
"""
from .settings import Settings, get_settings
from .prompts import AgentPrompts

__all__ = ["Settings", "get_settings", "AgentPrompts"]
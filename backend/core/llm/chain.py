"""Placeholder for LangChain chain definitions.

Implementers should define chains that orchestrate prompt templates, retrievers,
and LLM calls. This module is referenced from `core/llm/service.py` when the
LangChain-based pipeline is implemented.
"""

from typing import Any

class LLMChainWrapper:
    def __init__(self, llm_client: Any):
        self.llm = llm_client

    def run(self, **kwargs):
        # Placeholder
        return ""
from abc import ABC, abstractmethod
from typing import Any
from ..models import PipelineContext

class Stage(ABC):
    def __init__(self, context: PipelineContext):
        self.context = context

    @abstractmethod
    def execute(self, data: Any) -> Any:
        pass

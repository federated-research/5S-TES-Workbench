from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ...common.params.tes_builder_params import TESTaskParams

T = TypeVar("T")


class BaseTESTemplate(ABC, Generic[T]):
    """
    Abstract base class for all TES task templates.

    Each template must provide:
        - `name` property: Unique identifier used for registration
          and lookup in the template registry.
        - `resolve()`: Accepts user-provided params of type T and
          returns a fully resolved TESTaskParams.

    Use Generic[T] to declare the expected user params TypedDict:
        class MyTemplate(BaseTESTemplate[MyUserParams]):
            ...
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique name for this template. Used for
        registration and lookup in the template registry.
        """

    @abstractmethod
    def resolve(self, overrides: T) -> TESTaskParams:
        """
        Merges user-provided overrides with internal template
        defaults and returns the fully resolved TESTaskParams.
        """

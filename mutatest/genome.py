"""Genome class definition.
"""
import ast
import logging

from pathlib import Path
from typing import Optional, Set, Union

from mutatest.transformers import LocIndex, MutateAST


LOGGER = logging.getLogger(__name__)


class Genome:
    """The Genome class describes the source file to be mutated.

    The class describes a single .py file and has properties for the abstract syntax tree (AST)
    and the viable mutation targets. You can initialize without any arguments. If the source_file
    is changed the ast and targets properties will be recalculated for that file.
    """

    def __init__(self, source_file: Optional[Union[str, Path]] = None) -> None:
        """Initialize the Genome.

        There are internal properties prefixed with an underscore used for the lazy evaluation
        of the AST and mutation targets.

        Args:
            source_file: an optional source file path
        """
        self._source_file = Path(source_file) if source_file else None
        self._ast: Optional[ast.Module] = None
        self._targets: Optional[Set[LocIndex]] = None

    @property
    def source_file(self) -> Path:
        """The source .py file represented by this Genome."""
        return self._source_file

    @source_file.setter
    def source_file(self, value: Path) -> None:
        """Setter for the source_file that clears the AST and targets for recalculation."""
        self._source_file = Path(value)
        self._ast = None
        self._targets = None

    @property
    def ast(self) -> ast.Module:  # type: ignore
        """Abstract Syntax Tree (AST) representation of the source_file."""
        if self._ast is None:
            with open(self.source_file, "rb") as src_stream:
                self._ast = ast.parse(src_stream.read())
        return self._ast

    @property
    def targets(self) -> Set[LocIndex]:
        """Viable mutation targets within the AST of the source_file."""
        if self._targets is None:
            ro_mast = MutateAST(
                target_idx=None, mutation=None, readonly=True, src_file=self.source_file
            )
            ro_mast.visit(self.ast)
            self._targets = ro_mast.locs
        return self._targets

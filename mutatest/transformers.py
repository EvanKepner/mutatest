"""AST Transformers.
"""
import ast
import logging

from pathlib import Path
from typing import List, NamedTuple, Optional, Set, Union


LOGGER = logging.getLogger(__name__)

BINOP_TYPES: Set[type] = {ast.Add, ast.Sub, ast.Div, ast.Mult, ast.Pow, ast.Mod, ast.FloorDiv}

BINOP_BIT_TYPES: Set[type] = {ast.LShift, ast.RShift, ast.BitAnd, ast.BitOr, ast.BitXor}

CMPOP_TYPES: Set[type] = {ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE}


class LocIndex(NamedTuple):
    """Location index within AST to mark mutatest targets."""

    ast_class: str
    lineno: int
    col_offset: int
    op_type: type


class MutateAST(ast.NodeTransformer):
    """AST NodeTransformer to replace nodes with mutations by visits."""

    def __init__(
        self, target_idx: Optional[LocIndex] = None, mutation: Optional[type] = None
    ) -> None:
        """Create the AST node transformer for mutations.

        If the target_idx and mutatest are set to None then no transformations are applied;
        however, the locs attribute is updated with the locations of nodes that could
        be transformed. This allows the class to function both as an inspection method
        and as a mutatest transformer.

        Args:
            target_idx: Location index for the mutatest in the AST
            mutation: the mutatest to apply
        """
        self.locs: Set[LocIndex] = set()
        self.target_idx = target_idx
        self.mutation = mutation

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        self.generic_visit(node)

        idx = LocIndex("BinOp", node.lineno, node.col_offset, type(node.op))
        self.locs.add(idx)

        if idx == self.target_idx and self.mutation:
            LOGGER.debug("Mutating idx: %s with %s", self.target_idx, self.mutation)
            return ast.copy_location(
                ast.BinOp(left=node.left, op=self.mutation(), right=node.right), node
            )

        else:
            LOGGER.debug("No mutations applied")
            return node


def get_mutations_for_target(target: LocIndex) -> Set[type]:
    """Given a target, find all the mutations that could apply from the definitions.

    Args:
        target: the location index target

    Returns:
        Set of types that can mutated into the target op
    """
    search_space: List[Set[type]] = [BINOP_TYPES, BINOP_BIT_TYPES, CMPOP_TYPES]

    mutation_ops: Set[type] = set()

    for potential_ops in search_space:
        if target.op_type in potential_ops:
            LOGGER.debug("Potential mutatest operations found for target: %s", target.op_type)
            mutation_ops = potential_ops.copy()
            mutation_ops.remove(target.op_type)
            break

    return mutation_ops


def get_ast_from_src(src_file: Union[str, Path]) -> ast.Module:
    """Create an AST from a source file

    Args:
        src_file: the source file to  build into an AST

    Returns:
        The AST
    """
    with open(src_file, "rb") as src_stream:
        source = src_stream.read()
        return ast.parse(source)

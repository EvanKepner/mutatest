"""AST Transformers.
"""
import ast
import logging

from pathlib import Path
from typing import List, NamedTuple, Optional, Set, Union


LOGGER = logging.getLogger(__name__)


class LocIndex(NamedTuple):
    """Location index within AST to mark mutatest targets."""

    ast_class: str
    lineno: int
    col_offset: int
    op_type: type


class MutationOpSet(NamedTuple):
    """Container for compatible mutation operations. Also used in the CLI display."""

    name: str
    operations: Set[type]


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
        """BinOp nodes are bit-shifts and general operators like add, divide, etc."""
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

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        """Compare nodes are ==, >= etc."""
        self.generic_visit(node)

        # taking only the first operation in the compare node
        # in basic testing, things like (a==b)==1 still end up with lists of 1,
        # but since the AST docs specify a list of operations this seems safer.
        idx = LocIndex("Compare", node.lineno, node.col_offset, type(node.ops[0]))
        self.locs.add(idx)

        if idx == self.target_idx and self.mutation:
            LOGGER.debug("Mutating idx: %s with %s", self.target_idx, self.mutation)

            # TODO: Determine when/how this case would actually be called
            if len(node.ops) > 1:
                # unlikely test case where the comparison has multiple values
                LOGGER.debug("Multiple compare ops in node, len: %s", len(node.ops))
                existing_ops = [i for i in node.ops]
                mutation_ops = [self.mutation()] + existing_ops[1:]

                return ast.copy_location(
                    ast.Compare(left=node.left, ops=mutation_ops, comparators=node.comparators),
                    node,
                )

            else:
                # typical comparison case, will also catch (a==b)==1 as an example.
                LOGGER.debug("Single comparison node operation")
                new_node = ast.Compare(
                    left=node.left, ops=[self.mutation()], comparators=node.comparators
                )
                LOGGER.debug("New node:\n%s", ast.dump(new_node))

                return ast.copy_location(
                    ast.Compare(
                        left=node.left, ops=[self.mutation()], comparators=node.comparators
                    ),
                    node,
                )

        else:
            LOGGER.debug("No mutations applied")
            return node

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        """Boolean operations, AND/OR."""
        self.generic_visit(node)

        idx = LocIndex("BoolOp", node.lineno, node.col_offset, type(node.op))
        self.locs.add(idx)

        if idx == self.target_idx and self.mutation:
            LOGGER.debug("Mutating idx: %s with %s", self.target_idx, self.mutation)
            return ast.copy_location(ast.BoolOp(op=self.mutation(), values=node.values), node)

        else:
            LOGGER.debug("No mutations applied")
            return node


def get_compatible_operation_sets() -> List[MutationOpSet]:
    """Utility function to return a list of compatible AST mutations with names.

    All of the mutation transformation sets that are supported by mutatest are defined here.
    See: https://docs.python.org/3/library/ast.html#abstract-grammar

    This is used to create the search space in finding mutations for a target, and
    also to list the support operations in the CLI help function.

    Returns:
        List of MutationOpSets that have substitutable operations
    """
    binop_types: Set[type] = {ast.Add, ast.Sub, ast.Div, ast.Mult, ast.Pow, ast.Mod, ast.FloorDiv}
    binop_bit_cmp_types: Set[type] = {ast.BitAnd, ast.BitOr, ast.BitXor}
    binop_bit_shift_types: Set[type] = {ast.LShift, ast.RShift}
    cmpop_types: Set[type] = {ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE}
    cmpop_is_types: Set[type] = {ast.Is, ast.IsNot}
    cmpop_in_types: Set[type] = {ast.In, ast.NotIn}
    boolop_types: Set[type] = {ast.And, ast.Or}

    return [
        MutationOpSet(name="BinOp", operations=binop_types),
        MutationOpSet(name="BinOp Bit Comparison", operations=binop_bit_cmp_types),
        MutationOpSet(name="BinOp Bit Shifts", operations=binop_bit_shift_types),
        MutationOpSet(name="Compare", operations=cmpop_types),
        MutationOpSet(name="Compare Is", operations=cmpop_is_types),
        MutationOpSet(name="Compare In", operations=cmpop_in_types),
        MutationOpSet(name="BoolOp", operations=boolop_types),
    ]


def get_mutations_for_target(target: LocIndex) -> Set[type]:
    """Given a target, find all the mutations that could apply from the AST definitions.

    Args:
        target: the location index target

    Returns:
        Set of types that can mutated into the target op
    """
    search_space: List[Set[type]] = [m.operations for m in get_compatible_operation_sets()]
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

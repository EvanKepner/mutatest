"""AST Transformers
"""
import ast
import logging
import pathlib

from typing import Any, List, Optional, Set, Union, NamedTuple

LOGGER = logging.getLogger(__name__)

BINOP_TYPES: Set[type] = {
    ast.Add, ast.Sub,
    ast.Div, ast.Mult,
    ast.Pow,
}

CMPOP_TYPES: Set[type] = {
    ast.Eq, ast.NotEq,
    ast.Lt, ast.LtE, ast.Gt, ast.GtE,

}


class LocIndex(NamedTuple):
    ast_class: str
    lineno: int
    col_offset:int
    op_type: type


class MutateAST(ast.NodeTransformer):

    def __init__(self,
                 target_idx: Optional[LocIndex]=None,
                 mutation: Optional[type]=None) -> None:
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
                ast.BinOp(left=node.left, op=self.mutation(), right=node.right),
                node)

        else:
            LOGGER.debug("No mutations applied")
            return node


def get_mutations_for_target(target: LocIndex) -> Set[Any]:
    # the target must have an op_type propoerty

    search_space: List[Set[type]] = [BINOP_TYPES, CMPOP_TYPES]

    mutation_ops: Set[type] = set()

    for potential_ops in search_space:
        if target.op_type in potential_ops:
            LOGGER.debug("Potential mutation operations found for target: %s", target.op_type)
            mutation_ops = potential_ops.copy()
            mutation_ops.remove(target.op_type)
            break

    return mutation_ops


def get_ast_from_src(src_file: Union[str, pathlib.PurePath]) -> ast.Module:

    with open(src_file, "rb") as src_stream:
        source = src_stream.read()
        return ast.parse(source)

"""AST Transformers
"""
import ast
import logging
import pathlib

from typing import Any, Set, Union, NamedTuple

LOGGER = logging.getLogger(__name__)

BINOP_TYPES = {
    ast.Add, ast.Sub,
    ast.Div, ast.Mult, ast.Pow,
}

CMPOP_TYPES = {
    ast.Eq, ast.NotEq,
    ast.Lt, ast.LtE, ast.Gt, ast.GtE,

}


class LocIndex(NamedTuple):
    ast_class: str
    lineno: int
    col_offset:int
    op_type: type


class MutateAST(ast.NodeTransformer):

    def __init__(self, readonly=False, target=None):
        self.readonly = readonly
        self.locs = set()
        self.target = target

    def visit_BinOp(self, node):
        """Replace BinOps with ast.Sub()"""
        self.generic_visit(node)

        idx = LocIndex("BinOp", node.lineno, node.col_offset, type(node.op))
        self.locs.add(idx)

        if self.readonly:
            return node

        else:
            LOGGER.debug("Mutating binOp with Sub")
            return ast.copy_location(
                ast.BinOp(left=node.left, op=ast.Sub(), right=node.right),
                node)


def get_mutations_for_target(target: LocIndex) -> Set[Any]:

    search_space = [BINOP_TYPES, CMPOP_TYPES]

    mutation_ops = set()

    for potential_ops in search_space:
        if target.op_type in potential_ops:
            mutation_ops = potential_ops.copy()
            mutation_ops.remove(target.op_type)
            break

    return mutation_ops

def get_ast_from_src(src_file: Union[str, pathlib.PurePath]) -> ast.Module:

    with open(src_file, "rb") as src_stream:
        source = src_stream.read()
        return ast.parse(source)

"""AST Transformers
"""
import ast
import logging
import pathlib

from typing import Union, NamedTuple

LOGGER = logging.getLogger(__name__)


def get_ast_from_src(src_file: Union[str, pathlib.PurePath]) -> ast.Module:

    with open(src_file, "rb") as src_stream:
        source = src_stream.read()
        return ast.parse(source)


class LocIndex(NamedTuple):
    ast_class: str
    lineno: int
    col_offset:int
    op_type: type


class MutateAST(ast.NodeTransformer):

    def __init__(self, readonly=False):
        self.readonly = readonly
        self.locs = set()

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

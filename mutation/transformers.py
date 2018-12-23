"""AST Transformers
"""
import ast
import logging

LOGGER = logging.getLogger(__name__)


class RewriteAddSub(ast.NodeTransformer):

    def visit_BinOp(self, node):
        """Replace BinOps with ast.Sub()"""
        self.generic_visit(node)

        LOGGER.debug("Mutating binOp with Sub")
        return ast.copy_location(
            ast.BinOp(left=node.left, op=ast.Sub(), right=node.right),
            node)

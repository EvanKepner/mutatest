"""AST Transformers
"""
import ast


class RewriteAddSub(ast.NodeTransformer):

    def visit_BinOp(self, node):
        """Replace BinOps with ast.Sub()"""
        return ast.copy_location(
            ast.BinOp(left=node.left, op=ast.Sub(), right=node.right),
            node)

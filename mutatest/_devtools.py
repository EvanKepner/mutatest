"""Development tools.

These are utility classes and functions used in the development process for new operations
and features. They are not used by the main program, and are not covered in standard testing.
"""
import ast


class NodeLister(ast.NodeVisitor):  # pragma: no cover
    """Generic node listing tool to investigate operations on testing files.

    Use interactively by passing an AST e.g.

    >>> tree = mutatest.transformers.get_ast_from_src("somefile.py")
    >>> NodeLister().visit(tree)
    """

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        print(f"Function: {node.name}")
        print(ast.dump(node))
        self.generic_visit(node)

    # ADDED AND TESTED
    ################################################################################################

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        # +=, -=, /=, *=
        print(f"AugAssign: {node}")
        print(ast.dump(node))
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        # + - / * ^ %
        print(f"BinOP: {node}")
        print(ast.dump(node))
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # and, or
        print(f"Bool: {node}")
        print(ast.dump(node))
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        # > < >= == <= !=, is is not
        print(f"Compare: {node}")
        print(ast.dump(node))
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        # have is, is not already, not clear If directly is a valuable mutation
        print(f"If: {node}")
        print(ast.dump(node))
        self.generic_visit(node)

    def visit_Index(self, node: ast.Index) -> None:
        # actual slicing
        print(f"Index: {node}")
        print(ast.dump(node))

    def visit_NameConstant(self, node: ast.NameConstant) -> None:
        # True, False, None
        print(f"NameConstant: {node}")
        print(ast.dump(node))
        self.generic_visit(node)

    def visit_Slice(self, node: ast.Slice) -> None:
        # actual slicing
        print(f"Slice: {node}")
        print(ast.dump(node))
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        # iterable indexing, has Slice operations
        print(f"Subscript: {node}")
        print(ast.dump(node))
        self.generic_visit(node)

    # IN DEVELOPMENT
    ################################################################################################

    # FUTURE DEVELOPMENT
    ################################################################################################

    def visit_Assign(self, node: ast.Assign) -> None:
        # variable assignment
        # print(f"Assign: {node}")
        # print(ast.dump(node))
        self.generic_visit(node)

    # INVESTIGATED BUT NOT COVERED
    ################################################################################################

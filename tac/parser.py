"""
Recursive Descent Parser for C-like syntax with Operator Precedence.
"""
from typing import List, Optional
from .tokens import Token, TokenType
from .ast_nodes import (
    ASTNode, ProgramNode, BlockNode, VarDeclNode, VarDeclarator,
    AssignNode, BinaryOpNode, UnaryOpNode, LiteralNode, VarNode,
    ArrayRefNode, IfNode, WhileNode, DoWhileNode, ForNode,
    SwitchNode, CaseNode, BreakNode, ContinueNode, ReturnNode,
    FunctionCallNode, FunctionDeclNode
)


class ParserError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(f"Parser Error at line {token.line}, col {token.column}: {message} (found {token.value!r})")
        self.message = message
        self.token = token


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]  # EOF

    def _match(self, *types: TokenType) -> bool:
        if self._peek().type in types:
            self._advance()
            return True
        return False

    def _check(self, *types: TokenType) -> bool:
        return self._peek().type in types

    def _advance(self) -> Token:
        token = self._peek()
        if token.type != TokenType.EOF:
            self.pos += 1
        return token

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._peek().type == token_type:
            return self._advance()
        raise ParserError(message, self._peek())

    def parse(self) -> ProgramNode:
        statements = []
        while not self._check(TokenType.EOF):
            stmt = self._parse_top_level()
            if stmt:
                statements.append(stmt)
        return ProgramNode(statements=statements)

    def _parse_top_level(self) -> ASTNode:
        # Check for function definition vs variable declaration
        # e.g., 'int foo(...) { ... }' or 'void main() { ... }'
        if self._check(TokenType.INT, TokenType.FLOAT_KW, TokenType.CHAR, TokenType.VOID):
            # Look ahead: type ID (
            if self._peek(1).type == TokenType.IDENTIFIER and self._peek(2).type == TokenType.LPAREN:
                return self._parse_function_decl()
            return self._parse_var_decl()
        return self._parse_statement()

    def _parse_function_decl(self) -> FunctionDeclNode:
        type_tok = self._advance()
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected function name")
        self._consume(TokenType.LPAREN, "Expected '(' after function name")

        params = []
        if not self._check(TokenType.RPAREN):
            while True:
                if self._check(TokenType.INT, TokenType.FLOAT_KW, TokenType.CHAR, TokenType.VOID):
                    p_type = self._advance()
                    p_name = self._consume(TokenType.IDENTIFIER, "Expected parameter name")
                    decl = VarDeclNode(
                        type_name=p_type.value,
                        declarators=[VarDeclarator(name=p_name.value, line=p_name.line, column=p_name.column)],
                        line=p_type.line,
                        column=p_type.column
                    )
                    params.append(decl)
                if not self._match(TokenType.COMMA):
                    break

        self._consume(TokenType.RPAREN, "Expected ')' after parameters")
        body = self._parse_block()
        return FunctionDeclNode(
            return_type=type_tok.value,
            name=name_tok.value,
            parameters=params,
            body=body,
            line=type_tok.line,
            column=type_tok.column
        )

    def _parse_var_decl(self) -> VarDeclNode:
        type_tok = self._advance()
        declarators = []

        while True:
            name_tok = self._consume(TokenType.IDENTIFIER, "Expected variable name")
            dims = []
            while self._match(TokenType.LBRACKET):
                size_expr = self._parse_expression()
                self._consume(TokenType.RBRACKET, "Expected ']' after array size")
                dims.append(size_expr)

            init_val = None
            if self._match(TokenType.ASSIGN):
                init_val = self._parse_expression()

            declarators.append(VarDeclarator(
                name=name_tok.value,
                array_dimensions=dims,
                init_value=init_val,
                line=name_tok.line,
                column=name_tok.column
            ))

            if not self._match(TokenType.COMMA):
                break

        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")
        return VarDeclNode(
            type_name=type_tok.value,
            declarators=declarators,
            line=type_tok.line,
            column=type_tok.column
        )

    def _parse_block(self) -> BlockNode:
        lbrace = self._consume(TokenType.LBRACE, "Expected '{'")
        stmts = []
        while not self._check(TokenType.RBRACE, TokenType.EOF):
            s = self._parse_statement()
            if s:
                stmts.append(s)
        self._consume(TokenType.RBRACE, "Expected '}'")
        return BlockNode(statements=stmts, line=lbrace.line, column=lbrace.column)

    def _parse_statement(self) -> ASTNode:
        tok = self._peek()

        if tok.type in (TokenType.INT, TokenType.FLOAT_KW, TokenType.CHAR, TokenType.VOID):
            return self._parse_var_decl()

        if tok.type == TokenType.LBRACE:
            return self._parse_block()

        if tok.type == TokenType.IF:
            return self._parse_if()

        if tok.type == TokenType.WHILE:
            return self._parse_while()

        if tok.type == TokenType.DO:
            return self._parse_do_while()

        if tok.type == TokenType.FOR:
            return self._parse_for()

        if tok.type == TokenType.SWITCH:
            return self._parse_switch()

        if tok.type == TokenType.BREAK:
            b_tok = self._advance()
            self._consume(TokenType.SEMICOLON, "Expected ';' after break")
            return BreakNode(line=b_tok.line, column=b_tok.column)

        if tok.type == TokenType.CONTINUE:
            c_tok = self._advance()
            self._consume(TokenType.SEMICOLON, "Expected ';' after continue")
            return ContinueNode(line=c_tok.line, column=c_tok.column)

        if tok.type == TokenType.RETURN:
            r_tok = self._advance()
            expr = None
            if not self._check(TokenType.SEMICOLON):
                expr = self._parse_expression()
            self._consume(TokenType.SEMICOLON, "Expected ';' after return")
            return ReturnNode(expr=expr, line=r_tok.line, column=r_tok.column)

        if tok.type == TokenType.SEMICOLON:
            self._advance()
            return BlockNode(statements=[])  # Empty statement

        # Expression statement (assignment, increment, function call, etc.)
        expr = self._parse_expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression")
        return expr

    def _parse_if(self) -> IfNode:
        if_tok = self._consume(TokenType.IF, "Expected 'if'")
        self._consume(TokenType.LPAREN, "Expected '(' after 'if'")
        cond = self._parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after if condition")
        then_branch = self._parse_statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._parse_statement()
        return IfNode(
            condition=cond,
            then_branch=then_branch,
            else_branch=else_branch,
            line=if_tok.line,
            column=if_tok.column
        )

    def _parse_while(self) -> WhileNode:
        while_tok = self._consume(TokenType.WHILE, "Expected 'while'")
        self._consume(TokenType.LPAREN, "Expected '(' after 'while'")
        cond = self._parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after while condition")
        body = self._parse_statement()
        return WhileNode(condition=cond, body=body, line=while_tok.line, column=while_tok.column)

    def _parse_do_while(self) -> DoWhileNode:
        do_tok = self._consume(TokenType.DO, "Expected 'do'")
        body = self._parse_statement()
        self._consume(TokenType.WHILE, "Expected 'while' after do body")
        self._consume(TokenType.LPAREN, "Expected '(' after 'while'")
        cond = self._parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after do-while condition")
        self._consume(TokenType.SEMICOLON, "Expected ';' after do-while")
        return DoWhileNode(body=body, condition=cond, line=do_tok.line, column=do_tok.column)

    def _parse_for(self) -> ForNode:
        for_tok = self._consume(TokenType.FOR, "Expected 'for'")
        self._consume(TokenType.LPAREN, "Expected '(' after 'for'")

        init = None
        if not self._check(TokenType.SEMICOLON):
            if self._peek().type in (TokenType.INT, TokenType.FLOAT_KW, TokenType.CHAR):
                init = self._parse_var_decl()
            else:
                init = self._parse_expression()
                self._consume(TokenType.SEMICOLON, "Expected ';' after for init")
        else:
            self._consume(TokenType.SEMICOLON, "Expected ';'")

        cond = None
        if not self._check(TokenType.SEMICOLON):
            cond = self._parse_expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after for condition")

        step = None
        if not self._check(TokenType.RPAREN):
            step = self._parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after for clauses")

        body = self._parse_statement()
        return ForNode(init=init, condition=cond, step=step, body=body, line=for_tok.line, column=for_tok.column)

    def _parse_switch(self) -> SwitchNode:
        switch_tok = self._consume(TokenType.SWITCH, "Expected 'switch'")
        self._consume(TokenType.LPAREN, "Expected '(' after 'switch'")
        expr = self._parse_expression()
        self._consume(TokenType.RPAREN, "Expected ')' after switch expression")
        self._consume(TokenType.LBRACE, "Expected '{' to start switch body")

        cases = []
        while not self._check(TokenType.RBRACE, TokenType.EOF):
            if self._match(TokenType.CASE):
                case_val = self._parse_expression()
                self._consume(TokenType.COLON, "Expected ':' after case value")
                case_stmts = []
                while not self._check(TokenType.CASE, TokenType.DEFAULT, TokenType.RBRACE, TokenType.EOF):
                    s = self._parse_statement()
                    if s:
                        case_stmts.append(s)
                cases.append(CaseNode(value=case_val, statements=case_stmts))
            elif self._match(TokenType.DEFAULT):
                self._consume(TokenType.COLON, "Expected ':' after default")
                case_stmts = []
                while not self._check(TokenType.CASE, TokenType.DEFAULT, TokenType.RBRACE, TokenType.EOF):
                    s = self._parse_statement()
                    if s:
                        case_stmts.append(s)
                cases.append(CaseNode(value=None, statements=case_stmts))
            else:
                raise ParserError("Expected 'case' or 'default' in switch", self._peek())

        self._consume(TokenType.RBRACE, "Expected '}' to close switch body")
        return SwitchNode(expr=expr, cases=cases, line=switch_tok.line, column=switch_tok.column)

    # Precedence climbing / Pratt-style expression parsing
    def _parse_expression(self) -> ASTNode:
        return self._parse_assignment()

    def _parse_assignment(self) -> ASTNode:
        expr = self._parse_logical_or()

        if self._check(TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
                        TokenType.STAR_ASSIGN, TokenType.SLASH_ASSIGN, TokenType.PERCENT_ASSIGN):
            op_tok = self._advance()
            val = self._parse_assignment()  # Right associative
            return AssignNode(target=expr, op=op_tok.value, value=val, line=op_tok.line, column=op_tok.column)

        return expr

    def _parse_logical_or(self) -> ASTNode:
        expr = self._parse_logical_and()
        while self._match(TokenType.OR):
            op = '||'
            right = self._parse_logical_and()
            expr = BinaryOpNode(op=op, left=expr, right=right, line=expr.line, column=expr.column)
        return expr

    def _parse_logical_and(self) -> ASTNode:
        expr = self._parse_equality()
        while self._match(TokenType.AND):
            op = '&&'
            right = self._parse_equality()
            expr = BinaryOpNode(op=op, left=expr, right=right, line=expr.line, column=expr.column)
        return expr

    def _parse_equality(self) -> ASTNode:
        expr = self._parse_relational()
        while self._check(TokenType.EQ, TokenType.NEQ):
            op_tok = self._advance()
            right = self._parse_relational()
            expr = BinaryOpNode(op=op_tok.value, left=expr, right=right, line=op_tok.line, column=op_tok.column)
        return expr

    def _parse_relational(self) -> ASTNode:
        expr = self._parse_additive()
        while self._check(TokenType.LT, TokenType.LEQ, TokenType.GT, TokenType.GEQ):
            op_tok = self._advance()
            right = self._parse_additive()
            expr = BinaryOpNode(op=op_tok.value, left=expr, right=right, line=op_tok.line, column=op_tok.column)
        return expr

    def _parse_additive(self) -> ASTNode:
        expr = self._parse_multiplicative()
        while self._check(TokenType.PLUS, TokenType.MINUS):
            op_tok = self._advance()
            right = self._parse_multiplicative()
            expr = BinaryOpNode(op=op_tok.value, left=expr, right=right, line=op_tok.line, column=op_tok.column)
        return expr

    def _parse_multiplicative(self) -> ASTNode:
        expr = self._parse_exponent()
        while self._check(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op_tok = self._advance()
            right = self._parse_exponent()
            expr = BinaryOpNode(op=op_tok.value, left=expr, right=right, line=op_tok.line, column=op_tok.column)
        return expr

    def _parse_exponent(self) -> ASTNode:
        expr = self._parse_unary()
        while self._match(TokenType.CARET):
            right = self._parse_unary()
            expr = BinaryOpNode(op='^', left=expr, right=right, line=expr.line, column=expr.column)
        return expr

    def _parse_unary(self) -> ASTNode:
        if self._check(TokenType.PLUS, TokenType.MINUS, TokenType.NOT, TokenType.INCREMENT, TokenType.DECREMENT):
            op_tok = self._advance()
            operand = self._parse_unary()
            op_str = op_tok.value
            if op_str == '-':
                op_str = 'uminus'
            elif op_str == '+':
                return operand  # Unary plus is a no-op
            return UnaryOpNode(op=op_str, operand=operand, is_prefix=True, line=op_tok.line, column=op_tok.column)
        return self._parse_postfix()

    def _parse_postfix(self) -> ASTNode:
        expr = self._parse_primary()

        while True:
            # Array indexing: a[i][j]
            if self._match(TokenType.LBRACKET):
                indices = []
                idx_expr = self._parse_expression()
                self._consume(TokenType.RBRACKET, "Expected ']' after array index")
                indices.append(idx_expr)
                while self._match(TokenType.LBRACKET):
                    idx_expr = self._parse_expression()
                    self._consume(TokenType.RBRACKET, "Expected ']' after array index")
                    indices.append(idx_expr)

                if isinstance(expr, VarNode):
                    expr = ArrayRefNode(array_name=expr.name, indices=indices, line=expr.line, column=expr.column)
                elif isinstance(expr, ArrayRefNode):
                    expr.indices.extend(indices)
                else:
                    raise ParserError("Array subscript applied to non-variable expression", self._peek())

            # Function call: foo(a, b)
            elif self._match(TokenType.LPAREN):
                args = []
                if not self._check(TokenType.RPAREN):
                    while True:
                        args.append(self._parse_expression())
                        if not self._match(TokenType.COMMA):
                            break
                self._consume(TokenType.RPAREN, "Expected ')' after arguments")
                if isinstance(expr, VarNode):
                    expr = FunctionCallNode(name=expr.name, arguments=args, line=expr.line, column=expr.column)
                else:
                    raise ParserError("Call applied to non-identifier", self._peek())

            # Postfix ++ / --
            elif self._check(TokenType.INCREMENT, TokenType.DECREMENT):
                op_tok = self._advance()
                expr = UnaryOpNode(op=op_tok.value, operand=expr, is_prefix=False, line=op_tok.line, column=op_tok.column)

            else:
                break

        return expr

    def _parse_primary(self) -> ASTNode:
        tok = self._peek()

        if tok.type == TokenType.INTEGER:
            self._advance()
            return LiteralNode(value=int(tok.value), literal_type='int', line=tok.line, column=tok.column)

        if tok.type == TokenType.FLOAT:
            self._advance()
            return LiteralNode(value=float(tok.value), literal_type='float', line=tok.line, column=tok.column)

        if tok.type == TokenType.STRING:
            self._advance()
            return LiteralNode(value=tok.value, literal_type='string', line=tok.line, column=tok.column)

        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            return VarNode(name=tok.value, line=tok.line, column=tok.column)

        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN, "Expected ')' to close expression")
            return expr

        raise ParserError("Expected expression", tok)

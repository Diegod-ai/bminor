# grammar.py (versión actualizada para nuevo AST)
import logging
import sly
from rich import print

from lexer  import Lexer
from errors import error, errors_detected
from model  import *

from ast_printer import *


def _L(node, lineno):
	node.lineno = lineno
	return node
	
	
class Parser(sly.Parser):
	log = logging.getLogger()
	log.setLevel(logging.ERROR)
	expected_shift_reduce = 1
	debugfile='grammar.txt'
	
	tokens = Lexer.tokens
	
	# =================================================
	# PROGRAMA
	# =================================================
	
	@_("decl_list")
	def prog(self, p):
		return Program(p.decl_list)
	
	# =================================================
	# LISTAS DE DECLARACIONES
	# =================================================
	
	@_("decl decl_list")
	def decl_list(self, p):
		head = [p.decl] if p.decl is not None else []
		return head + p.decl_list
		
	@_("empty")
	def decl_list(self, p):
		return []
		
	# =================================================
	# DECLARACIONES
	# =================================================
	
	@_("ID COLON type_simple SEMICOLON")
	def decl(self, p):
		return _L(VarDecl(p.ID, p.type_simple), p.lineno)
		
	@_("ID COLON type_array_sized SEMICOLON")
	def decl(self, p):
		return _L(ListDecl(p.ID, p.type_array_sized), p.lineno)
		
	@_("ID COLON type_func SEMICOLON")
	def decl(self, p):
		return _L(FuncDecl(p.ID, p.type_func), p.lineno)
		
	@_("decl_init")
	def decl(self, p):
		return p.decl_init
		
	# === DECLARACIONES con inicialización
	
	@_("ID COLON type_simple ASSIGN expr SEMICOLON")
	def decl_init(self, p):
		return _L(VarDecl(p.ID, p.type_simple, p.expr), p.lineno)
		
	@_("ID COLON CONSTANT ASSIGN expr SEMICOLON")
	def decl_init(self, p):
		return _L(ConstDecl(p.ID, p.expr), p.lineno)
		
	@_("ID COLON type_array_sized ASSIGN LBRACE opt_expr_list RBRACE SEMICOLON")
	def decl_init(self, p):
		return _L(ListDecl(p.ID, p.type_array_sized, p.opt_expr_list), p.lineno)
		
	@_("ID COLON type_func ASSIGN LBRACE opt_stmt_list RBRACE")
	def decl_init(self, p):
		return _L(FuncDecl(p.ID, p.type_func, p.opt_stmt_list), p.lineno)
		
	# =================================================
	# STATEMENTS
	# =================================================
	
	@_("stmt_list")
	def opt_stmt_list(self, p):
		return p.stmt_list
		
	@_("empty")
	def opt_stmt_list(self, p):
		return []
		
	@_("stmt stmt_list")
	def stmt_list(self, p):
		head = [p.stmt] if p.stmt is not None else []
		return head + p.stmt_list
		
	@_("stmt")
	def stmt_list(self, p):
		return [p.stmt] if p.stmt is not None else []
		
	@_("open_stmt")
	@_("closed_stmt")
	def stmt(self, p):
		return p[0]

	@_("if_stmt_closed")
	@_("for_stmt_closed")
	@_("while_stmt_closed")
	@_("simple_stmt")
	def closed_stmt(self, p):
		return p[0]

	@_("if_stmt_open")
	@_("for_stmt_open")
	@_("while_stmt_open")
	def open_stmt(self, p):
		return p[0]

	# -------------------------------------------------
	# IF
	# -------------------------------------------------
	
	@_("if_cond closed_stmt ELSE if_stmt_open")
	def if_stmt_open(self, p):
		return _L(IfStmt(p.if_cond, as_block(p.closed_stmt), as_block(p.if_stmt_open)), p.lineno)
  
	@_("if_cond stmt")
	def if_stmt_open(self, p):
		return _L(IfStmt(p.if_cond, as_block(p.stmt)), p.lineno)
  
	@_("if_cond closed_stmt ELSE closed_stmt")
	def if_stmt_closed(self, p):
		return _L(IfStmt(p.if_cond, as_block(p.closed_stmt0), as_block(p.closed_stmt1)), p.lineno)
		
	@_("IF LPAREN opt_expr RPAREN")
	def if_cond(self, p):
		return p.opt_expr
	# -------------------------------------------------
	# FOR
	# -------------------------------------------------
	
	@_("for_header closed_stmt")
	def for_stmt_closed(self, p):
		return _L(ForStmt(p.for_header[0], p.for_header[1], p.for_header[2], as_block(p.closed_stmt)), p.lineno)
		
	@_("for_header open_stmt")
	def for_stmt_open(self, p):
		return _L(ForStmt(p.for_header[0], p.for_header[1], p.for_header[2], as_block(p.open_stmt)), p.lineno)
		
	@_("FOR LPAREN opt_expr SEMICOLON opt_expr SEMICOLON opt_expr RPAREN")
	def for_header(self, p):
		return p.opt_expr0, p.opt_expr1, p.opt_expr2
		
	# -------------------------------------------------
	# WHILE
	# -------------------------------------------------
	@_("while_cond closed_stmt")
	def while_stmt_closed(self, p):
		return _L(WhileStmt(p.while_cond, as_block(p.closed_stmt)), p.lineno)

	@_("while_cond open_stmt")
	def while_stmt_open(self, p):
		return _L(WhileStmt(p.while_cond, p.open_stmt), p.lineno)
	
	@_("WHILE LPAREN opt_expr RPAREN")
	def while_cond(self, p):
		return p.opt_expr
		
	# -------------------------------------------------
	# SIMPLE STATEMENTS
	# -------------------------------------------------
	
	@_("print_stmt")
	@_("return_stmt")
	@_("break_stmt")
	@_("continue_stmt")
	@_("block_stmt")
	@_("decl")
	@_("expr SEMICOLON")
	def simple_stmt(self, p):
		return p[0]

	# PRINT
	@_("PRINT opt_expr_list SEMICOLON")
	def print_stmt(self, p):
		return _L(PrintStmt(p.opt_expr_list), p.lineno)

	# RETURN
	@_("RETURN opt_expr SEMICOLON")
	def return_stmt(self, p):
		return _L(ReturnStmt(p.opt_expr), p.lineno)

	@_("BREAK SEMICOLON")
	def break_stmt(self, p):
		return _L(BreakStmt(), p.lineno)

	@_("CONTINUE SEMICOLON")
	def continue_stmt(self, p):
		return _L(ContinueStmt(), p.lineno)

	# RETURN sin ";"
	@_("RETURN opt_expr error")
	def return_stmt(self, p):
		lineno = getattr(p.opt_expr, 'lineno', p.lineno) if p.opt_expr else p.lineno
		error('se esperaba ";" después de "return"', lineno=lineno)
		return _L(ReturnStmt(p.opt_expr), p.lineno)

	# PRINT sin ";"
	@_("PRINT opt_expr_list error")
	def print_stmt(self, p):
		error('se esperaba ";" después de "print"', lineno=p.lineno)
		return _L(PrintStmt(p.opt_expr_list), p.lineno)

	# BREAK sin ";"
	@_("BREAK error")
	def break_stmt(self, p):
		error('se esperaba ";" después de "break"', lineno=p.lineno)
		return _L(BreakStmt(), p.lineno)

	# CONTINUE sin ";"
	@_("CONTINUE error")
	def continue_stmt(self, p):
		error('se esperaba ";" después de "continue"', lineno=p.lineno)
		return _L(ContinueStmt(), p.lineno)

	# BLOCK
	@_("LBRACE stmt_list RBRACE")
	def block_stmt(self, p):
		return _L(Block(p.stmt_list), p.lineno)
		
	# =================================================
	# EXPRESIONES
	# =================================================
	
	@_("empty")
	def opt_expr_list(self, p):
		return []
		
	@_("expr_list")
	def opt_expr_list(self, p):
		return p.expr_list	
		
	@_("expr COMMA expr_list")
	def expr_list(self, p):
		return [p.expr] + p.expr_list
		
	@_("expr")
	def expr_list(self, p):
		return [p.expr]
		
	@_("empty")
	def opt_expr(self, p):
		return None
		
	@_("expr")
	def opt_expr(self, p):
		return p.expr
		
	# -------------------------------------------------
	# PRIMARY
	# -------------------------------------------------
	
	@_("expr1")
	def expr(self, p):
		return p.expr1
		
	@_("lval  ASSIGN  expr1")
	@_("lval ADDEQ expr1")
	@_("lval SUBEQ expr1")
	@_("lval MULEQ expr1")
	@_("lval DIVEQ expr1")
	@_("lval MODEQ expr1")
	def expr1(self, p):
		return _L(Assign(p[1], p.lval, p.expr1), p.lineno)
		
	@_("expr2")
	def expr1(self, p):
		return p.expr2
		
	# ----------- LVALUES -------------------
	
	@_("ID")
	def lval(self, p):
		return _L(Variable(p.ID), p.lineno)
		
	@_("ID index")
	def lval(self, p):
		return _L(ArrayAccess(p.ID, p.index), p.lineno)
		
	# -------------------------------------------------
	# OPERADORES
	# -------------------------------------------------
	
	@_("expr2 LOR expr3")
	def expr2(self, p):
		return _L(BinaryOp("||", p.expr2, p.expr3), p.lineno)

	@_("expr3")
	def expr2(self, p):
		return p.expr3
		
	@_("expr3 LAND expr4")
	def expr3(self, p):
		return _L(BinaryOp("&&", p.expr3, p.expr4), p.lineno)
		
	@_("expr4")
	def expr3(self, p):
		return p.expr4
		
	@_("expr4 EQ expr5")
	@_("expr4 NE expr5")
	@_("expr4 LT expr5")
	@_("expr4 LE expr5")
	@_("expr4 GT expr5")
	@_("expr4 GE expr5")
	def expr4(self, p):
		return _L(BinaryOp(p[1], p.expr4, p.expr5), p.lineno)

	@_("expr5")
	def expr4(self, p):
		return p.expr5
		
	@_("expr5 PLUS expr6")
	@_("expr5 MINUS expr6")
	def expr5(self, p):
		return _L(BinaryOp(p[1], p.expr5, p.expr6), p.lineno)
		
	@_("expr6")
	def expr5(self, p):
		return p.expr6
		
	@_("expr6 TIMES expr7")
	@_("expr6 DIVIDE expr7")
	@_("expr6 MOD expr7")
	def expr6(self, p):
		return _L(BinaryOp(p[1], p.expr6, p.expr7), p.lineno)
		
	@_("expr7")
	def expr6(self, p):
		return p.expr7
		
	@_("expr7 EXPONENT expr8")
	def expr7(self, p):
		return _L(BinaryOp("^", p.expr7, p.expr8), p.lineno)
		
	@_("expr8")
	def expr7(self, p):
		return p.expr8
		
	@_("MINUS expr8")
	@_("LNOT expr8")
	def expr8(self, p):
		return _L(UnaryOp(p[0], p.expr8), p.lineno)

	@_("expr9")
	def expr8(self, p):
		return p.expr9

	@_("postfix")
	def expr9(self, p):
		return p.postfix

	@_("primary")
	def postfix(self, p):
		return p.primary

	@_("postfix INC")
	def postfix(self, p):
		return _L(PostfixOp("++", p.postfix), p.lineno)

	@_("postfix DEC")
	def postfix(self, p):
		return _L(PostfixOp("--", p.postfix), p.lineno)

	@_("prefix")
	def primary(self, p):
		return p.prefix

	@_("INC prefix")
	def prefix(self, p):
		return _L(PrefixOp("++", p.prefix), p.lineno)

	@_("DEC prefix")
	def prefix(self, p):
		return _L(PrefixOp("--", p.prefix), p.lineno)

	@_("group")
	def prefix(self, p):
		return p.group
		
	@_("LPAREN expr RPAREN")
	def group(self, p):
		return p.expr
		
	@_("ID LPAREN opt_expr_list RPAREN")
	def group(self, p):
		return _L(Call(p.ID, p.opt_expr_list), p.lineno)
		
	@_("ID index")
	def group(self, p):
		return _L(ArrayAccess(p.ID, p.index), p.lineno)
		
	@_("factor")
	def group(self, p):
		return p.factor
		
	# INDICE DE ARREGLO
	@_("LBRACKET expr RBRACKET")
	def index(self, p):
		return p.expr
	
	# -------------------------------------------------
	# FACTORES
	# -------------------------------------------------
	
	@_("ID")
	def factor(self, p):
		return _L(Variable(p.ID), p.lineno)
		
	@_("LITERAL_INTEGER")
	def factor(self, p):
		return _L(IntegerLiteral(p.LITERAL_INTEGER), p.lineno)
		
	@_("LITERAL_FLOAT")
	def factor(self, p):
		return _L(FloatLiteral(p.LITERAL_FLOAT), p.lineno)
		
	@_("LITERAL_CHAR")
	def factor(self, p):
		return _L(CharLiteral(p.LITERAL_CHAR), p.lineno)
		
	@_("LITERAL_STRING")
	def factor(self, p):
		return _L(StringLiteral(p.LITERAL_STRING), p.lineno)

	@_("TRUE", "FALSE")
	def factor(self, p):
		return _L(BooleanLiteral(p[0]), p.lineno)
		
	# =================================================
	# TIPOS
	# =================================================
	
	@_("INTEGER")
	@_("FLOAT")
	@_("BOOLEAN")
	@_("CHAR")	
	@_("STRING")
	@_("VOID")
	def type_simple(self, p):
		return SimpleType(p[0].lower())
		
	@_("ARRAY LBRACKET RBRACKET type_simple")
	@_("ARRAY LBRACKET RBRACKET type_array")
	def type_array(self, p):
		return ArrayType( p[3], None,)
		
	@_("ARRAY index type_simple")
	@_("ARRAY index type_array_sized")
	def type_array_sized(self, p):
		return ArrayType(p[2], p[1])
		
	@_("FUNCTION type_simple LPAREN opt_param_list RPAREN")
	@_("FUNCTION type_array_sized LPAREN opt_param_list RPAREN")
	def type_func(self, p):
		return FuncType(p[1], p[3])
		
	@_("empty")
	def opt_param_list(self, p):
		return []
		
	@_("param_list")
	def opt_param_list(self, p):
		return p.param_list
		
	@_("param_list COMMA param")
	def param_list(self, p):
		return p.param_list + [p.param]
		
	@_("param")
	def param_list(self, p):
		return [p.param]
		
	@_("ID COLON type_simple")
	@_("ID COLON type_array")
	@_("ID COLON type_array_sized")
	def param(self, p):
		return Param(p.ID, p[2])

	# =================================================
	# RECUPERACIÓN DE ERRORES
	# =================================================

	# Salta hasta el próximo ";" y descarta la sentencia inválida
	@_("error SEMICOLON")
	def simple_stmt(self, p):
		return None   # filtrado en stmt_list / decl_list

	# Sentencia sin ";" justo antes de "}" → reporta y devuelve None
	# El RBRACE queda en el flujo para cerrar el bloque correctamente.
	@_("error RBRACE")
	def simple_stmt(self, p):
		# Devolvemos el RBRACE al parser para que cierre el bloque
		self.errok()
		return None

	# Salta hasta el próximo "}" si falta cerrar un bloque
	@_("LBRACE error RBRACE")
	def block_stmt(self, p):
		return _L(Block([]), p.lineno)

	# =================================================
	# UTILIDAD: EMPTY
	# =================================================
	
	@_("")
	def empty(self, p):
		pass
		
	# Tokens que normalmente abren una sentencia nueva.
	# Si el parser los encuentra en un lugar inesperado
	# es muy probable que falte ";" en la línea anterior.
	_STMT_STARTERS = {
		'ID', 'IF', 'WHILE', 'FOR', 'RETURN', 'PRINT',
		'BREAK', 'CONTINUE', 'LBRACE',
		'INTEGER', 'FLOAT', 'BOOLEAN', 'CHAR', 'STRING',
		'VOID', 'FUNCTION', 'ARRAY', 'CONSTANT', 'AUTO',
	}

	def error(self, p):
		if p is None:
			error('fin de archivo inesperado — ¿falta cerrar un bloque "}"?')
			return

		lineno = p.lineno
		value  = p.value

		if p.type in self._STMT_STARTERS:
			# El token parece iniciar una nueva sentencia →
			# lo más probable es que falte ";" en la línea anterior.
			prev = lineno - 1
			error(
				f'se esperaba ";" al final de la línea {prev} '
				f'(se encontró {value!r} en la línea {lineno})',
				lineno=prev,
			)
		elif p.type == 'RBRACE':
			error(f'"}}": llave de cierre inesperada', lineno=lineno)
		elif p.type == 'RPAREN':
			error(f'")": paréntesis de cierre inesperado', lineno=lineno)
		elif p.type == 'RBRACKET':
			error(f'"]": corchete de cierre inesperado', lineno=lineno)
		elif p.type == 'ASSIGN':
			error(f'"=": asignación inesperada — ¿falta declarar la variable?', lineno=lineno)
		else:
			error(f'token inesperado {value!r}', lineno=lineno)
		
# ===================================================
# Utilidad: convertir algo en bloque si no lo es
# ===================================================
def as_block(x):
	if isinstance(x, Block):
		return x
	if isinstance(x, list):
		return Block(x)
	return Block([x])
	
	
# Convertir AST a diccionario
def ast_to_dict(node):
	if isinstance(node, list):
		return [ast_to_dict(item) for item in node]
	elif hasattr(node, "__dict__"):
		return {key: ast_to_dict(value) for key, value in node.__dict__.items()}
	else:
		return node

# ===================================================
# test
# ===================================================
def parse(txt):
	l = Lexer()
	p = Parser()
	return p.parse(l.tokenize(txt))
	
	
if __name__ == '__main__':
	import sys, json
	
	if sys.platform != 'ios':
	
		if len(sys.argv) != 2:
			raise SystemExit("Usage: python gparse.py <filename>")
			
		filename = sys.argv[1]
		
	else:
		
		from file_picker import file_picker_dialog
		
		filename = file_picker_dialog(
			title='Seleccionar una archivo',
			root_dir='./test/',
			file_pattern='^.*[.]bpp'
		)
		
	if filename:
		txt = open(filename, encoding='utf-8').read()
		ast = parse(txt)
		
		if not errors_detected():
			tree = build_rich_tree(ast)
			print(tree)

			graph = build_graphviz(ast)
			graph.render('ast', format='png', cleanup=True)
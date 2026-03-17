import sys
from rich import print
import sly


class Lexer(sly.Lexer):
    tokens  = {
        # Palabras Reservadas
        ARRAY, BOOLEAN, CHAR, ELSE, FALSE, FLOAT, FOR, FUNCTION, IF,
        INTEGER, PRINT, RETURN, STRING, TRUE, VOID, WHILE, AUTO, BREAK, CONTINUE, 
       
        # Aritméticos
        PLUS, MINUS, TIMES, DIVIDE, MOD, EXPONENT, INC, DEC,

        # Operadores de Relación
        LT, LE, GT, GE, EQ, NE, 
        
        # Operadores lógicos
        LAND, LOR, LNOT, 

        # Operadores de Assignación
        ASSIGN, ADDEQ, SUBEQ, MULEQ, DIVEQ, MODEQ, 

        # Identificador y Literales
        ID,LITERAL_INTEGER, LITERAL_FLOAT, LITERAL_CHAR, LITERAL_STRING,
        
        # Acceso y Puntuación
        COLON, SEMICOLON, COMMA, LPAREN, RPAREN, LBRACKET, RBRACKET, LBRACE, RBRACE
    }
    

    # simbolos a ignorar
    ignore = ' \t\r'
    ignore_comment = r'/\*[\s\S]*?\*/'
    ignore_cppcomment = r'//.*\n'
    
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    # Expresiones regulares para los tokens
    ID = r'[a-zA-Z_][a-zA-Z0-9_]*'

    # Palabras Reservadas
    
    # Tipos de Datos
    ID['array']    = ARRAY
    ID['boolean']  = BOOLEAN
    ID['char']     = CHAR  
    ID['integer']  = INTEGER
    ID['string']   = STRING
    ID['void']     = VOID
    ID['float']    = FLOAT
    
    # Control de Flujo
    ID['if']       = IF
    ID['else']     = ELSE
    ID['for']      = FOR
    ID['while']    = WHILE
    ID['return']   = RETURN
    
    # Valore Booleanos
    ID['true']     = TRUE
    ID['false']    = FALSE
    
    # Definiciones y Salida
    ID['function'] = FUNCTION
    ID['print']    = PRINT
    ID['auto']     = AUTO
    ID['break']    = BREAK
    ID['continue'] = CONTINUE

    # Operadores Aritmeticos
    INC      = r'\+\+'
    DEC      = r'--'
    PLUS     = r'\+'
    MINUS    = r'-'
    TIMES    = r'\*'
    DIVIDE   = r'/'
    MOD      = r'%'
    EXPONENT = r'\^'
    
    # Operadores comparativos
    LE   = r'<='
    GE   = r'>='
    EQ   = r'=='
    NE   = r'!='
    LT   = r'<'
    GT   = r'>'
    
    #Operadores lógicos
    LNOT  = r'!'
    LAND  = r'&&'
    LOR   = r'\|\|'
    
    # Operadores de assignación
    ADDEQ   = r'\+='
    SUBEQ   = r'-='
    MULEQ   = r'\*='
    DIVEQ   = r'/='
    MODEQ   = r'%='
    ASSIGN  = r'='
    
    # Tipos de datos literales
    LITERAL_FLOAT   = r'\d+\.\d+'
    LITERAL_INTEGER = r'\d+'
    LITERAL_CHAR    = r"'(\\[ntr'\"\\]|[^'\\])'"
    LITERAL_STRING  = r'"(\\[ntr\'\"\\]|[^"\\])*"'

    # Literales
    LPAREN    = r'\('
    RPAREN    = r'\)'
    LBRACE    = r'\{'
    RBRACE    = r'\}'
    LBRACKET  = r'\['
    RBRACKET  = r'\]'
    SEMICOLON = r';'
    COMMA     = r','
    COLON     = r':'
    
    
    def error(self, t):
        last_cr = self.text.rfind('\n', 0, self.index)
        if last_cr < 0:
            last_cr = -1
        column = (self.index - last_cr)

        raise SyntaxError(
            f"Error léxico en línea {self.lineno}, columna {column}: "
            f"carácter ilegal '{t.value[0]}'"
        )

def tokenize(txt):
    lex = Lexer()

    try:
        tokens = []
        for tok in lex.tokenize(txt):
            tokens.append((tok.type, tok.value, tok.lineno))
        print(tokens)
    except SyntaxError as e:
        print(f"[bold red]{e}[/bold red]")

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print(f'usage: python lexer.py <filename>')

    txt = open(sys.argv[1], encoding='utf-8').read()
    tokenize(txt)
 # model.py


""" 
Modelo de nodos para el AST (Árbol de Sintaxis Abstracta)

Cada clase representara cada una de las funciones en el parser, sus variables serán los "tokens" que se reciben en cada función. 
Por ejemplo, la función "factor" recibe un token llamado "LITERAL_INTEGER", entonces el nodo "FactorLiteralInteger" tendrá una variable llamada "value" que almacenará el valor del token.
"""

"""
Esta clase llamada "node" es la clase base para el AST, tiene como función almacenar la información de la línea sobre la que esta el parser, 
esto para poder reportar el errore en la línea correcta, el metodo '__repr__' es para imprimirla de manera legible
"""
class Node:
    lineno = 0
    def __repr__(self):
        fields = ', '.join(f'{k}={v!r}' for k, v in self.__dict__.items())
        return f'{self.__class__.__name__}({fields})'

##Nodo para el programa completo

class Program(Node):
    def __init__(self, decls):
        self.decls = decls                #Esto es para almacenar la lista de declaraciones del programa

# Nodos literales. 

class variable(Node):  
    def __init__(self, name):
        self.name = name  

class IntegerLiteral(Node):
    def __init__(self, value):
       self.value = int(value)

class FloatLiteral(Node):
    def __init__(self, value):
        self.value = float(value)   

class CharLiteral(Node):
    def __init__(self, value):
        self.value = value[1:-1]  
    
class StringLiteral(Node):
    def __init__(self, value):
        self.value = value[1:-1]  
        
class BooleanLiteral(Node):
    def __init__(self, value):
        self.value = value == 'true'

## Nodos para los tipos de datos

class SimpleType(Node):
    def __init__(self,name):
        self.name = name                  #Esto es para almacenar el nombre del tipo de dato, por ejemplo "int", "float", "bool", "string" etc.

class ArrayType(Node):
    def __init__ (self, element_type, size):
        self.size = size                  #Esto es para almacenar el tamaño del array, por ejemplo 10, 20, etc.
        self.element_type = element_type  #Esto es para almacenar el tipo de dato del elemento del array, por ejemplo "int", "float", "bool", "string" etc.

class FuncType(Node):
    def __init__(self, return_type, param_types):
        self.return_type = return_type    #Esto es para almacenar el tipo de dato de retorno de la función, por ejemplo "int", "float", "bool", "string" etc.
        self.param_types = param_types    #Esto es para almacenar los tipos de datos de los parámetros de la función, por ejemplo ["int", "float"], ["string"], etc.

class Param(Node):
    def __init__(self, name, type):
        self.name = name                  #Esto es para almacenar el nombre del parámetro, por ejemplo "x", "y", etc.
        self.type = type                  #Esto es para almacenar el tipo de dato del parámetro, por ejemplo "int", "float", "bool", "string" etc.

##Nodos para las declaraciones

class VarDecl(Node):
    def __init__(self, name, type, value=None):
        self.name = name                  #Esto es para almacenar el nombre de la variable, por ejemplo "x", "y", etc.
        self.type = type                  #Esto es para almacenar el tipo de dato de la variable, por ejemplo "int", "float", "bool", "string" etc.
        self.value = value                #Esto es para almacenar el valor de la variable, por ejemplo 10, 20, "hello", etc.   

class  ListDecl(Node):
    def __init__(self, name, array_type, elements=None,):
        self.name = name                  #Esto es para almacenar el nombre de la lista de declaraciones
        self.array_type = array_type      #Esto es para almacenar el tipo de dato del array
        self.elements = elements          #Esto es para almacenar la lista de elementos

class FuncDecl(Node):
    def __init__(self, name, func_type, body=None):
        self.name = name                  #Esto es para almacenar el nombre de la función
        self.func_type = func_type        #Esto es para almacenar el tipo de dato de la función
        self.body = body                  #Esto es para almacenar el cuerpo de la función, que puede ser una lista de sentencias o una expresión.

class ConstDecl(Node):
    def __init__(self, name, type, value):
        self.name = name                  #Esto es para almacenar el nombre de la constante
        self.value = value                #Esto es para almacenar el valor de la constante  

##Nodos para los statements simples 

class ReturnStmt(Node):
    def __init__(self, value=0):
        self.value = value                #Esto es para almacenar el valor de retorno de la función, que puede ser una expresión o una lista de sentencias. 

class PrintStmt(Node):
    def __init__(self, value):
        self.value = value                #Esto es para almacenar el valor a imprimir, que puede ser una expresión o una lista de sentencias.   

class BreakStmt(Node):
    def __init__(self):
        pass    

class ContinueStmt(Node):
    def __init__(self):
        pass    

class Block(Node):
    def __init__(self, statements):
        self.statements = statements      #Esto es para almacenar la lista de sentencias que conforman el bloque.
        
        
##Nodos para expresiones

class BinaryOp(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right


class UnaryOp(Node):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr


class Assign(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right


class PostfixOp(Node):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr


class PrefixOp(Node):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr


class Call(Node):
    def __init__(self, name, args):
        self.name = name
        self.args = args


class ArrayAccess(Node):
    def __init__(self, name, index):
        self.name = name
        self.index = index
        
        
##Nodos de control de flujo

class IfStmt(Node):
    def __init__(self, condition, then_branch, else_branch=None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch


class WhileStmt(Node):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class ForStmt(Node):
    def __init__(self, init, condition, update, body):
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body
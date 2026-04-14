# Compilador B-Minor — Analizador Semántico
 
Proyecto desarrollado para el curso de **Compiladores**. Implementa las fases de análisis léxico, sintáctico y semántico para el lenguaje **B-Minor**, un lenguaje fuertemente tipado de propósito educativo.
 
---
 
## Estructura del proyecto
 
```
bminor/
├── lexer.py        # Analizador léxico (tokenizador)
├── parser.py       # Analizador sintáctico (construcción del AST)
├── model.py        # Definición de nodos del AST
├── symtab.py       # Tabla de símbolos con alcance léxico
├── checker1.py     # Analizador semántico (Visitor)
├── ast_printer.py  # Utilidades de visualización del AST
├── errors.py       # Gestión centralizada de errores
└── tests/
    ├── good/       # Programas semánticamente correctos
    └── bad/        # Programas con errores semánticos
```
 
---
 
## Descripción de cada módulo
 
### `lexer.py`
Implementado con la librería `sly`. Reconoce los tokens del lenguaje B-Minor: palabras reservadas (`integer`, `boolean`, `string`, `float`, `char`, `void`, `function`, `if`, `else`, `for`, `while`, `return`, `print`, `const`, etc.), operadores aritméticos, relacionales, lógicos y de asignación, literales numéricos, de carácter y cadena, e identificadores.
 
### `parser.py`
Implementado con `sly.Parser`. Construye el AST a partir del flujo de tokens producido por el lexer. Maneja la precedencia de operadores, las declaraciones con y sin inicialización, estructuras de control (`if/else`, `for`, `while`), funciones, arreglos y expresiones complejas. Genera nodos del tipo definido en `model.py`.
 
### `model.py`
Define la jerarquía de nodos del AST. Todos los nodos heredan de la clase base `Node`, la cual almacena el número de línea para el reporte de errores. Los nodos principales son:
 
| Categoría | Nodos |
|---|---|
| Programa | `Program` |
| Literales | `IntegerLiteral`, `FloatLiteral`, `CharLiteral`, `StringLiteral`, `BooleanLiteral` |
| Tipos | `SimpleType`, `ArrayType`, `FuncType` |
| Declaraciones | `VarDecl`, `ConstDecl`, `ListDecl`, `FuncDecl`, `Param` |
| Sentencias | `Block`, `PrintStmt`, `ReturnStmt`, `BreakStmt`, `ContinueStmt` |
| Control de flujo | `IfStmt`, `WhileStmt`, `ForStmt` |
| Expresiones | `BinaryOp`, `UnaryOp`, `Assign`, `PostfixOp`, `PrefixOp`, `Call`, `ArrayAccess`, `Variable` |
 
### `symtab.py`
Tabla de símbolos respaldada internamente por `ChainMap` de Python. Soporta alcance léxico anidado con resolución de nombres de adentro hacia afuera. Detecta redeclaraciones en el mismo scope y conflictos de tipos. Permite inspección visual del árbol de scopes mediante `rich`.
 
**API principal:**
 
```python
tab = Symtab("global")
child = Symtab("function f", parent=tab)
child.add("x", symbol)     # define en el scope actual
child.get("x")             # busca con alcance léxico
tab.print()                # imprime árbol de scopes
```
 
**Excepciones manejadas:**
- `Symtab.SymbolDefinedError` — redeclaración en el mismo scope.
- `Symtab.SymbolConflictError` — símbolo ya existe con tipo diferente.
 
### `checker1.py`
Núcleo del **analizador semántico**. Implementa el patrón Visitor usando la librería `multimethod` (mediante `multimeta`). Recorre el AST anotando tipos en cada nodo y acumulando errores semánticos sin abortar en el primero que encuentre.
 
Cada símbolo registrado tiene la siguiente estructura:
 
```python
Symbol(name='x', kind='var', type='integer', mutable=True)
Symbol(name='f', kind='func', type=FuncType(...), mutable=False)
```
 
**Chequeos implementados:**
 
- Declaración de variables, constantes y parámetros en el scope adecuado.
- Detección de redeclaraciones inválidas.
- Verificación de que todo identificador usado esté previamente declarado.
- Apertura y cierre de scopes para bloques, funciones y parámetros formales.
- Resolución de llamadas a función: verifica que el nombre corresponda a una función.
- Anotación de tipo (`node.type`) en literales y expresiones.
- Soporte para expresiones binarias, unarias, asignaciones y accesos a arreglos.
 
### `ast_printer.py`
Utilidades de visualización del AST. Provee dos representaciones:
- **Rich Tree** (`build_rich_tree`): árbol en consola con formato coloreado.
- **Graphviz** (`build_graphviz`): genera un grafo renderizable como imagen PNG.
 
### `errors.py`
Módulo de gestión de errores con conteo global. Permite reportar errores con número de línea usando `rich` para salida coloreada en consola.
 
---
 
## Tabla de compatibilidad de operadores
 
| Operador | Tipos permitidos | Tipo resultado |
|---|---|---|
| `+`, `-`, `*`, `/`, `%` | `integer, integer` | `integer` |
| `^` | `integer, integer` | `integer` |
| `<`, `<=`, `>`, `>=` | `integer, integer` | `boolean` |
| `==`, `!=` | tipos compatibles | `boolean` |
| `&&`, `\|\|` | `boolean, boolean` | `boolean` |
| `!` | `boolean` | `boolean` |
| `-` (unario) | `integer` | `integer` |
 
---
 
## Jerarquía de tipos
 
```
              ┌─────────┐
              │  Type   │
              └────┬────┘
                   │
   ┌───────────────┼───────────────┐
   │               │               │
   ▼               ▼               ▼
┌─────────┐  ┌─────────┐   ┌─────────┐
│ integer │  │ boolean │   │ string  │
└─────────┘  └─────────┘   └─────────┘
    │              
    ▼              
┌────────────┐    ┌──────────┐
│ array[T]   │    │  float   │
└────────────┘    └──────────┘
```
 
---
 
## Cómo ejecutar el analizador semántico
 
### Requisitos
 
```bash
pip install sly rich multimethod graphviz
```
 
### Uso desde línea de comandos
 
```bash
# Parsear y visualizar el AST de un programa
python parser.py tests/good/test01.bpp
 
# Ejecutar el análisis semántico sobre un programa
python checker1.py tests/bad/test07.bpp
```
 
O desde un script principal (si se tiene `main.py`):
 
```bash
python main.py checker tests/good/test01.bpp
python main.py checker tests/bad/test07.bpp
```
 
### Salida esperada — programa correcto
 
```
semantic check: success
```
 
### Salida esperada — programa con errores
 
```
error:12: símbolo 'x' no definido
error:18: redeclaración de 'y' en el mismo alcance
semantic check: failed
```
 
---
 
## Patrón Visitor con `multimethod`
 
El analizador semántico usa `multimeta` de la librería `multimethod` para despachar métodos `visit` según el tipo concreto del nodo:
 
```python
from multimethod import multimeta
 
class Visitor(metaclass=multimeta):
    pass
 
class Checker(Visitor):
    def visit(self, n: VarDecl):
        ...
    def visit(self, n: FuncDecl):
        ...
    def visit(self, n: BinaryOp):
        ...
```
 
Cada nodo del AST delega en el visitor mediante el método `accept`:
 
```python
class Node:
    def accept(self, v):
        return v.visit(self)
```
 
---
 
## Manejo de errores
 
El analizador acumula todos los errores sin detenerse en el primero. Cada mensaje incluye número de línea, identificador involucrado y descripción del problema. Ejemplos:
 
```
error:12: símbolo 'x' no definido
error:18: redeclaración de 'contador' en el mismo alcance
error:27: 'suma' no es una función
```
 
---
 
## Aspectos pendientes
 
- Chequeo de compatibilidad de tipos en operadores binarios (e.g., rechazar `integer + boolean`).
- Verificación del tipo de retorno contra la firma declarada de la función.
- Validación del número y tipos de argumentos en llamadas a funciones.
- Chequeo de que condiciones de `if`, `while` y `for` sean de tipo `boolean`.
- Soporte completo para arreglos: validación de índice entero y tipo base.
- Verificación de que variables `const` no sean reasignadas.
- Verificación de que toda ruta de ejecución de una función no `void` retorne un valor.
 
---
 
## Flujo del compilador
 
```
Código fuente (.bpp)
        │
        ▼
  Analizador léxico (lexer.py)
        │  tokens
        ▼
  Analizador sintáctico (parser.py)
        │  AST (model.py)
        ▼
  Analizador semántico (checker1.py)
        │
        ├── Tabla de símbolos (symtab.py)
        ├── Alcance léxico
        ├── Chequeo de tipos
        └── Anotación de nodos con .type
        │
        ▼
  AST validado  /  Lista de errores semánticos
```

# Compilador B++ — Analizador Semántico

Proyecto desarrollado para el curso de **Compiladores**. Implementa las fases de análisis léxico, sintáctico y semántico para el lenguaje **B++** (`.bminor`), un lenguaje fuertemente tipado de propósito educativo.

---

## Estructura del proyecto

```
bpp/
├── lexer.py        # Analizador léxico (tokenizador)
├── parser.py       # Analizador sintáctico (construcción del AST)
├── model.py        # Definición de nodos del AST y clase Visitor base
├── symtab.py       # Tabla de símbolos con alcance léxico (ChainMap)
├── checker1.py     # Analizador semántico (Visitor)
├── ast_printer.py  # Utilidades de visualización del AST
├── errors.py       # Gestión centralizada de errores con Rich
├── main.py         # Punto de entrada principal del compilador
└── tests/
    ├── good/       # Programas semánticamente correctos
    └── bad/        # Programas con errores semánticos
```

---

## Descripción de cada módulo

### `lexer.py`

Implementado con la librería `sly`. Reconoce los tokens del lenguaje B++:

- **Palabras reservadas:** `array`, `boolean`, `char`, `integer`, `string`, `void`, `float`, `const`, `if`, `else`, `for`, `while`, `return`, `function`, `print`, `auto`, `break`, `continue`, `true`, `false`
- **Operadores aritméticos:** `+`, `-`, `*`, `/`, `%`, `^`, `++`, `--`
- **Operadores relacionales:** `<`, `<=`, `>`, `>=`, `==`, `!=`
- **Operadores lógicos:** `&&`, `||`, `!`
- **Operadores de asignación:** `=`, `+=`, `-=`, `*=`, `/=`, `%=`
- **Literales:** enteros, flotantes, caracteres y cadenas (con soporte de secuencias de escape)
- **Puntuación:** `(`, `)`, `{`, `}`, `[`, `]`, `;`, `,`, `:`

Los comentarios de bloque (`/* ... */`) y de línea (`// ...`) son ignorados automáticamente. Los errores léxicos se reportan con número de línea y columna.

### `parser.py`

Implementado con `sly.Parser`. Construye el AST a partir del flujo de tokens producido por el lexer. Maneja la precedencia de operadores, declaraciones con y sin inicialización, estructuras de control (`if/else`, `for`, `while`), funciones, arreglos y expresiones complejas. Genera nodos del tipo definido en `model.py`.

### `model.py`

Define la jerarquía de nodos del AST y la clase base `Visitor`. Todos los nodos heredan de `Node`, que almacena el número de línea para el reporte de errores y expone el método `accept(visitor)`.

| Categoría | Nodos |
|---|---|
| Programa | `Program` |
| Literales | `IntegerLiteral`, `FloatLiteral`, `CharLiteral`, `StringLiteral`, `BooleanLiteral` |
| Tipos | `SimpleType`, `ArrayType`, `FuncType` |
| Declaraciones | `VarDecl`, `ConstDecl`, `ListDecl`, `FuncDecl`, `Param` |
| Sentencias | `Block`, `PrintStmt`, `ReturnStmt`, `BreakStmt`, `ContinueStmt` |
| Control de flujo | `IfStmt`, `WhileStmt`, `ForStmt` |
| Expresiones | `BinaryOp`, `UnaryOp`, `Assign`, `PostfixOp`, `PrefixOp`, `Call`, `ArrayAccess`, `Variable` |

**Clase `Visitor`:** clase base que declara el método `visit(node)`. Las subclases lo sobrecargan para cada tipo de nodo que necesitan procesar.

**Campos relevantes por nodo:**

```python
Program(decls)
VarDecl(name, type, value=None)
ConstDecl(name, value)
FuncDecl(name, func_type, body=None)   # func_type es un FuncType
ListDecl(name, array_type, elements=None)
Param(name, type)
Block(statements)
PrintStmt(value)
ReturnStmt(value=None)
IfStmt(condition, then_branch, else_branch=None)
WhileStmt(condition, body)
ForStmt(init, condition, update, body)
BinaryOp(op, left, right)
UnaryOp(op, expr)
Assign(op, left, right)
PostfixOp(op, expr)
PrefixOp(op, expr)
Call(name, args)
ArrayAccess(name, index)
Variable(name)
```

### `symtab.py`

Tabla de símbolos respaldada internamente por `ChainMap` de Python. Soporta alcance léxico anidado con resolución de nombres de adentro hacia afuera. Detecta redeclaraciones en el mismo scope y conflictos de tipos. Permite inspección visual del árbol de scopes mediante `rich`.

**API principal:**

```python
tab = Symtab("global")
child = Symtab("function f", parent=tab)

child.add("x", symbol)       # define en el scope actual
child.get("x")               # busca con alcance léxico (padres incluidos)
tab.print()                  # imprime árbol de scopes con Rich

# Extras disponibles
child.entries                # dict del scope actual
child.merged_view()          # dict efectivo (scope actual + padres)
child.lineage()              # lista de nombres de scopes desde global
```

**Excepciones manejadas:**

- `Symtab.SymbolDefinedError` — redeclaración en el mismo scope con el mismo tipo.
- `Symtab.SymbolConflictError` — redeclaración en el mismo scope con tipo diferente.

El **shadowing** (sombrar un símbolo de un scope padre) está permitido.

### `checker1.py`

Núcleo del **analizador semántico**. Implementa el patrón Visitor heredando de `Visitor` (definida en `model.py`) con sobrecarga del método `visit` gracias a la librería `multimethod` (`multimeta`). Recorre el AST anotando tipos en cada nodo y acumulando errores semánticos sin abortar en el primero que encuentre.

Cada símbolo registrado en la tabla tiene la siguiente estructura:

```python
@dataclass
class Symbol:
    name: str
    kind: str        # "var", "param", "func"
    type: Any        # tipo del símbolo o firma FuncType
    node: Any        # referencia al nodo AST original
    mutable: bool    # False para constantes y funciones
```

**Punto de entrada:**

```python
checker = Checker.check(ast)   # retorna la instancia con checker.errors
```

**Chequeos implementados:**

- Declaración de variables (`VarDecl`), constantes (`ConstDecl`) y parámetros (`Param`) en el scope adecuado.
- Detección de redeclaraciones inválidas dentro del mismo scope.
- Verificación de que todo identificador usado esté previamente declarado.
- Apertura y cierre automático de scopes para bloques y funciones.
- Resolución de llamadas a función: verifica que el nombre corresponda a un símbolo de `kind="func"`.
- Anotación de tipo (`node.type`) en literales (`integer`, `boolean`, `string`) y expresiones.
- Soporte para expresiones binarias, unarias, asignaciones, bloques, sentencias de control de flujo y retorno.

### `ast_printer.py`

Utilidades de visualización del AST. Provee dos representaciones:

- **Rich Tree** (`build_rich_tree`): árbol en consola con formato coloreado usando la librería `rich`.
- **Graphviz** (`build_graphviz`): genera un grafo renderizable como imagen PNG con la librería `graphviz`.

Las etiquetas de los nodos muestran el nombre de la clase y, cuando aplica, el operador (`op`), nombre (`name`) o valor (`value`) del nodo.

### `errors.py`

Módulo de gestión de errores con soporte de múltiples niveles de severidad. Basado en la clase `ErrorManager` que acumula diagnósticos con contexto de fuente y los renderiza al estilo de compiladores modernos (clang/rustc).

**Niveles de severidad:** `NOTE`, `WARNING`, `ERROR`, `FATAL`

**API principal:**

```python
from errors import errors

errors.set_source(source_code, filename="main.bminor")  # registra el fuente para contexto

errors.error("símbolo 'x' no definido", lineno=5, column=10, hint="¿Lo declaraste?")
errors.warning("variable 'y' no usada", lineno=3)
errors.note("considera usar 'integer'", lineno=3)
errors.fatal("error irrecuperable")   # imprime todo y termina con SystemExit(1)

errors.has_errors()    # True si hay ERROR o FATAL
errors.count()         # total de diagnósticos
errors.print_all()     # imprime todos con formato Rich y resumen final
errors.clear()         # limpia el estado
```

**Compatibilidad con API funcional:**

```python
from errors import error, warning, note, errors_detected, clear_errors
```

### `main.py`

Punto de entrada del compilador. Ejecuta el pipeline completo con opciones de inspección intermedias.

**Pipeline:**

```
Lectura del archivo fuente
        ↓
Análisis léxico (Lexer)       [--tokens para inspección]
        ↓
Análisis sintáctico (Parser)  → AST
        ↓
[Visualización del AST]       [--ast, --graph]
        ↓
Análisis semántico (Checker)  → tabla de símbolos + errores
        ↓
Resultado final
```

---

## Cómo ejecutar el compilador

### Requisitos

```bash
pip install sly rich multimethod graphviz
```

### Uso desde línea de comandos

```bash
# Compilar un programa (análisis léxico + sintáctico + semántico)
python main.py archivo.bminor

# Imprimir la lista de tokens
python main.py archivo.bminor --tokens

# Mostrar el AST como árbol en consola
python main.py archivo.bminor --ast

# Generar imagen del AST (ast.png) con Graphviz
python main.py archivo.bminor --graph

# Mostrar la tabla de símbolos al final del análisis
python main.py archivo.bminor --symtab

# Combinaciones
python main.py archivo.bminor --tokens --ast --symtab
```

### Salida esperada — programa correcto

```
─────────────── Compilando: archivo.bminor ───────────────

──────────────── PARSING ────────────────
  ✔ Archivo parseado correctamente: archivo.bminor

──────────────── ANÁLISIS SEMÁNTICO ────────────────
  ✔ Sin errores semánticos.

───────────────────────────────────────────────────────
  ✔ Compilación exitosa.
```

### Salida esperada — programa con errores

```
──────────────── ANÁLISIS SEMÁNTICO ────────────────

 ✖ error  símbolo 'x' no definido
   ╰─ main.bminor:12

 ✖ error  redeclaración de 'contador' en el mismo alcance
   ╰─ main.bminor:18

  2 error(es) semántico(s) encontrado(s).

───────────────────────────────────────────────────────
  ✖ Compilación finalizada con errores.
```

---

## Patrón Visitor

El analizador semántico usa la librería `multimethod` (`multimeta`) para despachar métodos `visit` según el tipo concreto del nodo AST. La clase base `Visitor` está definida en `model.py` y cada nodo delega en ella mediante `accept`:

```python
# model.py
class Visitor:
    def visit(self, node):
        raise NotImplementedError(...)

class Node:
    def accept(self, visitor: Visitor):
        return visitor.visit(self)

# checker1.py
from multimethod import multimeta

class Checker(Visitor):
    def visit(self, n: VarDecl):
        ...
    def visit(self, n: FuncDecl):
        ...
    def visit(self, n: BinaryOp):
        ...
```

---

## Tabla de compatibilidad de operadores

| Operador | Descripción | Ejemplo |
|---|---|---|
| `+`, `-`, `*`, `/`, `%` | Aritmética entera/flotante | `x + y` |
| `^` | Potenciación | `x ^ 2` |
| `<`, `<=`, `>`, `>=` | Comparación relacional | `x < 10` |
| `==`, `!=` | Igualdad | `x == y` |
| `&&`, `\|\|` | Lógica binaria | `a && b` |
| `!` | Negación lógica | `!flag` |
| `-` (unario) | Negación aritmética | `-x` |
| `++`, `--` | Incremento/decremento (postfijo/prefijo) | `i++`, `--j` |
| `+=`, `-=`, `*=`, `/=`, `%=` | Asignación compuesta | `x += 1` |

---

## Aspectos pendientes

- Chequeo de compatibilidad de tipos en operadores binarios (e.g., rechazar `integer + boolean`).
- Verificación del tipo de retorno contra la firma declarada de la función.
- Validación del número y tipos de argumentos en llamadas a funciones.
- Verificación de que condiciones de `if`, `while` y `for` sean de tipo `boolean`.
- Soporte completo para arreglos: validación de índice entero y tipo base.
- Verificación de que variables `const` no sean reasignadas.
- Verificación de que toda ruta de ejecución de una función no `void` retorne un valor.
- Soporte de tipos `float` y `char` en el checker (actualmente solo `integer`, `boolean` y `string` se anotan).

---

## Flujo del compilador

```
Código fuente (.bminor)
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
        ├── Tabla de símbolos (symtab.py) — ChainMap con alcance léxico
        ├── Gestión de errores (errors.py) — diagnósticos con Rich
        └── Anotación de nodos con .type y .sym
        │
        ▼
  AST validado  /  Lista de errores semánticos
```

Analizador Semántico de B-Minor

Descripción
Este proyecto implementa el analizador semántico del lenguaje B-Minor como parte del curso de Compiladores.

El analizador recibe un AST (Abstract Syntax Tree) generado por el parser y verifica:
- uso de variables no declaradas
- incompatibilidad de tipos
- errores en funciones
- uso incorrecto de operadores
- problemas de alcance léxico

Cómo ejecutar

python3 main.py checker <archivo.bminor>

Ejemplos:

python3 main.py checker tests/good/test01.bminor
python3 main.py checker tests/bad/test07.bminor

Salida esperada:

Caso válido:
semantic check: success

Caso con errores:
error: símbolo 'x' no definido en la línea 8
error: la condición del while debe ser boolean en la línea 13
semantic check: failed

Tabla de símbolos

Se implementa usando ChainMap o symtab.py.

Características:
- Manejo de alcances léxicos
- Inserción en el scope actual
- Búsqueda jerárquica
- Detección de redeclaraciones

Cada símbolo contiene:
- nombre
- tipo
- clase (variable, función, parámetro)

Visitor con multimethod

Se usa el patrón Visitor con la librería multimethod para recorrer el AST.

Permite:
- modularidad
- extensión sencilla
- separación de lógica por nodo

Tipos soportados

- integer
- boolean
- string (opcional)
- array[T] (opcional)

Reglas:
- no hay conversiones implícitas
- los tipos deben coincidir

Chequeos semánticos

- Variables declaradas antes de uso
- No redeclaración en mismo alcance
- Validación de tipos en expresiones
- Validación de operadores
- Verificación de funciones y retornos

Manejo de errores

- No se detiene en el primer error
- Acumula errores
- Reporta mensajes claros con línea

Pruebas

tests/good → programas válidos
tests/bad → programas con errores

Casos cubiertos:
- variable no declarada
- redeclaración
- tipos incompatibles
- errores en funciones

Estructura

bminor/
├── lexer.py
├── parser.py
├── model.py
├── symtab.py
├── checker.py
├── tests/
│   ├── good/
│   └── bad/
└── main.py

Conclusión

El analizador garantiza la validez semántica del programa antes de etapas como generación de código o interpretación.

================================================================
  COMPILADOR BMINOR — GUÍA DE USO
================================================================

DESCRIPCIÓN
-----------
Este es un compilador front-end para el lenguaje Bminor escrito
en Python. Actualmente cubre las siguientes fases:

  1. Análisis léxico    (lexer.py)
  2. Análisis sintáctico / Parser  (parser.py)
  3. Análisis semántico — Fase 1   (checker1.py)
     - Construcción de tabla de símbolos
     - Detección de redeclaraciones
     - Verificación de símbolos no definidos
     - Verificación de llamadas a función


================================================================
  REQUISITOS
================================================================

Python >= 3.10
pip     >= 21

Instalar dependencias:

  pip install sly rich multimethod graphviz


================================================================
  ARCHIVOS DEL PROYECTO
================================================================

  main.py          Punto de entrada. Orquesta todo el pipeline.
  lexer.py         Analizador léxico (tokenizador).
  parser.py        Analizador sintáctico. Genera el AST.
  model.py         Definición de nodos del AST.
  checker1.py      Verificador semántico — Fase 1.
  symtab.py        Tabla de símbolos (ChainMap).
  typesys.py       Sistema de tipos (operaciones válidas).
  ast_printer.py   Visualización del AST (Rich + Graphviz).
  errors.py        Sistema centralizado de reporte de errores.


================================================================
  USO BÁSICO
================================================================

  python main.py <archivo.bminor>

Ejemplo:

  python main.py programa.bminor


================================================================
  OPCIONES DE LÍNEA DE COMANDOS
================================================================

  --tokens    Imprime la lista de tokens antes de parsear.
  --ast       Imprime el AST como árbol en la consola.
  --graph     Genera el archivo ast.png con el AST (requiere
              que graphviz esté instalado en el sistema, no
              solo la librería Python).
  --symtab    Imprime la tabla de símbolos al finalizar el
              análisis semántico.

Ejemplos:

  python main.py programa.bminor --ast
  python main.py programa.bminor --tokens --symtab
  python main.py programa.bminor --graph


================================================================
  ARCHIVOS DE PRUEBA INCLUIDOS
================================================================

Se incluyen tres archivos para verificar la detección de errores:

--------------------------------------------------------------
1. test_errores_lexicos.bminor
   Prueba: carácter ilegal en el código fuente.

   Ejecutar:
     python main.py test_errores_lexicos.bminor

   Error esperado:
     ✖ error  Error léxico en línea 2, columna 21: carácter ilegal '@'

--------------------------------------------------------------
2. test_errores_sintacticos.bminor
   Prueba los siguientes errores sintácticos:
     - Falta ";" al final de una declaración   (línea 2)
     - Falta ";" después de "return"           (línea 4)
     - Falta ";" después de "break"            (línea 8)
     - Falta ";" después de "continue"         (línea 9)

   Ejecutar:
     python main.py test_errores_sintacticos.bminor

   Errores esperados (el parser continúa después de cada uno):
     ✖ se esperaba ";" al final de la línea 2
     ✖ se esperaba ";" después de "return"
     ✖ se esperaba ";" después de "break"
     ✖ se esperaba ";" después de "continue"

   NOTA: pueden aparecer errores en cascada (e.g. "}" inesperado)
   cuando un error de recuperación consume un token de cierre.
   Esto es comportamiento normal en parsers LR.

--------------------------------------------------------------
3. test_errores_semanticos.bminor
   Prueba los siguientes errores semánticos:
     - Uso de variable no declarada            (línea 6)
     - Redeclaración en el mismo alcance       (línea 8)
     - Llamada a algo que no es una función    (línea 9)

   Ejecutar:
     python main.py test_errores_semanticos.bminor

   Errores esperados:
     ✖ símbolo 'variable_no_declarada' no definido
     ✖ redeclaración de 'duplicada' en el mismo alcance
     ✖ 'duplicada' no es una función


================================================================
  SINTAXIS DEL LENGUAJE BMINOR (REFERENCIA RÁPIDA)
================================================================

-- Declaración de variable:
     nombre: tipo;
     nombre: tipo = valor;

-- Declaración de constante:
     nombre: const = valor;

-- Tipos simples:
     integer, float, boolean, char, string, void

-- Declaración de arreglo:
     datos: array[10] integer;
     datos: array[10] integer = {1, 2, 3};

-- Declaración de función:
     nombre: function tipo_retorno(param1: tipo, param2: tipo) = {
         ...
     }

-- Estructuras de control:
     if (condicion) { ... }
     if (condicion) { ... } else { ... }
     while (condicion) { ... }
     for (init; condicion; update) { ... }

-- Sentencias:
     print expr1, expr2;
     return expr;
     break;
     continue;

-- Operadores:
     Aritméticos:  + - * / % ^
     Relacionales: < <= > >= == !=
     Lógicos:      && || !
     Asignación:   = += -= *= /= %=
     Incremento:   ++ --

-- Comentarios:
     // comentario de línea
     /* comentario de bloque */

-- Ejemplo de programa completo:
     main: function integer(args: string) = {
         x: integer = 10;
         y: integer = 20;
         result: integer = x + y;
         print result;
         return result;
     }


================================================================
  CÓMO INTERPRETAR LOS MENSAJES DE ERROR
================================================================

El compilador reporta errores en el siguiente formato:

  ✖ error  <descripción del error>
     ╰─ archivo.bminor:LÍNEA
       │
    N  │  <línea de código donde ocurre el error>
       │

Tipos de error:
  · note     — información adicional (sin detener compilación)
  ▲ warning  — advertencia (sin detener compilación)
  ✖ error    — error que impide continuar a la siguiente fase
  ☠ fatal    — error crítico que aborta de inmediato

Orden de fases:
  Si hay errores LÉXICOS   → no se ejecuta el parser.
  Si hay errores SINTÁCTICOS → no se ejecuta el checker.
  Si hay errores SEMÁNTICOS → el checker reporta todos antes
                              de detener la compilación.


================================================================
  SOLUCIÓN DE PROBLEMAS COMUNES
================================================================

Problema: ModuleNotFoundError: No module named 'sly'
Solución: pip install sly

Problema: ModuleNotFoundError: No module named 'rich'
Solución: pip install rich

Problema: ModuleNotFoundError: No module named 'multimethod'
Solución: pip install multimethod

Problema: graphviz.backend.execute.ExecutableNotFound
Solución: Instalar graphviz en el sistema operativo:
  - Windows:  https://graphviz.org/download/
  - Linux:    sudo apt install graphviz
  - macOS:    brew install graphviz

Problema: grammar.txt aparece al ejecutar
Solución: Es normal. Sly genera ese archivo de depuración
          automáticamente. Puede ignorarlo.

================================================================

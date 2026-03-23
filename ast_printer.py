from rich.tree import Tree
from graphviz import Digraph

# =========================================
# UTILIDAD: obtener hijos del AST
# =========================================

def get_children(node):
    children = []

    if isinstance(node, list):
        return node

    if hasattr(node, "__dict__"):
        for value in node.__dict__.values():
            if isinstance(value, list):
                children.extend(value)
            elif hasattr(value, "__dict__"):
                children.append(value)

    return children


# =========================================
# LABEL BONITO PARA NODOS
# =========================================

def node_label(node):
    name = node.__class__.__name__

    if hasattr(node, "op"):
        return f"{name}({node.op})"

    if hasattr(node, "name") and isinstance(node.name, str):
        return f"{name}({node.name})"

    if hasattr(node, "value"):
        return f"{name}({node.value})"

    return name


# =========================================
# RICH TREE
# =========================================

def build_rich_tree(node):
    tree = Tree(node_label(node))

    for child in get_children(node):
        tree.add(build_rich_tree(child))

    return tree


# =========================================
# GRAPHVIZ
# =========================================

def build_graphviz(node, graph=None, parent=None, counter=[0]):
    if graph is None:
        graph = Digraph()

    node_id = str(counter[0])
    counter[0] += 1

    graph.node(node_id, node_label(node))

    if parent is not None:
        graph.edge(parent, node_id)

    for child in get_children(node):
        build_graphviz(child, graph, node_id, counter)

    return graph
import os
import ast
import igraph

def get_user_input():
    return input("Relative File/Folder Path:")

# Opens up a file and parses into an AST object
def generate_ast_from_file(filename):
    # Read the source code from the file
    with open(filename, 'r') as file:
        source_code = file.read()

    # Generate the AST
    ast_object = ast.parse(source_code)
    return ast_object

# Recursively opens files and folders
def recursive_get_files(name):
    if os.path.isfile(name) and name.split('.')[-1] == 'py':
        print("Found File")
        parse_ast(generate_ast_from_file(name), os.getcwd() + "\\" + name)
        igraph.plot(graph, name.split('.')[0] + '.png', margin=50, layout='reingold_tilford', vertex_label_size=14, vertex_size=34)
        graph.clear()
        print("Dependency Graph Created")

    elif os.path.isdir(name):
        print("Found Directory")
        for it in os.scandir(name):
            if os.path.isfile(it.path) or os.path.isdir(it.path):
                recursive_get_files(it.path)

def parse_ast(ast_node, location):

    def recursive_add_nodes(ast_node, location):
        if str(type(ast_node)) == '<class \'ast.Module\'>':
            graph.add_vertex(name=(location + '/' + str(type(ast_node))), label=location.split('\\')[-1], color='red')
        if str(type(ast_node)) == '<class \'ast.FunctionDef\'>':
            graph.add_vertex(name=(location + '/' + ast_node.name), label=(ast_node.name + '()'), color='green')
        if str(type(ast_node)) == '<class \'ast.ClassDef\'>':
            graph.add_vertex(name=(location + '/' + ast_node.name), label=(ast_node.name + '()'), color='yellow')

        if hasattr(ast_node, 'body'):
            if str(type(ast_node)) == '<class \'ast.Module\'>':
                location = location + '/' + str(type(ast_node))
            elif str(type(ast_node)) == '<class \'ast.FunctionDef\'>' or str(type(ast_node)) == '<class \'ast.ClassDef\'>':
                location = location + '/' + ast_node.name

            for child in ast_node.body:
                recursive_add_nodes(child, location)

    def recursive_add_children(ast_node, location):
        if hasattr(ast_node, 'body'):

            if str(type(ast_node)) == '<class \'ast.Module\'>':
                    location = location + '/' + str(type(ast_node))
            elif str(type(ast_node)) == '<class \'ast.FunctionDef\'>' or str(type(ast_node)) == '<class \'ast.ClassDef\'>':
                    location = location + '/' + ast_node.name

            for child in ast_node.body:
                if hasattr(child, 'name'):
                    graph.add_edge(location, (location + '/' + child.name), color='blue')
                
                recursive_add_children(child, location)

    def recursive_add_loose_statements(ast_node, location):
        if str(type(ast_node)) == '<class \'ast.FunctionDef\'>' or str(type(ast_node)) == '<class \'ast.ClassDef\'>' or str(type(ast_node)) == '<class \'ast.Module\'>':
            
            if str(type(ast_node)) == '<class \'ast.Module\'>':
                    location = location + '/' + str(type(ast_node))
            elif str(type(ast_node)) == '<class \'ast.FunctionDef\'>' or str(type(ast_node)) == '<class \'ast.ClassDef\'>':
                    location = location + '/' + ast_node.name
            
            for child in ast_node.body:

                if str(type(child)) != '<class \'ast.FunctionDef\'>' or str(type(child)) != '<class \'ast.ClassDef\'>' or str(type(child)) != '<class \'ast.Module\'>':
                    graph.add_vertex(name=(location + 'loose'), label='loose', color='grey')
                    graph.add_edge(location, (location + 'loose'), color='blue')
                    break
            
            for child in ast_node.body:
                recursive_add_loose_statements(child, location)

    def recursive_add_calls(ast_node, location):
        if hasattr(ast_node, 'value') and hasattr(ast_node.value, 'func') and hasattr(ast_node.value.func, 'id') and (location + '/' + ast_node.value.func.id in graph.vs._name_index):
            if str(type(ast_node)) == '<class \'ast.Module\'>':
                graph.add_edge((location + '/' + str(type(ast_node))), (location + '/' + ast_node.value.func.id), color='green')
            elif (str(type(ast_node)) == '<class \'ast.FunctionDef\'>' or str(type(ast_node)) == '<class \'ast.ClassDef\'>'):
                graph.add_edge((location + '/' + ast_node.name), (location + '/' + ast_node.value.func.id), color='green')
            else:
                graph.add_edge((location + 'loose'), (location + '/' + ast_node.value.func.id), color='green')

        if hasattr(ast_node, 'body'):

            if str(type(ast_node)) == '<class \'ast.Module\'>':
                    location = location + '/' + str(type(ast_node))
            elif str(type(ast_node)) == '<class \'ast.FunctionDef\'>' or str(type(ast_node)) == '<class \'ast.ClassDef\'>':
                    location = location + '/' + ast_node.name

            for child in ast_node.body:
                recursive_add_calls(child, location)

    def recursive_add_returns(ast_node, location):
        if str(type(ast_node)) == '<class \'ast.Return\'>':
            graph.add_edge((location + 'loose'), (location), color='red')

        if hasattr(ast_node, 'body'):

            if str(type(ast_node)) == '<class \'ast.Module\'>':
                    location = location + '/' + str(type(ast_node))
            elif str(type(ast_node)) == '<class \'ast.FunctionDef\'>' or str(type(ast_node)) == '<class \'ast.ClassDef\'>':
                    location = location + '/' + ast_node.name

            for child in ast_node.body:
                recursive_add_returns(child, location)
        
    recursive_add_nodes(ast_node, location)
    recursive_add_children(ast_node, location)
    recursive_add_loose_statements(ast_node, location)
    recursive_add_calls(ast_node, location)
    recursive_add_returns(ast_node, location)

graph = igraph.Graph(directed=True)
user_input = get_user_input()
recursive_get_files(user_input)
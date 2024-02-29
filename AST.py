import os
import ast
import igraph

node_list = list()
debugfile = open('debug.txt', 'w')

# Redefines functions within the NodeVisitor class to print to file in specific format
class NodePrinter(ast.NodeVisitor):
    def __init__(self, output_file):
        self.output_file = output_file

    def generic_visit(self, node):
        print('\n', file=self.output_file)
        print('Type: ' + type(node).__name__, file=self.output_file)
        print('Address: ' + str(id(node)), file=self.output_file)

        dict_entry = {'Type':type(node).__name__, 'Address':str(id(node))}

        if type(node).__name__ == "Module":
            print('Location: ' + current_file, file=self.output_file)
            dict_entry['Location'] = current_file

        if hasattr(node, 'name'):
            print('Name: ' + str(node.name), file=self.output_file)
            dict_entry['Name'] = str(node.name)

        if hasattr(node, 'body'):
            print('Children: ', file=self.output_file)
            temp_array = list()

            for i in node.body:
                print(str(id(i)), file=self.output_file)
                temp_array.append([str(id(i)), type(i).__name__])

            dict_entry['Children'] = temp_array

        if type(node).__name__ == "Expr":
            if hasattr(node.value.func, "id"):
                print('Calling: ', file=self.output_file)
                print(str(node.value.func.id), file=self.output_file)  
                dict_entry['Calling'] = [str(node.value.func.id)]
            elif hasattr(node.value.func, "attr"):
                dict_entry['Attr'] = str(node.value.func.attr)

        if type(node).__name__ == "Import":
            print('Names: ', file=self.output_file)
            temp_array = list()

            for i in node.names:
                print(str(id(i)), file=self.output_file)
                temp_array.append([str(id(i)), type(i).__name__])

            dict_entry['Names'] = temp_array

        if type(node).__name__ == "ImportFrom":
            print('Module: ' + str(node.module), file=self.output_file)
            dict_entry['Module'] = str(node.module)

            print('Names: ', file=self.output_file)
            temp_array = list()

            for i in node.names:
                print(str(id(i)), file=self.output_file)
                temp_array.append([str(id(i)), type(i).__name__])

            dict_entry['Names'] = temp_array

        node_list.append(dict_entry)

        super().generic_visit(node)


# Opens up a file and parses into an AST object
def generate_ast_from_file(filename):
    # Read the source code from the file
    with open(filename, 'r') as file:
        source_code = file.read()

    # Generate the AST
    ast_object = ast.parse(source_code)
    return ast_object


# Opens file in write mode and then starts the AST traversal
def save_ast(ast_object):
    NodePrinter(debugfile).visit(ast_object)


# Modifies the node_list so that every node with Expr will have a Loose Statement instead
def tie_up_loose_statements():
    # Helper Function for tie_up_loose_statements() that combines 2 nodes calling list
    def combine_nodes(ID1, ID2):
        # Finds specificed nodes
        for node in node_list:
            if node['Address'] == ID1:
                node1 = node
            elif node['Address'] == ID2:
                node2 = node
        
        # Adds node2's list of calls to node1's calls and then deletes node2
        if node1 and node2:
            node1['Type'] = 'Loose Statements'
            node2['Type'] = 'Loose Statements'
            if 'Calling' in node1 and 'Calling' in node2:
                node1['Calling'] += node2['Calling']
            elif 'Calling' in node2:
                node1['Calling'] = node2['Calling']
            node_list.remove(node2)


    # Go through node_list looking for nodes with children
    for node in node_list:
        if 'Children' in node:
            # Once a node with children is found collect the children that are Expr
            loose_expressions = list()
            for child in node['Children']:
                if child[1] == 'Expr':
                    loose_expressions.append(child)
            # Once a node with children is found delete the children that are Expr (Have to do this in a seperate step since traversal gets mess up if deleting elements while traversing)
            for child in reversed(node['Children']):
                if child[1] == 'Expr':
                    node['Children'].remove(child)

        
            # Combine the Expr into one
            count = len(loose_expressions)    
            while count > 1:
                combine_nodes(loose_expressions[0][0], loose_expressions[count-1][0])
                count = count - 1

            # Rename the combined Expr to Loose Statements and add back to the parent's children
            if len(loose_expressions) > 0:
                loose_expressions[0][1] = 'Loose Statements'
                node['Children'].append(loose_expressions[0])


# Utilizes import statements to connect modules
def link_modules():
    for index in node_list:
        if index['Type'] == 'ImportFrom':
            source = index['Module']


# Traverses through node list and adds each node to the graph
def add_nodes(graph):
    for index in node_list:
        if index['Type'] == 'FunctionDef':
            graph.add_vertex(name=index['Address'], label='Function - ' + index['Name'], color='blue')
        else:
            graph.add_vertex(name=index['Address'], label=index['Type'])


# Traverses through node list and adds each edge relationship to the graph
def add_edges(graph):

    # Children relationships
    for index in node_list:
        if 'Children' in index:
            for child in index['Children']:
                graph.add_edge(index['Address'], child[0], color='blue')

    # Calling relationships
    for index in node_list:
        if 'Calling' in index:
            for call in index['Calling']:
                for sIndex in node_list:
                    if 'Name' in sIndex and sIndex['Name'] == call:
                        graph.add_edge(index['Address'], sIndex['Address'], color='green')


# Reads file and generates graph from file
def visualize_ast():
    newGraph = igraph.Graph(directed=True)
    
    # Collects Expr and puts them together
    tie_up_loose_statements()

    # Links Modules together
    link_modules()

    add_nodes(newGraph)
    add_edges(newGraph)

    # Deletes the vertices with degree 0
    newGraph.delete_vertices([v.index for v in newGraph.vs if newGraph.degree()[v.index] == 0])
    # Deletes self-loop edges
    newGraph.simplify(multiple=False, loops=True)


    # My favorite layouts
    #igraph.plot(newGraph, 'AST.png', layout='reingold_tilford', vertex_label_size=14, vertex_size=34)
    #igraph.plot(newGraph, 'AST.png', layout='sugiyama')
    #igraph.plot(newGraph, 'AST.png', vertex_label_size=14, vertex_size=34)
    #igraph.plot(newGraph, 'AST.png', layout='davidson_harel')
    igraph.plot(newGraph, 'AST.png', layout='fruchterman_reingold')


# Input name of folder here, folder must be in res
current_file = str()
ast_object = list()
folder_name = "data"
path = os.getcwd() + "\\" + folder_name
for filename in os.listdir(path):
    # Check for python file extensions
    if filename.endswith('.py'):  
        current_file = os.path.join(path, filename)
        # Generates AST then writes AST to file and object
        save_ast(generate_ast_from_file(current_file))


# Visualize the AST
visualize_ast()
debugfile.close()
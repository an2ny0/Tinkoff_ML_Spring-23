import argparse
import ast


class NormIdentifiers(ast.NodeTransformer):
    def __init__(self):
        self.identifiers = {}
        super().__init__()

    def visit_Name(self, node):
        try:
            id = self.identifiers[node.id]
        except KeyError:
            id = f'id{len(self.identifiers)}'
            self.identifiers[node.id] = id

        return ast.copy_location(ast.Name(id=id), node)


class NormFunctions(ast.NodeTransformer):
    def __init__(self, func=None):
        self.identifiers = {}
        self.func = func
        super().__init__()

    def visit_FunctionDef(self, node):
        if self.func and self.func != node.name:
            return None

        try:
            name = self.identifiers[node.name]
        except KeyError:
            name = f'func{len(self.identifiers):x}'
            self.identifiers[node.name] = name

        for i, arg in enumerate(node.args.args):
            arg.arg = f'arg{i}'

        new_func = ast.FunctionDef(name=name, args=node.args, body=node.body, decorator_list=node.decorator_list)

        if isinstance(new_func.body[0], ast.Expr) and isinstance(new_func.body[0].value, ast.Constant):
            del new_func.body[0]

        return ast.copy_location(new_func, node)


def levenstein_distance(str_1, str_2):
    n, m = len(str_1), len(str_2)
    if n > m:
        str_1, str_2 = str_2, str_1
        n, m = m, n

    current_row = range(n + 1)
    for i in range(1, m + 1):
        previous_row, current_row = current_row, [i] + [0] * n
        for j in range(1, n + 1):
            add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
            if str_1[j - 1] != str_2[i - 1]:
                change += 1
            current_row[j] = min(add, delete, change)

    return current_row[n]


def compare():
    parser = argparse.ArgumentParser(
        description='Антиплагиат (сравнивает два текста программ на Python и выдает оценку их похожести)'
    )
    parser.add_argument('input_file', type=str, help='Путь к файлу со списком пар документов для анализа')
    parser.add_argument('output_file', type=str, help='Путь до выходного файла')
    args = parser.parse_args()
    with open(args.input_file) as input_file, open(args.output_file, 'w') as output_file:
        for line in input_file:
            file1_path, file2_path = line.strip().split()
            with open(file1_path) as file1, open(file2_path) as file2:
                code1, code2 = file1.read(), file2.read()
                tree1, tree2 = ast.parse(code1), ast.parse(code2)
                tree1 = NormFunctions().visit(tree1)
                tree1 = NormIdentifiers().visit(tree1)
                tree2 = NormFunctions().visit(tree2)
                tree2 = NormIdentifiers().visit(tree2)
                code1_norm, code2_norm = ast.unparse(tree1), ast.unparse(tree2)
                distance = levenstein_distance(code1_norm, code2_norm)
                distance = distance / len(code1_norm)
                output_file.write(str(round(distance, 3)) + '\n')


if __name__ == '__main__':
    compare()
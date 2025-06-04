from lexer.yalex import YALexLexer
from parser.yapar import Grammar
import os

# Archivos YALP y entradas correspondientes
yalp_files = [
    ('parser/slr-1.yalp', 'input/numbers_expressions.txt'),
    ('parser/slr-2.yalp', 'input/numbers_expressions.txt'),
    ('parser/slr-3.yalp', 'input/test_yalp3.txt'),
    ('parser/slr-4.yalp', 'input/test_yalp4.txt')
]

lexer = YALexLexer('lexer/lexer.yal')

def save_parse_table(grammar, index):
    with open(f'output/tabla_parseo_{index+1}.txt', 'w') as f:
        f.write("ACTION TABLE:\n")
        for (state, token), action in grammar.action_table.items():
            f.write(f"State {state}, Token {token}: {action}\n")
        
        f.write("\nGOTO TABLE:\n")
        for (state, nonterm), target in grammar.goto_table.items():
            f.write(f"State {state}, Non-Terminal {nonterm}: {target}\n")

def save_lr0_items(grammar, index):
    with open(f'output/items_lr0_{index+1}.txt', 'w') as f:
        for i, state in enumerate(grammar.states):
            f.write(f"State {i}:\n")
            for item in state:
                head, body, pos = item
                before_dot = ' '.join(body[:pos])
                after_dot = ' '.join(body[pos:])
                f.write(f"  {head} -> {before_dot} . {after_dot}\n")
            f.write("\n")

def check_conflicts(grammar, index):
    conflicts = []
    # Agrupar acciones por estado y token
    action_groups = {}
    for (state, token), action in grammar.action_table.items():
        action_groups.setdefault((state, token), []).append(action)

    for (state, token), actions in action_groups.items():
        if len(actions) > 1:
            conflicts.append((state, token, actions))

    with open(f'output/conflictos_{index+1}.txt', 'w') as f:
        if conflicts:
            f.write("Conflictos encontrados:\n")
            for state, token, acts in conflicts:
                f.write(f"Estado {state}, Token {token}: {acts}\n")
        else:
            f.write("No se encontraron conflictos.\n")

def run_all():
    os.makedirs("output", exist_ok=True)

    for i, (yalp_path, input_path) in enumerate(yalp_files):
        grammar = Grammar(yalp_path)

        with open(input_path, 'r') as f:
            source_code = f.read()

        tokens = lexer.tokenize(source_code)
        grammar.build_slr_table()

        save_parse_table(grammar, i)
        save_lr0_items(grammar, i)
        check_conflicts(grammar, i)

        log = grammar.simulate_parser(tokens)

        with open(f'output/salida_parser_{i+1}.txt', 'w', encoding='utf-8') as out:
            out.write("Tokens:\n")
            out.write('\n'.join(f"{t[0]}: {t[1]}" for t in tokens))
            out.write("\n\nSimulación del Parser:\n")
            for line in log:
                out.write(line + '\n')

if __name__ == '__main__':
    run_all()

class Grammar:
    def __init__(self, yalp_file):
        self.productions = {}
        self.symbols = set()
        self.terminals = set()
        self.nonterminals = set()
        self.start_symbol = None  # Inicializar aquí
        self.first_sets = {}
        self.follow_sets = {}
        self.states = []
        self.action_table = {}
        self.goto_table = {}

        self.load_yalp(yalp_file)  # Cargar el archivo después de inicializar

    def load_yalp(self, yalp_file):
        with open(yalp_file, 'r') as f:
            lines = f.readlines()

        clean_lines = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("/*") or line.startswith("%token"):
                continue
            clean_lines.append(line)

        current_head = None
        current_bodies = []

        for line in clean_lines:
            if ':' in line:
                if current_head is not None:
                    if current_head not in self.productions:
                        self.productions[current_head] = []
                    self.productions[current_head].extend(current_bodies)

                parts = line.split(':', 1)
                current_head = parts[0].strip()

                if self.start_symbol is None:
                    self.start_symbol = current_head  # Asigna el primer no terminal como inicial
                    print(f"Start symbol asignado a: {self.start_symbol}")

                body = parts[1].strip()
                bodies = [alt.strip().split() for alt in body.split('|')]
                current_bodies = bodies

            elif line == ';':
                if current_head is not None:
                    if current_head not in self.productions:
                        self.productions[current_head] = []
                    self.productions[current_head].extend(current_bodies)
                current_head = None
                current_bodies = []

            else:
                bodies = [alt.strip().split() for alt in line.split('|')]
                current_bodies.extend(bodies)

        if current_head is not None:
            if current_head not in self.productions:
                self.productions[current_head] = []
            self.productions[current_head].extend(current_bodies)

        # Construir conjuntos de símbolos
        self.nonterminals = set(self.productions.keys())
        self.symbols = self.nonterminals.copy()
        for prods in self.productions.values():
            for prod in prods:
                self.symbols.update(prod)
        self.terminals = self.symbols - self.nonterminals

    def compute_first_sets(self):
        self.first_sets = {sym: set() for sym in self.symbols}

        # Los terminales tienen como First el mismo símbolo
        for t in self.terminals:
            self.first_sets[t].add(t)

        changed = True
        while changed:
            changed = False
            for head, productions in self.productions.items():
                for prod in productions:
                    for symbol in prod:
                        before = len(self.first_sets[head])
                        # Añadimos first(symbol) excepto epsilon (aquí no manejamos epsilon explícito)
                        self.first_sets[head].update(self.first_sets.get(symbol, set()))
                        after = len(self.first_sets[head])
                        if after > before:
                            changed = True
                        # En esta versión simple, no manejamos epsilon, así que rompemos
                        break

    def compute_follow_sets(self):
        self.follow_sets = {nt: set() for nt in self.nonterminals}
        # Símbolo de fin de cadena $
        self.follow_sets[self.start_symbol].add('$')

        changed = True
        while changed:
            changed = False
            for head, productions in self.productions.items():
                for prod in productions:
                    for i, symbol in enumerate(prod):
                        if symbol in self.nonterminals:
                            follow_before = len(self.follow_sets[symbol])
                            # Siguiente símbolo
                            rest = prod[i + 1:]
                            if rest:
                                # First del resto (solo el primero en esta versión simple)
                                first_rest = set()
                                for sym in rest:
                                    first_rest.update(self.first_sets.get(sym, set()))
                                    # Aquí no manejo epsilon, así que salgo
                                    break
                                # Añadir first_rest al follow
                                self.follow_sets[symbol].update(first_rest - set(['ε']))
                            else:
                                # Si no hay símbolos a la derecha, añadimos follow del head
                                self.follow_sets[symbol].update(self.follow_sets[head])
                            follow_after = len(self.follow_sets[symbol])
                            if follow_after > follow_before:
                                changed = True

    def build_slr_table(self):
        # Creamos símbolo inicial aumentado S'
        augmented_start = self.start_symbol + "'"
        while augmented_start in self.nonterminals or augmented_start in self.terminals:
            augmented_start += "'"
        # Añadimos la producción aumentada S' -> start_symbol
        self.productions[augmented_start] = [[self.start_symbol]]
        self.nonterminals.add(augmented_start)
        self.symbols.add(augmented_start)

        # Item inicial (S' -> .S)
        start_item = (augmented_start, tuple([self.start_symbol]), 0)

        def closure(items):
            closure_set = set(items)
            added = True
            while added:
                added = False
                new_items = set()
                for (head, body, dot) in closure_set:
                    if dot < len(body):
                        symbol = body[dot]
                        if symbol in self.nonterminals:
                            for prod_body in self.productions[symbol]:
                                item = (symbol, tuple(prod_body), 0)
                                if item not in closure_set:
                                    new_items.add(item)
                if new_items:
                    closure_set.update(new_items)
                    added = True
            return closure_set

        def goto(items, symbol):
            moved_items = set()
            for (head, body, dot) in items:
                if dot < len(body) and body[dot] == symbol:
                    moved_items.add((head, body, dot + 1))
            return closure(moved_items)

        # Construir estados
        states = []
        state_map = {}  # mapear conjunto items a índice de estado

        start_closure = closure([start_item])
        states.append(start_closure)
        state_map[frozenset(start_closure)] = 0

        added = True
        while added:
            added = False
            for i, state in enumerate(states):
                for symbol in self.symbols:
                    next_state = goto(state, symbol)
                    if not next_state:
                        continue
                    frozen = frozenset(next_state)
                    if frozen not in state_map:
                        state_map[frozen] = len(states)
                        states.append(next_state)
                        added = True

        self.states = states

        # Calcular first y follow
        self.compute_first_sets()
        self.compute_follow_sets()

        # Construir tabla action y goto
        action_table = {}
        goto_table = {}

        for i, state in enumerate(states):
            for item in state:
                head, body, dot = item
                if dot < len(body):
                    symbol = body[dot]
                    if symbol in self.terminals:
                        # shift a estado goto(state, symbol)
                        next_state = state_map[frozenset(goto(state, symbol))]
                        action_table[(i, symbol)] = ("shift", next_state)
                    else:
                        # goto para no terminales se pone en goto_table
                        next_state = state_map[frozenset(goto(state, symbol))]
                        goto_table[(i, symbol)] = next_state
                else:
                    # punto al final: reduce o accept
                    if head == augmented_start:
                        # aceptamos si la producción es S' -> S .
                        action_table[(i, '$')] = ("accept",)
                    else:
                        # reduce con la producción head -> body
                        # en SLR se reduce para todos los terminales en FOLLOW(head)
                        for terminal in self.follow_sets.get(head, set()):
                            if (i, terminal) in action_table:
                                # Conflicto S/R o R/R detectado (podrías agregar reporte)
                                pass
                            else:
                                action_table[(i, terminal)] = ("reduce", (head, list(body)))

        self.action_table = action_table
        self.goto_table = goto_table

    def simulate_parser(self, tokens):
        stack = [0]
        index = 0
        tokens.append(("$", "$"))  # Añadimos el EOF ficticio

        output = []
        while True:
            state = stack[-1]
            token_type, token_value = tokens[index]

            action = self.action_table.get((state, token_type))
            if action is None:
                output.append(f"Error: token inesperado '{token_value}' en estado {state}")
                break

            if action[0] == "shift":
                next_state = action[1]
                output.append(f"Shift: '{token_value}' ({token_type}) y vamos a estado {next_state}")
                stack.append(token_type)
                stack.append(next_state)
                index += 1

            elif action[0] == "reduce":
                head, body = action[1]
                if body != ['ε']:  # para producciones vacías, si usas 'ε'
                    for _ in range(len(body) * 2):  # Quita 2 * |body| elementos (símbolo, estado)
                        stack.pop()
                state = stack[-1]
                output.append(f"Reduce con regla: {head} → {' '.join(body)}")
                stack.append(head)
                goto_state = self.goto_table.get((state, head))
                if goto_state is None:
                    output.append(f"Error: goto no encontrado para {head} desde estado {state}")
                    break
                stack.append(goto_state)

            elif action[0] == "accept":
                output.append("Cadena aceptada por la gramática.")
                break

        return output

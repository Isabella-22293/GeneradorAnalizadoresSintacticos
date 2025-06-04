import re

class YALexLexer:
    def __init__(self, filename):
        self.filename = filename
        self.token_exprs = []
        self.read_lexer_file()

    def read_lexer_file(self):
        with open(self.filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Ignorar líneas vacías o comentarios
                if not line or line.startswith("//"):
                    continue
                # Leer líneas con formato TOKEN "regex"
                if ' ' in line:
                    token_name, expr = line.split(None, 1)
                    expr = expr.strip().strip('"')
                    self.token_exprs.append((token_name, expr))

    def tokenize(self, text):
        tokens = []
        index = 0
        while index < len(text):
            match = None
            for token_type, pattern in self.token_exprs:
                regex = re.compile(pattern)
                match = regex.match(text, index)
                if match:
                    # Guardar TODOS los tokens, incluidos WHITESPACE
                    tokens.append((token_type, match.group(0)))
                    index = match.end()
                    break
            if not match:
                raise RuntimeError(f"Illegal character: {text[index]}")
        return tokens
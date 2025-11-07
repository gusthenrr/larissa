from cs50 import SQL
import shutil
import os
from datetime import datetime

# caminho do seu banco
DB_PATH = "sqlite:///data/dados.db"
RAW_PATH = "data/dados.db"
var = True

if var:
    DATABASE_PATH = "/data/dados.db"
    if not os.path.exists(DATABASE_PATH):
        shutil.copy("dados.db", DATABASE_PATH)
    db = SQL("sqlite:///" + DATABASE_PATH)
else:
    DATABASE_PATH = "data/dados.db"
    db=SQL("sqlite:///" + DATABASE_PATH)

# só as tabelas que (pelo schema que você mandou) têm coluna carrinho
tabelas_com_carrinho = [
    "estoque",
    "usuarios",
    "estoque_geral",
    "alteracoes",
    "tokens",
    "pagamentos",
    "cardapio",
    "promotions",
    "opcoes",
    "opcoes_audit",
    "clientes",
    # se você depois adicionar carrinho em outras, é só colocar aqui
]

# preenche só onde está NULL ou vazio
for tabela in tabelas_com_carrinho:
    try:
        db.execute(f'ALTER TABLE {tabela} ADD COLUMN carrinho TEXT')
        q = f"""
        UPDATE {tabela}
        SET carrinho = 'nossopoint'
        WHERE carrinho IS NULL OR carrinho = '';
        """
        db.execute(q)
        print(f"[OK] Atualizado: {tabela}")
    except Exception as e:
        print(f"[ERRO] {tabela}: {e}")

print("[FINISH] Tudo que tinha coluna carrinho nessas tabelas foi preenchido com 'nossopoint'.")


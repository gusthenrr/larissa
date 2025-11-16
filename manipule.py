import sqlite3
import shutil
import os

# Mesmo esquema do seu código
var = True

if var:
    DATABASE_PATH = "/data/dados.db"
    if not os.path.exists(DATABASE_PATH):
        shutil.copy("dados.db", DATABASE_PATH)
else:
    DATABASE_PATH = "data/dados.db"


def limpar_interrogacoes(valor):
    """
    Remove todos os '?' se for string.
    Se não for string, retorna como está.
    """
    if isinstance(valor, str):
        return valor.replace("?", "")
    return valor


# Conecta direto com sqlite3, fugindo do cs50.SQL aqui
conn = sqlite3.connect(DATABASE_PATH)
conn.row_factory = sqlite3.Row  # permite acessar colunas por nome
cur = conn.cursor()

# Busca registros do carrinho original
cur.execute("SELECT * FROM cardapio WHERE carrinho = ?", ("nossopoint",))
rows = cur.fetchall()

for row in rows:
    # Limpa possíveis '?' em TODAS as colunas de texto usadas
    item = limpar_interrogacoes(row["item"])
    opcoes = limpar_interrogacoes(row["opcoes"])
    instrucoes = limpar_interrogacoes(row["instrucoes"])
    image = limpar_interrogacoes(row["image"])
    subcategoria = limpar_interrogacoes(row["subcategoria"])

    preco = row["preco"]
    categoria_id = row["categoria_id"]
    preco_base = row["preco_base"]
    usable_on_qr = row["usable_on_qr"]

    # novo carrinho
    carrinho = "nossopoint2"

    # INSERT seguro com parâmetros de verdade (DB-API)
    cur.execute(
        """
        INSERT OR IGNORE INTO cardapio
        (item, preco, categoria_id, opcoes, instrucoes, image, preco_base, usable_on_qr, subcategoria, carrinho)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item,
            preco,
            categoria_id,
            opcoes,
            instrucoes,
            image,
            preco_base,
            usable_on_qr,
            subcategoria,
            carrinho,
        ),
    )

# Confirma as alterações
conn.commit()
conn.close()

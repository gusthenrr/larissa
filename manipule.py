from cs50 import SQL
import shutil
import os
from datetime import datetime

var = True

if var:
    DATABASE_PATH = "/data/dados.db"
    if not os.path.exists(DATABASE_PATH):
        shutil.copy("dados.db", DATABASE_PATH)
    db = SQL("sqlite:///" + DATABASE_PATH)
else:
    DATABASE_PATH = "data/dados.db"
    db = SQL("sqlite:///" + DATABASE_PATH)

# Query com string correta
query = "SELECT * FROM cardapio WHERE carrinho = ?"
dados = db.execute(query, "nossopoint")

for row in dados:
    insert_query = """
        INSERT INTO cardapio 
        (item, preco, categoria_id, opcoes, instrucoes, image, preco_base, usable_on_qr, subcategoria, carrinho)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    db.execute(
        insert_query,
        row.get("item"),
        row.get("preco"),
        row.get("categoria_id"),
        row.get("opcoes"),
        row.get("instrucoes"),
        row.get("image"),
        row.get("preco_base"),
        row.get("usable_on_qr"),
        row.get("subcategoria"),
        "nossopoint2"
    )

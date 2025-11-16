from cs50 import SQL
import shutil
import os

var = True

if var:
    DATABASE_PATH = "/data/dados.db"
    if not os.path.exists(DATABASE_PATH):
        shutil.copy("dados.db", DATABASE_PATH)
    db = SQL("sqlite:///" + DATABASE_PATH)
else:
    DATABASE_PATH = "data/dados.db"
    db = SQL("sqlite:///" + DATABASE_PATH)

# Buscar itens do carrinho 'nossopoint'
dados = db.execute("SELECT * FROM cardapio WHERE carrinho = ?", "nossopoint")

for row in dados:
    
    # Remove caracteres inválidos do JSON
    opcoes_limpo = (row.get("opcoes") or "").replace("?", "")

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
        opcoes_limpo,
        row.get("instrucoes"),
        row.get("image"),
        row.get("preco_base"),
        row.get("usable_on_qr"),
        row.get("subcategoria"),
        "nossopoint2"
    )

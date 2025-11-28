from cs50 import SQL
import shutil
import os

# caminho de origem (no projeto)
DB_SOURCE_PATH = "data/dados.db"  # ajuste se for outro caminho

# caminho de destino (por exemplo, em produção / Docker)
DATABASE_PATH = "/data/dados.db"

# Se ainda não existir o /data/dados.db, copia do arquivo local
if not os.path.exists(DATABASE_PATH):
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    shutil.copy(DB_SOURCE_PATH, DATABASE_PATH)
    print(f"Copiado {DB_SOURCE_PATH} -> {DATABASE_PATH}")

# Abre o banco usando cs50.SQL
db = SQL("sqlite:///" + DATABASE_PATH)


def adicionar_id_referencia():
    # 1) Verificar se a coluna id_referencia já existe
    info = db.execute("PRAGMA table_info(cardapio);")
    # Em cs50.SQL, cada linha é um dict: { 'cid': ..., 'name': ..., 'type': ... }
    colunas = [linha["name"] for linha in info]

    if "id_referencia" not in colunas:
        print("Adicionando coluna id_referencia na tabela cardapio...")
        db.execute("ALTER TABLE cardapio ADD COLUMN id_referencia INTEGER;")
    else:
        print("Coluna id_referencia já existe, seguindo para atualização dos dados...")

    # 2) Copiar os valores de id para id_referencia (somente onde está NULL)
    print("Atualizando id_referencia com os valores de id...")
    db.execute("""
        UPDATE cardapio
        SET id_referencia = id
        WHERE id_referencia IS NULL;
    """)

    print("Concluído.")


if __name__ == "__main__":
    adicionar_id_referencia()

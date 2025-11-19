# migracao_ids.py
from cs50 import SQL
import shutil, os
from datetime import datetime

DB_URL   = "sqlite:///data/dados.db"   # URL para cs50.SQL
RAW_PATH = "/data/dados.db"             # caminho físico

def backup_db():
    if os.path.exists(RAW_PATH):
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = f"/data/dados.backup.{ts}.db"
        shutil.copyfile(RAW_PATH, backup_path)
        print(f"[OK] Backup criado em {backup_path}")
    else:
        print("[AVISO] Base não encontrada em", RAW_PATH)

def column_exists(db, table, column):
    # Garante retorno em forma de linhas (lista), nunca bool
    rows = db.execute(
        "SELECT 1 AS ok FROM pragma_table_info(?) WHERE name = ? LIMIT 1",
        table, column
    )
    return len(rows) > 0

def index_exists(db, table, index_name):
    # Usa sqlite_master para checar a existência do índice
    rows = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND tbl_name=? AND name=? LIMIT 1",
        table, index_name
    )
    return len(rows) > 0

def ensure_column_id(db, table):
    if not column_exists(db, table, "id"):
        db.execute(f"ALTER TABLE {table} ADD COLUMN id INTEGER")
        print(f"[OK] Coluna id criada em {table}")
    else:
        print(f"[OK] Coluna id já existe em {table}")

def ensure_column(db, table, column, type_sql="TEXT"):
    """Cria a coluna se não existir. Ex.: ensure_column(db,'cardapio','ingredientes','TEXT')"""
    if not column_exists(db, table, column):
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_sql}")
        print(f"[OK] Coluna {column} ({type_sql}) criada em {table}")
    else:
        print(f"[OK] Coluna {column} já existe em {table}")

def max_existing_id(db):
    m1 = db.execute("SELECT COALESCE(MAX(id), 0) AS mx FROM cardapio")[0]["mx"]
    if column_exists(db, "estoque", "id"):
        m2 = db.execute("SELECT COALESCE(MAX(id), 0) AS mx FROM estoque WHERE id IS NOT NULL")[0]["mx"]
    else:
        m2 = 0
    return max(m1, m2)

def main():
    backup_db()
    DATABASE_PATH = "/data/dados.db"
    if not os.path.exists(DATABASE_PATH):
        shutil.copy("dados.db", DATABASE_PATH)
    db = SQL("sqlite:///" + DATABASE_PATH)

    try:
        db.execute("BEGIN")

        # === Novas colunas solicitadas ===
        ensure_column(db, "cardapio", "ingredientes", "TEXT")       # lista JSON de ingredientes
        ensure_column(db, "estoque", "unidade", "TEXT")             # unidade informada no estoque (opcional para UI)
        ensure_column(db, "estoque_geral", "unidade", "TEXT")       # unidade informada no estoque_geral (opcional para UI)

        # 1) Garantir coluna id em estoque
        ensure_column_id(db, "estoque")

        # 2) Copiar id do cardapio -> estoque (quando item coincide; não sobrescreve ids já preenchidos)
        updated_from_cardapio = db.execute("""
            UPDATE estoque AS e
               SET id = (
                    SELECT c.id
                      FROM cardapio c
                     WHERE c.item = e.item
                     LIMIT 1
               )
             WHERE e.id IS NULL
               AND EXISTS (SELECT 1 FROM cardapio c WHERE c.item = e.item)
        """)
        print(f"[OK] IDs copiados do cardapio -> estoque: {updated_from_cardapio} linha(s)")

        # 3) Serializar ids restantes em estoque sem colidir
        next_id = max_existing_id(db) + 1
        pendentes = db.execute("SELECT item FROM estoque WHERE id IS NULL ORDER BY item")
        for row in pendentes:
            db.execute("UPDATE estoque SET id = ? WHERE item = ?", next_id, row["item"])
            next_id += 1
        if pendentes:
            print(f"[OK] IDs novos atribuídos em estoque: {len(pendentes)} (a partir de {next_id - len(pendentes)})")
        else:
            print("[OK] Não havia itens pendentes em estoque para serializar")

        # 3.1) Índice único em estoque.id
        if not index_exists(db, "estoque", "ux_estoque_id"):
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_estoque_id ON estoque(id)")
            print("[OK] Índice único ux_estoque_id criado em estoque")

        # 4) Garantir coluna id em estoque_geral
        ensure_column_id(db, "estoque_geral")

        # 5) Sincronizar estoque_geral.id = estoque.id por item (não sobrescreve já preenchidos)
        updated_geral = db.execute("""
            UPDATE estoque_geral AS g
               SET id = (
                    SELECT e.id
                      FROM estoque e
                     WHERE e.item = g.item
                     LIMIT 1
               )
             WHERE g.id IS NULL
               AND EXISTS (SELECT 1 FROM estoque e WHERE e.item = g.item)
        """)
        print(f"[OK] IDs sincronizados estoque -> estoque_geral: {updated_geral} linha(s)")

        # 5.1) Índices úteis
        if not index_exists(db, "estoque", "ix_estoque_item"):
            db.execute("CREATE INDEX IF NOT EXISTS ix_estoque_item ON estoque(item)")
            print("[OK] Índice ix_estoque_item criado")
        if not index_exists(db, "estoque_geral", "ix_estoque_geral_item"):
            db.execute("CREATE INDEX IF NOT EXISTS ix_estoque_geral_item ON estoque_geral(item)")
            print("[OK] Índice ix_estoque_geral_item criado")

        # Relatórios rápidos
        tot_e = db.execute("SELECT COUNT(*) AS n FROM estoque")[0]["n"]
        tot_e_id = db.execute("SELECT COUNT(*) AS n FROM estoque WHERE id IS NOT NULL")[0]["n"]
        tot_g = db.execute("SELECT COUNT(*) AS n FROM estoque_geral")[0]["n"]
        tot_g_id = db.execute("SELECT COUNT(*) AS n FROM estoque_geral WHERE id IS NOT NULL")[0]["n"]
        print(f"[RESUMO] estoque: {tot_e_id}/{tot_e} com id")
        print(f"[RESUMO] estoque_geral: {tot_g_id}/{tot_g} com id")

        db.execute("COMMIT")
        print("[OK] Migração concluída.")
    except Exception as e:
        print("[ERRO] Migração revertida por erro:", e)
        raise

if __name__ == "__main__":
    main()


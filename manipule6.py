from cs50 import SQL
import shutil
import os
from datetime import datetime

# caminho do banco
DB_PATH = "sqlite:///data/dados.db"
RAW_PATH = "/data/dados.db"

# 1. backup rápido antes de mexer
if os.path.exists(RAW_PATH):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"/data/dados.backup.{ts}.db"
    shutil.copyfile(RAW_PATH, backup_path)
    print(f"[OK] Backup criado em {backup_path}")

DATABASE_PATH = "/data/dados.db"
if not os.path.exists(DATABASE_PATH):
    shutil.copy("dados.db", DATABASE_PATH)
db = SQL("sqlite:///" + DATABASE_PATH)

try:
    print("[INFO] Iniciando migração da tabela estoque_geral...")
    db.execute("PRAGMA foreign_keys = OFF;")
    db.execute("BEGIN;")

    # Contar linhas da tabela original
    row = db.execute("SELECT COUNT(*) AS n FROM estoque_geral;")[0]
    n_orig = row["n"]
    print(f"[INFO] Linhas originais: {n_orig}")

    # 1) Renomear tabela antiga
    db.execute("ALTER TABLE estoque_geral RENAME TO estoque_geral_old;")

    # 2) Criar nova tabela com id autoincrement
    db.execute("""
        CREATE TABLE estoque_geral (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT,
            quantidade INTEGER,
            estoque_ideal INTEGER,
            carrinho TEXT,
            unidade TEXT,
            quantidade_total REAL,
            quantidade_por_unidade REAL
        );
    """)

    # 3) Copiar dados SEM o ID (SQLite gera ID novo)
    db.execute("""
        INSERT INTO estoque_geral (
            item, quantidade, estoque_ideal, carrinho, unidade, quantidade_total, quantidade_por_unidade
        )
        SELECT
            item, quantidade, estoque_ideal, carrinho, unidade, quantidade_total, quantidade_por_unidade
        FROM estoque_geral_old;
    """)

    # 4) Deletar tabela antiga
    db.execute("DROP TABLE estoque_geral_old;")

    # 5) Recriar índice
    db.execute("""
        CREATE INDEX IF NOT EXISTS ix_estoque_geral_item
        ON estoque_geral(item);
    """)

    # 6) Conferir contagem
    row = db.execute("SELECT COUNT(*) AS n FROM estoque_geral;")[0]
    n_new = row["n"]

    if n_new != n_orig:
        raise RuntimeError(f"Contagem divergente: original={n_orig}, novo={n_new}")

    db.execute("COMMIT;")
    print("[OK] Migração concluída com sucesso.")
    print(f"[OK] Linhas migradas: {n_new}")
    print("[OK] IDs antigos descartados. IDs novos criados automaticamente.")

except Exception as e:
    print("[ERRO] Falha na migração. Revertendo alterações.")
    print("Motivo:", e)
    db.execute("ROLLBACK;")

finally:
    db.execute("PRAGMA foreign_keys = ON;")
    print("[INFO] PRAGMA foreign_keys restaurado.")


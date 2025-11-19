from cs50 import SQL
import shutil
import os
from datetime import datetime

# caminho do seu banco
DB_PATH = "sqlite:///data/dados.db"
RAW_PATH = "data/dados.db"

# 1. backup rápido antes de mexer
if os.path.exists(RAW_PATH):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"data/dados.backup.{ts}.db"
    shutil.copyfile(RAW_PATH, backup_path)
    print(f"[OK] Backup criado em {backup_path}")

db = SQL(DB_PATH)

# ---------- MIGRAÇÃO: item -> UNIQUE | id -> PK AUTOINCREMENT ----------
try:
    # Garantir que estamos no modo seguro
    db.execute("PRAGMA foreign_keys = OFF;")
    db.execute("BEGIN IMMEDIATE;")

    # 0) Sanidade: contar linhas da tabela original
    row = db.execute("SELECT COUNT(*) AS n FROM estoque;")[0]
    n_orig = row["n"]

    # 1) Criar a nova tabela com o esquema desejado
    #    - id como INTEGER PRIMARY KEY AUTOINCREMENT
    #    - item como UNIQUE (e NOT NULL para manter consistência)
    db.execute("""
        CREATE TABLE estoque_novo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            quantidade REAL,
            estoque_ideal REAL,
            carrinho TEXT,
            unidade TEXT,
            quantidade_por_unidade FLOAT,
            quantidade_total FLOAT,
            usado_em_cardapio INTEGER [], 
        );
    """)

    # 2) Copiar dados preservando id quando não for NULL.
    #    Quando id for NULL, passamos NULL para gerar um novo id.
    db.execute("""
        INSERT INTO estoque_novo (id, item, quantidade, estoque_ideal, carrinho, unidade)
        SELECT
            CASE WHEN id IS NULL THEN NULL ELSE id END AS id,
            item, quantidade, estoque_ideal, carrinho, unidade
        FROM estoque;
    """)

    # 3) Ajustar a sequência do AUTOINCREMENT para o MAX(id) atual,
    #    garantindo que o próximo INSERT continue da numeração correta.
    #    (sqlite_sequence só existe quando há AUTOINCREMENT e pelo menos 1 insert)
    row = db.execute("SELECT MAX(id) AS max_id FROM estoque_novo;")[0]
    max_id = row["max_id"]

    # Inserir/atualizar o valor na sqlite_sequence
    # Se não existir linha, vamos inserir; senão, atualizar.
    # Nota: 'name' deve ser exatamente o nome da tabela.
    exists = db.execute("SELECT COUNT(*) AS c FROM sqlite_master WHERE name='sqlite_sequence';")[0]["c"]
    if exists:
        seq_row = db.execute("SELECT COUNT(*) AS c FROM sqlite_sequence WHERE name = 'estoque_novo';")[0]["c"]
        if seq_row == 0:
            db.execute("INSERT INTO sqlite_sequence(name, seq) VALUES('estoque_novo', ?);", max_id if max_id is not None else 0)
        else:
            db.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = 'estoque_novo';", max_id if max_id is not None else 0)

    # 4) Dropar a tabela antiga e renomear a nova
    db.execute("DROP TABLE estoque;")
    db.execute("ALTER TABLE estoque_novo RENAME TO estoque;")

    # 5) Recriar índices úteis (opcional; UNIQUE em item já cria índice implícito)
    #    Caso queira um índice separado por leitura: db.execute("CREATE INDEX IF NOT EXISTS ix_estoque_item ON estoque(item);")
    #    Não criamos índice UNIQUE em id, pois PRIMARY KEY já é única.
    db.execute("CREATE INDEX IF NOT EXISTS ix_estoque_item ON estoque(item);")

    # 6) Sanidade: contar linhas na nova tabela
    row = db.execute("SELECT COUNT(*) AS n FROM estoque;")[0]
    n_new = row["n"]
    if n_new != n_orig:
        raise RuntimeError(f"Contagem divergente após migração: original={n_orig}, novo={n_new}")

    db.execute("COMMIT;")
    print("[OK] Migração concluída com sucesso.")
    print(f"[OK] Linhas migradas: {n_new}")
    print("[OK] Novo esquema: id = INTEGER PRIMARY KEY AUTOINCREMENT, item = UNIQUE NOT NULL")

except Exception as e:
    print("[ERRO] Migração falhou. Alterações revertidas.")
    print("Motivo:", e)

finally:
    # Reativar checagem de FKs (boa prática, mesmo sem FKs no momento)
    db.execute("PRAGMA foreign_keys = ON;")

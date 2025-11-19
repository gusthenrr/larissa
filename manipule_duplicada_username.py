# -*- coding: utf-8 -*-
from cs50 import SQL
import os
import shutil
from datetime import datetime

# Caminho do banco
DB_PATH = "sqlite:///data/dados.db"
RAW_PATH = "/data/dados.db"

# 1) Backup rápido antes de mexer
if os.path.exists(RAW_PATH):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"/data/dados.usuarios.backup.{ts}.db"
    shutil.copyfile(RAW_PATH, backup_path)
    print(f"[OK] Backup criado em {backup_path}")
else:
    print("[AVISO] Arquivo de banco não encontrado em", RAW_PATH)

DATABASE_PATH = "/data/dados.db"
if not os.path.exists(DATABASE_PATH):
    shutil.copy("dados.db", DATABASE_PATH)
db = SQL("sqlite:///" + DATABASE_PATH)

# 2) Mostrar quantos registros existem antes
total_antes = db.execute("SELECT COUNT(*) AS n FROM usuarios")[0]["n"]
print(f"Registros em usuarios (antes): {total_antes}")

# 3) Apagar duplicados mantendo SEMPRE o mais novo (maior id)
#    - Para cada username, mantemos o registro com MAX(id)
#    - Todos os outros ids para aquele username serão apagados
print("[INFO] Removendo duplicados de username, mantendo o mais recente (maior id)...")

db.execute("""
    DELETE FROM usuarios
    WHERE id NOT IN (
        SELECT MAX(id)
        FROM usuarios
        GROUP BY username
    )
""")

# 4) Mostrar quantos registros ficaram depois da limpeza
total_depois = db.execute("SELECT COUNT(*) AS n FROM usuarios")[0]["n"]
print(f"Registros em usuarios (depois): {total_depois}")
print(f"[OK] Removidos {total_antes - total_depois} registros duplicados.")

# 5) Criar índice UNIQUE no username para não deixar repetir mais
print("[INFO] Criando índice UNIQUE em usuarios.username...")

db.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_username
    ON usuarios(username)
""")

print("[OK] Índice UNIQUE criado. Agora username não pode mais repetir.")


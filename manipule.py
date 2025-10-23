#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
manipule.py
Executa a migração das opções do cardápio imediatamente (sem CLI e sem if __main__).
- Converte formato legado:  Tamanho(300g-500g+18-1kg+65)Adicionais(cheddar e bacon+20-cebola empanada+17)
- Para formato JSON canônico:
  [
    {"nome":"Adicionais","ids":"","options":[{"nome":"cebola empanada","valor_extra":15.0,"esgotado":0}, ...],
     "max_selected":1,"obrigatorio":1},
    {"nome":"Tamanho","ids":"","options":[{"nome":"1kg","valor_extra":65.0,"esgotado":0}, ...],
     "max_selected":1,"obrigatorio":1}
  ]
"""

import os
import re
import json
import sqlite3
import sys
import unicodedata
import datetime as _dt
import ast
from typing import Any, Dict, List, Tuple

# ========================= CONFIG =========================
DB_PATH = "/data/dados.db"   # caminho fixo solicitado

# Ordem preferida dos grupos no JSON final (deixe [] para manter a ordem original)
PREFERRED_GROUP_ORDER = ["Adicionais", "Tamanho"]

# Defaults por grupo:
DEFAULT_OBRIGATORIO = 1
DEFAULT_MAX_SELECTED = 1
DEFAULT_IDS = ""

# Overrides opcionais: { (grupo_slug, opcao_slug): esgotado(0/1) }
ESGOTADO_OVERRIDES: Dict[Tuple[str, str], int] = {
    # ("tamanho","1kg"): 1,
}

# ========================= UTILS =========================
def now_iso() -> str:
    return _dt.datetime.now().replace(microsecond=0).isoformat()

def slugify(text: str) -> str:
    s = str(text or "").strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s

def to_float(s: Any, default: float = 0.0) -> float:
    try:
        return float(str(s).strip().replace(",", "."))
    except Exception:
        return float(default)

def is_jsonish(text: Any) -> bool:
    if text is None:
        return False
    s = str(text).strip()
    return s.startswith("[") or s.startswith("{")

# ========================= PARSE LEGADO =========================
# Ex.: "NomeGrupo(op1-op2+19.9-op3)OutroGrupo(x+y+1-z)"
GROUP_RE = re.compile(r"([^(]+)\(([^)]*)\)")

def parse_legacy(text: str) -> List[Dict[str, Any]]:
    """
    Converte string legado em lista de grupos canônicos.
    Cada bloco é "Nome(...)" e dentro de (...) temos tokens separados por '-'.
    Token pode ser "nome" ou "nome+valor".
    """
    groups: List[Dict[str, Any]] = []
    if not text:
        return groups

    for m in GROUP_RE.finditer(str(text)):
        group_name = (m.group(1) or "").strip()
        inside = (m.group(2) or "").strip()
        if not group_name:
            continue

        options = []
        if inside:
            tokens = [t for t in inside.split("-") if t.strip()]
            for tok in tokens:
                m2 = re.match(r"^\s*([^\+]+?)(?:\+([0-9]+(?:[.,][0-9]+)?))?\s*$", tok)
                if not m2:
                    continue
                name = re.sub(r"\s+", " ", (m2.group(1) or "").strip())
                val = to_float(m2.group(2) or 0.0, 0.0)

                grp_slug = slugify(group_name)
                opt_slug = slugify(name)
                esg = ESGOTADO_OVERRIDES.get((grp_slug, opt_slug), 0)

                options.append({
                    "nome": name,
                    "valor_extra": float(val),
                    "esgotado": int(esg),
                })

        groups.append({
            "nome": group_name,
            "ids": DEFAULT_IDS,
            "options": options,
            "max_selected": DEFAULT_MAX_SELECTED,
            "obrigatorio": DEFAULT_OBRIGATORIO,
        })

    if PREFERRED_GROUP_ORDER:
        index = {n: i for i, n in enumerate(PREFERRED_GROUP_ORDER)}
        groups.sort(key=lambda g: index.get(g["nome"], 10_000))
    return groups

def canonicalize_from_json(obj: Any) -> List[Dict[str, Any]]:
    """
    Normaliza um objeto já-JSON (dict/list) para a forma canônica.
    """
    groups: List[Dict[str, Any]] = []
    if isinstance(obj, dict):
        obj = [obj]
    if not isinstance(obj, list):
        return groups

    for g in obj:
        if not isinstance(g, dict):
            continue
        nome = str(g.get("nome") or g.get("Nome") or "Opções").strip()
        ids = str(g.get("ids") or DEFAULT_IDS).strip()

        obrig_raw = g.get("obrigatorio", DEFAULT_OBRIGATORIO)
        try:
            obrig = 1 if str(obrig_raw).strip().lower() in ("1", "true", "sim", "yes", "y") else 0
        except Exception:
            obrig = DEFAULT_OBRIGATORIO

        max_sel_raw = g.get("max_selected", DEFAULT_MAX_SELECTED)
        try:
            max_sel = int(max_sel_raw) if int(max_sel_raw) > 0 else DEFAULT_MAX_SELECTED
        except Exception:
            max_sel = DEFAULT_MAX_SELECTED

        raw_opts = g.get("options") or g.get("opcoes") or []
        if not isinstance(raw_opts, list):
            raw_opts = []

        options = []
        for o in raw_opts:
            if isinstance(o, str):
                name = re.sub(r"\s+", " ", o.strip())
                val = 0.0
                esg = 0
            elif isinstance(o, dict):
                name = re.sub(r"\s+", " ", str(o.get("nome") or "").strip())
                val = to_float(o.get("valor_extra") or 0.0, 0.0)
                esg_raw = o.get("esgotado", 0)
                try:
                    esg = 1 if str(esg_raw).strip().lower() in ("1", "true", "sim", "yes", "y") else 0
                except Exception:
                    esg = 0
            else:
                continue

            grp_slug = slugify(nome)
            opt_slug = slugify(name)
            esg = ESGOTADO_OVERRIDES.get((grp_slug, opt_slug), esg)

            options.append({
                "nome": name,
                "valor_extra": float(val),
                "esgotado": int(esg),
            })

        groups.append({
            "nome": nome,
            "ids": ids,
            "options": options,
            "max_selected": int(max_sel),
            "obrigatorio": int(obrig),
        })

    if PREFERRED_GROUP_ORDER:
        index = {n: i for i, n in enumerate(PREFERRED_GROUP_ORDER)}
        groups.sort(key=lambda g: index.get(g["nome"], 10_000))
    return groups

# ========================= DB HELPERS =========================
def connect_db(path: str) -> sqlite3.Connection:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Banco não encontrado em: {path}")
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    return con

def table_exists(con: sqlite3.Connection, name: str) -> bool:
    cur = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?;", (name,))
    return cur.fetchone() is not None

def ensure_opcoes_table(con: sqlite3.Connection):
    con.execute("""
        CREATE TABLE IF NOT EXISTS opcoes(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          id_cardapio INTEGER,
          item TEXT,
          nome_grupo TEXT,
          opcao TEXT,
          valor_extra REAL,
          esgotado_bool INTEGER,
          grupo_slug TEXT,
          opcao_slug TEXT,
          updated_at TEXT
        )
    """)

def clear_opcoes_for_cardapio(con: sqlite3.Connection, cid: int):
    con.execute("DELETE FROM opcoes WHERE id_cardapio = ?;", (cid,))

def insert_opcao(con: sqlite3.Connection, row: Dict[str, Any]):
    con.execute(
        """INSERT INTO opcoes
           (id_cardapio, item, nome_grupo, opcao, valor_extra, esgotado_bool, grupo_slug, opcao_slug, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""",
        (
            row["id_cardapio"], row["item"], row["nome_grupo"], row["opcao"],
            row["valor_extra"], row["esgotado_bool"], row["grupo_slug"], row["opcao_slug"], row["updated_at"]
        )
    )

def backup_cardapio(con: sqlite3.Connection) -> str:
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"cardapio_backup_{ts}"
    con.execute(f"CREATE TABLE {name} AS SELECT * FROM cardapio;")
    return name

# ========================= MIGRAÇÃO =========================
def migrate_apply() -> None:
    con = connect_db(DB_PATH)
    try:
        if not table_exists(con, "cardapio"):
            raise RuntimeError("Tabela 'cardapio' não existe no banco.")

        backup_name = backup_cardapio(con)
        print(f"[backup] Tabela clonada para '{backup_name}'")

        ensure_opcoes_table(con)

        cur = con.execute("SELECT id, item, opcoes FROM cardapio;")
        rows = cur.fetchall()

        total = len(rows)
        updated = 0
        skipped = 0
        inserted_opcoes = 0

        con.execute("BEGIN;")

        for r in rows:
            cid = r["id"]
            item = (r["item"] or "").strip()
            raw = r["opcoes"]

            # 1) Parse/normalize
            if raw and is_jsonish(raw):
                obj = None
                try:
                    obj = json.loads(raw)
                except Exception:
                    try:
                        obj = ast.literal_eval(raw)
                    except Exception:
                        obj = []
                groups = canonicalize_from_json(obj)
            else:
                groups = parse_legacy(raw)

            if not groups:
                skipped += 1
                continue

            # 2) JSON canônico compacto
            canon_json = json.dumps(groups, ensure_ascii=False, separators=(",", ":"))

            con.execute("UPDATE cardapio SET opcoes = ? WHERE id = ?;", (canon_json, cid))
            updated += 1

            # 3) (Re)popular tabela opcoes
            clear_opcoes_for_cardapio(con, cid)
            now = now_iso()
            for g in groups:
                gname = g["nome"]
                gslug = slugify(gname)
                for o in (g.get("options") or []):
                    oname = o["nome"]
                    oslug = slugify(oname)
                    val = float(o.get("valor_extra") or 0.0)
                    esg = int(o.get("esgotado") or 0)
                    insert_opcao(con, {
                        "id_cardapio": cid,
                        "item": item,
                        "nome_grupo": gname,
                        "opcao": oname,
                        "valor_extra": val,
                        "esgotado_bool": esg,
                        "grupo_slug": gslug,
                        "opcao_slug": oslug,
                        "updated_at": now
                    })
                    inserted_opcoes += 1

        con.execute("COMMIT;")

        print(f"[ok] banco: {DB_PATH}")
        print(f"[ok] cardapio lidos: {total}")
        print(f"[ok] cardapio atualizados: {updated}")
        print(f"[ok] linhas inseridas em opcoes: {inserted_opcoes}")
        print(f"[ok] registros sem mudança/pulados: {skipped}")

    except Exception as e:
        try:
            con.execute("ROLLBACK;")
        except Exception:
            pass
        print("[erro] migração falhou:", repr(e))
        sys.exit(1)
    finally:
        con.close()

# ========================= EXECUÇÃO IMEDIATA =========================
# ATENÇÃO: sem guard; roda ao importar/rodar como subprocess.
migrate_apply()

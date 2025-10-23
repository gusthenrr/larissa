# scripts/migrar_opcoes.py
from cs50 import SQL
import os, re, json, unicodedata, datetime

# ========================= CONFIG =========================

DRY_RUN = False  # True = só mostra o que faria; False = aplica no banco

# Se quiser forçar algum "esgotado" por regra, mapeie aqui (opcional):
# chave: (grupo_slug, opcao_slug) -> esgotado (0/1)
ESGOTADO_OVERRIDES = {
    # ("tamanho", "1kg"): 1,   # exemplo: marca 1kg como esgotado
}


# obrigatorio e max_selected padrão por grupo
DEFAULT_OBRIGATORIO = 1
DEFAULT_MAX_SELECTED = 1

# ========================= UTILS =========================
def now_iso():
    return datetime.datetime.now().replace(microsecond=0).isoformat()

def to_float(s, default=0.0):
    if s is None:
        return float(default)
    try:
        s = str(s).strip().replace(",", ".")
        return float(s)
    except Exception:
        return float(default)

def slugify(text):
    s = str(text or "").strip().lower()
    # remove acentos
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    # troca qualquer coisa não alfanumérica por "-"
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s

def is_jsonish(text):
    if text is None:
        return False
    s = str(text).strip()
    return s.startswith("[") or s.startswith("{")

# ========================= PARSER LEGADO =========================
GROUP_RE = re.compile(r"([^(]+)\(([^)]*)\)")

def parse_legacy_group_block(text):
    """
    Recebe string no formato legado e retorna lista de grupos:
    [
      { "nome": "...", "ids": "", "options": [ {nome, valor_extra, esgotado}, ...], "max_selected": 1, "obrigatorio": 1 },
      ...
    ]
    """
    result = []
    if not text:
        return result

    # encontra todos os blocos Nome( ... ) em sequência
    for m in GROUP_RE.finditer(str(text)):
        group_name = (m.group(1) or "").strip()
        inside = (m.group(2) or "").strip()
        if not group_name:
            continue

        options = []
        if inside:
            # divide por "-" (cada token é uma opção)
            tokens = [t for t in inside.split("-") if t.strip()]
            for tok in tokens:
                # padrão: "nome" ou "nome+valor"
                m2 = re.match(r"^\s*([^\+]+?)(?:\+([0-9]+(?:[.,][0-9]+)?))?\s*$", tok)
                if not m2:
                    continue
                name = (m2.group(1) or "").strip()
                val = to_float(m2.group(2) or 0, 0.0)
                opt_slug = slugify(name)
                grp_slug = slugify(group_name)
                # aplica override opcional de esgotado
                esgotado = ESGOTADO_OVERRIDES.get((grp_slug, opt_slug), 0)
                options.append({
                    "nome": name,
                    "valor_extra": val,
                    "esgotado": int(esgotado),
                })

        result.append({
            "nome": group_name,
            "ids": "",
            "options": options,
            "max_selected": DEFAULT_MAX_SELECTED,
            "obrigatorio": DEFAULT_OBRIGATORIO,
        })
    return result

def canonicalize_json_groups(obj):
    """
    Recebe um obj (list/dict) vindo de JSON e devolve no formato canônico:
    [
      { nome, ids:"", options:[{nome,valor_extra,esgotado:int}], max_selected:int, obrigatorio:int },
      ...
    ]
    """
    groups = []
    if isinstance(obj, dict):
        obj = [obj]
    if not isinstance(obj, list):
        return groups

    for g in obj:
        if not isinstance(g, dict):
            continue
        nome = str(g.get("nome") or g.get("Nome") or "Opções").strip()
        ids = str(g.get("ids") or "").strip()
        obrig = g.get("obrigatorio", DEFAULT_OBRIGATORIO)
        try:
            obrig = 1 if str(obrig).strip().lower() in ("1", "true", "sim", "yes", "y") else 0
        except Exception:
            obrig = DEFAULT_OBRIGATORIO
        max_sel = g.get("max_selected", DEFAULT_MAX_SELECTED)
        try:
            max_sel = int(max_sel) if int(max_sel) > 0 else DEFAULT_MAX_SELECTED
        except Exception:
            max_sel = DEFAULT_MAX_SELECTED

        raw_opts = g.get("options") or g.get("opcoes") or []
        if not isinstance(raw_opts, list):
            raw_opts = []

        options = []
        for o in raw_opts:
            if isinstance(o, str):
                name = o.strip()
                val = 0.0
                # string simples, sem esgotado no legado
                esg = 0
            elif isinstance(o, dict):
                name = str(o.get("nome") or "").strip()
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
            # override opcional:
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
    return groups

# ========================= DB HELPERS =========================
def ensure_opcoes_table(db: SQL):
    db.execute("""
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

def upsert_row_opcoes(db: SQL, row):
    """
    Insere linha na tabela opcoes. Se quiser evitar duplicatas,
    pode fazer DELETE ON CONFLICT com UNIQUE, mas como a tabela
    está vazia, só insert simples já resolve.
    """
    db.execute(
        """INSERT INTO opcoes
           (id_cardapio, item, nome_grupo, opcao, valor_extra, esgotado_bool, grupo_slug, opcao_slug, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        row["id_cardapio"], row["item"], row["nome_grupo"], row["opcao"],
        row["valor_extra"], row["esgotado_bool"], row["grupo_slug"], row["opcao_slug"], row["updated_at"]
    )

def clear_opcoes_for_cardapio(db: SQL, id_cardapio: int):
    db.execute("DELETE FROM opcoes WHERE id_cardapio = ?", id_cardapio)

# ========================= MAIN =========================
def main():
    var = True
    if var:
        DATABASE_PATH = "/data/dados.db"
        db = SQL("sqlite:///" + DATABASE_PATH)
        
    else:
        db = SQL('sqlite:///data/dados.db')
    ensure_opcoes_table(db)

    # pega colunas relevantes
    rows = db.execute("SELECT id, item, opcoes FROM cardapio")
    total = len(rows)
    updated_cardapio = 0
    inserted_opcoes = 0
    skipped = 0

    for r in rows:
        cid = r["id"]
        item = r.get("item") or ""
        raw = r.get("opcoes")

        # 1) Detecta e normaliza
        groups = []
        if raw and is_jsonish(raw):
            try:
                obj = json.loads(raw)
            except Exception:
                # às vezes vem com aspas simples
                try:
                    obj = json.loads(str(raw).replace("'", '"'))
                except Exception:
                    obj = []
            groups = canonicalize_json_groups(obj)
        else:
            # legado "Nome(... )Nome(... )"
            groups = parse_legacy_group_block(raw)

        # se não achar nada, pula
        if not groups:
            skipped += 1
            continue

        # 2) monta JSON canônico (compacto e estável)
        canon_json = json.dumps(groups, ensure_ascii=False, separators=(",", ":"))

        # 3) Atualiza cardapio.opcoes
        if not DRY_RUN:
            db.execute("UPDATE cardapio SET opcoes = ? WHERE id = ?", canon_json, cid)
        updated_cardapio += 1

        # 4) (Re)popula tabela opcoes para esse item
        if not DRY_RUN:
            clear_opcoes_for_cardapio(db, cid)

        now = now_iso()
        for g in groups:
            nome_grupo = g["nome"]
            grp_slug = slugify(nome_grupo)
            for o in (g.get("options") or []):
                opcao_nome = o["nome"]
                opcao_slug = slugify(opcao_nome)
                valor_extra = float(o.get("valor_extra") or 0.0)
                esgotado = int(o.get("esgotado") or 0)
                row_op = {
                    "id_cardapio": cid,
                    "item": item,
                    "nome_grupo": nome_grupo,
                    "opcao": opcao_nome,
                    "valor_extra": valor_extra,
                    "esgotado_bool": esgotado,
                    "grupo_slug": grp_slug,
                    "opcao_slug": opcao_slug,
                    "updated_at": now
                }
                if not DRY_RUN:
                    upsert_row_opcoes(db, row_op)
                inserted_opcoes += 1

    print(f"[OK] cardapio lidos: {total}")
    print(f"[OK] cardapio atualizados: {updated_cardapio}")
    print(f"[OK] linhas inseridas em opcoes: {inserted_opcoes}")
    print(f"[OK] sem mudança/pulados: {skipped}")
    if DRY_RUN:
        print("[DRY RUN] Nada foi gravado. Altere DRY_RUN=False para aplicar.")

if __name__ == "__main__":
    main()








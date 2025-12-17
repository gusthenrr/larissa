from cs50 import SQL
import shutil
import os

# Configuração do caminho do banco de dados (mantida a original)
var = True
if var:
    DATABASE_PATH = "/data/dados.db"
    if not os.path.exists(DATABASE_PATH):
        shutil.copy("dados.db", DATABASE_PATH)
    db = SQL("sqlite:///" + DATABASE_PATH)
else:
    DATABASE_PATH = "data/dados.db"
    db = SQL("sqlite:///" + DATABASE_PATH)

# --- INÍCIO DA FUNÇÃO MODIFICADA ---

def migrar_estoque_geral_para_reserva():
    # 1) Definir as colunas de reserva necessárias
    required_cols = [
        ("quantidade_reserva", "REAL"),             # Seu tipo 'real'
        ("estoque_ideal_reserva", "REAL"),          # Seu tipo 'real'
        ("quantidade_total_reserva", "FLOAT"),      # Seu tipo 'float'
    ]

    # 2) Verificar e Adicionar colunas se necessário
    print("Verificando a estrutura da tabela 'estoque'...")
    for col_name, col_type in required_cols:
        # Verifica se a coluna já existe
        info = db.execute("SELECT name FROM pragma_table_info('estoque') WHERE name = ?", col_name)

        if not info:
            # Coluna NÃO existe, então adiciona
            print(f"-> Coluna '{col_name}' não encontrada. Adicionando como {col_type}...")
            
            # Comando SQL para adicionar a coluna com o tipo especificado
            try:
                db.execute(f"ALTER TABLE estoque ADD COLUMN {col_name} {col_type} DEFAULT 0")
                print(f"   SUCESSO: Coluna '{col_name}' adicionada.")
            except Exception as e:
                print(f"   ERRO ao adicionar coluna '{col_name}': {e}")
                # Se falhar ao adicionar, interrompe a migração.
                return
        else:
            print(f"-> Coluna '{col_name}' já existe. Prosseguindo.")

    # 3) O restante da migração de dados (que estava no seu código original)
    # ... (O CÓDIGO RESTANTE ABAIXO É O MESMO QUE O SEU, AGORA GARANTIDO QUE FUNCIONARÁ)
    
    # Buscar dados da tabela estoque_geral
    rows = db.execute(
        """
        SELECT
            item,
            carrinho,
            quantidade,
            estoque_ideal,
            quantidade_total,
            unidade,
            quantidade_por_unidade,
            usado_em_cardapio
        FROM estoque_geral
        """
    )

    print(f"\nEncontradas {len(rows)} linhas em estoque_geral para migrar...")

    atualizados = 0
    criados = 0
    ignorados = 0

    for row in rows:
        item = row["item"]
        carrinho = row["carrinho"]

        # garante que zeros sejam inseridos mesmo assim (só troca None por 0)
        quantidade = row["quantidade"] if row["quantidade"] is not None else 0
        estoque_ideal = row["estoque_ideal"] if row["estoque_ideal"] is not None else 0
        quantidade_total = (
            row["quantidade_total"] if row["quantidade_total"] is not None else 0
        )

        unidade = row.get("unidade")
        quantidade_por_unidade = row.get("quantidade_por_unidade")
        usado_em_cardapio_id = row.get("usado_em_cardapio")

        if not item:
            # sem nome de item não dá pra usar, continua ignorando
            ignorados += 1
            continue

        # Verifica se existe o mesmo item+carrinho na tabela estoque
        existe = db.execute(
            "SELECT id FROM estoque WHERE item = ? AND carrinho = ? LIMIT 1",
            item,
            carrinho,
        )

        if not existe:
            # 3a) NÃO existe em estoque -> criar linha nova em estoque
            db.execute(
                """
                INSERT INTO estoque (
                    item,
                    carrinho,
                    unidade,
                    quantidade,
                    estoque_ideal,
                    quantidade_total,
                    quantidade_reserva,
                    estoque_ideal_reserva,
                    quantidade_total_reserva,
                    quantidade_por_unidade,
                    usado_em_cardapio
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                item,
                carrinho,
                unidade,
                0,  # quantidade "normal" começa em 0
                0,  # estoque_ideal "normal" começa em 0
                0,  # quantidade_total "normal" começa em 0
                quantidade,         # RESERVA recebe o valor do estoque_geral
                estoque_ideal,      # idem
                quantidade_total,   # idem
                quantidade_por_unidade,
                usado_em_cardapio_id,
            )
            criados += 1
        else:
            # 3b) Já existe em estoque -> apenas atualizar colunas de reserva
            db.execute(
                """
                UPDATE estoque
                SET quantidade_reserva          = ?,
                    estoque_ideal_reserva       = ?,
                    quantidade_total_reserva    = ?
                WHERE item = ? AND carrinho = ?
                """,
                quantidade,
                estoque_ideal,
                quantidade_total,
                item,
                carrinho,
            )
            atualizados += 1

    # 4) ZERAR reservas de itens que existem em 'estoque' mas NÃO existem em 'estoque_geral'
    res = db.execute(
        """
        SELECT COUNT(*) AS n
        FROM estoque
        WHERE (item, carrinho) NOT IN (
            SELECT item, carrinho
            FROM estoque_geral
            WHERE item IS NOT NULL
        )
        """
    )
    zerados = res[0]["n"] if res else 0

    db.execute(
        """
        UPDATE estoque
        SET quantidade_reserva          = 0,
            estoque_ideal_reserva       = 0,
            quantidade_total_reserva    = 0
        WHERE (item, carrinho) NOT IN (
            SELECT item, carrinho
            FROM estoque_geral
            WHERE item IS NOT NULL
        )
        """
    )

    print("\n--- RESUMO DA MIGRAÇÃO ---")
    print(f"Linhas de 'estoque' ATUALIZADAS com dados de reserva: {atualizados}")
    print(f"Linhas de 'estoque' CRIADAS a partir de 'estoque_geral': {criados}")
    print(f"Linhas de 'estoque' com reserva ZERADA (sem correspondente em estoque_geral): {zerados}")
    print(f"Linhas de 'estoque_geral' ignoradas (sem item): {ignorados}")
    print("Migração concluída.")


if __name__ == "__main__":
    migrar_estoque_geral_para_reserva()

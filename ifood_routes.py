# ===================================================================
# BACKEND - Endpoints para Integração com iFood (Python + Flask)
# ===================================================================
# Este arquivo mostra como implementar os endpoints necessários
# para integração com iFood no seu servidor Flask
# ===================================================================

import time
import secrets
import logging
import threading
import shutil
import json
from datetime import datetime, timezone
from cs50 import SQL
import os

# Arquivo dentro do projeto (commitado no Git)
# Se o seu .db está em data/dados.db no projeto, use isso:
DB_SOURCE_PATH = os.path.join(os.path.dirname(__file__), "data", "dados.db")

# Caminho “oficial” dentro do container (Render)
DATABASE_PATH = "/data/dados.db"

# Se ainda não existir o /data/dados.db, copia do projeto
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
if not os.path.exists(DATABASE_PATH):
    if not os.path.exists(DB_SOURCE_PATH):
        raise RuntimeError(f"Banco de origem não encontrado em {DB_SOURCE_PATH}")
    shutil.copy(DB_SOURCE_PATH, DATABASE_PATH)
    print(f"Copiado {DB_SOURCE_PATH} -> {DATABASE_PATH}")

# Agora sim, abre o banco
db = SQL("sqlite:///" + DATABASE_PATH)


import requests
from flask import Blueprint, request, jsonify, Response
try:
    import zoneinfo
    TZ_SP = zoneinfo.ZoneInfo("America/Sao_Paulo")
except Exception:
    # fallback se não tiver zoneinfo (Python mais antigo)
    from datetime import timezone, timedelta
    TZ_SP = timezone(timedelta(hours=-3))

def _parse_created_at_sp(created_at: str):
    """
    Recebe o createdAt do iFood (geralmente algo como
    '2025-11-25T23:29:00.917Z' ou com offset) e devolve:
      - dt_br: datetime em America/Sao_Paulo
      - dia_br: string 'YYYY-MM-DD' no fuso de SP
    """
    if not created_at:
        return None, None

    s = created_at.strip()

    # Normaliza alguns formatos comuns do iFood:
    #  - termina com 'Z' (UTC)
    #  - pode vir com milissegundos
    #  - pode vir já com offset (-03:00)
    if s.endswith("Z"):
        # tira o 'Z' e deixa só a parte até os segundos/milisegundos
        s = s[:-1]  # remove o 'Z'
        dt = datetime.fromisoformat(s)
        # assume que isso é UTC
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = datetime.fromisoformat(s)
        # se vier sem tzinfo, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

    # converte pra São Paulo
    dt_br = dt.astimezone(TZ_SP)
    dia_br = dt_br.date().isoformat()
    return dt_br, dia_br

# Configurações (SUBSTITUA com suas credenciais)
IFOOD_CONFIG = {
    "clientId": "56e71065-d3cf-4e7c-bcef-cb9cd7331b23",
    "clientSecret": "109bvjgxv5ikvhry42u8z7v6ogqrwbaa9b8ehwsk5vna57cn76row3kph3344xp5j262kywkm745hwbcermdayffbzvbq87x1tdk",
    # Ambiente: 'sandbox' para testes, 'production' para produção
    "environment": "sandbox",
}

# URLs da API do iFood
IFOOD_API = {
    "sandbox": {
        "auth": "https://merchant-api.ifood.com.br/authentication/v1.0/oauth",
        "base": "https://merchant-api.ifood.com.br",
    },
    "production": {
        "auth": "https://merchant-api.ifood.com.br/authentication/v1.0/oauth",
        "base": "https://merchant-api.ifood.com.br",
    },
}


API = IFOOD_API[IFOOD_CONFIG["environment"]]

# ===================================================================
# LOGGING
# ===================================================================

logger = logging.getLogger(__name__)


# ===================================================================
# FUNÇÕES AUXILIARES
# ===================================================================

# ===================================================================
# FUNÇÕES AUXILIARES
# ===================================================================

def generateState() -> str:
    return secrets.token_hex(16)


def _safe_response_json(resp: requests.Response):
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


def request_user_code():
    """
    Gera userCode + authorizationCodeVerifier para aplicativo distribuído.
    POST /authentication/v1.0/oauth/userCode?clientId=...
    """
    url = f"{API['auth']}/userCode"
    params = {"clientId": IFOOD_CONFIG["clientId"]}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    resp = requests.post(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    return _safe_response_json(resp)

ifood_bp = Blueprint("ifood", __name__)

@ifood_bp.route("/ifood/user-code", methods=["POST"])
def ifood_user_code():
    """
    Início do fluxo de aplicativo distribuído.
    Gera userCode + authorizationCodeVerifier e devolve para o front.
    """
    try:
        body = _get_json_body()
        carrinho = body.get("carrinho")

        if not carrinho:
            return jsonify({"success": False, "message": "Carrinho não informado"})

        data = request_user_code()
        if "userCode" not in data:
            return jsonify({
                "success": False,
                "message": "Falha ao gerar userCode",
                "error": data,
            })

        _save_link_code(carrinho, data)

        return jsonify({
            "success": True,
            "userCode": data.get("userCode"),
            "verificationUrl": data.get("verificationUrl"),
            "verificationUrlComplete": data.get("verificationUrlComplete"),
            "expiresIn": data.get("expiresIn"),
        })
    except Exception as error:
        logger.exception("Erro ao gerar userCode do iFood")
        return jsonify({"success": False, "message": str(error)})



def _normalize_token_payload(payload: dict):
    """
    Normaliza possíveis formatos de resposta do /oauth/token.
    """
    if not isinstance(payload, dict):
        return {"access_token": None, "refresh_token": None, "expires_in": 0, "token_type": None}

    access_token = payload.get("accessToken") or payload.get("access_token")
    refresh_token = payload.get("refreshToken") or payload.get("refresh_token")
    expires_in = payload.get("expiresIn") or payload.get("expires_in") or 0
    token_type = payload.get("type") or payload.get("token_type")

    try:
        expires_in = int(expires_in)
    except Exception:
        expires_in = 0

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "token_type": token_type,
    }


def exchangeAuthorizationCodeForTokens(authorization_code: str, verifier: str):
    """
    Troca authorizationCode + authorizationCodeVerifier por accessToken/refreshToken
    (fluxo de aplicativo distribuído).
    """
    try:
        url = f"{API['auth']}/token"
        data = {
            "grantType": "authorization_code",
            "clientId": IFOOD_CONFIG["clientId"],
            "clientSecret": IFOOD_CONFIG["clientSecret"],
            "authorizationCode": authorization_code,
            "authorizationCodeVerifier": verifier,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        resp = requests.post(url, data=data, headers=headers, timeout=30)
        body = _safe_response_json(resp)

        if 200 <= resp.status_code < 300:
            norm = _normalize_token_payload(body)
            return {"success": True, "data": norm, "raw": body}
        else:
            logger.error("Erro ao trocar authorizationCode por tokens: %s", body)
            return {"success": False, "error": body}
    except Exception as error:
        logger.exception("Erro ao trocar authorizationCode por tokens")
        return {"success": False, "error": str(error)}


def refreshAccessToken(refreshToken: str):
    """
    Renova access token usando refresh token (grantType=refresh_token).
    """
    try:
        url = f"{API['auth']}/token"
        data = {
            "grantType": "refresh_token",
            "clientId": IFOOD_CONFIG["clientId"],
            "clientSecret": IFOOD_CONFIG["clientSecret"],
            "refreshToken": refreshToken,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        resp = requests.post(url, data=data, headers=headers, timeout=30)
        body = _safe_response_json(resp)

        if 200 <= resp.status_code < 300:
            norm = _normalize_token_payload(body)
            return {"success": True, "data": norm, "raw": body}
        else:
            logger.error("Erro ao renovar token: %s", body)
            return {"success": False, "error": body}
    except Exception as error:
        logger.exception("Erro ao renovar token")
        return {"success": False, "error": str(error)}



def getMerchantInfo(accessToken: str):
    """
    Busca informações do merchant (estabelecimento)
    """
    try:
        url = f"{API['base']}/merchant/v1.0/merchants"
        headers = {
            "Authorization": f"Bearer {accessToken}",
        }

        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code >= 200 and response.status_code < 300:
            return {
                "success": True,
                "data": _safe_response_json(response),
            }
        else:
            logger.error(
                "Erro ao buscar merchant: %s",
                _safe_response_json(response),
            )
            return {
                "success": False,
                "error": _safe_response_json(response),
            }
    except Exception as error:
        logger.exception("Erro ao buscar merchant")
        return {
            "success": False,
            "error": str(error),
        }


def fetchOrders(accessToken: str):
    """
    Busca novos pedidos (polling)
    """
    try:
        url = f"{API['base']}/order/v1.0/events:polling"
        headers = {
            "Authorization": f"Bearer {accessToken}",
        }

        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code >= 200 and response.status_code < 300:
            return {
                "success": True,
                "data": _safe_response_json(response),
            }
        else:
            logger.error(
                "Erro ao buscar pedidos: %s",
                _safe_response_json(response),
            )
            return {
                "success": False,
                "error": _safe_response_json(response),
            }
    except Exception as error:
        logger.exception("Erro ao buscar pedidos")
        return {
            "success": False,
            "error": str(error),
        }


def confirmOrder(accessToken: str, orderId: str):
    """
    Confirma pedido
    """
    try:
        url = f"{API['base']}/order/v1.0/orders/{orderId}/confirm"
        headers = {
            "Authorization": f"Bearer {accessToken}",
        }

        response = requests.post(url, json={}, headers=headers, timeout=30)
        if response.status_code >= 200 and response.status_code < 300:
            return {
                "success": True,
                "data": _safe_response_json(response),
            }
        else:
            logger.error(
                "Erro ao confirmar pedido: %s",
                _safe_response_json(response),
            )
            return {
                "success": False,
                "error": _safe_response_json(response),
            }
    except Exception as error:
        logger.exception("Erro ao confirmar pedido")
        return {
            "success": False,
            "error": str(error),
        }

def acknowledgeEvents(accessToken: str, events: list):
    """
    Manda um ACK pro iFood dizendo que os eventos foram recebidos,
    pra ele não ficar mandando o mesmo evento pra sempre.
    """
    try:
        if not events:
            return

        ids = [e.get("id") for e in events if e.get("id")]
        if not ids:
            return

        url = f"{API['base']}/order/v1.0/events/acknowledgment"
        headers = {
            "Authorization": f"Bearer {accessToken}",
            "Content-Type": "application/json",
        }

        resp = requests.post(url, json=ids, headers=headers, timeout=30)
        body = _safe_response_json(resp)
        if 200 <= resp.status_code < 300:
            logger.info("Eventos iFood reconhecidos (ACK): %s", ids)
        else:
            logger.error("Falha ao reconhecer eventos iFood: %s", body)
    except Exception:
        logger.exception("Erro ao reconhecer eventos iFood")

# ===================================================================
# "ROTAS EXPRESS" -> Blueprint do Flask
# ===================================================================



# Armazenamento temporário (em produção, use um banco de dados)
# authStates: state -> { "carrinho": str, "created_at": float }
authStates = {}

linkCodes = {}
# ifoodTokens: carrinho -> { accessToken, refreshToken, expiresAt, merchantId, storeName, autoAccept }
ifoodTokens = {}

STATE_TTL_SECONDS = 10 * 60  # 10 minutos
LINK_CODE_TTL_SECONDS = 10 * 60

def _insert_ifood_event_in_pedidos(carrinho: str, order_data: dict):
    """
    Converte um order_data do iFood em linhas na tabela 'pedidos'.
    Uma linha por item.

    Protegido contra duplicados: se já existir um pedido com o mesmo
    order_id + carrinho + extra='IFOOD', não insere de novo.
    """
    if not order_data:
        return

    order_id = order_data.get("id")
    if not order_id:
        return

    # --------- ANTI-DUPLICADO ---------
    # Se já existe qualquer linha desse order_id para esse carrinho, não insere de novo
    existing = db.execute(
        """
        SELECT id FROM pedidos
        WHERE order_id = ? AND carrinho = ? AND extra = 'IFOOD'
        LIMIT 1
        """,
        order_id,
        carrinho,
    )
    if existing:
        logger.info(
            "[IFOOD] Pedido %s (carrinho %s) já está na tabela 'pedidos'. Ignorando duplicado.",
            order_id,
            carrinho,
        )
        return
    # ----------------------------------

    display_id = order_data.get("displayId") or order_id
    order_timing = order_data.get("orderTiming")
    created_at = order_data.get("createdAt")  # ex: "2025-11-25T23:29:00.917Z"

    created_at_br = created_at  # default
    dia = None

    if created_at:
        try:
            dt_br, dia_br = _parse_created_at_sp(created_at)
            if dt_br is not None:
                created_at_br = dt_br.isoformat()
            if dia_br is not None:
                dia = dia_br
        except Exception as e:
            # loga pra você ver se vier algo muito estranho
            logger.exception("Falha ao converter createdAt=%r para fuso de SP: %s", created_at, e)
            # como último recurso, pega só a parte da data original (melhor que nada)
            dia = (created_at or "")[:10]


    # Cliente
    customer = (order_data.get("customer") or {})
    customer_name = customer.get("name")
    remetente = customer_name

    # Endereço de entrega (se for DELIVERY)
    delivery = order_data.get("delivery") or {}
    delivery_address = delivery.get("deliveryAddress") or {}
    endereco_entrega = delivery_address.get("formattedAddress")

    if not endereco_entrega and delivery_address:
        # monta um endereço simples se não tiver formattedAddress
        parts = [
            delivery_address.get("streetName"),
            delivery_address.get("streetNumber"),
            delivery_address.get("neighborhood"),
            delivery_address.get("city"),
            delivery_address.get("state"),
        ]
        endereco_entrega = ", ".join([p for p in parts if p])

    # Horário para entrega (se pedido agendado)
    schedule = order_data.get("schedule") or {}
    horario_para_entrega = schedule.get("deliveryDateTimeStart") or delivery.get("deliveryDateTime")

    categoria_pedido = order_data.get("category")

    items = order_data.get("items") or []

    # Se por algum motivo não vier item, ainda assim salva uma linha "resumo"
    if not items:
        db.execute(
            """
            INSERT INTO pedidos
            (comanda, pedido, quantidade, preco, inicio, fim, comecar, estado,
             extra, username, ordem, nome, dia, orderTiming, endereco_entrega,
             order_id, remetente, horario_para_entrega, categoria,
             preco_unitario, opcoes, carrinho)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            display_id,      # comanda
            None,            # pedido
            None,            # quantidade
            None,            # preco
            created_at_br,      # inicio
            None,            # fim
            None,            # comecar
            "ABERTO",        # estado
            "IFOOD",         # extra
            "IFOOD",         # username
            0,            # ordem
            customer_name,   # nome (cliente)
            dia,             # dia
            order_timing,    # orderTiming
            endereco_entrega,# endereco_entrega
            order_id,        # order_id
            remetente,       # remetente
            horario_para_entrega,  # horario_para_entrega
            categoria_pedido,      # categoria
            None,            # preco_unitario
            None,            # opcoes
            carrinho,        # carrinho
        )
        return

    # Uma linha por item
    for idx, item in enumerate(items):
        nome_item = item.get("name")
        id_integracao = item.get('id')
        quantidade = item.get("quantity") or 0
        unit_price = (
            item.get("unitPrice")
            or item.get("price")
            or 0
        )
        total_price = (
            item.get("totalPrice")
            or (unit_price * quantidade)
        )

        # Opções / adicionais em JSON
        options = item.get("options") or []
        try:
            opcoes_str = json.dumps(options, ensure_ascii=False)
        except Exception:
            opcoes_str = None
        id_integracao_str = str(id_integracao)

        rows = db.execute(
            """
            SELECT *
            FROM cardapio
            WHERE (',' || ids_integracoes || ',') LIKE '%,' || ? || ',%'
            """,
            id_integracao_str,
        )
        if not rows:
            db.execute(
                """
                INSERT INTO pedidos
                (pedido, quantidade, preco, inicio, fim, comecar, estado,
                extra, username, ordem, nome, dia, orderTiming, endereco_entrega,
                order_id, remetente, horario_para_entrega, categoria,
                preco_unitario, opcoes, id_integracao, carrinho)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                nome_item,               # pedido (nome do item)
                int(quantidade),         # quantidade
                float(total_price),      # preco (total do item)
                created_at_br,              # inicio
                None,                    # fim
                None,                    # comecar
                "ABERTO",                # estado
                "IFOOD",                 # extra
                "IFOOD",                 # username (quem "lançou" o pedido)
                0,                     # ordem (posição na lista de itens)
                customer_name,           # nome (cliente)
                dia,                     # dia
                order_timing,            # orderTiming
                endereco_entrega,        # endereco_entrega
                order_id,                # order_id
                remetente,               # remetente
                horario_para_entrega,    # horario_para_entrega
                categoria_pedido,        # categoria
                float(unit_price),       # preco_unitario
                opcoes_str,              # opcoes (JSON das opções do item)
                id_integracao_str,
                carrinho,                # carrinho
            )
        else:
            db.execute("""
                INSERT INTO pedidos
                (pedido, quantidade, preco, inicio, fim, comecar, estado,
                extra, username, ordem, nome, dia, orderTiming, endereco_entrega,
                order_id, remetente, horario_para_entrega, categoria,
                preco_unitario, opcoes, carrinho)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows['item'],               # pedido (nome do item)
                int(quantidade),         # quantidade
                float(total_price),      # preco (total do item)
                created_at_br,              # inicio
                None,                    # fim
                None,                    # comecar
                "ABERTO",                # estado
                "IFOOD",                 # extra
                "IFOOD",                 # username (quem "lançou" o pedido)
                0,                     # ordem (posição na lista de itens)
                customer_name,           # nome (cliente)
                dia,                     # dia
                order_timing,            # orderTiming
                endereco_entrega,        # endereco_entrega
                order_id,                # order_id
                remetente,               # remetente
                horario_para_entrega,    # horario_para_entrega
                categoria_pedido,        # categoria
                float(unit_price),       # preco_unitario
                opcoes_str,              # opcoes (JSON das opções do item)
                id_integracao_str,
                carrinho, )




def _save_link_code(carrinho: str, data: dict):
    expires_in = int(data.get("expiresIn", LINK_CODE_TTL_SECONDS))
    linkCodes[carrinho] = {
        "userCode": data.get("userCode"),
        "authorizationCodeVerifier": data.get("authorizationCodeVerifier"),
        "expiresAt": int(time.time() + expires_in),
    }


def _get_link_code(carrinho: str):
    entry = linkCodes.get(carrinho)
    if not entry:
        return None
    if time.time() > entry.get("expiresAt", 0):
        linkCodes.pop(carrinho, None)
        return None
    return entry


def _get_json_body():
    return request.get_json(silent=True) or {}


def _get_valid_state(state: str):
    """
    Retorna o carrinho se o state existir e não estiver expirado.
    Caso contrário, retorna None.
    """
    entry = authStates.get(state)
    if not entry:
        return None

    created_at = entry.get("created_at", 0)
    if time.time() - created_at > STATE_TTL_SECONDS:
        # expirou
        authStates.pop(state, None)
        return None

    return entry.get("carrinho")


# ===================================================================
# Endpoint: Obter URL de autenticação
# ===================================================================

@ifood_bp.route("/ifood/auth-url", methods=["POST"])
def ifood_auth_url():
    try:
        body = _get_json_body()
        carrinho = body.get("carrinho")

        if not carrinho:
            return jsonify({"success": False, "message": "Carrinho não informado"})

        state = generateState()
        authStates[state] = {
            "carrinho": carrinho,
            "created_at": time.time(),
        }

        authUrl = (
            f"{API['auth']}/authorize"
            f"?client_id={IFOOD_CONFIG['clientId']}"
            f"&response_type=code"
            f"&redirect_uri={IFOOD_CONFIG['redirectUri']}"
            f"&state={state}"
        )

        return jsonify(
            {
                "success": True,
                "authUrl": authUrl,
            }
        )
    except Exception as error:
        return jsonify({"success": False, "message": str(error)})


# ===================================================================
# Endpoint: Callback de autenticação
# ===================================================================

@ifood_bp.route("/ifood/activate", methods=["POST"])
def ifood_activate():
    """
    Recebe o authorizationCode (que o dono da loja recebeu no Portal do Parceiro),
    troca por accessToken/refreshToken e salva para o carrinho.
    """
    try:
        body = _get_json_body()
        carrinho = body.get("carrinho")
        authorization_code = body.get("authorizationCode")

        if not carrinho or not authorization_code:
            return jsonify({"success": False, "message": "Parâmetros inválidos"})

        link = _get_link_code(carrinho)
        if not link:
            return jsonify({
                "success": False,
                "message": "Código de vínculo expirado ou inexistente. Gere um novo userCode.",
            })

        verifier = link.get("authorizationCodeVerifier")
        token_resp = exchangeAuthorizationCodeForTokens(authorization_code, verifier)

        if not token_resp.get("success"):
            return jsonify({
                "success": False,
                "message": "Erro ao obter tokens de acesso",
                "error": token_resp.get("error"),
            })

        token_data = token_resp["data"]
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data["expires_in"]

        if not access_token:
            return jsonify({
                "success": False,
                "message": "Resposta do iFood não trouxe accessToken",
                "raw": token_resp.get("raw"),
            })

        # Buscar merchant / nome da loja
        merchantInfo = getMerchantInfo(access_token)
        merchantId = ""
        storeName = ""

        if merchantInfo.get("success") and isinstance(merchantInfo.get("data"), list) and merchantInfo["data"]:
            merchant = merchantInfo["data"][0]
            merchantId = merchant.get("id", "")
            storeName = merchant.get("name", "")

        ifoodTokens[carrinho] = {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresAt": int(time.time() + (expires_in or 0)),
            "merchantId": merchantId,
            "storeName": storeName,
            "autoAccept": False,
        }

        # descarta o userCode usado
        linkCodes.pop(carrinho, None)

        return jsonify({
            "success": True,
            "storeName": storeName,
            "merchantId": merchantId,
        })
    except Exception as error:
        logger.exception("Erro no /ifood/activate")
        return jsonify({"success": False, "message": str(error)})

def _get_access_token_for_carrinho(carrinho: str):
    tokenData = ifoodTokens.get(carrinho)
    if not tokenData:
        return None, "iFood não conectado"

    now = int(time.time())
    expires_at = int(tokenData.get("expiresAt", 0))

    # se estiver perto de expirar, tenta renovar
    if now >= expires_at - 60:
        rt = tokenData.get("refreshToken")
        if rt:
            refresh_resp = refreshAccessToken(rt)
            if refresh_resp.get("success"):
                new = refresh_resp["data"]
                tokenData["accessToken"] = new["access_token"] or tokenData["accessToken"]
                tokenData["refreshToken"] = new["refresh_token"] or rt
                tokenData["expiresAt"] = int(time.time() + (new["expires_in"] or 0))
                ifoodTokens[carrinho] = tokenData
            else:
                return None, "Falha ao renovar token do iFood"

    return tokenData.get("accessToken"), None

def getOrderDetails(accessToken: str, order_id: str):
    """
    Busca os detalhes completos de um pedido no módulo de Order.
    GET /order/v1.0/orders/{id}
    """
    try:
        url = f"{API['base']}/order/v1.0/orders/{order_id}"
        headers = {
            "Authorization": f"Bearer {accessToken}",
        }

        response = requests.get(url, headers=headers, timeout=30)
        if 200 <= response.status_code < 300:
            return {
                "success": True,
                "data": _safe_response_json(response),
            }
        else:
            logger.error(
                "Erro ao buscar detalhes do pedido %s: %s",
                order_id,
                _safe_response_json(response),
            )
            return {
                "success": False,
                "error": _safe_response_json(response),
            }
    except Exception as error:
        logger.exception("Erro ao buscar detalhes do pedido %s", order_id)
        return {
            "success": False,
            "error": str(error),
        }


def _poll_ifood_for_carrinho(carrinho: str):
    """
    Chama fetchOrders para um carrinho, pega o orderId de cada evento,
    busca os detalhes do pedido em /order/v1.0/orders/{id} e salva
    na tabela 'pedidos' via _insert_ifood_event_in_pedidos.

    Depois disso, manda ACK dos eventos pra não receber de novo.
    """
    # 1) pegar access_token válido (renova se estiver perto de expirar)
    access_token, err = _get_access_token_for_carrinho(carrinho)
    if not access_token:
        logger.debug("[IFOOD] Carrinho %s sem token ou erro: %s", carrinho, err)
        return

    # 2) buscar eventos (events:polling)
    resp = fetchOrders(access_token)
    if not resp.get("success"):
        logger.error("[IFOOD] Erro no fetchOrders para carrinho %s: %s", carrinho, resp.get("error"))
        return

    events = resp.get("data") or []

    # Alguns ambientes retornam {"events": [...]} em vez de lista direta
    if isinstance(events, dict) and "events" in events:
        events = events["events"]

    if not events:
        # sem eventos novos
        return

    logger.info("[IFOOD] %d evento(s) recebido(s) para carrinho %s", len(events), carrinho)

    for ev in events:
        logger.info("[IFOOD] Evento bruto recebido: %s", ev)

        # Só nos interessam os eventos de pedido colocado (PLC)
        if ev.get("code") != "PLC":
            continue

        # orderId vem do evento (não é o pedido completo ainda)
        order_id = ev.get("orderId")
        if not order_id:
            logger.warning("[IFOOD] Evento PLC sem orderId para carrinho %s: %s", carrinho, ev)
            continue

        # 3) Buscar detalhes completos do pedido
        order_resp = getOrderDetails(access_token, order_id)
        if not order_resp.get("success"):
            logger.error(
                "[IFOOD] Erro ao buscar detalhes do pedido %s (carrinho %s): %s",
                order_id,
                carrinho,
                order_resp.get("error"),
            )
            continue

        order_data = order_resp.get("data") or {}
        logger.info("[IFOOD] Detalhes do pedido %s: %s", order_id, order_data)

        # 4) Salvar no banco (tabela 'pedidos')
        try:
            _insert_ifood_event_in_pedidos(carrinho, order_data)
        except Exception as db_err:
            logger.exception(
                "[IFOOD] Erro ao inserir pedido %s no banco para carrinho %s: %s",
                order_id,
                carrinho,
                db_err,
            )

    # 5) Depois de processar TODOS os eventos, manda ACK pra limpar a fila
    try:
        acknowledgeEvents(access_token, events)
    except Exception:
        logger.exception("[IFOOD] Erro ao enviar ACK dos eventos para carrinho %s", carrinho)



# ===================================================================
# Endpoint: Verificar status de autenticação (polling do app)
# ===================================================================

@ifood_bp.route("/ifood/check-auth", methods=["POST"])
def ifood_check_auth():
    try:
        body = _get_json_body()
        carrinho = body.get("carrinho")

        if not carrinho:
            return jsonify({"authenticated": False})

        tokenData = ifoodTokens.get(carrinho)

        if not tokenData:
            return jsonify({"authenticated": False})

        return jsonify(
            {
                "authenticated": True,
                "storeName": tokenData.get("storeName"),
                "merchantId": tokenData.get("merchantId"),
            }
        )
    except Exception:
        return jsonify({"authenticated": False})


# ===================================================================
# Endpoint: Obter configurações do iFood
# ===================================================================

@ifood_bp.route("/ifood/settings", methods=["POST"])
def ifood_settings():
    try:
        body = _get_json_body()
        carrinho = body.get("carrinho")

        if not carrinho:
            return jsonify({"success": False, "message": "Carrinho não informado"})

        tokenData = ifoodTokens.get(carrinho)

        if not tokenData:
            return jsonify({"success": True, "connected": False})

        return jsonify(
            {
                "success": True,
                "connected": True,
                "storeName": tokenData.get("storeName"),
                "merchantId": tokenData.get("merchantId"),
                "autoAccept": tokenData.get("autoAccept", False),
            }
        )
    except Exception as error:
        return jsonify({"success": False, "message": str(error)})


# ===================================================================
# Endpoint: Atualizar configuração de auto-aceitar pedidos
# ===================================================================

@ifood_bp.route("/ifood/auto-accept", methods=["POST"])
def ifood_auto_accept():
    try:
        body = _get_json_body()
        carrinho = body.get("carrinho")
        autoAccept = body.get("autoAccept")

        if not carrinho:
            return jsonify({"success": False, "message": "Carrinho não informado"})

        tokenData = ifoodTokens.get(carrinho)

        if not tokenData:
            return jsonify({"success": False, "message": "iFood não conectado"})

        tokenData["autoAccept"] = bool(autoAccept)
        ifoodTokens[carrinho] = tokenData

        return jsonify({"success": True})
    except Exception as error:
        return jsonify({"success": False, "message": str(error)})


# ===================================================================
# Endpoint: Desconectar iFood
# ===================================================================

@ifood_bp.route("/ifood/disconnect", methods=["POST"])
def ifood_disconnect():
    try:
        body = _get_json_body()
        carrinho = body.get("carrinho")

        if not carrinho:
            return jsonify({"success": False, "message": "Carrinho não informado"})

        if carrinho in ifoodTokens:
            ifoodTokens.pop(carrinho, None)

        return jsonify({"success": True})
    except Exception as error:
        return jsonify({"success": False, "message": str(error)})


# ===================================================================
# Endpoint: Testar conexão com iFood
# ===================================================================

@ifood_bp.route("/ifood/test-connection", methods=["POST"])
def ifood_test_connection():
    try:
        body = _get_json_body()
        carrinho = body.get("carrinho")

        if not carrinho:
            return jsonify({"success": False, "message": "Carrinho não informado"})

        tokenData = ifoodTokens.get(carrinho)

        if not tokenData:
            return jsonify({"success": False, "message": "iFood não conectado"})

        merchantInfo = getMerchantInfo(tokenData.get("accessToken"))

        if merchantInfo.get("success"):
            return jsonify(
                {
                    "success": True,
                    "message": f"Conexão OK! Estabelecimento: {tokenData.get('storeName')}",
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "message": "Falha ao conectar com iFood. Token pode estar expirado.",
                }
            )
    except Exception as error:
        return jsonify({"success": False, "message": str(error)})


# ===================================================================
# Endpoint: Buscar novos pedidos do iFood
# ===================================================================

@ifood_bp.route("/ifood/fetch-orders", methods=["POST"])
def ifood_fetch_orders():
    try:
        body = _get_json_body()
        carrinho = body.get("carrinho")

        if not carrinho:
            return jsonify({"success": False, "message": "Carrinho não informado"})

        access_token, err = _get_access_token_for_carrinho(carrinho)
        if not access_token:
            return jsonify({"success": False, "message": err})

        ordersResponse = fetchOrders(access_token)

        if ordersResponse.get("success"):
            return jsonify({"success": True, "orders": ordersResponse.get("data")})
        else:
            return jsonify(
                {
                    "success": False,
                    "message": "Erro ao buscar pedidos",
                    "error": ordersResponse.get("error"),
                }
            )
    except Exception as error:
        return jsonify({"success": False, "message": str(error)})


# ===================================================================
# Endpoint: Confirmar pedido do iFood
# ===================================================================

@ifood_bp.route("/ifood/confirm-order", methods=["POST"])
def ifood_confirm_order():
    try:
        body = _get_json_body()
        carrinho = body.get("carrinho")
        orderId = body.get("orderId")

        if not carrinho or not orderId:
            return jsonify({"success": False, "message": "Parâmetros inválidos"})

        tokenData = ifoodTokens.get(carrinho)

        if not tokenData:
            return jsonify({"success": False, "message": "iFood não conectado"})

        confirmResponse = confirmOrder(tokenData.get("accessToken"), orderId)

        if confirmResponse.get("success"):
            return jsonify({"success": True})
        else:
            return jsonify(
                {
                    "success": False,
                    "message": "Erro ao confirmar pedido",
                    "error": confirmResponse.get("error"),
                }
            )
    except Exception as error:
        return jsonify({"success": False, "message": str(error)})


# ===================================================================
# "EXPORTAR" ROTAS (equivalente ao module.exports do Node)
# ===================================================================

# Para manter o espírito do module.exports:
router = ifood_bp  # você pode usar `router` ao registrar no app Flask
def start_ifood_polling():
    """
    Inicia uma thread em background que a cada 30s chama
    o events:polling para cada carrinho conectado ao iFood.
    """
    def _loop():
        while True:
            try:
                # copia as chaves pra não quebrar se o dict mudar no meio
                for carrinho in list(ifoodTokens.keys()):
                    _poll_ifood_for_carrinho(carrinho)
            except Exception:
                logger.exception("Erro no loop de polling do iFood")
            # espera 30 segundos entre as rodadas
            time.sleep(30)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    logger.info("Thread de polling do iFood iniciada.")

__all__ = [
    "ifood_bp",
    "router",
    "ifoodTokens",
    "fetchOrders",
    "confirmOrder",
    "start_ifood_polling",  # <- adiciona isto
]


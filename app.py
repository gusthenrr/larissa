import ast
import sqlite3
from contextlib import closing
import atexit
import time
import unicodedata
import math
import matplotlib
matplotlib.use('Agg')
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from cs50 import SQL
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from pytz import timezone
import os, time, requests, threading
import pandas as pd
import logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)
import subprocess
import requests
import re
from twilio.rest import Client
from dotenv import load_dotenv
import jwt
import json
import os, re, unicodedata 
from typing import Any, List, Dict
from ifood_routes import ifood_bp, start_ifood_polling



from werkzeug.utils import secure_filename
var = True
manipule = True
if manipule:
    subprocess.run(['python','manipule6.py'])

# Inicialização do app Flask e SocketIO
app = Flask(
    __name__,
    static_folder='/data',      # pasta que vai servir arquivos
    static_url_path='/data'    # endereço para acessar esses arquivos
)
app.register_blueprint(ifood_bp)
# Inicia o polling de pedidos do iFood em background
start_ifood_polling()


load_dotenv()
app.config['SECRET_KEY'] = os.getenv("MOST_SECRET_KEY",'quero-quero17')
socketio = SocketIO(app, cors_allowed_origins="*")
import shutil


SECRET_KEY = os.getenv("MOST_SECRET_KEY", 'quero-quero17')

print('SECRET_KEY',SECRET_KEY)
ACCOUNT_SID = os.getenv("ACCOUNT_SID_TWILIO",'ACe2b44d7bd27f18525eb33dd4ea8b891a')
AUTH_TOKEN  = os.getenv("AUTH_TOKEN_TWILIO",'a03519e493ce0f003228acfaa3e669c2')
VERIFY_SID  = os.getenv("VERIFY_SID",'VAda3089a24c0b290e57138ff2c44f7016') 



client = Client(ACCOUNT_SID, AUTH_TOKEN)

CORS(
    app,
    resources={r"/*": {"origins": '*'}},
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)



connected_carts = {}


def _register_carrinho_room(carrinho):
    """Associate the current Socket.IO session with a cart room."""
    if not carrinho:
        return None

    try:
        sid = getattr(request, 'sid', None)
    except RuntimeError:
        sid = None
    if not sid:
        return carrinho

    current = connected_carts.get(sid)
    if current == carrinho:
        return carrinho

    if current:
        leave_room(current, sid=sid)

    join_room(carrinho, sid=sid)
    connected_carts[sid] = carrinho
    return carrinho


def emit_for_carrinho(event, payload, *, broadcast, carrinho=None, include_self=True):
    """Emit helper that limits broadcasts to the caller's cart when requested."""
    if broadcast and carrinho:
        socketio.emit(event, payload, room=carrinho, include_self=include_self)
    elif broadcast:
        socketio.emit(event, payload, include_self=include_self)
    else:
        emit(event, payload, include_self=include_self)


def decode_number_jwt(token: str) -> int:
    decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    # decoded é dict; o sub tem o número
    print(decoded['sub'])
    return int(decoded["sub"])

@app.route("/validate_table_number_on_qr", methods=['POST'])
def validate_table_number_on_qr():
    try:
        print('validate')
        data = request.get_json()
        print('data',data)
        numero = data.get('numero')
        print('numero',numero)
        if not numero:
            return jsonify({'valid': False}), 200
        tableNumber = decode_number_jwt(numero)
        print('tablenumver',tableNumber)
        if 1 <= tableNumber <= 80:
            return jsonify({'valid': True,'tableNumber':tableNumber}), 200
        return jsonify({'valid': False}), 200
    except Exception as e:
        print('erro ao validar numero:', e)
        return jsonify({'valid': False}), 200



@app.route("/auth/sms/create", methods=["POST"])
def send_verification():
    try:
        print('creatingsms')
        phone = request.json.get("phone")
        print('phone',phone)
        verification = client.verify.v2.services('VAda3089a24c0b290e57138ff2c44f7016').verifications.create(to='+5513978258866', channel='sms')
        print(verification.sid)
        return jsonify({"status": 'pending'}), 200
    except Exception as e:
        print('erro no envio:', e)
        return jsonify({"status": 'error'}), 200

@app.route("/auth/sms/check", methods=["POST"])
def check_verification():
    try:
        print('verification')
        phone = request.json.get("phone")
        code = request.json.get("code")
        chk = client.verify.v2.services(VERIFY_SID).verification_checks.create(to=phone, code=code)
        print(chk)
        return jsonify({"status": 'approved'}), 200  # 'approved' se ok
    except Exception as e:
        print('erro na verificacao:', e)
        return jsonify({"status": 'denied'}), 200

@app.route('/pegar_pagamentos_comanda', methods=['POST'])
def pegar_pagamentos_comanda():
    data = request.get_json()
    comanda = data.get('comanda')
    carrinho = data.get('carrinho', 'NossoPoint')
    dia = data_brasil_corte_3h()
    pagamentos = db.execute('SELECT * FROM pagamentos WHERE comanda = ? AND dia = ? AND ordem = 0 AND carrinho = ?',comanda,dia,carrinho)
    if not pagamentos:
        pagamentos = []
    return {'pagamentos': pagamentos}

@socketio.on('excluir_pedido')
def excluir_pedido(data):

    def _to_float(v, default=0.0):
            try:
                return float(v)
            except Exception:
                return default

            
    def _deduzir_estoque_por_ingrediente(id_ingrediente: str, unidade: str, quantidade_necessaria: float, carrinho: str, estoque_id: int):
            if not id_ingrediente:
                return
            if estoque_id == '1':
                estoque='estoque'
            else:
                estoque='estoque_geral'
            print('estoque',estoque)
            row = db.execute(
                f'SELECT quantidade, quantidade_total, quantidade_por_unidade FROM {estoque} WHERE id = ? AND carrinho = ?',
                id_ingrediente, carrinho
            )
            print('row', row)
            if not row:
                # Se não existe no estoque, nada a fazer aqui
                return
            print('Quantidade unid:', row[0]['quantidade'])
            quantidade_atual_unid = _to_float(row[0]['quantidade'], 0.0)
            quantidade_atual_total = _to_float(row[0]['quantidade_total'], 0.0)
            qpu = _to_float(row[0].get('quantidade_por_unidade', 1), 1.0)

            if (unidade or '').strip() == 'unidade(s)':
                print('deduzindo por unidade interna')
                nova_qtd_unid = quantidade_atual_unid + _to_float(quantidade_necessaria, 0.0)
                nova_qtd_total = quantidade_atual_total + (_to_float(quantidade_necessaria, 0.0)* qpu)
                if nova_qtd_unid < 0:
                    nova_qtd_unid = 0
                if nova_qtd_total < 0:
                    nova_qtd_total = 0
                # mantém compat: espelha em quantidade_total como já era feito
                db.execute(
                    f'UPDATE {estoque} SET quantidade = ?, quantidade_total = ? WHERE id = ? AND carrinho = ?',
                    nova_qtd_unid, nova_qtd_total, id_ingrediente, carrinho
                )
            else:
                nova_qtd_total = quantidade_atual_total + _to_float(quantidade_necessaria, 0.0)
                if nova_qtd_total < 0:
                    nova_qtd_total = 0
                # quantidade (em "unidades" internas) arredondada pelo passo quantidade_por_unidade
                nova_qtd_unid = arredondar_personalizado(nova_qtd_total, qpu)
                db.execute(
                    f'UPDATE {estoque} SET quantidade = ?, quantidade_total = ? WHERE id = ? AND carrinho = ?',
                    nova_qtd_unid, nova_qtd_total, id_ingrediente, carrinho
                )
            # Atualiza painel/assinantes
            getEstoque({'emitir': True, 'carrinho': carrinho})
            getEstoqueGeral({'emitir': True, 'carrinho': carrinho})
    

    try:
        pedido_id = data.get('id')
        carrinho = data.get('carrinho')
        comanda = data.get('comanda')
        usuario = data.get('usuario')
        devolver= data.get('devolver', True)
        item_data=db.execute('SELECT item, ingredientes FROM cardapio WHERE item = (SELECT pedido FROM pedidos WHERE id = ?)', pedido_id)
        item = item_data[0]['item']
        if devolver:
            ingredientes_format=item_data[0]['ingredientes']
            dados_pedidos_=db.execute('SELECT quantidade, opcoes FROM pedidos WHERE id = ?', pedido_id)[0]
            quantidade=dados_pedidos_['quantidade']
            opcoes_format=dados_pedidos_['opcoes']
            opcoes =str_para_lista_de_dicts(opcoes_format) if opcoes_format else []
            ingredientes=str_para_lista_de_dicts(ingredientes_format) if ingredientes_format else []
            if ingredientes == []:
                quantidade_estoque=db.execute('SELECT quantidade FROM estoque WHERE item = ? and carrinho=?', item, carrinho)
                if quantidade_estoque:
                    nova_quantidade=quantidade_estoque[0]['quantidade'] + quantidade
                    db.execute('UPDATE estoque SET quantidade = ? WHERE item = ? and carrinho = ?', nova_quantidade, item, carrinho)
            else:
                for ingrediente in ingredientes:
                    id_ingrediente = ingrediente.get('id')
                    unidade        = ingrediente.get('unidade')
                    qtd_por_item   = _to_float(ingrediente.get('quantidade') or 0, 0.0)
                    qtd_total      = qtd_por_item * quantidade
                    estoque_id     = ingrediente.get('estoque_id')
                    _deduzir_estoque_por_ingrediente(id_ingrediente, unidade, qtd_total, carrinho, estoque_id)
            if opcoes:
                for grupo in opcoes:
                    options = grupo.get('options') or []
                    for opt in options:
                        ingredientes_opt = opt.get('ingredientes') or []
                        for ingrediente in ingredientes_opt:
                            id_ingrediente = ingrediente.get('id')
                            unidade        = ingrediente.get('unidade')
                            qtd_por_item   = _to_float(ingrediente.get('quantidade') or 0, 0.0)
                            qtd_total      = qtd_por_item * quantidade
                            estoque_id     = ingrediente.get('estoque_id')
                            _deduzir_estoque_por_ingrediente(id_ingrediente, unidade, qtd_total, carrinho, estoque_id)


        db.execute('DELETE FROM pedidos WHERE id = ?', pedido_id)
        
    except Exception as e:
        print('Erro ao excluir pedido:', e)
    insertAlteracoesTableSql('Pedidos', f'Pedido id:{pedido_id}\nPedido: {item}\nComanda: {comanda}', 'Removeu','Tela Pedidos', usuario,carrinho)
    getPedidos({'emitir': True, 'carrinho': carrinho})
    getComandas({'emitir': True, 'carrinho': carrinho})
    getPedidosCC({'emitir': True, 'carrinho': carrinho})
    getEstoque({'emitir': True, 'carrinho': carrinho})
    getEstoqueGeral({'emitir': True, 'carrinho': carrinho})
    handle_get_cardapio(data.get('comanda'), carrinho)
    
@app.route('/excluir_pagamento', methods=['POST'])
def excluir_pagamento():
    try:
        data = request.get_json()
        pagamento_id = data.get('pagamento_id')
        ids = db.execute('SELECT ids FROM pagamentos WHERE id = ?', pagamento_id)
        comanda = data.get('comanda')
        carrinho = data.get('carrinho', 'NossoPoint')
        if ids and ids[0]['ids']:
            ids_list = json.loads(ids[0]['ids'])
            print('ids_list', ids_list)
            for row in ids_list:
                db.execute('UPDATE pedidos SET quantidade_paga = quantidade_paga - ?, preco = preco_unitario *NULLIF((quantidade-(quantidade_paga - ?)),0) WHERE id = ? AND dia = ?',row['quantidade'],row['quantidade'],row['id'],data_brasil_corte_3h())
        db.execute('DELETE FROM pagamentos WHERE id = ?', pagamento_id)
        
        handle_get_cardapio(comanda, carrinho)
        return jsonify({'status': 'success'}),200
    except Exception as e:
        print('Erro ao excluir pagamento:', e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

if var:
    DATABASE_PATH = "/data/dados.db"
    if not os.path.exists(DATABASE_PATH):
        shutil.copy("dados.db", DATABASE_PATH)
    db = SQL("sqlite:///" + DATABASE_PATH)
else:
    DATABASE_PATH = "data/dados.db"
    db=SQL("sqlite:///" + DATABASE_PATH)

brazil = timezone('America/Sao_Paulo')

def data_brasil_corte_3h(dt=None):
    """
    Retorna a data considerando que o 'dia' vai de 03:00 a 02:59.
    Se dt for None, usa o agora no fuso do Brasil.
    """
    if dt is None:
        dt = datetime.now(brazil)
    else:
        # garante que está no fuso do Brasil
        if dt.tzinfo is None:
            dt = brazil.localize(dt)
        else:
            dt = dt.astimezone(brazil)

    return (dt - timedelta(hours=3)).date()


os.makedirs(app.static_folder, exist_ok=True)



# def now_utc_iso():
#     return datetime.now(pytz.utc).isoformat()
# def expires_in_minutes_iso(minutes: int):
#     return (datetime.now(pytz.utc) + timedelta(minutes=minutes)).isoformat()
# def generate_code(n: int = 6) -> str:
#     return f"{random.randint(0, 10**n - 1):0{n}d}"


@app.route("/")
def home():
    return "Aplicação funcionando!", 200



@app.route('/validate_token_on_qr', methods=['POST'])
def validate_token_on_qr():
    try:
        print('entrou validate token')
        print('validate token')
        data = request.get_json()
        print('data',data)
        token = data.get('token')
        print('token',token)
        exist = db.execute('SELECT dataUpdateToken FROM clientes WHERE token = ?', token)
        if exist:
            data_update = exist[0]['dataUpdateToken']
            if isinstance(data_update, str):
                try:
                    # tenta converter do formato padrão ISO (YYYY-MM-DD)
                    data_update_date = datetime.strptime(data_update, "%Y-%m-%d").date()
                except ValueError:
                    # se vier num formato inesperado, tenta com hora
                    data_update_date = datetime.fromisoformat(data_update).date()
            else:
                data_update_date = data_update
            print('data_update',data_update_date)
            if data_update_date < data_brasil_corte_3h() + timedelta(days=5):
                print('valid token')
                return jsonify({'valid': True}), 200
        print('invalid token or expired')
        return jsonify({'valid': False}), 200
    except Exception as e:
        print('erro ao validar token:', e)
        return jsonify({'valid': False}), 200

@app.route('/guardar_login', methods=['POST'])
def guardar_login():
    
    print('entrou guardar login')
    data = request.get_json()
    number = str(data.get('numero'))
    

    if not number:
        print('sem numero')
        return jsonify({"error": "Campo 'number' é obrigatório."}), 400
    else:
        print('number',number)
    
    # Busca 1 usuário; evite depender de != 'bloqueado' no WHERE para mensagens claras
    
    payload = {
    "sub": f"{number}",      # identificador do usuário (pode ser id, CPF, etc.)
    "name": f"nome:{number}",  # nome do usuário
    "iat": int(time.time()),  # emitido em (timestamp)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    print('token',token)
    rows = db.execute('SELECT numero, nome, status FROM clientes WHERE numero = ? LIMIT 1', number)
    print('rows')
    if not rows:
        db.execute('INSERT INTO clientes (numero,nome,status,token,dataUpdateToken) VALUES (?,?,?,?,?)',number,f'nome:{number}','aprovado',token,datetime.now().date())
        rows = [{'numero':number,'nome':f'nome:{number}','status':'aprovado'}]
        print('novo usuario inserido')
    
    else:
        db.execute('UPDATE clientes SET token = ?, dataUpdateToken = ? WHERE numero = ?',token,datetime.now().date(),number)

    user = rows[0]
    if user.get('status') == 'bloqueado':
        print('usuario bloqueado')
        return jsonify({"error": "Usuário bloqueado."}), 403

    
    
    return jsonify({"authToken": token}), 200


@app.route('/salvarTokenCargo', methods=['POST'])
#!!
def salvarTokenCargo():
    data = request.get_json()
    username = data.get('username')
    cargo = data.get('cargo')
    token = data.get('token')
    carrinho = data.get('carrinho')
    print(f'data {data}, username {username}, token {token}')
    if db.execute('SELECT * FROM tokens WHERE token =?',token):
        db.execute('DELETE FROM tokens WHERE token = ?',token)
    if token and token!='semtoken':
        db.execute('INSERT INTO tokens (username,cargo,token,carrinho) VALUES (?,?,?,?)',username,cargo,token,carrinho)
    

    return "cargo e user inserido com sucesso"

def enviar_notificacao_expo(cargo,titulo,corpo,token_user,carrinho, canal="default"):
    print(f'cargo {cargo} titulo, {titulo},corpo {corpo} canal {canal}')
    try:
        if cargo:
            tokens = db.execute('SELECT token FROM tokens WHERE carrinho = ? AND cargo = ? AND token != ? GROUP BY token',carrinho,cargo,'semtoken')
        else:
            tokens = db.execute('SELECT token FROM tokens WHERE token != ? AND carrinho = ? GROUP BY token','semtoken', carrinho)
        tokens = [row for row in tokens if row['token'] != token_user]
        respostas = []
        for row in tokens:
            try:
                token = row['token']
                url = "https://exp.host/--/api/v2/push/send"
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
                payload = {
                    "to": token,
                    "title": titulo,
                    "body": corpo,
                    "sound": "default",
                    "android_channel_id": canal  # precisa estar igual ao definido no app
                }
                res = requests.post(url, json=payload, headers=headers, timeout=5)
                respostas.append(res.json())
            except Exception as e:
                print(f"Erro ao enviar notificação para token {token}: {e}")
                respostas.append({"error": str(e)})
        print(f"Notificações enviadas: {len(respostas)} de {len(tokens)} tokens")
        return respostas
    except Exception as e:
        print(f"Erro geral na função enviar_notificacao_expo: {e}")
        return [{"error": str(e)}]



def atualizar_faturamento_diario():
    db.execute('UPDATE usuarios SET liberado = ? WHERE cargo != ? AND cargo != ?',0,'ADM','Dono')
    db.execute('DELETE FROM tokens WHERE cargo!=? AND username != ? AND cargo!=?','ADM','cozinha_principal', 'Dono')
    dia = data_brasil_corte_3h()
    db.execute('INSERT INTO pedidos (pedido,comanda,dia, ordem) VALUES (?,?,?,?)','Comanda Aberta','controle de estoque',dia,0)
    db.execute('INSERT INTO pedidos (pedido,comanda,dia, ordem) VALUES (?,?,?,?)','Comanda Aberta','pago na hora',dia,0)
    end_p_dict = db.execute('SELECT products,status FROM promotions WHERE endDate < ? ',data_brasil_corte_3h().strftime('%Y-%m-%d'))
    if end_p_dict:
        db.execute('UPDATE promotions SET status = ? WHERE endDate < ?','expired',data_brasil_corte_3h().strftime('%Y-%m-%d'))
        for row in end_p_dict:
            itens = json.loads(row.get('products',[]))
            for item in itens:
                db.execute('UPDATE cardapio SET preco = preco_base WHERE id = ?',item['id'])




# Agendador para rodar à meia-noite
scheduler = BackgroundScheduler()
scheduler.add_job(
    atualizar_faturamento_diario,
    'cron',
    hour=3,
    minute=5,
    timezone=brazil
)
scheduler.start()

# Garante que o scheduler pare quando encerrar o servidor
atexit.register(lambda: scheduler.shutdown())


@socketio.on('imprimir_conta')
def handle_imprimir_conta(payload):
    socketio.emit('imprimir_conta', payload)

@app.route('/opcoes', methods=['POST'])
def opc():
    #!!
    print('entrou no opcoes')
    data = request.get_json()
    item = data.get('pedido')
    carrinho=data.get('carrinho')
    print(item) 
    opcoes = db.execute('SELECT opcoes FROM cardapio WHERE item = ? AND carrinho = ?', item,carrinho)
    if opcoes:
        palavra = ''
        selecionaveis = []
        dados = []
        for i in opcoes[0]['opcoes']:
            if i == '(':
                nome_selecionavel = palavra
                print(nome_selecionavel)
                palavra = ''
            elif i == '-':
                selecionaveis.append(palavra)
                palavra = ''
            elif i == ')':
                selecionaveis.append(palavra)
                dados.append({nome_selecionavel: selecionaveis})
                selecionaveis = []
                palavra = ''
            else:
                palavra += i
        print(dados)
        return {'options': dados}


@app.route('/pegar_pedidos', methods=['POST'])
def pegar_pedidos():
    # Pegando os dados do JSON enviado na requisição
    print('entrou pegar pedidos')
    data = request.get_json()
    comanda = data.get('comanda')
    ordem = data.get('ordem')
    carrinho = data.get('carrinho')
    if int(ordem) != 0:
        
        print(f'ORDEM : {ordem}')
        dia = data_brasil_corte_3h()
        dados = db.execute('''
                SELECT pedido, id, ordem, SUM(quantidade) AS quantidade, SUM(preco) AS preco, preco_unitario
                FROM pedidos WHERE comanda = ? AND ordem = ? AND dia = ? AND pedido != ? AND carrinho = ?
                GROUP BY pedido, (preco/quantidade)
            ''', comanda, int(ordem),dia, 'Comanda Aberta', carrinho)
        print('dados',dados)
    
        return{'data':dados,'preco':''}
    else:
        print('ordem 0')
        handle_get_cardapio(comanda, carrinho)
        return{'status':'success'}





@app.route('/verificar_username', methods=['POST'])
def verificar_usu():
    data = request.json
    username = data.get('username')
    print(username)
    senha = data.get('senha')
    print(senha)
    existe = db.execute(
        'SELECT * FROM usuarios WHERE username =? AND senha =? AND liberado=?', username, senha, '1')
    if existe:
        print('true')
        return {'data': True, 'cargo': existe[0]['cargo'], 'carrinho':existe[0]['carrinho']}
    else:
        print('false')
        return {'data': False}
    

def str_para_lista_de_dicts(s: str):
    s = s.strip()
    # Tenta como JSON
    try:
        obj = json.loads(s)
        if isinstance(obj, list) and all(isinstance(x, dict) for x in obj):
            return obj
    except json.JSONDecodeError:
        pass

    # Tenta como literal Python seguro
    try:
        obj = ast.literal_eval(s)
        if isinstance(obj, list) and all(isinstance(x, dict) for x in obj):
            return obj
    except (ValueError, SyntaxError):
        pass

    raise ValueError("A string não parece ser uma lista de dicionários válida.")

def lista_dicts_para_str(dados, pretty=False):
    """
    Converte uma lista de dicionários em string JSON.
    - pretty=True gera uma saída legível (indentada).
    - pretty=False gera uma string compacta (melhor para armazenamento).
    """
    if pretty:
        return json.dumps(dados, ensure_ascii=False, indent=2, default=str)
    # compacto
    return json.dumps(dados, ensure_ascii=False, separators=(",", ":"), default=str)

def get_usado_em_cardapio_ids(estoque_id, carrinho, estoque):
    """
    Pega a lista atual de IDs do campo usado_em_cardapio_id.
    Retorna uma lista de inteiros.
    """
    result = db.execute(f'SELECT usado_em_cardapio_id FROM {estoque} WHERE id = ? AND carrinho = ?', estoque_id, carrinho)
    if not result:
        return []
    
    current_value = result[0]['usado_em_cardapio_id']
    if current_value is None:
        return []
    
    # Se já for uma lista (JSON), converte
    if isinstance(current_value, str):
        try:
            return json.loads(current_value)
        except:
            return []
    
    # Se for um número único, converte para lista
    if isinstance(current_value, int):
        return [current_value]
    
    # Se já for lista, retorna
    if isinstance(current_value, list):
        return current_value
    
    return []

def add_to_usado_em_cardapio_ids(estoque_id, cardapio_id, carrinho, estoque):
    """
    Adiciona um ID do cardápio à lista de usado_em_cardapio_id sem substituir os existentes.
    """
    current_ids = get_usado_em_cardapio_ids(estoque_id, carrinho, estoque)
    
    # Evita duplicatas
    if cardapio_id not in current_ids:
        current_ids.append(cardapio_id)
    
    # Converte para JSON e salva
    ids_json = json.dumps(current_ids)
    db.execute(f'UPDATE {estoque} SET usado_em_cardapio_id = ? WHERE id = ? AND carrinho = ?', ids_json, estoque_id, carrinho)

def remove_from_usado_em_cardapio_ids(estoque_id, cardapio_id, carrinho, estoque):
    """
    Remove um ID do cardápio da lista de usado_em_cardapio_id.
    """
    current_ids = get_usado_em_cardapio_ids(estoque_id, carrinho)
    
    # Remove o ID se existir
    if cardapio_id in current_ids:
        current_ids.remove(cardapio_id)
    
    # Se ficou vazio, salva NULL
    if not current_ids:
        db.execute(f'UPDATE {estoque} SET usado_em_cardapio_id = NULL WHERE id = ? AND carrinho = ?', estoque_id, carrinho)
    else:
        # Converte para JSON e salva
        ids_json = json.dumps(current_ids)
        db.execute(f'UPDATE {estoque} SET usado_em_cardapio_id = ? WHERE id = ? AND carrinho = ?', ids_json, estoque_id, carrinho)

@app.route('/verificar_quantidade', methods=['POST'])
def verif_quantidade():
    data = request.json
    item = data.get('item')
    quantidade_pedida = data.get('quantidade', 1)
    opcoes_sel = data.get('opcoesSelecionadas') or []
    carrinho = data.get('carrinho')

    print('opcoes', opcoes_sel)
    print(f'Item: {item}, Quantidade: {quantidade_pedida}')

    # ---- helpers locais ----
    def _to_float(v, default=0.0):
        try:
            return float(v)
        except Exception:
            return default

    # Mapa de necessidade total por ingrediente-id:
    # id -> { 'nome': str, 'unidade': str, 'req': float, 'is_unit': bool }
    requerimentos = {}

    def _acumular_req(ing, multiplicador=1.0):
        """
        Soma a quantidade requerida de um ingrediente no dicionário 'requerimentos',
        usando o 'id' do ingrediente. Se não houver id, ignora (conforme requisito).
        """
        if not isinstance(ing, dict):
            return
        ing_id = ing.get('id')
        if not ing_id:
            return  # requisito: pegar pelo id; se não veio id, ignoramos

        nome = (ing.get('nome') or '').strip()
        unidade = (ing.get('unidade') or '').strip()
        estoque_id = ing.get('estoque_id')
        qtd_por_item = _to_float(ing.get('quantidade'), 0.0)

        req_total = qtd_por_item * multiplicador
        is_unit = (unidade == 'unidade(s)')

        acc = requerimentos.get(ing_id)
        if not acc:
            requerimentos[ing_id] = {
                'nome': nome,
                'unidade': unidade,
                'estoque_id': estoque_id,
                'req': req_total,
                'is_unit': is_unit
            }
        else:
            acc['req'] += req_total
            # caso misturem unidades (improvável), preserva decisão do primeiro
            if not acc.get('unidade'):
                acc['unidade'] = unidade
            if 'is_unit' not in acc:
                acc['is_unit'] = is_unit

    multiplicador = _to_float(quantidade_pedida, 1.0)

    # ---- 1) Ingredientes do item (campo 'ingredientes' da tabela cardapio) ----
    ingredientes_format = db.execute(
        'SELECT ingredientes FROM cardapio WHERE item = ? AND carrinho = ?',
        item, carrinho
    )
    if ingredientes_format and ingredientes_format[0].get('ingredientes'):
        print('tem ingredientes no item')
        try:
            ingredientes_item = str_para_lista_de_dicts(ingredientes_format[0]['ingredientes'])
        except Exception:
            ingredientes_item = []
        for ing in (ingredientes_item or []):
            _acumular_req(ing, multiplicador=multiplicador)

    # ---- 2) Ingredientes das opções selecionadas ----
    # Estrutura esperada: [{'nome': <grupo>, 'ids': '', 'options': [
    #   {'nome':'Limao','valor_extra':0,'ingredientes':[ {...}, {...} ]}, ...
    # ]}, ...]
    for grupo in (opcoes_sel if isinstance(opcoes_sel, list) else []):
        opts = (grupo or {}).get('options') or []
        for opt in opts:
            for ing in (opt or {}).get('ingredientes') or []:
                _acumular_req(ing, multiplicador=multiplicador)

    # ---- 3) Verificar estoque para cada ingrediente requerido ----
    # Para unidade(s) -> comparar com estoque.quantidade
    # Demais unidades -> comparar com estoque.quantidade_total
    for ing_id, info in requerimentos.items():
        if info['estoque_id']=='1':
            estoque='estoque'
        else:
            estoque='estoque_geral'
        row = db.execute(
            f'SELECT item, quantidade, estoque_ideal, quantidade_total FROM {estoque} WHERE id = ? AND carrinho = ?',
            ing_id, carrinho
        )
        if not row:
            # Se o ingrediente não estiver no estoque, consideramos insuficiente
            print(f'estoque não encontrado para ingrediente id={ing_id}')
            return {'erro': False, 'quantidade': 0}

        estoque = row[0]
        atual_unidades = _to_float(estoque.get('quantidade'), 0.0)
        atual_total = _to_float(estoque.get('quantidade_total'), 0.0)
        ideal = _to_float(estoque.get('estoque_ideal'), 0.0)

        if info['is_unit']:
            atual = atual_unidades
        else:
            atual = atual_total

        req = _to_float(info['req'], 0.0)

        if req > atual:
            print('estoque insuficiente para', info.get('nome'), 'req:', req, 'atual:', atual)
            # Mantemos o contrato anterior: retornar 'quantidade' do campo de unidades
            return {'erro': 'Estoque insuficiente', 'quantidade': atual_unidades}

        # Sinalizar estoque baixo (abaixo do ideal após o consumo)
        if ideal > (atual - req):
            print('estoque baixo para', info.get('nome'))
            return {
                'erro': False,
                'item_name': info.get('nome'),
                'quantidade': atual_unidades
            }

    # ---- 4) Caso especial: categoria_id == 1 (Restante) sem ingredientes definidos ----
    categoria = db.execute(
        'SELECT categoria_id FROM cardapio WHERE item = ? AND carrinho = ?',
        item, carrinho
    )
    if categoria and categoria[0]['categoria_id'] == 1 and not requerimentos:
        print('categoria 1 (Restante) sem ingredientes específicos; verificar estoque do próprio item')
        verificar_estoque = db.execute(
            'SELECT quantidade, estoque_ideal FROM estoque WHERE item = ? AND carrinho = ?',
            item, carrinho
        )
        if verificar_estoque:
            estoque_atual = _to_float(verificar_estoque[0]['quantidade'], 0.0)
            if _to_float(quantidade_pedida, 0.0) > estoque_atual:
                print('estoque insuficiente (categoria 1)')
                return {'erro': 'Estoque insuficiente', 'quantidade': estoque_atual}
            else:
                estoque_ideal = _to_float(verificar_estoque[0].get('estoque_ideal'), 0.0)
                if estoque_ideal and estoque_ideal >= (estoque_atual - _to_float(quantidade_pedida, 0.0)):
                    print('estoque baixo (categoria 1)')
                    return {'erro': False, 'quantidade': estoque_atual}

    print('estoque ok')
    return {'erro': False}

@app.route('/transferir_comanda', methods=['POST'])
def transferir_comanda():
    try:
        data = request.get_json()
        comanda_origem = data.get('comanda_origem')
        comanda_destino = data.get('comanda_destino')
        carrinho = data.get('carrinho')

        if not comanda_origem or not comanda_destino:
            return jsonify({'error': 'Both source and destination comandas must be provided.'}), 400

        if comanda_origem == comanda_destino:
            return jsonify({'error': 'Source and destination comandas must be different.'}), 400

        # Fetch orders from the source comanda
        db.execute("UPDATE pedidos SET comanda = ? WHERE comanda = ? AND ordem = ? AND dia = ? AND carrinho = ?", comanda_destino, comanda_origem, 0, data_brasil_corte_3h(), carrinho)
        db.execute("UPDATE pagamentos SET comanda = ? WHERE comanda = ? AND ordem = ? AND dia = ? AND carrinho = ?", comanda_destino, comanda_origem, 0, data_brasil_corte_3h(), carrinho)
        getPedidos({'emitir': True, 'carrinho': carrinho})
        getComandas({'emitir': True, 'carrinho': carrinho})
        handle_get_cardapio(comanda_destino, carrinho)
        
        return jsonify({'message': 'Orders transferred successfully.'}), 200
        
    except Exception as e:
        print('erro ao transferir comanda:', e)
        return jsonify({'error': str(e)}), 500

@app.route('/updatePrinted', methods=['POST'])
def update_printed():
    data = request.json or {}
    carrinho = data.get('carrinho')
    pedido_ids = data.get('pedidoIds')
    pedido_id = data.get('pedidoId')

    ids_para_atualizar = []
    if isinstance(pedido_ids, list):
        ids_para_atualizar.extend([pid for pid in pedido_ids if pid is not None])
    if pedido_id is not None:
        ids_para_atualizar.append(pedido_id)

    if not ids_para_atualizar:
        return jsonify({'status': 'error', 'message': 'pedidoId ausente'}), 400

    for pid in ids_para_atualizar:
        db.execute('UPDATE pedidos SET printed = ? WHERE id = ? AND carrinho = ?', 1, pid, carrinho)

    return jsonify({'status': 'success', 'updated': len(ids_para_atualizar)}), 200


@app.route('/getPendingPrintOrders', methods=['POST'])
def get_pending_print_orders():
    print('getPendingPrintOrders')
    data = request.json or {}
    carrinho = data.get('carrinho')
    print('CARRINHO', carrinho)
    categoria = data.get('categoria',1)

    # opcional: permitir que o cliente mande printed/ordem; manter defaults
    printed = 0
    ordem = 0

    dia = data_brasil_corte_3h()
    inicio_limite = (datetime.now(brazil) - timedelta(minutes=25)).strftime('%H:%M')

    # CORREÇÃO: usar tupla de parâmetros
    pedidos = db.execute(
        'SELECT * FROM pedidos WHERE printed = ? AND ordem = ? AND dia = ? AND inicio > ? AND categoria = ? AND carrinho = ? ORDER BY inicio ASC',
        printed, ordem, dia, inicio_limite, categoria, carrinho
    )
    pedidos_formatados = []
    if pedidos:
        for row in pedidos:
            mesa = row['comanda']
            pedido_nome = row['pedido']
            quantidade = row['quantidade']
            extra = row['extra']
            hora = row['inicio']
            pedido_id = row['id']
            username = row['username']
            categoria_row = row.get('categoria')
            opcoes = format_opcoes_text(row['opcoes']) if row.get('opcoes',None) else None

            item = {
                'pedido': pedido_nome,
                'quantidade': quantidade,
            }
            if opcoes:
                item['opcoes'] = opcoes
            if extra:
                item['extra'] = extra
            item['id'] = pedido_id

            pedidos_formatados.append({
                'mesa': mesa,
                'pedido': [item],
                'quantidade': quantidade,
                'opcoes': opcoes,
                'remetente': row.get('remetente') or carrinho,
                'extra': extra,
                'hora': hora,
                'id': pedido_id,
                'ids': [pedido_id],
                'sendBy': username,
                'categoria': str(categoria_row) if categoria_row is not None else None,
                'categoria_id': categoria_row,
                'endereco_entrega': row.get('endereco_entrega'),
                'prazo': row.get('horario_para_entrega'),
            })


    # Se seu db.execute retorna cursor, talvez precise fetchall()
    # pedidos = db.execute(...).fetchall()

    print('pedidos', pedidos)
    return jsonify({'pedidos': pedidos_formatados}), 200

@socketio.on('connect')
def handle_connect():
    print(f'Cliente conectado:{request.sid}')


@socketio.on('getCardapio')
def getCardapio(data):
    emitirBroadcast = data.get('emitir')
    carrinho = data.get('carrinho')
    print("Carrinho", carrinho)
    _register_carrinho_room(carrinho)
    dataCardapio = db.execute("SELECT * FROM cardapio WHERE carrinho = ? ORDER BY item ASC", carrinho)
    if emitirBroadcast:
        emit_for_carrinho('respostaCardapio', {'dataCardapio': dataCardapio}, broadcast=True, carrinho=carrinho)
    else:
        emit_for_carrinho('respostaCardapio', {'dataCardapio': dataCardapio}, broadcast=False, carrinho=carrinho)

@socketio.on('getCarrinhos')
def getCarrinhos(data):
    if isinstance(data, dict):
        emitirBroadcast = data.get('emitir', True)
        carrinho = data.get('carrinho')
    else:
        emitirBroadcast = data if isinstance(data, bool) else True
        carrinho = None

    if carrinho:
        _register_carrinho_room(carrinho)

    carrinhos = db.execute('SELECT empresas FROM carrinhos where carrinho = ? ORDER BY empresas ASC', carrinho)
    empresas = []
    for car in carrinhos:
        if car:
            empresas.append(car['empresas'])
    emit_for_carrinho('respostaCarrinhos', {'carrinhos': empresas}, broadcast=emitirBroadcast, carrinho=carrinho)


@socketio.on('getPedidosCC')
def getPedidosCC(data):
    print('getPedidos')
    if isinstance(data, dict):
        emitirBroadcast = data.get('emitir', True)
        carrinho = data.get('carrinho')
    
    print('emitirBroadcast', emitirBroadcast)
    _register_carrinho_room(carrinho)
    dia = data_brasil_corte_3h()
    empresas=db.execute('SELECT empresas FROM carrinhos WHERE carrinho = ?', carrinho)
    data_pedidos_completos = []
    for e in empresas:
        dataPedidos = db.execute('SELECT * FROM pedidos WHERE dia = ? AND pedido != ? AND carrinho = ? AND categoria = ?',dia,'Comanda Aberta',e['empresas'],3)
        if dataPedidos:
            data_pedidos_completos.extend(dataPedidos)
    for i in db.execute('SELECT * FROM pedidos WHERE dia = ? AND pedido != ? AND carrinho = ? AND categoria = ?',dia,'Comanda Aberta',carrinho,3):
        data_pedidos_completos.append(i)
    if not data_pedidos_completos:
        data_pedidos_completos = []
    if emitirBroadcast:
        emit_for_carrinho('respostaPedidosCC', {'dataPedidos': data_pedidos_completos}, broadcast=True, carrinho=carrinho)
    else:
        emit_for_carrinho('respostaPedidosCC', {'dataPedidos': data_pedidos_completos}, broadcast=False, carrinho=carrinho)

@socketio.on('getPedidos')
def getPedidos(data):
    print('getPedidos')
    if isinstance(data, dict):
        emitirBroadcast = data.get('emitir', True)
        carrinho = data.get('carrinho')
    print('emitirBroadcast', emitirBroadcast)
    print('carrinho', carrinho)
    _register_carrinho_room(carrinho)
    dia = data_brasil_corte_3h()
    dataPedidos = db.execute('SELECT * FROM pedidos WHERE dia = ? AND pedido != ? AND carrinho = ?',dia,'Comanda Aberta',carrinho)
    if not dataPedidos:
        dataPedidos = []
    if emitirBroadcast:
        emit_for_carrinho('respostaPedidos', {'dataPedidos': dataPedidos}, broadcast=True, carrinho=carrinho)
    else:
        emit_for_carrinho('respostaPedidos', {'dataPedidos': dataPedidos}, broadcast=False, carrinho=carrinho)

@socketio.on('getItensPromotion')
def getPedidosPromotion(data):
    #!!
    emitirBroadcast=data.get('emitir')
    carrinho = data.get("carrinho")
    _register_carrinho_room(carrinho)
    dataCardapio = db.execute('SELECT id,item,preco_base FROM cardapio WHERE carrinho = ?', carrinho)
    if dataCardapio:
        emit_for_carrinho('respostaItensPromotion', {'dataCardapio': dataCardapio}, broadcast=emitirBroadcast, carrinho=carrinho)

@socketio.on('getEstoque')
def getEstoque(data):
    emitirBroadcast=data.get('emitir')
    carrinho=data.get('carrinho')
    _register_carrinho_room(carrinho)
    dataEstoque=db.execute('SELECT * FROM estoque WHERE carrinho = ? ORDER BY item', carrinho)
    if dataEstoque:
        emit_for_carrinho('respostaEstoque', {'dataEstoque': dataEstoque}, broadcast=emitirBroadcast, carrinho=carrinho)

@socketio.on('getEstoqueGeral')
def getEstoqueGeral(data):
    emitirBroadcast=data.get('emitir')
    carrinho=data.get('carrinho')
    _register_carrinho_room(carrinho)
    dataEstoqueGeral=db.execute('SELECT * FROM estoque_geral WHERE carrinho = ? ORDER BY item', carrinho)
    if dataEstoqueGeral:
        emit_for_carrinho('respostaEstoqueGeral', {'dataEstoqueGeral': dataEstoqueGeral}, broadcast=emitirBroadcast, carrinho=carrinho)


@socketio.on('getComandas')
def getComandas(data):
    if isinstance(data, dict):
        emitirBroadcast = data.get('emitir', True)
        carrinho = data.get('carrinho')

    _register_carrinho_room(carrinho)
    dia = data_brasil_corte_3h()
    sql_abertas = """
        SELECT comanda
        FROM pedidos
        WHERE ordem = ? AND dia = ? AND carrinho = ?
        GROUP BY comanda
        ORDER BY
        CASE
            WHEN comanda GLOB '[0-9]*' THEN CAST(comanda AS INTEGER)
            ELSE NULL
        END,
        comanda ASC
        """
    dados_comandaAberta = db.execute(sql_abertas, 0, dia, carrinho)

    dados_comandaFechada = db.execute(
        'SELECT comanda,ordem FROM pedidos WHERE ordem !=? AND dia = ? AND carrinho = ? GROUP BY comanda ORDER BY comanda ASC', 0,dia, carrinho)
    if dados_comandaAberta or dados_comandaFechada:
        if emitirBroadcast:
            emit_for_carrinho('respostaComandas', {'dados_comandaAberta': dados_comandaAberta, 'dados_comandaFechada': dados_comandaFechada}, broadcast=True, carrinho=carrinho)
        else:
            emit_for_carrinho('respostaComandas', {'dados_comandaAberta': dados_comandaAberta, 'dados_comandaFechada': dados_comandaFechada}, broadcast=False, carrinho=carrinho)


@socketio.on('users')
def users(data):
    emitirBroadcast=data.get('emitir')
    carrinho=data.get('carrinho')
    _register_carrinho_room(carrinho)
    users = db.execute('SELECT * from usuarios WHERE carrinho = ?', carrinho)
    emit_for_carrinho('usuarios', {'users': users}, broadcast=emitirBroadcast, carrinho=carrinho)


@socketio.on('disconnect')
def handle_disconnect():
    try:
        sid = getattr(request, 'sid', None)
    except RuntimeError:
        sid = None
    if sid:
        carrinho = connected_carts.pop(sid, None)
        if carrinho:
            leave_room(carrinho, sid=sid)
    print('Cliente desconectado')

# Manipulador para inserir dados


@socketio.on('refresh')
def refresh():
    handle_connect()

@socketio.on('EditingEstoque')
def editEstoque(data):
    print('editar estoque')
    carrinho = data.get('carrinho')
    tipo = data.get('tipo')
    item = data.get('item')
    novoNome = data.get('novoNome')
    quantidade = data.get('quantidade')
    estoque_ideal = data.get('estoqueIdeal')
    unidade = data.get('unidade')
    quantidade_por_unidade = data.get('quantidade_por_unidade')
    quantidade_total = data.get('quantidade_total')
    estoque = data.get('estoque')
    usuario = data.get('username')
    token_user = data.get('token')
    mudar_os_dois = data.get('mudar_os_dois')
    print("item", tipo)
    print("item", item)
    print("item", quantidade)
    print("item", estoque_ideal)
    print("estoque", estoque)
    print("unidade", unidade)
    print("quantidade_por_unidade", quantidade_por_unidade)
    print("quantidade_total", quantidade_total)
    alteracao = f'{item}'
    if not item: emit(f'{estoque}Alterado', {'erro':'Item nao identificado'})
    if tipo == 'Adicionar':
        existe=db.execute(f'SELECT item FROM {estoque} WHERE item = ? AND carrinho = ?',item, carrinho)
        if existe:
            emit(f'{estoque}Alterado',{'erro':'Nome Igual'})
            return
        tipo = 'Adicionou'
        if estoque_ideal:
            alteracao+=f' com estoque ideal de {estoque_ideal}'
        if unidade:
            alteracao+=f' unidade: {unidade}'
        print("Entrou no adicionar")                                            
        if db.execute(f'SELECT item FROM {estoque} WHERE item = ? AND carrinho = ?',item, carrinho): emit(f'{estoque}Alterado',{'erro':'Nome Igual'})
        db.execute(f"INSERT INTO {estoque} (item,quantidade,estoque_ideal,unidade,quantidade_por_unidade,quantidade_total,carrinho) VALUES (?,?,?,?,?,?,?)",
                   item,quantidade,estoque_ideal,unidade,quantidade_por_unidade,quantidade_total,carrinho)
        if mudar_os_dois:
            alteracao+=' em ambos os estoques'
            estoque_sec = 'estoque' if estoque=='estoque_geral' else 'estoque_geral'
            if not db.execute(f'SELECT item FROM {estoque_sec} WHERE item = ? AND carrinho = ?',item, carrinho): 
                db.execute(f"INSERT INTO {estoque_sec} (item,quantidade,estoque_ideal,unidade,quantidade_por_unidade,quantidade_total,carrinho) VALUES (?,?,?,?,?,?,?)",
                          item,0,0,unidade,quantidade_por_unidade,0,carrinho)

    elif tipo == 'Remover':
        tipo='Removeu'
        db.execute(f"DELETE FROM {estoque} WHERE item=? AND carrinho = ?",item, carrinho)
        if mudar_os_dois:
            alteracao+=' de ambos os estoques'
            estoque_sec = 'estoque' if estoque=='estoque_geral' else 'estoque_geral'
            db.execute(f"DELETE FROM {estoque_sec} WHERE item=? AND carrinho = ?",item, carrinho)
    else:
        alteracao+=': alterou'
        tipo='Editou'
        antigo = db.execute(f'SELECT estoque_ideal FROM {estoque} WHERE item = ? AND carrinho = ?',item, carrinho)
        antig = 'inexistente' if not antigo else antigo[0]['estoque_ideal']
        
        # Construir query de update dinamicamente baseado nos campos recebidos
        updates = []
        params = []
        
        if novoNome:
            existe=db.execute(f'SELECT item FROM {estoque} WHERE item = ? AND carrinho = ?',novoNome, carrinho)
            if existe:
                print('Nome igual encontrado no estoque')
                emit(f'{estoque}Alterado',{'erro':'Nome Igual'})
                return
            updates.append("item=?")
            params.append(novoNome)
            alteracao+= f' Nome do {item} para {novoNome}'
            ids = get_usado_em_cardapio_ids(db.execute(f"SELECT id FROM {estoque} WHERE item = ? AND carrinho = ?",item, carrinho)[0]['id'], carrinho, estoque)
            if ids:
                for cardapio_id in ids:
                    try:
                        dados_cardapio=db.execute("SELECT ingredientes,opcoes FROM cardapio WHERE id = ? AND carrinho = ?", cardapio_id, carrinho)
                        if dados_cardapio:
                            dados_cardapio = dados_cardapio[0]
                            ingredientes_dict=dados_cardapio['ingredientes']
                            opcoes_str=dados_cardapio['opcoes']
                            if ingredientes_dict:
                                try:
                                    ingredientes_lista=str_para_lista_de_dicts(ingredientes_dict)
                                    for ingrediente in ingredientes_lista:
                                        if ingrediente.get('nome')==item:
                                            ingrediente['nome']=novoNome
                                    novos_ingredientes = lista_dicts_para_str(ingredientes_lista)
                                    db.execute("UPDATE cardapio SET ingredientes = ? WHERE id = ? AND carrinho = ?", novos_ingredientes, cardapio_id, carrinho)
                                except Exception as e:
                                    print('Erro ao atualizar ingredientes no cardapio:', e)
                            if opcoes_str:
                                try:
                                    opcoes_lista=str_para_lista_de_dicts(opcoes_str)
                                    opcoes_modificadas=False
                                    nova_opcao_lista = []
                                    for grupo in opcoes_lista:
                                        print('GRUPO:', grupo)
                                        options = grupo.get('options') or []
                                        for option in options:
                                            print('OPCAO:', option)
                                            ingredientes_opcao = option.get('ingredientes') or []
                                            for ingrediente in ingredientes_opcao:
                                                if ingrediente.get('nome')==item:
                                                    ingrediente['nome']=novoNome
                                                    opcoes_modificadas=True
                                            option['ingredientes'] = ingredientes_opcao
                                        grupo['options'] = options
                                        nova_opcao_lista.append(grupo)
                                    opcoes_lista = nova_opcao_lista
                                    if opcoes_modificadas:
                                        novas_opcoes = _normalize_opcoes(opcoes_lista)
                                        db.execute("UPDATE cardapio SET opcoes = ? WHERE id = ? AND carrinho = ?", novas_opcoes, cardapio_id, carrinho)
                                except Exception as e:
                                    print('Erro ao atualizar ingredientes nas opcoes do cardapio:', e)
                    except Exception as e:
                        print(f'Erro ao processar cardapio id {cardapio_id}:', e)


            #preciso mudar o nome de todos os ingredientes que estavam conectados a esse item do estoque, 
            #tanto dos ingredientes do cardapio, quanto das opcoes desse cardapio.
            
        if estoque_ideal is not None:
            updates.append("estoque_ideal=?")
            params.append(estoque_ideal)
            if type(antig)!=str and float(estoque_ideal) != float(antig):
                alteracao+= f' estoque ideal de {float(antig)} para {estoque_ideal}'

        if unidade is not None:
            updates.append("unidade=?")
            params.append(unidade)
            alteracao+= f' unidade para {unidade}'
                
        if quantidade_por_unidade is not None:
            updates.append("quantidade_por_unidade=?")
            params.append(quantidade_por_unidade)
            
        if quantidade_total is not None:
            updates.append("quantidade_total=?")
            params.append(quantidade_total)
        
        if updates:
            params.extend([item, carrinho])
            query = f"UPDATE {estoque} SET {', '.join(updates)} WHERE item=? AND carrinho = ?"
            db.execute(query, *params)
            
            if mudar_os_dois and novoNome:
                alteracao+=f' em ambos os estoques'
                estoque_sec = 'estoque' if estoque=='estoque_geral' else 'estoque_geral'
                db.execute(f"UPDATE {estoque_sec} SET item=? WHERE item=? AND carrinho = ?",novoNome,item, carrinho)

    insertAlteracoesTable(estoque,alteracao,tipo,f'Botao + no Editar {estoque}',usuario, carrinho)
    alteracao=f"{usuario} {tipo} {alteracao}"
    enviar_notificacao_expo('ADM','Estoque Editado',alteracao,token_user,carrinho=carrinho)
    getCardapio({'emitir':True,'carrinho':carrinho})
    if mudar_os_dois:
        getEstoqueGeral({'emitir':True,'carrinho':carrinho})
        getEstoque({'emitir':True,'carrinho':carrinho})
    elif estoque=='estoque_geral':
        getEstoqueGeral({'emitir':True,'carrinho':carrinho})
    else: getEstoque({'emitir':True,'carrinho':carrinho})
            
@socketio.on("editCargo")
def edit_cargo(data):
    carrinho = data.get('carrinho')
    print('editcargo')
    usuario=data.get("usuario")
    print (usuario)
    cargo=data.get("cargo")
    print(cargo)
    db.execute("UPDATE usuarios SET cargo = ? WHERE username = ? AND carrinho = ?", cargo, usuario, carrinho)
    users({'emitir':True,'carrinho':carrinho})
    
     



import json

def somar_extra_por_unidade(selection):
    """
    Soma 'valor_extra' das opções selecionadas na estrutura recebida.
    Aceita:
      - [ {nome, options:[{nome, valor_extra, ...}, ...]}, ... ]
      - { nome, options:[...] }
      - [ {nome, valor_extra}, ... ]  (lista de opções avulsas)
    Ignora options com 'selecionado': False
    """
    def _sum_from_groups(groups):
        total = 0.0
        for g in groups:
            if not isinstance(g, dict):
                continue
            opts = g.get('options') or g.get('opcoes') or []
            if not isinstance(opts, list):
                continue
            for opt in opts:
                if not isinstance(opt, dict):
                    continue
                if opt.get('selecionado') is False:
                    continue
                try:
                    total += float(opt.get('valor_extra') or 0)
                except Exception:
                    pass
        return total

    if not selection:
        return 0.0

    # caso seja dict de 1 grupo
    if isinstance(selection, dict):
        # se já parecer "grupo", trata como lista de grupos com 1 elemento
        if isinstance(selection.get('options') or selection.get('opcoes'), list):
            return _sum_from_groups([selection])
        # se for um dict genérico: tente encontrar 'groups/opcoes/options'
        groups = selection.get('groups') or selection.get('opcoes') or selection.get('options') or []
        if isinstance(groups, dict):
            groups = [groups]
        if isinstance(groups, list):
            # se cair aqui como lista de opções avulsas, embrulha
            if groups and isinstance(groups[0], dict) and 'valor_extra' in groups[0] and 'options' not in groups[0]:
                groups = [{'nome': 'Opções', 'options': groups}]
            return _sum_from_groups(groups)
        return 0.0

    # caso seja list
    if isinstance(selection, list):
        if not selection:
            return 0.0
        # se é lista de grupos? (primeiro tem 'options')
        first = selection[0]
        if isinstance(first, dict) and ('options' in first or 'opcoes' in first):
            return _sum_from_groups(selection)
        # se é lista de opções avulsas
        if isinstance(first, dict) and 'valor_extra' in first and 'options' not in first:
            return _sum_from_groups([{'nome': 'Opções', 'options': selection}])
        return 0.0

    return 0.0

def arredondar_personalizado(qtd, por_unidade, down=0.30, up=0.31):
    x = qtd / por_unidade
    base = math.floor(x)
    frac = x - base

    if frac <= down:
        return base
    elif frac >= up:
        return base + 1
    else:
        # faixa morta entre 0.30 e 0.31
        return base

@socketio.on('insert_order')
def handle_insert_order(data):
    try:
        dia = data_brasil_corte_3h()

        # ---------- Helpers ----------
        def to_list(x):
            if isinstance(x, list):
                return x
            if x is None:
                return []
            return [x]

        def parse_json_maybe(val):
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    return val
            return val

        def get_or_default(seq, idx, default):
            if isinstance(seq, list):
                return seq[idx] if idx < len(seq) else default
            return seq if not isinstance(seq, (list, tuple)) else default

        def _to_float(v, default=0.0):
            try:
                return float(v)
            except Exception:
                return default

        # Abate do estoque por ingrediente (id) respeitando unidade
        def _deduzir_estoque_por_ingrediente(id_ingrediente: str, unidade: str, quantidade_necessaria: float, carrinho: str, estoque_id: int):
            if not id_ingrediente:
                return
            if estoque_id == '1':
                estoque='estoque'
            else:
                estoque='estoque_geral'
            row = db.execute(
                f'SELECT quantidade, quantidade_total, quantidade_por_unidade FROM {estoque} WHERE id = ? AND carrinho = ?',
                id_ingrediente, carrinho
            )
            print('row', row)
            if not row:
                # Se não existe no estoque, nada a fazer aqui
                return
            print('Quantidade unid:', row[0]['quantidade'])
            quantidade_atual_unid = _to_float(row[0]['quantidade'], 0.0)
            quantidade_atual_total = _to_float(row[0]['quantidade_total'], 0.0)
            qpu = _to_float(row[0].get('quantidade_por_unidade', 1), 1.0)

            if (unidade or '').strip() == 'unidade(s)':
                print('deduzindo por unidade interna')
                nova_qtd_unid = quantidade_atual_unid - _to_float(quantidade_necessaria, 0.0)
                nova_qtd_total = quantidade_atual_total - (_to_float(quantidade_necessaria, 0.0)* qpu)
                if nova_qtd_unid < 0:
                    nova_qtd_unid = 0
                if nova_qtd_total < 0:
                    nova_qtd_total = 0
                # mantém compat: espelha em quantidade_total como já era feito
                db.execute(
                    f'UPDATE {estoque} SET quantidade = ?, quantidade_total = ? WHERE id = ? AND carrinho = ?',
                    nova_qtd_unid, nova_qtd_total, id_ingrediente, carrinho
                )
            else:
                nova_qtd_total = quantidade_atual_total - _to_float(quantidade_necessaria, 0.0)
                if nova_qtd_total < 0:
                    nova_qtd_total = 0
                # quantidade (em "unidades" internas) arredondada pelo passo quantidade_por_unidade
                nova_qtd_unid = arredondar_personalizado(nova_qtd_total, qpu)
                db.execute(
                    f'UPDATE {estoque} SET quantidade = ?, quantidade_total = ? WHERE id = ? AND carrinho = ?',
                    nova_qtd_unid, nova_qtd_total, id_ingrediente, carrinho
                )
            # Atualiza painel/assinantes
            getEstoque({'emitir': True, 'carrinho': carrinho})
            getEstoqueGeral({'emitir': True, 'carrinho': carrinho})

        # Percorre a seleção de opções (em qualquer formato aceito) e gera (id, unidade, quantidade_por_item)
        def _iter_ingredientes_de_opcoes(selection):
            """
            Itera pelos ingredientes das opções selecionadas.
            Aceita selection como:
              - lista de grupos: [{nome, options:[{..., ingredientes:[...]}, ...]}, ...]
              - dict grupo único com 'options'
              - lista de opções avulsas: [{nome, valor_extra, ingredientes:[...]}, ...]
              - dict de opção (fallback)
            Considera 'selecionado' == False para pular opções.
            """
            if not selection:
                return
            # lista
            if isinstance(selection, list):
                for elem in selection:
                    # se elem for grupo com options/opcoes
                    if isinstance(elem, dict) and ('options' in elem or 'opcoes' in elem):
                        opts = elem.get('options') or elem.get('opcoes') or []
                        if isinstance(opts, list):
                            for opt in opts:
                                if not isinstance(opt, dict):
                                    continue
                                if opt.get('selecionado') is False:
                                    continue
                                ing_list = opt.get('ingredientes') or []
                                if isinstance(ing_list, list):
                                    for ing in ing_list:
                                        if isinstance(ing, dict):
                                            yield ing
                    # se elem já parece uma opção
                    elif isinstance(elem, dict) and 'valor_extra' in elem and 'options' not in elem and 'opcoes' not in elem:
                        if elem.get('selecionado') is False:
                            return
                        ing_list = elem.get('ingredientes') or []
                        if isinstance(ing_list, list):
                            for ing in ing_list:
                                if isinstance(ing, dict):
                                    yield ing
                    # senão, recursivo (para estruturas aninhadas incomuns)
                    else:
                        for ing in _iter_ingredientes_de_opcoes(elem):
                            yield ing
                return
            # dict
            if isinstance(selection, dict):
                if 'options' in selection or 'opcoes' in selection:
                    opts = selection.get('options') or selection.get('opcoes') or []
                    if isinstance(opts, list):
                        for opt in opts:
                            if not isinstance(opt, dict):
                                continue
                            if opt.get('selecionado') is False:
                                continue
                            ing_list = opt.get('ingredientes') or []
                            if isinstance(ing_list, list):
                                for ing in ing_list:
                                    if isinstance(ing, dict):
                                        yield ing
                    return
                # opção isolada
                if 'valor_extra' in selection and 'options' not in selection and 'opcoes' not in selection:
                    if selection.get('selecionado') is not False:
                        ing_list = selection.get('ingredientes') or []
                        if isinstance(ing_list, list):
                            for ing in ing_list:
                                if isinstance(ing, dict):
                                    yield ing
                    return
            # outros tipos: ignorar
            return

        # ---------- Campos base ----------
        comanda       = data.get('comanda') or ""
        pedidos       = to_list(data.get('pedidosSelecionados'))
        quantidades   = to_list(data.get('quantidadeSelecionada'))
        horario       = datetime.now(brazil).strftime('%H:%M')
        username      = data.get('username')
        preco_flag    = data.get('preco')  # brinde (mantém compat.)
        preco_modificado = data.get('precosUnitarios')
        print('preco modificado antes: ', preco_modificado)
        nomes         = to_list(data.get('nomeSelecionado'))
        token_user    = data.get('token_user')
        carrinho_primario      = data.get('carrinho')
        _register_carrinho_room(carrinho_primario)
        carrinho_destino = data.get('carrinho_destino',None)
        if carrinho_destino:
            exist = db.execute('SELECT 1 FROM carrinhos WHERE empresas = ?', carrinho_destino)
            if not exist:
                db.execute('INSERT INTO carrinhos (carrinho, empresas) VALUES (?,?)', carrinho_primario, carrinho_destino)
            else:
                db.execute('UPDATE carrinhos SET carrinho = ? WHERE empresas = ?', carrinho_primario, carrinho_destino)
            carrinho = carrinho_destino
            
        else:
            carrinho = carrinho_primario

        # opções estruturadas (podem vir str/json/list/dict)
        opcoesSelecionadas = parse_json_maybe(data.get('opcoesSelecionadas')) or []
        print('opcoesSelecionadas parsed: ', opcoesSelecionadas)

        # "extraSelecionados" é texto livre (lista 1-para-1 com pedidos)
        extra_list    = to_list(data.get('extraSelecionados'))

        # ---------- Metadados de entrega ----------
        modo_entrega  = data.get('modo_entrega')
        carrinho_nome = (data.get('carrinho') or '').strip()
        endereco_cli  = (data.get('endereco') or '').strip()

        if (modo_entrega or '').lower() == 'residencial':
            remetente_padrao     = 'Residencial'
            endereco_entrega_pad = endereco_cli
        else:
            remetente_padrao     = f'Carrinho:{carrinho_nome or carrinho}'
            endereco_entrega_pad = None

        # ---------- Seleção de opções por índice ----------
        def selecionar_opcoes_por_indice(idx):
            sel = opcoesSelecionadas
            if isinstance(sel, list):
                if idx < len(sel) and (isinstance(sel[idx], (list, dict))):
                    return sel[idx]
                if len(pedidos) == 1:
                    return sel
                return []
            elif isinstance(sel, dict):
                return sel
            else:
                return []

        # ---------- Soma de valor_extra (por unidade) ----------
        def somar_extra_por_unidade(selection):
            print('selection para somar extra por unidade: ', selection)
            def _sum_from_groups(groups):
                print('groups para somar extra por unidade: ', groups)
                total = 0.0
                custo_total = 0.0
                for g in groups:
                    if not isinstance(g, dict):
                        continue
                    opts = g.get('options') or g.get('opcoes') or []
                    if not isinstance(opts, list):
                        continue
                    for opt in opts:
                        if not isinstance(opt, dict):
                            continue
                        if opt.get('selecionado') is False:
                            continue
                        try:
                            total += float(opt.get('valor_extra') or 0)
                            custo_total += float(opt.get('custo') or 0)
                            print('custo extra: ', custo_total)
                        except Exception:
                            pass
                return total, custo_total

            if not selection:
                return 0.0, 0.0

            if isinstance(selection, dict):
                if isinstance(selection.get('options') or selection.get('opcoes'), list):
                    return _sum_from_groups([selection])
                groups = selection.get('groups') or selection.get('opcoes') or selection.get('options') or []
                if isinstance(groups, dict):
                    groups = [groups]
                if isinstance(groups, list):
                    if groups and isinstance(groups[0], dict) and 'valor_extra' in groups[0] and 'options' not in groups[0]:
                        groups = [{'nome': 'Opções', 'options': groups}]
                    return _sum_from_groups(groups)
                return 0.0, 0.0

            if isinstance(selection, list):
                if not selection:
                    return 0.0
                first = selection[0]
                if isinstance(first, dict) and ('options' in first or 'opcoes' in first):
                    return _sum_from_groups(selection)
                if isinstance(first, dict) and 'valor_extra' in first and 'options' not in first:
                    return _sum_from_groups([{'nome': 'Opções', 'options': selection}])
                return 0.0, 0.0

            return 0.0, 0.0

        # ---------- Logs úteis ----------
        print("[insert_order] username:", username)
        print("[insert_order] comanda:", comanda)
        print("[insert_order] pedidos:", pedidos)
        print("[insert_order] quantidades:", quantidades)
        print("[insert_order] horario:", horario)
        print("[insert_order] nomes:", nomes)
        print("[insert_order] carrinho:", carrinho)
        print("[insert_order] modo_entrega:", modo_entrega, "| carrinho:", carrinho_nome, "| endereco:", endereco_cli)
        print("[insert_order] opcoesSelecionadas:", opcoesSelecionadas)

        if not nomes:
            nomes = ["-1"] * len(pedidos)

        # ---------- Loop por item ----------
        pedidos_formatados_1=[]
        pedidos_formatados_3=[]
        ids_formatados_1 = []
        ids_formatados_3 = []
        for i, pedido in enumerate(pedidos):
            pedido = str(pedido).strip()
            if not pedido:
                continue
                
            quantidade = _to_float(get_or_default(quantidades, i, 1) or 1, 1.0)
            preco_modificado_item = float(preco_modificado[i]) if preco_modificado and i < len(preco_modificado) and preco_modificado[i] else None
            print('preco modificado depois: ', preco_modificado_item)
            # preço/categoria do cardápio
            preco_unitario_row = db.execute(
                'SELECT preco, categoria_id, custo FROM cardapio WHERE item = ? WHERE carrinho = ?', pedido, carrinho
            )
            
            if preco_unitario_row:
                categoria = preco_unitario_row[0]['categoria_id']
                if comanda != 'controle de estoque':
                    preco_base = float(preco_unitario_row[0]['preco'])
                    custo_base = float(preco_unitario_row[0]['custo'] or 0.0)
                else:
                    preco_base = 0.0
            else:
                categoria = 4
                preco_base = 0.0
                print('[insert_order] item não encontrado no cardápio:', pedido)

            # campos por item
            extra_txt      = (get_or_default(extra_list, i, "") or "").strip()
            nome_cliente   = get_or_default(nomes, i, "-1") or "-1"
            selecao_opcoes = selecionar_opcoes_por_indice(i)
            print('selecao_opcoes para item', i, ': ', selecao_opcoes)
            extra_unidade, custo_extra_unidade  = somar_extra_por_unidade(selecao_opcoes)
            opcoes_json    = json.dumps(selecao_opcoes or [], ensure_ascii=False)

            # ETA por categoria + notificação
            horario_entrega = None
            if categoria == 3:
                horario_entrega = (datetime.now(brazil) + timedelta(minutes=40)).strftime('%H:%M')
                enviar_notificacao_expo('Cozinha', 'Novo Pedido',
                                        f'{quantidade} {pedido} {extra_txt} na {comanda}', token_user, carrinho)
            elif categoria == 2:
                horario_entrega = (datetime.now(brazil) + timedelta(minutes=15)).strftime('%H:%M')
                enviar_notificacao_expo('Colaborador', 'Novo Pedido',
                                        f'{quantidade} {pedido} {extra_txt} na {comanda}', token_user, carrinho)

            # cálculo de preço
            preco_unitario_final = preco_base + float(extra_unidade or 0)
            custo_unitario_final = custo_base + float(custo_extra_unidade or 0)
            preco_total          = preco_unitario_final * quantidade
            custo_total          = custo_unitario_final * quantidade

            # remetente/endereço    
            remetente        = remetente_padrao
            endereco_entrega = endereco_entrega_pad
            lucro_unitario = preco_unitario_final - custo_unitario_final
            lucro_total    = lucro_unitario * quantidade
            # ---------- INSERT ----------
            if preco_flag:  # brinde
                print('entrou aqui')
                db.execute(
                    'INSERT INTO pedidos (comanda, pedido, quantidade, preco, categoria, inicio, estado, extra, opcoes, username, ordem, nome, remetente, endereco_entrega, dia, horario_para_entrega, lucro_unitario, lucro_total, carrinho) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    comanda, pedido, quantidade, 0, categoria, horario, 'A Fazer',
                    extra_txt, opcoes_json, username, 0, nome_cliente, remetente, endereco_entrega, dia, horario_entrega, 0.0, 0.0,carrinho
                )
            elif preco_modificado_item:
                preco_unitario_final = preco_modificado_item
                preco_total = preco_unitario_final * quantidade
                lucro_unitario = preco_unitario_final - custo_unitario_final
                lucro_total    = lucro_unitario * quantidade
                enviar_notificacao_expo('Colaborador', 'Novo Pedido',f'Alterou o preco de {preco_base} para {preco_unitario_final}', token_user, carrinho)
                insertAlteracoesTable('Pedidos', f'Preco modificado de {preco_base} para {preco_unitario_final} no pedido de {pedido} na comanda {comanda}', 'Modificou Preco', 'Inicio', username, carrinho)
                db.execute(
                    'INSERT INTO pedidos (comanda, pedido, quantidade, preco, preco_unitario, categoria, inicio, estado, extra, opcoes, username, ordem, nome, remetente, endereco_entrega, dia, horario_para_entrega, lucro_unitario, lucro_total, carrinho) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    comanda, pedido, quantidade,
                    preco_total, preco_unitario_final, categoria, horario, 'A Fazer',
                    extra_txt, opcoes_json, username, 0, nome_cliente, remetente, endereco_entrega, dia, horario_entrega, lucro_unitario, lucro_total, carrinho
                )
            elif not preco_unitario_row:  # fora do cardápio
                db.execute(
                    'INSERT INTO pedidos (comanda, pedido, quantidade, preco, categoria, inicio, estado, extra, opcoes, username, ordem, nome, remetente, endereco_entrega, dia, horario_para_entrega, carrinho) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    comanda, pedido, quantidade, 0, categoria, horario, 'A Fazer',
                    extra_txt, opcoes_json, username, 0, nome_cliente, remetente, endereco_entrega, dia, horario_entrega, carrinho
                )
            else:
                db.execute(
                    'INSERT INTO pedidos (comanda, pedido, quantidade, preco, preco_unitario, categoria, inicio, estado, extra, opcoes, username, ordem, nome, remetente, endereco_entrega, dia, horario_para_entrega, lucro_unitario, lucro_total, carrinho) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    comanda, pedido, quantidade,
                    preco_total, preco_unitario_final, categoria, horario, 'A Fazer',
                    extra_txt, opcoes_json, username, 0, nome_cliente, remetente, endereco_entrega, dia, horario_entrega, lucro_unitario, lucro_total, carrinho
                )

            # ---------- Eventos/estoque ----------
                        # ---------- Eventos/estoque ----------
            ingredientes_format = db.execute(
                'SELECT ingredientes FROM cardapio WHERE item = ? AND carrinho = ?',
                pedido, carrinho
            )

            # Se não achou linha no cardápio, tratamos como se não tivesse ingredientes
            ingredientes_veri = None
            if ingredientes_format and 'ingredientes' in ingredientes_format[0]:
                ingredientes_veri = ingredientes_format[0]['ingredientes']

            # 1) baixa do próprio item no estoque (quando existir como "Restante" ou cardápio sem registro)
            if ingredientes_veri is None:
                quantidade_anterior = db.execute(
                    'SELECT quantidade FROM estoque WHERE item = ? AND carrinho = ?',
                    pedido, carrinho
                )
                if quantidade_anterior:
                    quantidade_nova = _to_float(quantidade_anterior[0]['quantidade'], 0.0) - quantidade
                    if quantidade_nova < 0:
                        quantidade_nova = 0
                    db.execute(
                        'UPDATE estoque SET quantidade = ? WHERE item = ? AND carrinho = ?',
                        quantidade_nova, pedido, carrinho
                    )
                    if quantidade_nova < 10:
                        emit_for_carrinho(
                            'alerta_restantes',
                            {'quantidade': quantidade_nova, 'item': pedido},
                            broadcast=True,
                            carrinho=carrinho_primario
                        )
                    getEstoque({'emitir': True, 'carrinho': carrinho})

            # 2) baixa dos ingredientes do item
            if ingredientes_veri:
                ingredientes = str_para_lista_de_dicts(ingredientes_veri) or []
                for ingrediente in ingredientes:
                    id_ingrediente = ingrediente.get('id')
                    print('id_ingrediente', id_ingrediente)
                    unidade      = ingrediente.get('unidade')
                    qtd_por_item = _to_float(ingrediente.get('quantidade') or 0, 0.0)
                    qtd_total    = qtd_por_item * quantidade
                    estoque_id   = ingrediente.get('estoque_id')
                    _deduzir_estoque_por_ingrediente(
                        id_ingrediente, unidade, qtd_total, carrinho, estoque_id
                    )


            # 3) baixa dos ingredientes das OPÇÕES selecionadas
            for ing in _iter_ingredientes_de_opcoes(selecao_opcoes):
                id_ingrediente = ing.get('id')
                print('id_ingrediente opcao', id_ingrediente)
                unidade        = ing.get('unidade')
                qtd_por_item   = _to_float(ing.get('quantidade') or 0, 0.0)
                qtd_total      = qtd_por_item * quantidade
                estoque_id     = ing.get('estoque_id')
                _deduzir_estoque_por_ingrediente(id_ingrediente, unidade, qtd_total, carrinho, estoque_id)

            # ---- formatações e emissões por categoria (inalteradas) ----
            if categoria == 1:
                new_id = db.execute("SELECT last_insert_rowid() AS id")[0]['id']
                hora   = datetime.now(brazil).strftime('%H:%M')
                opcoes_fmt = format_opcoes_text(opcoes_json)
                print('endereco', endereco_entrega)
                dicionario_pedido={
                    'pedido':pedido,
                    'quantidade':quantidade,
                }
                if opcoes_fmt:
                    dicionario_pedido['opcoes']=opcoes_fmt
                if extra_txt:
                    dicionario_pedido['extra']=extra_txt
                dicionario_pedido['id'] = new_id
                pedidos_formatados_1.append(dicionario_pedido)
                ids_formatados_1.append(new_id)

            elif categoria == 3:
                new_id = db.execute("SELECT last_insert_rowid() AS id")[0]['id']
                hora   = datetime.now(brazil).strftime('%H:%M')
                opcoes_fmt = format_opcoes_text(opcoes_json)
                dicionario_pedido={
                    'pedido':pedido,
                    'quantidade':quantidade,
                }
                if opcoes_fmt:
                    dicionario_pedido['opcoes']=opcoes_fmt
                if extra_txt:
                    dicionario_pedido['extra']=extra_txt
                dicionario_pedido['id'] = new_id
                pedidos_formatados_3.append(dicionario_pedido)
                ids_formatados_3.append(new_id)
            
        if pedidos_formatados_1:
            ultimo_id_1 = ids_formatados_1[-1] if ids_formatados_1 else None
            emit_for_carrinho(
            'emitir_pedido_restante',
            {'mesa': comanda, 'pedido': pedidos_formatados_1,'remetente': carrinho, 'endereco': endereco_entrega,'prazo': horario_entrega,
                'hora': hora, 'sendBy': username, 'id': ultimo_id_1, 'ids': ids_formatados_1},
            broadcast=True,
            carrinho=carrinho_primario,)
        if pedidos_formatados_3:
            ultimo_id_3 = ids_formatados_3[-1] if ids_formatados_3 else None
            emit_for_carrinho(
                'emitir_pedido_cozinha',
                {'mesa': comanda, 'pedido': pedidos_formatados_3,'remetente': carrinho, 'endereco_entrega': endereco_entrega,'prazo': horario_entrega,
                    'hora': hora, 'sendBy': username, 'id': ultimo_id_3, 'ids': ids_formatados_3},
                broadcast=True,
                carrinho=carrinho_primario,
            )

        # Atualizações finais
        faturamento({'emitir': True, 'carrinho': carrinho_primario})
        getPedidos({'emitir': True, 'carrinho': carrinho_primario})
        getPedidosCC({'emitir': True, 'carrinho': carrinho_primario})
        getComandas({'emitir': True, 'carrinho': carrinho_primario})
        handle_get_cardapio(comanda, carrinho)

    except Exception as e:
        print("Erro ao inserir ordem:", e)
        emit('error', {'message': str(e)})




@socketio.on('faturamento')
def faturamento(data):

    if isinstance(data, dict):
        change = data.get('change', 0)
        dia = data_brasil_corte_3h() + timedelta(days=(change))
        dia_formatado = dia.strftime('%d/%m')
        emitir = data.get('emitir', True)
        carrinho = data.get('carrinho')
    else:
        dia = data_brasil_corte_3h()
        emitir = data if isinstance(data, bool) else True
        dia_formatado = dia.strftime('%d/%m')
        carrinho = 'NossoPoint'

    _register_carrinho_room(carrinho)
        
    metodosDict=db.execute("SELECT forma_de_pagamento,SUM(valor_total) AS valor_total FROM pagamentos WHERE dia =? AND carrinho = ? GROUP BY forma_de_pagamento",dia,carrinho)
    dinheiro=0
    credito=0
    debito=0
    pix=0
    for row in metodosDict:
        if row["forma_de_pagamento"]=="dinheiro":
            dinheiro+=row["valor_total"]
        elif row["forma_de_pagamento"]=="credito":
            credito+=row["valor_total"]
        elif row["forma_de_pagamento"]=="debito":
            debito+=row["valor_total"]
        elif row["forma_de_pagamento"]=="pix":
            pix+=row["valor_total"]

    # Executar a consulta e pegar o resultado
    caixinha = db.execute("SELECT COALESCE(SUM(caixinha),0) AS total_caixinha FROM pagamentos WHERE dia = ? AND carrinho = ?", dia, carrinho)
    caixinha = caixinha[0]['total_caixinha'] or 0
    dezporcento = db.execute("SELECT COALESCE(SUM(dez_por_cento),0) AS total_dezporcento FROM pagamentos WHERE dia = ? AND carrinho = ?", dia, carrinho)
    dezporcento = dezporcento[0]['total_dezporcento'] or 0
    desconto = db.execute("SELECT SUM(valor) AS total_desconto FROM pagamentos WHERE dia = ? AND tipo = ? AND carrinho = ?", dia, 'desconto', carrinho)
    desconto = desconto[0]['total_desconto'] or 0
        
    total_recebido = db.execute("SELECT SUM(valor_total) AS total_recebido FROM pagamentos WHERE dia = ? AND tipo = ? AND carrinho = ?", dia, 'normal', carrinho)
    total_recebido = total_recebido[0]['total_recebido'] or 0
    pedidosQuantDict = db.execute("""
        SELECT categoria,
               SUM(quantidade) AS quantidade_total,
               SUM(preco_unitario*NULLIF(quantidade,0))      AS preco_total,
               SUM(lucro_unitario*NULLIF(quantidade,0))      AS lucro_total
        FROM pedidos
        WHERE dia = ?
          AND pedido != ? AND carrinho = ?
        GROUP BY categoria
        ORDER BY categoria ASC
    """, dia, 'Comanda Aberta', carrinho)
    print('predidosQuantDict', pedidosQuantDict)
    drink = restante = porcao = 0
    faturamento_drink = faturamento_restante = faturamento_porcao = 0
    faturamento_previsto = 0
    lucro_previsto = 0
    lucro_drink = lucro_restante = lucro_porcao = 0
    for row in pedidosQuantDict:
        cat = row.get('categoria')
        qtd = row.get('quantidade_total') or 0
        preco_cat= row.get('preco_total') or 0
        if cat == '1':
            restante = qtd
            faturamento_restante = preco_cat
            lucro_restante = (row.get('lucro_total') or 0)
        elif cat == '2':
            drink = qtd
            faturamento_drink = preco_cat
            lucro_drink = (row.get('lucro_total') or 0)
        elif cat == '3':
            porcao = qtd
            faturamento_porcao = preco_cat
            lucro_porcao = (row.get('lucro_total') or 0)
        faturamento_previsto += (row.get('preco_total') or 0)
        lucro_previsto += (row.get('lucro_total') or 0)


    pedidos = (drink or 0) + (restante or 0) + (porcao or 0)
    vendas_user = []
    vendas_user =db.execute('SELECT username, SUM(preco_unitario *NULLIF(quantidade,0)) AS valor_vendido, SUM(quantidade)  AS quant_vendida FROM pedidos WHERE dia = ? AND carrinho = ? GROUP BY username ORDER BY SUM(preco_unitario*NULLIF(quantidade,0)) DESC',dia, carrinho)
    print('vendas_user', vendas_user)

    emit_for_carrinho(
        'faturamento_enviar',
        {'dia': str(dia_formatado),
         'faturamento': total_recebido,
         'faturamento_previsto': faturamento_previsto,
         'lucro_previsto': lucro_previsto,
         'drink': drink,
         'porcao': porcao,
         "restante": restante,
         "faturamento_drink": faturamento_drink,
         "faturamento_porcao": faturamento_porcao,
         "faturamento_restante": faturamento_restante,
         "lucro_drink": lucro_drink,
         "lucro_porcao": lucro_porcao,
         "lucro_restante": lucro_restante,
         "pedidos": pedidos,
         "caixinha": caixinha,
         "dezporcento": dezporcento,
         "desconto": desconto,
         "pix": pix,
         "debito": debito,
         "credito": credito,
         "dinheiro": dinheiro,
         "vendas_user": vendas_user},
        broadcast=emitir,
        carrinho=carrinho,
    )
    


@socketio.on('alterarValor')
def alterarValor(data):
    dia = data_brasil_corte_3h()
    valor = float(data.get('valor'))
    comanda = data.get('comanda')
    carrinho = data.get('carrinho')
    print(valor)
    horario = datetime.now(brazil).strftime('%H:%M')
    db.execute('INSERT INTO pagamentos(valor,valor_total,comanda,ordem,tipo,dia,horario,carrinho) VALUES (?,?,?,?,?,?,?,?)',valor,valor,comanda,0,'desconto',dia,horario,carrinho)
    faturamento({'emitir': True, 'carrinho': carrinho})
    handle_get_cardapio(comanda, carrinho)



from decimal import Decimal, InvalidOperation

# ... seu setup (brazil tz, db, socketio, etc.)
def _json_safe(o):
    if isinstance(o, Decimal):
        # envie como string para manter precisão (ou use float() se preferir número)
        return f"{o:.2f}"
    if isinstance(o, dict):
        return {k: _json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_json_safe(v) for v in o]
    return o
def _to_int(x, default=0):
    try:
        if x is None or x == '':
            return default
        return int(x)
    except (ValueError, TypeError):
        try:
            return int(float(str(x).replace(',', '.')))
        except Exception:
            return default

def _to_decimal(x, default=Decimal('0.00')):
    if x is None or x == '':
        return default
    try:
        return Decimal(str(x).replace(',', '.'))
    except (InvalidOperation, ValueError, TypeError):
        return default

#Formatar opcoes para impressao na cozinha
def format_opcoes_text(
    raw: Any,
    *,
    sep_groups: str = "\n",
    sep_label: str = ": ",
    sep_opts: str = ", ",
) -> str:
    """
    Converte 'opcoes' JSON no texto:
      "Grupo : op1, op2 | Outro : opA"
    Suporta raw como str JSON, dict (um grupo) ou list (vários grupos).
    """
    if not raw:
        return ""

    data = raw
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return ""
        try:
            data = json.loads(s)
        except Exception:
            # não é JSON válido; não arriscamos interpretar
            return ""

    groups: List[Dict] = []
    if isinstance(data, list):
        groups = data
    elif isinstance(data, dict) and "options" in data:
        groups = [data]
    else:
        return ""

    parts: List[str] = []
    for g in groups:
        group_name = str(g.get("nome", "")).strip()
        opts = g.get("options") or []

        # pega só nomes não vazios
        opt_names = []
        for o in opts:
            name = o.get("nome")
            if name is None:
                continue
            name = str(name).strip()
            if name:
                opt_names.append(name)

        if not opt_names:
            continue

        opts_txt = sep_opts.join(opt_names)
        parts.append(f"{group_name}{sep_label}{opts_txt}" if group_name else opts_txt)
    print(sep_groups.join(parts))
    return sep_groups.join(parts)

def _ajusta_estoque(item_nome, delta_estoque, carrinho):
    """
    Aplica delta no estoque:
      delta_estoque > 0  => aumenta estoque
      delta_estoque < 0  => diminui estoque
    """
    if not item_nome:
        return

    # Lê quantidade atual (se houver)
    row = db.execute(
        'SELECT quantidade FROM estoque WHERE item = ? AND carrinho = ?',
        item_nome, carrinho
    )
    if row:
        atual = _to_int(row[0]['quantidade'], 0)
        novo = max(0, atual + _to_int(delta_estoque, 0))  # evita negativo
        db.execute(
            'UPDATE estoque SET quantidade = ? WHERE item = ? AND carrinho = ?',
            novo, item_nome, carrinho
        )
    else:
        # Se não existe o item no estoque e delta for positivo, cria; se negativo, cria 0.
        qtd = max(0, _to_int(delta_estoque, 0))
        db.execute(
            'INSERT INTO estoque (item, quantidade, carrinho) VALUES (?, ?, ?)',
            item_nome, qtd, carrinho
        )


#helpers atualizar pedido
def _to_int(v, default=0):
    try:
        if v is None or v == '':
            return default
        return int(float(str(v).replace(',', '.')))
    except Exception:
        return default

def _to_decimal(v, default=0.0):
    try:
        if v is None or v == '':
            return default
        return float(str(v).replace(',', '.'))
    except Exception:
        return default

def _normalize_horario(h):
    if not h:
        return None
    s = str(h).strip()
    if re.fullmatch(r'\d{1,2}:\d{2}', s):
        hh, mm = s.split(':', 1)
        try:
            hh = max(0, min(23, int(hh)))
            mm = max(0, min(59, int(mm)))
            return f"{hh:02d}:{mm:02d}"
        except Exception:
            return None
    return None

# --------- NOVO: limpeza profunda de opcoes ---------
_KEY_FIXES = {
    'max_selected?': 'max_selected',
    'obrigatorio?':  'obrigatorio',
    'valor_extra?':  'valor_extra',
    # pode expandir aqui se surgirem outras
}

def _coerce_value_for_key(k, v):
    """Força tipos esperados para algumas chaves conhecidas."""
    base = k.rstrip('?')
    if base == 'max_selected':
        return _to_int(v, 0)
    if base == 'obrigatorio':
        # aceita "true"/"false", 1/0, "1"/"0"
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        return s in ('1', 'true', 'on', 'yes', 'y', 'sim')
    if base == 'valor_extra':
        return _to_decimal(v, 0.0)
    return v

def _deep_sanitize_opcoes(obj):
    """Remove '?' de chaves, força tipos, percorre recursivamente dict/list."""
    if isinstance(obj, dict):
        new_d = {}
        for k, v in obj.items():
            # renomeia chaves que terminam com '?'
            k2 = _KEY_FIXES.get(k, k.rstrip('?'))
            # recursão no valor
            v2 = _deep_sanitize_opcoes(v)
            # força tipos para chaves conhecidas
            v2 = _coerce_value_for_key(k2, v2)
            new_d[k2] = v2
        return new_d
    if isinstance(obj, list):
        return [_deep_sanitize_opcoes(x) for x in obj]
    # strings “normais”: apenas retorna (não removo '?' de conteúdo textual do usuário)
    return obj

def _normalize_opcoes(val):
    """
    Garante que 'opcoes' seja uma STRING JSON sem '?' solto e com chaves corretas.
    - Se for dict/list: limpa recursivamente, força tipos, dumps
    - Se for string: tenta limpar '?' problemáticos e validar
    - Fallback: "[]"
    """
    if val is None:
        return "[]"

    def _dumps_safe(obj):
        # ❌ NÃO usar separators=(',', ':')
        # Isso gera '"max_selected":1' -> cria ':1' dentro do SQL
        #
        # ✅ Usa o padrão (ou ': '), que gera '"max_selected": 1'
        s = json.dumps(obj, ensure_ascii=False)  # já usa ': ' por padrão
        # safety net: remove qualquer '?' perdido
        if '?' in s:
            s = s.replace('?', '')
        return s

    # Já objeto/array
    if isinstance(val, (list, dict)):
        try:
            clean = _deep_sanitize_opcoes(val)
            return _dumps_safe(clean)
        except Exception:
            return "[]"

    # String -> limpar marcadores '?' que surgem do editor
    s = str(val).strip()
    # remoções dirigidas (quando o ? está grudado ao nome da chave)
    s = re.sub(r'("max_selected")\s*\?', r'\1', s)
    s = re.sub(r'("obrigatorio")\s*\?',  r'\1', s)
    s = re.sub(r'("valor_extra")\s*\?',  r'\1', s)
    # safety net: tira qualquer '?' remanescente
    s = s.replace('?', '')

    try:
        obj = json.loads(s)
        clean = _deep_sanitize_opcoes(obj)
        return _dumps_safe(clean)
    except Exception:
        return "[]"

def update_pedidos_opcoes_sqlite(params):
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            conn.execute(
                """
                UPDATE pedidos
                   SET comanda = :comanda,
                       pedido = :pedido,
                       quantidade = :quantidade,
                       quantidade_paga = :quantidade_paga,
                       preco_unitario = :preco_unitario,
                       preco = :preco,
                       extra = :extra,
                       opcoes = :opcoes,
                       horario_para_entrega = :horario,
                       carrinho = :carrinho
                 WHERE id = :id AND dia = :dia
                """,
                params
            )
def insertAlteracoesTableSql(tabela, alteracao, tipo, tela, usuario, carrinho):
    #!!
    data_brasil_corte_3h()
    horario = datetime.now(brazil).strftime('%H:%M')
    hoje = data_brasil_corte_3h()
    # 🚫 não usar db.execute aqui
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            conn.execute(
                """
                INSERT INTO alteracoes (tabela,alteracao,tipo,usuario,tela,dia,horario, carrinho)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (tabela, alteracao, tipo, usuario, tela, hoje, horario,carrinho)
            )
import json

def _safe_json_loads(v):
    """Tenta carregar JSON; aceita já-dict/list; senão retorna None."""
    if v is None:
        return None
    if isinstance(v, (dict, list)):
        return v
    if not isinstance(v, str):
        return None
    s = v.strip()
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None

def _groups_to_map(lst):
    """
    Converte lista de grupos em dict: {grupo_nome: [ {nome, valor_extra, esgotado}, ... ] }.
    Suporta formatos comuns: {"nome": "...", "options":[...]}, ou {"grupo_slug": "...", "opcao": "..."}.
    """
    out = {}
    seq = lst if isinstance(lst, list) else [lst] if lst is not None else []
    for g in seq:
        if not isinstance(g, dict):
            continue
        gname = (g.get("nome") or g.get("grupo") or g.get("grupo_slug") or "").strip()
        if not gname:
            continue
        opts = []
        if isinstance(g.get("options"), list):
            for it in g["options"]:
                if isinstance(it, dict):
                    opts.append({
                        "nome": (it.get("nome") or it.get("opcao") or "").strip(),
                        "valor_extra": it.get("valor_extra"),
                        "esgotado": it.get("esgotado"),
                    })
        else:
            # formato unitário: {"opcao": "..."}
            if "opcao" in g or "nome" in g:
                opts.append({
                    "nome": (g.get("opcao") or g.get("nome") or "").strip(),
                    "valor_extra": g.get("valor_extra"),
                    "esgotado": g.get("esgotado"),
                })
        out[gname] = opts
    return out

def summarize_opcoes_diff(old_opcoes, new_opcoes):
    """
    Retorna uma string curta só com o que mudou nas 'opcoes', ou None se não houve mudança
    ou se não for possível comparar como JSON.
    - Mostra adicionados/retirados por grupo.
    - Para opções em comum, mostra campos alterados (valor_extra, esgotado).
    """
    o = _safe_json_loads(old_opcoes)
    n = _safe_json_loads(new_opcoes)
    if o is None or n is None:
        # fallback: se não deu pra comparar estruturalmente, só acusa mudança ou não
        return None if str(old_opcoes) == str(new_opcoes) else "opções alteradas"

    om = _groups_to_map(o)
    nm = _groups_to_map(n)

    parts = []
    for g in sorted(set(om.keys()) | set(nm.keys())):
        oset = {x["nome"] for x in om.get(g, []) if x.get("nome")}
        nset = {x["nome"] for x in nm.get(g, []) if x.get("nome")}

        added = sorted(nset - oset)
        removed = sorted(oset - nset)
        changes = []
        if removed:
            changes.append("de " + ", ".join(removed))
        if added:
            changes.append("para " + ", ".join(added))

        # campos alterados nas opções em comum
        common = oset & nset
        for name in sorted(common):
            oitem = next((x for x in om[g] if x.get("nome") == name), {})
            nitem = next((x for x in nm[g] if x.get("nome") == name), {})
            sub = []
            if oitem.get("valor_extra") != nitem.get("valor_extra"):
                sub.append(f"valor: {oitem.get('valor_extra')}→{nitem.get('valor_extra')}")
            if oitem.get("esgotado") != nitem.get("esgotado"):
                sub.append(f"esgotado: {oitem.get('esgotado')}→{nitem.get('esgotado')}")
            if sub:
                changes.append(f"{name} ({'; '.join(sub)})")

        if changes:
            parts.append(f"{g}: " + " ".join(changes))

    return " | ".join(parts) if parts else None

def _carregar_ingredientes_base(item_nome, carrinho):
    """
    Lê ingredientes do cardápio para um item.
    Retorna lista de dicts ou [].
    """
    if not item_nome:
        return []
    rows = db.execute(
        'SELECT ingredientes FROM cardapio WHERE item = ? AND carrinho = ?',
        item_nome, carrinho
    )
    if not rows:
        return []
    ingredientes_raw = rows[0].get('ingredientes')
    if not ingredientes_raw:
        return []
    try:
        return str_para_lista_de_dicts(ingredientes_raw) or []
    except Exception:
        return []
    
def _extract_ingredientes_from_opcoes(opcoes_val):
    """
    Extrai todos os ingredientes presentes nas opções:
    percorre grupos -> options -> ingredientes
    Retorna lista de dicts (cada dict é um ingrediente).
    """
    if not opcoes_val:
        return []

    obj = None
    # já objeto/lista
    if isinstance(opcoes_val, (list, dict)):
        obj = opcoes_val
    else:
        obj = _safe_json_loads(opcoes_val)
        if obj is None:
            try:
                obj = json.loads(str(opcoes_val))
            except Exception:
                return []

    ingredientes = []
    for g in obj or []:
        options = g.get('options') or []
        for opt in options:
            for ing in opt.get('ingredientes') or []:
                ingredientes.append(ing)
    return ingredientes

def _ajustar_estoque_por_ingrediente(
    id_ingrediente,
    unidade,
    quantidade_necessaria,
    carrinho,
    estoque_id,
    devolver: bool,
):
    """
    Ajusta estoque de UM ingrediente:
      devolver=True  -> devolve para o estoque (somar)
      devolver=False -> consome do estoque (subtrair)
    Respeita unidade e quantidade_por_unidade, e escolhe
    entre 'estoque' e 'estoque_geral' pelo estoque_id.
    """
    if not id_ingrediente or not quantidade_necessaria:
        return

    # escolhe tabela de estoque pela flag estoque_id
    estoque = 'estoque' if str(estoque_id) == '1' else 'estoque_geral'

    row = db.execute(
        f'''
        SELECT quantidade, quantidade_total, quantidade_por_unidade
        FROM {estoque}
        WHERE id = ? AND carrinho = ?
        ''',
        id_ingrediente, carrinho
    )
    if not row:
        return

    quantidade_atual_unid = _to_float(row[0].get('quantidade'), 0.0)
    quantidade_atual_total = _to_float(row[0].get('quantidade_total'), 0.0)
    qpu = _to_float(row[0].get('quantidade_por_unidade', 1), 1.0)

    # + se devolver, - se consumir
    sinal = 1.0 if devolver else -1.0
    qtd = _to_float(quantidade_necessaria, 0.0) * sinal

    if (unidade or '').strip() == 'unidade(s)':
        # trabalha em unidades + espelha em total usando qpu
        nova_qtd_unid = quantidade_atual_unid + qtd
        nova_qtd_total = quantidade_atual_total + (qtd * qpu)
        if nova_qtd_unid < 0:
            nova_qtd_unid = 0
        if nova_qtd_total < 0:
            nova_qtd_total = 0
    else:
        # trabalha direto em quantidade_total e converte pra unidades
        nova_qtd_total = quantidade_atual_total + qtd
        if nova_qtd_total < 0:
            nova_qtd_total = 0
        nova_qtd_unid = arredondar_personalizado(nova_qtd_total, qpu)

    db.execute(
        f'''
        UPDATE {estoque}
        SET quantidade = ?, quantidade_total = ?
        WHERE id = ? AND carrinho = ?
        ''',
        nova_qtd_unid, nova_qtd_total, id_ingrediente, carrinho
    )

def _to_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default

def _ajusta_ingredientes_estado(
    ingredientes_base,
    ingredientes_opcoes,
    qtd_item,
    carrinho,
    devolver: bool,
):
    """
    Aplica ajuste no estoque para TODOS os ingredientes de um estado:
    - ingredientes_base: lista de dicts do cardápio
    - ingredientes_opcoes: lista de dicts vindos das opções
    - qtd_item: quantidade de itens no pedido
    - devolver=True  -> devolve tudo pro estoque (estado antigo)
    - devolver=False -> consome do estoque (estado novo)
    """
    qtd_item = _to_float(qtd_item, 0.0)
    if qtd_item <= 0:
        return

    for ing in (ingredientes_base or []):
        id_ing = ing.get('id')
        unidade_ing = ing.get('unidade')
        estoque_id = ing.get('estoque_id')
        qtd_por_item = _to_float(ing.get('quantidade') or 0, 0.0)
        qtd_total_ing = qtd_por_item * qtd_item
        _ajustar_estoque_por_ingrediente(
            id_ing, unidade_ing, qtd_total_ing,
            carrinho, estoque_id, devolver
        )

    for ing in (ingredientes_opcoes or []):
        id_ing = ing.get('id')
        unidade_ing = ing.get('unidade')
        estoque_id = ing.get('estoque_id')
        qtd_por_item = _to_float(ing.get('quantidade') or 0, 0.0)
        qtd_total_ing = qtd_por_item * qtd_item
        _ajustar_estoque_por_ingrediente(
            id_ing, unidade_ing, qtd_total_ing,
            carrinho, estoque_id, devolver
        )

@socketio.on('atualizar_pedidos')
def handle_atualizar_pedidos(data):
    dia = data_brasil_corte_3h()
    p = data.get('pedidoAlterado') or {}
    usuario = data.get('usuario')
    token_user = data.get('token')
    carrinho = data.get('carrinho')

    if not p or 'id' not in p:
        return emit('erro_pedidos', {'msg': 'Payload inválido para atualizar_pedidos'})

    atual_rows = db.execute(
        '''SELECT comanda, pedido, quantidade, quantidade_paga, preco_unitario, preco, extra, opcoes, horario_para_entrega
           FROM pedidos WHERE id = ? AND dia = ?''',
        p['id'], dia
    )
    if not atual_rows:
        return emit('erro_pedidos', {'msg': 'Pedido não encontrado para hoje'})

    atual = atual_rows[0]

    # --- normalizações de opcoes/horário antes, para usar em log e estoque ---
    old_opcoes_raw = atual.get('opcoes')
    raw_novas_opcoes = p.get('opcoes', old_opcoes_raw)
    opcoes_normalizadas = _normalize_opcoes(raw_novas_opcoes)

    old_horario_raw = atual.get('horario_para_entrega')
    raw_novo_horario = p.get('horario_para_entrega', old_horario_raw)
    horario_normalizado = _normalize_horario(raw_novo_horario)

    # --- normalizações seguras dos demais campos ---
    novo = {
        'comanda':              p.get('comanda', atual['comanda']),
        'pedido':               p.get('pedido',  atual['pedido']),
        'quantidade':           _to_int(p.get('quantidade', atual['quantidade'])),
        'quantidade_paga':      _to_int(p.get('quantidade_paga', atual.get('quantidade_paga'))),
        'preco_unitario':       _to_decimal(p.get('preco_unitario', atual.get('preco_unitario'))),
        'preco':                _to_decimal(p.get('preco', atual['preco'])),
        'extra':                p.get('extra',   atual['extra']),
        'opcoes':               opcoes_normalizadas,
        'horario_para_entrega': horario_normalizado,
    }

    # log de alterações (sem quebrar se algum valor for None)
    alteracoes = []
    titulo_item = p.get('pedido', atual['pedido'])
    campos = [
        'comanda', 'pedido', 'quantidade', 'quantidade_paga',
        'preco_unitario', 'preco', 'extra', 'opcoes',
        'horario_para_entrega'
    ]

    for k in campos:
        if k == 'opcoes':
            old_v = old_opcoes_raw
            new_v = novo['opcoes']
            diff = summarize_opcoes_diff(old_v, new_v)
            if diff:  # só loga se houve mudança real
                alteracoes.append(f"opções: {diff}")
            continue

        if k == 'horario_para_entrega':
            old_v = old_horario_raw
            new_v = novo['horario_para_entrega']
        else:
            old_v = atual.get(k)
            new_v = novo.get(k)

        # demais campos: só loga se mudou de fato (comparação robusta como string)
        if str(old_v) != str(new_v):
            alteracoes.append(f"{k}: de {old_v} para {new_v}")

    old_item = atual['pedido']
    new_item = novo['pedido']

    try:
        db.execute('BEGIN')

        # normalizações finais
        opcoes_str = novo['opcoes']
        horario_str = novo['horario_para_entrega']
        dia_str = dia.isoformat()

        params = {
            "comanda": novo['comanda'],
            "pedido": new_item,
            "quantidade": _to_int(novo['quantidade']),
            "quantidade_paga": _to_int(novo['quantidade_paga']),
            "preco_unitario": str(_to_decimal(novo['preco_unitario'])),
            "preco": str(_to_decimal(novo['preco'])),
            "extra": novo['extra'],
            "opcoes": opcoes_str,
            "horario": horario_str,
            "id": p['id'],
            "dia": dia_str,
            "carrinho": carrinho,
        }

        # Atualiza o pedido na tabela pedidos (via sqlite nativo)
        update_pedidos_opcoes_sqlite(params)

        # ===================== AJUSTE DE ESTOQUE =====================
        old_qtd = _to_int(atual['quantidade'])
        new_qtd = _to_int(novo['quantidade'])
        old_opcoes = old_opcoes_raw
        new_opcoes = opcoes_str

        # ingredientes base e das opções do estado antigo
        ing_base_old = _carregar_ingredientes_base(old_item, carrinho)
        ing_opc_old = _extract_ingredientes_from_opcoes(old_opcoes)

        # ingredientes base e das opções do novo estado
        if new_item == old_item:
            ing_base_new = ing_base_old
        else:
            ing_base_new = _carregar_ingredientes_base(new_item, carrinho)
        ing_opc_new = _extract_ingredientes_from_opcoes(new_opcoes)

        usa_ing_old = bool(ing_base_old or ing_opc_old)
        usa_ing_new = bool(ing_base_new or ing_opc_new)

        if usa_ing_old or usa_ing_new:
            # 1) Devolve tudo que o estado antigo consumiu
            if usa_ing_old:
                _ajusta_ingredientes_estado(
                    ing_base_old, ing_opc_old,
                    old_qtd, carrinho,
                    devolver=True
                )
            else:
                # estado antigo não tinha ingredientes -> devolve por item
                _ajusta_estoque(old_item, +old_qtd, carrinho)

            # 2) Consome o que o novo estado precisa
            if usa_ing_new:
                _ajusta_ingredientes_estado(
                    ing_base_new, ing_opc_new,
                    new_qtd, carrinho,
                    devolver=False
                )
            else:
                # novo estado não tem ingredientes -> consome por item
                _ajusta_estoque(new_item, -new_qtd, carrinho)
        else:
            # Nenhum dos dois estados tem ingredientes -> lógica antiga pura
            if new_item != old_item:
                _ajusta_estoque(old_item, +old_qtd, carrinho)
                _ajusta_estoque(new_item, -new_qtd, carrinho)
            else:
                delta_estoque = _to_int(atual['quantidade']) - _to_int(novo['quantidade'])
                if delta_estoque != 0:
                    _ajusta_estoque(new_item, delta_estoque, carrinho)

        db.execute('COMMIT')

    except Exception as e:
        db.execute('ROLLBACK')
        print('Erro ao atualizar pedido:', e)
        return emit('erro_pedidos', {'msg': 'Falha ao atualizar pedido', 'erro': str(e)})

    alter_str = (
        f"{titulo_item} — " + "\n".join(alteracoes)
        if alteracoes
        else f"{titulo_item} (sem alterações detectadas)"
    )
    insertAlteracoesTableSql('pedidos', alter_str, 'editou', 'Tela Pedidos', usuario, carrinho)
    enviar_notificacao_expo('ADM', 'Pedido Editado', f'{usuario} Editou {alter_str}', token_user, usuario, carrinho)

    # Atualiza telas de pedidos/cardápio + estoques
    getEstoque({'emitir': True, 'carrinho': carrinho})
    getEstoqueGeral({'emitir': True, 'carrinho': carrinho})
    getPedidos({'emitir': True, 'carrinho': carrinho})
    handle_get_cardapio(str(novo['comanda']), carrinho)


@socketio.on('desfazer_pagamento')
def desfazer_pagamento(data):
    dia = data_brasil_corte_3h()
    comanda = data.get('comanda')
    carrinho = data.get('carrinho')
    ids_dict = db.execute('''
        SELECT ids FROM pagamentos
        WHERE id = (
            SELECT id FROM pagamentos
            WHERE comanda = ? AND ordem = ? AND dia = ? AND carrinho = ?
            ORDER BY id DESC
            LIMIT 1
        )
    ''', comanda, 1, dia, carrinho)
    print('ids_dict', ids_dict)
    if ids_dict:
        ids = ids_dict[0]['ids']
        print('ids', ids)
        if ids:
            print('tem ids')
            ids_list = json.loads(ids)
            print('ids_list', ids_list)
            for row in ids_list:
                db.execute('UPDATE pedidos SET quantidade_paga = quantidade_paga - ?, preco = preco_unitario *NULLIF((quantidade-(quantidade_paga - ?)),0) WHERE id = ? AND dia = ?',row['quantidade'],row['quantidade'],row['id'],dia)
    db.execute('''
        DELETE FROM pagamentos
        WHERE id = (
            SELECT id FROM pagamentos
            WHERE comanda = ? AND ordem = ? AND dia = ? AND carrinho = ?
            ORDER BY id DESC
            LIMIT 1
        )
    ''', comanda, 1, dia, carrinho)

    db.execute('UPDATE pagamentos SET ordem = ordem - ? WHERE comanda = ? AND dia = ? AND ordem != ? AND carrinho = ?',1,comanda,dia,0,carrinho)
    db.execute('UPDATE pedidos SET ordem = ordem - ? WHERE comanda = ? AND dia = ? AND ordem != ? AND carrinho = ?',1,comanda,dia,0,carrinho)
    faturamento({'emitir': True, 'carrinho': carrinho})
    handle_get_cardapio(comanda, carrinho)
    getComandas({'emitir': True, 'carrinho': carrinho})



@socketio.on('delete_comanda')
def handle_delete_comanda(data):
    try:
        dia = data_brasil_corte_3h()
        carrinho = data.get('carrinho')
        _register_carrinho_room(carrinho)

        comanda = data.get('fcomanda')

        # pode vir None quando é chamado a partir do pagar_parcial
        valor_pago_dict = data.get('valor_pago')

        if valor_pago_dict is not None:
            # fluxo "Pagar Restante" vindo do app
            valor_pago = float(valor_pago_dict)

            caixinha = data.get('caixinha', 0)
            dez_por_cento = data.get('dez_por_cento', 0)

            if not caixinha:
                caixinha = 0
            else:
                caixinha = float(caixinha)

            if not dez_por_cento:
                dez_por_cento = 0
            else:
                dez_por_cento = float(dez_por_cento)

            forma_de_pagamento = data.get('forma_de_pagamento')
            print('forma de pagamento', forma_de_pagamento)
            print(f'Data de hoje: {dia}')

            # só insere pagamento se valor_pago veio no payload
            db.execute(
                'INSERT INTO pagamentos (valor,valor_total,caixinha,dez_por_cento,tipo,ordem,dia,forma_de_pagamento,comanda,horario,carrinho) '
                'VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                valor_pago,
                valor_pago + caixinha + dez_por_cento,
                caixinha,
                dez_por_cento,
                'normal',
                0,
                dia,
                forma_de_pagamento,
                comanda,
                datetime.now(brazil).strftime('%H:%M'),
                carrinho
            )

        # daqui pra baixo SEMPRE roda: só “fecha” a comanda
        db.execute(
            'UPDATE pedidos SET ordem = ordem + ? WHERE comanda = ? AND dia = ? AND carrinho = ?',
            1, comanda, dia, carrinho
        )
        db.execute(
            'UPDATE pagamentos SET ordem = ordem + ? WHERE comanda = ? AND dia = ? AND carrinho = ?',
            1, comanda, dia, carrinho
        )

        faturamento({'emitir': True, 'carrinho': carrinho})
        getComandas({'emitir': True, 'carrinho': carrinho})
        getPedidos({'emitir': True, 'carrinho': carrinho})
        handle_get_cardapio(comanda, carrinho)
        emit_for_carrinho('comanda_deleted', {'fcomanda': comanda}, broadcast=True, carrinho=carrinho)

    except Exception as e:
        print("Erro ao apagar comanda:", e)
        emit('error', {'message': str(e)})




@socketio.on('pagar_parcial')
def pagar_parcial(data):
    comanda = data.get('fcomanda')
    carrinho = data.get('carrinho')
    print(f'pagar parcial comanda : {comanda}')
    valor_pago = float(data.get('valor_pago'))
    print(f'valor pago : {valor_pago}')
    forma_de_pagamento = data.get('forma_de_pagamento')
    caixinha = data.get('caixinha',0)
    dez_por_cento = data.get('dez_por_cento',0)
    if not caixinha:
        caixinha=0
    else:
        caixinha=float(caixinha)
    if not dez_por_cento:
        dez_por_cento=0
    else:
        dez_por_cento=float(dez_por_cento)
    
    dia = data_brasil_corte_3h()
    
    totalComandaDict = db.execute('SELECT SUM(preco) AS total FROM pedidos WHERE comanda = ? AND ordem = ? AND dia = ? AND carrinho = ?', comanda, 0,dia, carrinho)
    valorTotalDict = db.execute('SELECT SUM(valor_total) as total FROM pagamentos WHERE dia = ? AND comanda = ? AND ordem = ? AND tipo = ? AND carrinho = ?',dia,comanda,0,'normal',carrinho)
    
    if valorTotalDict and valorTotalDict[0]['total']:
        valorTotal = valorTotalDict[0]['total']
    else:
        valorTotal = 0

    db.execute('INSERT INTO pagamentos (valor,valor_total,caixinha,dez_por_cento,tipo,ordem,dia,forma_de_pagamento,comanda,horario,carrinho) VALUES (?,?,?,?,?,?,?,?,?,?,?)',valor_pago,valor_pago+caixinha+dez_por_cento,caixinha,dez_por_cento,'normal',0,dia,forma_de_pagamento,comanda,datetime.now(brazil).strftime('%H:%M'),carrinho)
    faturamento({'emitir': True, 'carrinho': carrinho})
    if valorTotal+valor_pago>=totalComandaDict[0]['total']:
        handle_delete_comanda({'fcomanda':comanda, 'carrinho':carrinho})
    
    handle_get_cardapio(comanda, carrinho)


@socketio.on('get_ingredientes')
def get_ingredientes(data):
    carrinho = data.get('carrinho')
    item = data.get('ingrediente')
    ingredientes = db.execute(
        'SELECT instrucoes FROM cardapio WHERE item = ? AND carrinho = ?', item, carrinho)

    if ingredientes:
        ingrediente = ingredientes[0]['instrucoes']
        data = []
        letras = ''
        key = ''
        dado = ''
        for j in ingrediente:
            if j == ':':
                key = letras
                letras = ''
            elif j == '-':
                dado = letras
                letras = ''
                data.append({'key': key, 'dado': dado})
            else:
                letras += j
        print(data)
        emit('ingrediente', {
             'data': data})



@socketio.on('inserir_preparo')
def inserir_preparo(data):
    id = data.get('id')
    carrinho = data.get('carrinho')
    estado = data.get('estado')
    horario = datetime.now(pytz.timezone(
        "America/Sao_Paulo")).strftime('%H:%M')
    print(f'id: {id}, estado: {estado}, horario: {horario}')

    if estado == 'Pronto':
        print('entrou no pronto')
        db.execute('UPDATE pedidos SET fim = ? WHERE id = ?', horario, id)
    elif estado == 'Em Preparo':
        print('entrou no em preparo')
        db.execute('UPDATE pedidos SET comecar = ? WHERE id = ? ', horario, id)
    
    db.execute('UPDATE pedidos SET estado = ? WHERE id = ?',estado,
               id)
    print('depois do update')
    getPedidos({'emitir':True, 'carrinho': carrinho})
    getPedidosCC({'emitir':True, 'carrinho': carrinho})


@socketio.on('atualizar_estoque_geral')
def atualizar_estoque_geral(data):
    carrinho = data.get('carrinho')
    usuario = data.get('username')
    itensAlterados = data.get('itensAlterados')
    token_user = data.get('token')
    for i in itensAlterados:
        item = i['item']
        anterior=''
        quantidade = i['quantidade']
        quantidadeAnterior=db.execute("SELECT quantidade,quantidade_por_unidade,quantidade_total FROM estoque_geral WHERE item=? AND carrinho = ?",item, carrinho)
        if quantidadeAnterior:
            anterior=quantidadeAnterior[0]['quantidade']
            diferenca=float(anterior)-float(quantidade)
            quantidade_por_unidade=quantidadeAnterior[0]['quantidade_por_unidade'] or 1
            quantidade_total_anterior=quantidadeAnterior[0]['quantidade_total']
            if quantidade_total_anterior is None:
                    db.execute('UPDATE estoque_geral SET quantidade = ? WHERE item = ? AND carrinho = ?',
                    float(quantidade) ,item, carrinho)
            else:
                quantidade_diferenca=quantidade_por_unidade*diferenca
                nova_quantidade_total=quantidade_total_anterior - quantidade_diferenca
                print('nova quantidade total', nova_quantidade_total)
                db.execute('UPDATE estoque_geral SET quantidade = ?, quantidade_total = ? WHERE item = ? AND carrinho = ?',
                        float(quantidade),nova_quantidade_total ,item, carrinho)
        socketio.start_background_task(
            insertAlteracoesTable,
            'estoque geral',f'{i["item"]} de {str(anterior)} para {i["quantidade"]}','editou','Editar Estoque Geral',usuario, carrinho
        )
        socketio.start_background_task(
            enviar_notificacao_expo,
            'ADM','Estoque Geral Atualizado',f'{usuario} Editou {i["item"]} de {str(anterior)} para {i["quantidade"]}',token_user, carrinho
        )
    getEstoqueGeral({'emitir':True, 'carrinho': carrinho})


@socketio.on('atualizar_estoque')
def atualizar_estoque(data):
    carrinho = data.get('carrinho')
    print('carrinho no atualizar estoque', carrinho)
    usuario = data.get('username')
    print('usuario no atualizar estoque', usuario)
    itensAlterados = data.get('itensAlterados')
    print('itensAlterados no atualizar estoque', itensAlterados)
    token_user = data.get('token')
    print('token_user no atualizar estoque', token_user)
    for i in itensAlterados:
        item = i['item']
        anterior=''
        quantidade = i['quantidade']
        quantidadeAnterior=db.execute("SELECT quantidade,quantidade_por_unidade,quantidade_total FROM estoque WHERE item=? AND carrinho = ?",item, carrinho)
        if quantidadeAnterior:
            anterior=quantidadeAnterior[0]['quantidade']
            diferenca=float(anterior)-float(quantidade)
            quantidade_por_unidade=quantidadeAnterior[0]['quantidade_por_unidade'] or 1
            quantidade_total_anterior=quantidadeAnterior[0]['quantidade_total']
            if quantidade_total_anterior is None:
                    db.execute('UPDATE estoque SET quantidade = ? WHERE item = ? AND carrinho = ?',
                    float(quantidade) ,item, carrinho)
            else:
                quantidade_diferenca=quantidade_por_unidade*diferenca
                nova_quantidade_total=quantidade_total_anterior - quantidade_diferenca
                db.execute('UPDATE estoque SET quantidade = ?, quantidade_total = ? WHERE item = ? AND carrinho = ?',
                        float(quantidade),nova_quantidade_total ,item, carrinho)
        socketio.start_background_task(
            insertAlteracoesTable,
            'estoque carrinho',f'{i["item"]} de {int(anterior)} para {i["quantidade"]}','editou','Editar Estoque',usuario, carrinho
        )

        socketio.start_background_task(
            enviar_notificacao_expo,
            'ADM','Estoque Atualizado',f'{usuario} Editou {i["item"]} de {int(anterior)} para {i["quantidade"]}',token_user, carrinho
        )
    getEstoque({'emitir':True, 'carrinho': carrinho})


@socketio.on('atualizar_comanda')
def atualizar__comanda(data):
    print(data)
    itensAlterados = data.get('itensAlterados') or []
    comanda = data.get('comanda')
    usuario = data.get('username')
    carrinho = data.get('carrinho')
    data_brasil_corte_3h()
    token_user = data.get('token')
    dia = data_brasil_corte_3h()

    # ===== helpers iguais à ideia do excluir_pedido =====
    def _to_float(v, default=0.0):
        try:
            return float(v)
        except Exception:
            return default

    def _ajustar_estoque_por_ingrediente(
        id_ingrediente: str,
        unidade: str,
        quantidade_necessaria: float,
        carrinho: str,
        estoque_id,
        devolver: bool,
    ):
        """
        Ajusta estoque de UM ingrediente:
        - devolver=True  -> devolve pro estoque (somar)
        - devolver=False -> consome do estoque (subtrair)
        Respeita unidade e quantidade_por_unidade, e escolhe
        entre 'estoque' e 'estoque_geral' pelo estoque_id.
        """
        if not id_ingrediente or not quantidade_necessaria:
            return

        estoque = 'estoque' if str(estoque_id) == '1' else 'estoque_geral'

        row = db.execute(
            f'''
            SELECT quantidade, quantidade_total, quantidade_por_unidade
            FROM {estoque}
            WHERE id = ? AND carrinho = ?
            ''',
            id_ingrediente, carrinho
        )
        if not row:
            # ingrediente não está cadastrado nesse estoque
            return

        quantidade_atual_unid = _to_float(row[0].get('quantidade'), 0.0)
        quantidade_atual_total = _to_float(row[0].get('quantidade_total'), 0.0)
        qpu = _to_float(row[0].get('quantidade_por_unidade', 1), 1.0)

        # + se devolver, - se consumir
        sinal = 1.0 if devolver else -1.0
        qtd = _to_float(quantidade_necessaria, 0.0) * sinal

        if (unidade or '').strip() == 'unidade(s)':
            # trabalha em unidades + espelha em total usando qpu
            nova_qtd_unid = quantidade_atual_unid + qtd
            nova_qtd_total = quantidade_atual_total + (qtd * qpu)
            if nova_qtd_unid < 0:
                nova_qtd_unid = 0
            if nova_qtd_total < 0:
                nova_qtd_total = 0
        else:
            # trabalha direto em quantidade_total e converte pra unidades
            nova_qtd_total = quantidade_atual_total + qtd
            if nova_qtd_total < 0:
                nova_qtd_total = 0
            nova_qtd_unid = arredondar_personalizado(nova_qtd_total, qpu)

        db.execute(
            f'''
            UPDATE {estoque}
            SET quantidade = ?, quantidade_total = ?
            WHERE id = ? AND carrinho = ?
            ''',
            nova_qtd_unid, nova_qtd_total, id_ingrediente, carrinho
        )

    # =====================================================

    for i in itensAlterados:
        try:
            item_nome = i.get('pedido')
            quantidade_nova = _to_float(i.get('quantidade'), 0.0)
            preco_total_novo = _to_float(i.get('preco'), 0.0)

            # Todos os pedidos desse item na comanda (ordem=0)
            pedidos_item_comanda = db.execute(
                '''
                SELECT id, quantidade, opcoes, preco
                FROM pedidos
                WHERE pedido = ?
                  AND comanda = ?
                  AND ordem   = 0
                  AND dia     = ?
                  AND carrinho = ?
                ''',
                item_nome, comanda, dia, carrinho
            )
            if not pedidos_item_comanda:
                continue

            # quantidade total atual desse item na comanda
            quantidade_antes = sum(
                _to_float(p['quantidade'], 0.0) for p in pedidos_item_comanda
            )

            # Pega ingredientes base do cardápio
            cardapio_row = db.execute(
                '''
                SELECT item, ingredientes
                FROM cardapio
                WHERE item = ? AND carrinho = ?
                ''',
                item_nome, carrinho
            )
            ingredientes_base = []
            if cardapio_row:
                ingredientes_str = cardapio_row[0].get('ingredientes')
                if ingredientes_str:
                    try:
                        ingredientes_base = str_para_lista_de_dicts(ingredientes_str)
                    except Exception:
                        ingredientes_base = []

            # Descobre se há ingredientes dentro de opcoes (para qualquer pedido desse item)
            def _tem_ingredientes_opcoes(opcoes_str):
                if not opcoes_str:
                    return False
                try:
                    grupos = str_para_lista_de_dicts(opcoes_str)
                except Exception:
                    return False
                for g in grupos or []:
                    for opt in g.get('options') or []:
                        if opt.get('ingredientes'):
                            return True
                return False

            tem_ingredientes_base = bool(ingredientes_base)
            tem_ingredientes_opcoes = any(
                _tem_ingredientes_opcoes(p['opcoes']) for p in pedidos_item_comanda
            )
            # Só usamos estoque "por item" quando NÃO há nenhum ingrediente
            usa_ingredientes = tem_ingredientes_base or tem_ingredientes_opcoes

            # helper: aplica ajuste de TODOS os ingredientes (base + opções)
            # para "qtd_itens" unidades do item (1 unidade do item = quantidades
            # cadastradas em ingredientes / ingredientes das opções).
            def _ajustar_todos_ingredientes(qtd_itens, devolver):
                if qtd_itens <= 0:
                    return
                qtd_itens = _to_float(qtd_itens, 0.0)

                # Ingredientes base do cardápio (valem pra qualquer pedido do item)
                for ing in ingredientes_base:
                    id_ing = ing.get('id')
                    unidade_ing = ing.get('unidade')
                    qtd_por_item = _to_float(ing.get('quantidade') or 0, 0.0)
                    estoque_id = ing.get('estoque_id')
                    qtd_total_ing = qtd_por_item * qtd_itens
                    _ajustar_estoque_por_ingrediente(
                        id_ing, unidade_ing, qtd_total_ing,
                        carrinho, estoque_id, devolver
                    )

                # Ingredientes nas opções
                # Pegamos uma referência de opcoes (todas devem ter mesma estrutura
                # para essa combinação de preço).
                opcoes_str_ref = None
                for p in pedidos_item_comanda:
                    if p['opcoes']:
                        opcoes_str_ref = p['opcoes']
                        break

                if not opcoes_str_ref:
                    return

                try:
                    grupos_ref = str_para_lista_de_dicts(opcoes_str_ref) or []
                except Exception:
                    grupos_ref = []

                for g in grupos_ref:
                    for opt in g.get('options') or []:
                        for ing in opt.get('ingredientes') or []:
                            id_ing = ing.get('id')
                            unidade_ing = ing.get('unidade')
                            qtd_por_item = _to_float(ing.get('quantidade') or 0, 0.0)
                            estoque_id = ing.get('estoque_id')
                            qtd_total_ing = qtd_por_item * qtd_itens
                            _ajustar_estoque_por_ingrediente(
                                id_ing, unidade_ing, qtd_total_ing,
                                carrinho, estoque_id, devolver
                            )

            # ========== CASO 1: quantidade_nova == 0  → apagar item ==========
            if quantidade_nova == 0:
                # devolve pro estoque o total que tinha
                if usa_ingredientes:
                    _ajustar_todos_ingredientes(quantidade_antes, devolver=True)
                else:
                    # lógica antiga de estoque simples por item
                    verifEstoq = db.execute(
                        'SELECT * FROM estoque WHERE item = ? AND carrinho = ?',
                        item_nome, carrinho
                    )
                    if verifEstoq:
                        db.execute(
                            '''
                            UPDATE estoque
                            SET quantidade = quantidade + ?
                            WHERE item = ? AND carrinho = ?
                            ''',
                            quantidade_antes, item_nome, carrinho
                        )

                insertAlteracoesTable(
                    'Pedido Editado',
                    f'{item_nome} de {quantidade_antes} para {quantidade_nova}',
                    'editou',
                    'Editar Comanda',
                    usuario,
                    carrinho
                )
                enviar_notificacao_expo(
                    'ADM',
                    'Comanda Editada',
                    f'{usuario} Editou {item_nome} de {quantidade_antes} para {quantidade_nova}',
                    token_user,
                    carrinho
                )

                db.execute(
                    '''
                    DELETE FROM pedidos
                    WHERE pedido  = ?
                      AND comanda = ?
                      AND ordem   = 0
                      AND dia     = ?
                      AND carrinho = ?
                    ''',
                    item_nome, comanda, dia, carrinho
                )

            # ========== CASO 2: quantidade_nova > 0  → ajustar pra cima/baixo ==========
            else:
                if quantidade_nova == 0:
                    # (por segurança, mas já tratado acima)
                    continue

                # preço unitário calculado pelo front
                preco_unitario = preco_total_novo / quantidade_nova if quantidade_nova else 0.0

                # pega apenas a combinação dessa comanda + preço unitário
                pedidos_combo = db.execute(
                    '''
                    SELECT id, quantidade, opcoes, preco
                    FROM pedidos
                    WHERE pedido = ?
                      AND comanda = ?
                      AND ordem   = 0
                      AND preco / quantidade = ?
                      AND dia     = ?
                      AND carrinho = ?
                    ''',
                    item_nome, comanda, preco_unitario, dia, carrinho
                )
                # fallback se não achar (por arredondamento, etc)
                if not pedidos_combo:
                    pedidos_combo = pedidos_item_comanda

                total_antigo_combo = sum(
                    _to_float(p['quantidade'], 0.0) for p in pedidos_combo
                )
                # delta = quanto vai mudar
                delta = quantidade_nova - total_antigo_combo

                if delta == 0:
                    # não mudou nada
                    continue

                # ------ diminuir quantidade (delta < 0) -> devolve estoque ------
                if delta < 0:
                    qtd_removida = -delta

                    if usa_ingredientes:
                        _ajustar_todos_ingredientes(qtd_removida, devolver=True)
                    else:
                        verifEstoq = db.execute(
                            'SELECT * FROM estoque WHERE item = ? AND carrinho = ?',
                            item_nome, carrinho
                        )
                        if verifEstoq:
                            db.execute(
                                '''
                                UPDATE estoque
                                SET quantidade = quantidade + ?
                                WHERE item = ? AND carrinho = ?
                                ''',
                                qtd_removida, item_nome, carrinho
                            )

                    # mesma lógica antiga: vai comendo as linhas até zerar a diferença
                    ids = db.execute(
                        '''
                        SELECT id, quantidade
                        FROM pedidos
                        WHERE pedido  = ?
                          AND comanda = ?
                          AND ordem   = 0
                          AND dia     = ?
                          AND carrinho = ?
                        ''',
                        item_nome, comanda, dia, carrinho
                    )
                    restante = qtd_removida
                    for k in ids:
                        if restante <= 0:
                            break
                        q_linha = _to_float(k['quantidade'], 0.0)
                        if q_linha <= restante:
                            db.execute(
                                'DELETE FROM pedidos WHERE id = ? AND dia = ?',
                                k['id'], dia
                            )
                            restante -= q_linha
                        else:
                            db.execute(
                                '''
                                UPDATE pedidos
                                SET preco = preco/quantidade * (quantidade - ?),
                                    quantidade = quantidade - ?
                                WHERE id = ? AND dia = ?
                                ''',
                                restante, restante, k['id'], dia
                            )
                            restante = 0

                # ------ aumentar quantidade (delta > 0) -> consome estoque ------
                else:
                    qtd_adicionada = delta

                    # descobre preço unitário base a partir de algum pedido existente
                    if pedidos_combo:
                        base_qtd = _to_float(pedidos_combo[0]['quantidade'], 1.0)
                        base_preco = _to_float(pedidos_combo[0]['preco'], 0.0)
                        preco_unitario_existente = base_preco / base_qtd if base_qtd else 0.0
                    else:
                        preco_unitario_existente = preco_unitario

                    preco_unitario_final = preco_unitario or preco_unitario_existente
                    preco_atualizado = preco_unitario_final * qtd_adicionada

                    if usa_ingredientes:
                        _ajustar_todos_ingredientes(qtd_adicionada, devolver=False)
                    else:
                        verifEstoq = db.execute(
                            'SELECT * FROM estoque WHERE item = ? AND carrinho = ?',
                            item_nome, carrinho
                        )
                        if verifEstoq:
                            db.execute(
                                '''
                                UPDATE estoque
                                SET quantidade = quantidade - ?
                                WHERE item = ? AND carrinho = ?
                                ''',
                                qtd_adicionada, item_nome, carrinho
                            )

                    # Atualiza uma linha da combinação (como estava antes)
                    alvo_id = pedidos_combo[0]['id']
                    db.execute(
                        '''
                        UPDATE pedidos
                        SET quantidade = quantidade + ?,
                            preco      = preco + ?
                        WHERE id = ? AND dia = ?
                        ''',
                        qtd_adicionada, preco_atualizado, alvo_id, dia
                    )

                # logs/notificação (mantidos)
                insertAlteracoesTable(
                    'Pedido Editado',
                    f'{item_nome} de {quantidade_antes} para {quantidade_nova} na comanda:{comanda}',
                    'editou',
                    'Editar Comanda',
                    usuario,
                    carrinho
                )
                enviar_notificacao_expo(
                    'ADM',
                    'Comanda Editada',
                    f'{usuario} Editou {item_nome} de {quantidade_antes} para {quantidade_nova} na comanda:{comanda}',
                    token_user,
                    carrinho
                )

            # limpa pedidos com quantidade total 0
            db.execute(
                '''
                DELETE FROM pedidos
                WHERE id IN (
                    SELECT id
                    FROM (
                        SELECT id
                        FROM pedidos
                        WHERE comanda = ?
                          AND ordem = 0
                          AND dia   = ?
                          AND pedido != ?
                          AND carrinho = ?
                        GROUP BY pedido
                        HAVING SUM(quantidade) = 0
                    ) subquery
                )
                ''',
                comanda, dia, 'Comanda Aberta', carrinho
            )

        except Exception as e:
            print('Erro ao atualizar item da comanda:', e)

    # Atualiza telas
    getEstoque({'emitir': True, 'carrinho': carrinho})
    getEstoqueGeral({'emitir': True, 'carrinho': carrinho})
    getPedidos({'emitir': True, 'carrinho': carrinho})
    getComandas({'emitir': True, 'carrinho': carrinho})
    handle_get_cardapio(comanda, carrinho)


@socketio.on('transferir_para_estoque_carrinho')
def transferir_para_estoque_carrinho(data):
    itensAlterados = data.get('itensAlterados')
    token = data.get('token')
    usuario = data.get('username')
    carrinho = data.get('carrinho')
    for i in itensAlterados:
        
        quantidade_antiga = db.execute('SELECT quantidade, quantidade_total,quantidade_por_unidade FROM estoque_geral WHERE item = ? AND carrinho = ?',i['item'], carrinho)
        existe_no_estoque = db.execute('SELECT quantidade FROM estoque WHERE item = ? AND carrinho = ?',i['item'], carrinho)

        if quantidade_antiga and existe_no_estoque:
            quantidade_antig = float(quantidade_antiga[0]['quantidade'])
            quantidade_por_unidade=quantidade_antiga[0]['quantidade_por_unidade'] or 1
            quantidade = float(i['quantidade'])
            diferenca=quantidade_antig-quantidade
            nova_quantidade_total=diferenca*quantidade_por_unidade
            db.execute('UPDATE estoque SET quantidade = quantidade + ?, quantidade_total = quantidade_total + ? WHERE item = ? AND carrinho = ?',diferenca,nova_quantidade_total, i['item'], carrinho)
            getEstoque({'emitir':True, 'carrinho': carrinho})
            insertAlteracoesTable('Estoque Carrinho',f'{i["item"]} de {existe_no_estoque[0]["quantidade"]} para {quantidade_antig-quantidade}','editou','Transferir para Estoque Carrinho',usuario, carrinho)
            enviar_notificacao_expo('ADM','Estoque Carrinho Tranferir',f'{usuario} Editou {i["item"]} de {existe_no_estoque[0]["quantidade"]} para {quantidade_antig-quantidade}',token, carrinho)
    atualizar_estoque_geral(data)
            

@socketio.on('get_cardapio')
def handle_get_cardapio(data, carrinho_param=None):
    print('get_cardapio')
    try:
        dia = data_brasil_corte_3h()  # valor padrão
        
        if type(data) == str:
            print('if')
            fcomanda = data
            ordem = 0
            # Se carrinho_param foi passado, use ele
            if carrinho_param:
                carrinho = carrinho_param
        else:
            print('else')
            fcomanda = data.get('fcomanda')
            ordem = data.get('ordem')
            carrinho = data.get('carrinho')
            # Se carrinho_param foi passado, use ele (prioridade)
            if carrinho_param:
                carrinho = carrinho_param

        _register_carrinho_room(carrinho)

        if ordem == 0:
            valor_pago = db.execute('SELECT SUM(valor) AS total FROM pagamentos WHERE comanda = ? AND ordem = ? AND dia = ? AND tipo = ? AND carrinho = ?', fcomanda, ordem,dia,'normal',carrinho)
            print('valor_pago', valor_pago)
            preco_pago = 0
            if valor_pago and valor_pago[0]['total']:
                
                preco_pago = float(valor_pago[0]['total'])
            
            desconto = db.execute('SELECT SUM(valor) AS total FROM pagamentos WHERE comanda = ? AND ordem = ? AND dia = ? AND tipo = ? AND carrinho = ?', fcomanda, ordem,dia,'desconto',carrinho)
            if desconto and desconto[0]['total']:
                desconto_valor = float(desconto[0]['total'])
            else:
                desconto_valor = 0
            
            total_comanda = db.execute('SELECT SUM(preco_unitario*quantidade) AS total FROM pedidos WHERE comanda = ? AND ordem = ? AND dia = ? AND pedido != ? AND carrinho = ?', fcomanda, ordem,dia, 'Comanda Aberta', carrinho)
            preco_total = 0
            print('total_comanda', total_comanda)
            if total_comanda and total_comanda[0]['total']:
                
                print(total_comanda)
                preco_total = float(total_comanda[0]['total'])
            

                dados = db.execute('''
                    SELECT pedido,id,ordem,nome,extra,opcoes, SUM(quantidade) AS quantidade, SUM(quantidade_paga) as quantidade_paga, SUM(preco) AS preco, preco_unitario
                    FROM pedidos WHERE comanda =? AND ordem = ? AND dia = ? AND carrinho = ? GROUP BY pedido, preco_unitario
                ''', fcomanda, ordem,dia, carrinho)
                nomes = db.execute(
                    'SELECT nome FROM pedidos WHERE comanda = ? AND ordem = ? AND nome != ? AND dia = ? AND pedido != ? AND carrinho = ? GROUP BY nome', fcomanda, ordem, '-1',dia, 'Comanda Aberta', carrinho)
                if not nomes or not nomes[0]['nome']:
                    nomes = []
                preco_a_pagar = preco_total-preco_pago-desconto_valor
                emit_for_carrinho('preco', {'preco_a_pagar': preco_a_pagar, 'preco_total': preco_total, 'preco_pago': preco_pago,
                               'dados': dados, 'comanda': fcomanda, 'nomes': nomes, 'desconto': desconto_valor}, broadcast=True, carrinho=carrinho)
            else:
                print('primeiro else')
                emit_for_carrinho('preco', {'preco_a_pagar': 0, 'preco_total': 0, 'preco_pago': 0, 'dados': [], 'nomes': [],
                               'comanda': fcomanda}, broadcast=True, carrinho=carrinho)
        else:
            print('segundo else')
            dados = db.execute('''
                    SELECT pedido,id,ordem,nome,extra,opcoes, SUM(quantidade) AS quantidade, SUM(quantidade_paga) as quantidade_paga, SUM(preco) AS preco
                    FROM pedidos WHERE comanda =? AND ordem = ? AND dia = ? AND carrinho = ? GROUP BY pedido, preco_unitario
                ''', fcomanda, ordem,dia, carrinho)
            emit_for_carrinho('preco', {'preco_a_pagar': 0, 'preco_total': 0, 'preco_pago': 0, 'dados': dados, 'nomes': '',
                           'comanda': fcomanda}, broadcast=True, carrinho=carrinho)


    except Exception as e:
        print("Erro ao calcular preço:", e)


@socketio.on('permitir')
def permitir(data):
    id = data.get('id')
    carrinho = data.get('carrinho')
    _register_carrinho_room(carrinho)
    # Corrigido para buscar 'numero', que está vindo do frontend
    numero = data.get('numero')
    db.execute('UPDATE usuarios SET liberado = ? WHERE id = ? AND carrinho = ?',
               numero, id, carrinho)  # Atualiza a coluna 'liberado'
    username=db.execute('SELECT username FROM usuarios WHERE id = ? AND carrinho = ?',id, carrinho)[0]['username']
    print('username no permitir', username)
    users({'emitir':True, 'carrinho': carrinho})
    if numero=='0':
        print('entrou no if do permitir')
        emit_for_carrinho('LogOut', {'username':username}, broadcast=True, carrinho=carrinho)
    


@socketio.on('Delete_user')
def delete_user(data):
    #!!
    id = data.get('id')
    carrinho = data.get('carrinho')
    db.execute('DELETE FROM usuarios WHERE id = ?',id)
    users({'emitir':True, 'carrinho': carrinho})

@socketio.on('cadastrar')
def cadastro(data):
    carrinho=data.get('carrinho')
    username = data.get('username')
    cargo = data.get('cargo')
    print(username)
    senha = data.get('senha')
    print(senha)
    
    # Verificar se o username já existe
    existing_user = db.execute('SELECT id FROM usuarios WHERE username = ?', username)
    if existing_user:
        print('username ja existe')
        # Emitir erro para o frontend
        emit('erro_cadastro', {
            'message': 'Username já está sendo usado. Escolha outro nome de usuário.',
            'error': 'username_already_exists'
        })
        return
    
    try:
        db.execute('INSERT INTO usuarios (username,senha,cargo,liberado, carrinho) VALUES (?,?,?,?,?)',
                   username, senha, cargo, '1',carrinho)
        print('sucesso')
        emit(
            'cadastro_resposta',        # nome do evento que o front está ouvindo
            {'status': 'ok'},          # payload (opcional, se vc quiser usar)  
        )
        users({'emitir':True, 'carrinho': carrinho})
    except Exception as e:
        # Emitir erro genérico caso algo dê errado
        emit('erro_cadastro', {
            'message': 'Erro ao cadastrar usuário. Tente novamente.',
            'error': 'database_error'
        })

def _bool_int(v):
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (int, float)):
        return 1 if int(v) != 0 else 0
    s = str(v).strip().lower()
    return 1 if s in ("1", "true", "t", "yes", "y", "sim") else 0

def _slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "n-a"

def _process_opcoes_ingredients_inplace(grupos: list, carrinho):
    """
    Percorre grupos -> options -> ingredientes e processa cada lista
    usando _process_ingredientes_list_inplace.
    """
    if not isinstance(grupos, list):
        return grupos

    for g in grupos:
        opts = (g or {}).get('options') or []
        for o in opts:
            ingr_list = (o or {}).get('ingredientes')
            if isinstance(ingr_list, list):
                _process_ingredientes_list_inplace(ingr_list, carrinho)
    return grupos


def _process_ingredientes_list_inplace(ingredientes_list: list, carrinho):
    if not isinstance(ingredientes_list, list):
        return

    for ingrediente in ingredientes_list:
        if not isinstance(ingrediente, dict):
            continue

        nome_ingrediente = (ingrediente.get('nome') or '').strip()
        if not nome_ingrediente:
            continue
        estoque_id=ingrediente.get('estoque_id', None)
        if estoque_id=='1':
            estoque='estoque'
        else:
            estoque='estoque_geral'
        ingrediente['estoque_id']=str(estoque_id)
        ingrediente_id = db.execute(f"SELECT id FROM {estoque} WHERE item = ? AND carrinho = ?", nome_ingrediente, carrinho)[0]["id"]

        # limpa transitórios e anexa id
        ingrediente.pop('quantidade_estoque', None)
        ingrediente.pop('estoque_ideal', None)
        ingrediente.pop('quantidade_por_unidade', None)
        ingrediente.pop('destino_estoque', None)
        ingrediente['id'] = str(ingrediente_id)


def _parse_opcoes(obj):
    """Aceita string JSON ou lista já estruturada; retorna lista saneada no formato:
       [{
          nome, ids, max_selected:int, obrigatorio:0/1,
          options:[{
            nome, valor_extra:float, esgotado:0/1,
            ingredientes: [{
              id?: str (pode vir, mas normalmente será resolvido no backend),
              nome: str, quantidade: str, unidade: str,
              quantidade_estoque?: num, estoque_ideal?: num, quantidade_por_unidade?: num
            }, ...]
          }]}
       ]
    """
    if obj is None:
        return []
    if isinstance(obj, str):
        try:
            obj = json.loads(obj)
        except Exception:
            return []

    out = []
    if isinstance(obj, list):
        for g in obj:
            try:
                nome = (g.get("nome") or g.get("titulo") or "").strip()
                if not nome:
                    continue
                ids = str(g.get("ids") or "")
                max_selected = int(g.get("max_selected") or 1)
                if max_selected < 1:
                    max_selected = 1
                obrigatorio = _bool_int(g.get("obrigatorio"))

                opts_in = g.get("options") or []
                opts_out = []
                for o in opts_in:
                    onome = str(o.get("nome") or "").strip()
                    if not onome:
                        continue
                    extra = float(o.get("valor_extra") or 0.0)
                    custo = float(o.get("custo") or 0.0)
                    esgotado = _bool_int(o.get("esgotado"))

                    # ingredientes por opcao (se vierem)
                    ing_in = o.get("ingredientes") or []
                    ing_out = []
                    if isinstance(ing_in, list):
                        for i in ing_in:
                            if not isinstance(i, dict):
                                continue
                            inome = (i.get('nome') or '').strip()
                            if not inome:
                                continue
                            ing_out.append({
                                # id pode vir do cliente; será sobrescrito se criarmos/acharmos no servidor
                                "id": str(i.get('id')) if i.get('id') is not None else None,
                                "nome": inome,
                                "quantidade": str(i.get('quantidade') or '').strip(),
                                "unidade": str(i.get('unidade') or '').strip(),
                                "estoque_id":str(i.get('estoque_id', '')),
                                # campos de criação — se vierem, significam "criar no estoque"
                                "quantidade_estoque": i.get('quantidade_estoque', None),
                                "estoque_ideal": i.get('estoque_ideal', None),
                                "quantidade_por_unidade": i.get('quantidade_por_unidade', 1),
                            })

                    opts_out.append({
                        "nome": onome,
                        "valor_extra": extra,
                        "custo": custo,
                        "esgotado": esgotado,
                        "ingredientes": ing_out,  # <-- preserva ingredientes por opção
                    })

                if opts_out:
                    out.append({
                        "nome": nome,
                        "ids": ids,
                        "max_selected": max_selected,
                        "obrigatorio": obrigatorio,
                        "options": opts_out,
                    })
            except Exception:
                # ignora grupo problemático
                pass
    return out


def _sync_opcoes_rows(id_cardapio: int, item_nome: str, grupos: list, carrinho):
    """Limpa e re-insere as linhas em `opcoes` para este cardápio."""
    db.execute("DELETE FROM opcoes WHERE id_cardapio = ? AND carrinho = ?", id_cardapio, carrinho)
    now = datetime.now().isoformat(timespec="seconds")
    for g in grupos:
        gname = g["nome"]
        gslug = _slugify(g.get("grupo_slug") or gname)
        for o in g.get("options", []):
            oname = o["nome"]
            oslug = _slugify(o.get("opcao_slug") or oname)
            extra = float(o.get("valor_extra") or 0.0)
            esgotado = _bool_int(o.get("esgotado"))
            db.execute(
                """
                INSERT INTO opcoes
                  (id_cardapio, item, nome_grupo, opcao, valor_extra, esgotado_bool, grupo_slug, opcao_slug, updated_at, carrinho)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                id_cardapio, item_nome, gname, oname, extra, esgotado, gslug, oslug, now, carrinho
            )


@socketio.on('adicionarCardapio')
def adicionarCardapio(data):
    item = (data.get('item') or '').strip()
    preco = data.get('preco')
    custo = data.get('custo', None)
    categoria = data.get('categoria')
    id_referencia = data.get('id_referencia', None)
    usuario = data.get('username')
    token_user = data.get('token')
    carrinho = data.get('carrinho')
    if db.execute('SELECT carrinho FROM carrinhos WHERE empresas = ?', carrinho):
        permission_categoria3=False
    else:
        permission_categoria3=True
    # --- INGREDIENTES (nível do item) ---
    ingredientes_list  = data.get('ingredientes', [])
    for ingrediente in ingredientes_list:
        nome_ingrediente = ingrediente.get('nome')
        print('ingediente (criar): ', nome_ingrediente)
        estoque_id=ingrediente.get('estoque_id')
        if estoque_id == 1:
            estoque='estoque'
        else:
            estoque='estoque_geral'
        ingrediente['estoque_id'] = str(estoque_id)
        ingrediente_id = db.execute(f'''SELECT id FROM {estoque} WHERE item = ? AND carrinho = ?;''',nome_ingrediente, carrinho)[0]
        ingrediente['id'] = str(ingrediente_id['id'])
        print('ingrediente com id: ', ingrediente)   
        ingrediente.pop('quantidade_estoque', None)
        ingrediente.pop('estoque_ideal', None)
        ingrediente.pop('quantidade_por_unidade', None)
        ingrediente.pop('destino_estoque', None)

    ingredientes = lista_dicts_para_str(ingredientes_list)
    print('ingredientes string: ', ingredientes)
    # ingredientes é uma lista de dicionarios, com as chaves: id, nome, quantidade e unidade.

    if not item or preco is None or not categoria:
        emit('Erro', {'erro': 'Alguma categoria faltando'})
        return

    if categoria == 'Bebida':
        categoria_id = 2
    elif categoria == 'Porção':
        categoria_id = 3
    else:
        categoria_id = 1

    # ======= OPÇÕES (com ingredientes por opção) =======
    grupos = _parse_opcoes(data.get('opcoes'))
    print('grupos parseados: ', grupos)
    # processa ingredientes dentro de cada opção (cria no estoque se vier quantidade_estoque, etc.)
    _process_opcoes_ingredients_inplace(grupos, carrinho)
    opcoes_json = json.dumps(grupos, ensure_ascii=False)

    # INSERT cardapio + pegar id
    if permission_categoria3:
        print('permitido adicionar porcao')
        db.execute(
            'INSERT INTO cardapio (item, categoria_id, preco,preco_base, opcoes, ingredientes, carrinho, custo, id_referencia) VALUES (?,?,?,?,?,?,?,?,?)',
            item, categoria_id, float(preco), float(preco), opcoes_json, ingredientes, carrinho, custo, id_referencia
        )
    else:
        print('nao permitido adicionar porcao')
        emit('cardapioResponse', {'ok': False,'mensagem': 'Permissao negada para adicionar porcao'})
        return
    new_id = db.execute("SELECT last_insert_rowid() AS id")[0]["id"]
    for i in ingredientes_list:
        add_to_usado_em_cardapio_ids(i['id'], new_id, carrinho, i['estoque_id'])
    # sincroniza linhas da tabela `opcoes` (tabela *flat*; não armazena ingredientes)
    _sync_opcoes_rows(new_id, item, grupos, carrinho)

    alteracoes = f'item: {item} preco: {preco} categoria: {categoria} (com opcoes)'
    insertAlteracoesTable('Cardapio', alteracoes, 'Adicionou', 'Tela Cardapio', usuario, carrinho)
    
    # Enviar resposta de sucesso ANTES das notificações
    emit('cardapioResponse', {'sucesso': True, 'item': item, 'id': new_id, 'mensagem': 'Item adicionado com sucesso'})
    
    # Executar notificações após o emit (para não bloquear)
    try:
        enviar_notificacao_expo('ADM', 'Item Adicionado Cardapio', f"{usuario} Adicionou {alteracoes}", token_user, carrinho)
    except Exception as e:
        print(f"Erro ao enviar notificação: {e}")
    
    getCardapio({'emitir':True, 'carrinho': carrinho})



@socketio.on('adicionar_ingrediente_estoque')
def adicionar_ingrediente_estoque(data):
    ingredientes=data.get('ingredientes')
    carrinho=data.get('carrinho')
    usuario=data.get('username')  # 'carrinho' ou 'geral'
    for i in ingredientes:
        destino_estoque=i.get('destino_estoque')
        print(destino_estoque)
        nome_ingrediente=i['nome']
        quantidade_estoque=i['quantidade_estoque']
        print(quantidade_estoque)
        estoque_ideal=i['estoque_ideal'] 
        unidade_ingrediente=i['unidade']
        quantidade_por_unidade=i.get('quantidade_por_unidade',1)
        if quantidade_por_unidade is None:
            quantidade_por_unidade=1
        print(quantidade_por_unidade)
        quantidade_total=quantidade_estoque*quantidade_por_unidade
        if destino_estoque=='estoque_local' or destino_estoque=='ambos':
            existe=db.execute('SELECT quantidade FROM estoque WHERE item = ? AND carrinho = ?',nome_ingrediente,carrinho)
            if existe:
                emit('Erro', {'erro': f'O ingrediente {nome_ingrediente} já existe no estoque do carrinho.'})
                return
            db.execute('INSERT INTO estoque (item,quantidade,estoque_ideal,carrinho,unidade,quantidade_por_unidade,quantidade_total) VALUES (?,?,?,?,?,?,?)', nome_ingrediente,quantidade_estoque,estoque_ideal,carrinho,unidade_ingrediente,quantidade_por_unidade,quantidade_total)
            getEstoque({'emitir':True,'carrinho':carrinho})
        if destino_estoque=='estoque_geral' or destino_estoque=='ambos':
            existe=db.execute('SELECT quantidade FROM estoque_geral WHERE item = ? AND carrinho = ?',nome_ingrediente,carrinho)
            if existe:
                emit('Erro', {'erro': f'O ingrediente {nome_ingrediente} já existe no estoque geral.'})
                return
            db.execute('INSERT INTO estoque_geral (item, quantidade, estoque_ideal, carrinho, unidade, quantidade_por_unidade, quantidade_total) VALUES (?,?,?,?,?,?,?)', nome_ingrediente,quantidade_estoque,estoque_ideal,carrinho,unidade_ingrediente,quantidade_por_unidade,quantidade_total)
            getEstoqueGeral({'emitir':True,'carrinho':carrinho})
    



@socketio.on('editarCardapio')
def editarCardapio(data):
    import json

    item = (data.get('item') or '').strip()
    preco = data.get('preco')
    custo = data.get('custo', None)
    categoria = data.get('categoria')
    id_referencia = data.get('id_referencia', None)
    novoNome = (data.get('novoNome') or '').strip()
    raw_opcoes = data.get('opcoes')
    carrinho = data.get('carrinho')
    print('raw_opcoes recebido: ', raw_opcoes)
    usuario = data.get('username')
    token_user = data.get('token')

    # --- validações básicas ---
    if not item or preco in (None, '') or not categoria:
        emit('Erro', {'erro': 'Dados insuficientes'})
        return
    try:
        preco = float(preco)
    except Exception:
        emit('Erro', {'erro': 'Preço inválido'})
        return

    # categoria -> id
    if categoria == 'Bebida':
        categoria_id = 2
    elif categoria == 'Porção':
        categoria_id = 3
    else:
        categoria_id = 1

    
    # pega "antes" para log
    dadoAntigo = db.execute('SELECT * FROM cardapio WHERE item = ? AND carrinho = ?', item, carrinho)
    dadoAntigo = dadoAntigo[0] if dadoAntigo else {}

    # opcoes: saneia só se veio algo (senão mantém como está)
    carrinho2=db.execute('SELECT empresas FROM carrinhos WHERE empresas = ?', carrinho)
    categoria_antiga = dadoAntigo.get('categoria_id')
    if (categoria_antiga == 3 or categoria_id == 3) and carrinho2:
        permission_categoria3=False
    else:
        permission_categoria3=True
    if not permission_categoria3:
        emit('cardapioResponse', {'ok': False,'mensagem': 'Permissao negada para editar para porcao'})
        return

    grupos = None
    opcoes_json = None
    if raw_opcoes is not None:
        grupos = _parse_opcoes(raw_opcoes)
        # processa ingredientes dentro das opções (criação / mapeamento de id)
        _process_opcoes_ingredients_inplace(grupos, carrinho)
        opcoes_json = json.dumps(grupos, ensure_ascii=False)

    # ingredientes (nível do item): só processa se veio lista
    ingredientes_list = data.get('ingredientes')
    print('ingredientes_list recebido: ', ingredientes_list)
    ingredientes_json = None
    if ingredientes_list is not None:
        if not isinstance(ingredientes_list, list):
            emit('Erro', {'erro': 'Ingredientes inválidos'})
            return

    # --- transação para manter consistência ---
    db.execute("BEGIN IMMEDIATE;")
    try:
        # ====== INGREDIENTES DO ITEM (somente se foram enviados) ======
        if ingredientes_list is not None:
            for ingrediente in ingredientes_list:
                if not isinstance(ingrediente, dict):
                    continue
                ingrediente.pop('quantidade_estoque', None)
                ingrediente.pop('estoque_ideal', None)
                ingrediente.pop('quantidade_por_unidade', None)
                ingrediente.pop('destino_estoque', None)
                nome_ingrediente = (ingrediente.get('nome') or '').strip()
                # UPSERT no estoque (preferindo RETURNING; fallback se não suportado)
                estoque_id=ingrediente.get('estoque_id', None)
                if estoque_id=='1':
                    estoque='estoque'
                else:
                    estoque='estoque_geral'
                ingrediente['estoque_id']=str(estoque_id)
                ingrediente_id=db.execute(f'SELECT id FROM {estoque} WHERE item = ? AND carrinho = ?;', nome_ingrediente, carrinho)[0]
                # limpa transitórios e anexa id do estoque
                if ingrediente_id is not None:
                    ingrediente['id'] = str(ingrediente_id['id'])
                    add_to_usado_em_cardapio_ids(ingrediente_id['id'], dadoAntigo['id'], carrinho, ingrediente['estoque_id'])

        # serializa ingredientes para gravar no cardápio
        ingredientes_json = lista_dicts_para_str(ingredientes_list)

        # ====== UPDATE principal no cardápio ======
        sets = ["preco = ?", "custo = ?","categoria_id = ?", "id_referencia = ?"]
        params = [preco, custo, categoria_id, id_referencia]

        if opcoes_json is not None:
            sets.append("opcoes = ?")
            params.append(opcoes_json)

        if ingredientes_json is not None:
            sets.append("ingredientes = ?")
            params.append(ingredientes_json)

        if novoNome:
            sets.append("item = ?")
            params.append(novoNome)

        sql = f"UPDATE cardapio SET {', '.join(sets)} WHERE item = ? AND carrinho = ?"
        params.extend([item, carrinho])
        db.execute(sql, *params)

        # chave atual para buscar id
        chaveBusca = novoNome if novoNome else item
        dadoAtualizado = db.execute(
            'SELECT * FROM cardapio WHERE item = ? AND carrinho = ? ORDER BY id DESC LIMIT 1',
            chaveBusca, carrinho
        )
        dadoAtualizado = dadoAtualizado[0] if dadoAtualizado else {}

        # sincroniza tabela `opcoes`
        if dadoAtualizado:
            id_cardapio = dadoAtualizado.get("id")
            if grupos is not None:
                _sync_opcoes_rows(id_cardapio, chaveBusca, grupos, carrinho)
            elif novoNome:
                # só renomeou item — reflita em `opcoes.item`
                db.execute("UPDATE opcoes SET item = ? WHERE id_cardapio = ? AND carrinho = ?",
                           chaveBusca, id_cardapio, carrinho)

        db.execute("COMMIT;")

    except Exception as e:
        db.execute("ROLLBACK;")
        emit('Erro', {'erro': f'Falha ao editar: {e}'})
        return

    # --- logs / notificações / refresh ---
    alteracoes = f'{item}, '
    if dadoAntigo and dadoAtualizado:
        dif = {k for k in (dadoAtualizado.keys() & dadoAntigo.keys())
               if dadoAtualizado[k] != dadoAntigo.get(k)}
        for key in dif:
            alteracoes += f'{key} de {dadoAntigo.get(key)} para {dadoAtualizado.get(key)}; '

    insertAlteracoesTable('Cardapio', alteracoes, 'Editou', 'Tela Cardapio', usuario, carrinho)
    
    # Enviar resposta de sucesso ANTES das notificações
    emit('cardapioResponse', {'sucesso': True, 'item': novoNome if novoNome else item, 'mensagem': 'Item editado com sucesso'})
    
    # Executar notificações após o emit
    try:
        enviar_notificacao_expo('ADM', 'Cardapio editado', f"{usuario} Editou {alteracoes}", token_user, carrinho)
    except Exception as e:
        print(f"Erro ao enviar notificação: {e}")
    
    getCardapio({'emitir': True, 'carrinho': carrinho})




  

@socketio.on('removerCardapio')
def removerCardapio(data):
    item=data.get('item')
    usuario = data.get('username')
    token_user = data.get('token')
    carrinho = data.get('carrinho')
    
    if not item:
        emit('Erro', {'erro': 'Item não especificado'})
        return
    
    print("Removendo item:", item)
    
    try:
        # Pegar o ID do item antes de remover
        cardapio_data = db.execute("SELECT id, ingredientes FROM cardapio WHERE item=? AND carrinho = ?", item, carrinho)
        if cardapio_data:
            cardapio_id = cardapio_data[0]['id']
            ingredientes_json = cardapio_data[0]['ingredientes']
            
            # Se o item tem ingredientes, remover as referências do estoque
            if ingredientes_json:
                try:
                    ingredientes_list = str_para_lista_de_dicts(ingredientes_json)
                    for ingrediente in ingredientes_list:
                        estoque_id = ingrediente.get('id')
                        if estoque_id:
                            remove_from_usado_em_cardapio_ids(estoque_id, cardapio_id, carrinho, ingrediente.get('estoque_id'))
                except Exception as e:
                    print(f"Erro ao remover referências do estoque: {e}")
        
        db.execute("DELETE FROM cardapio WHERE item=? AND carrinho = ?",item, carrinho)
        insertAlteracoesTable('Cardapio',item,'Removeu','Tela Cardapio',usuario, carrinho)
        
        # Enviar resposta de sucesso ANTES das notificações
        emit('cardapioResponse', {'sucesso': True, 'item': item, 'mensagem': 'Item removido com sucesso'})
        
        # Executar notificações após o emit
        try:
            enviar_notificacao_expo('ADM','Item Removido Cardapio',f"{usuario} Removeu {item} do Cardapio",token_user, carrinho)
        except Exception as e:
            print(f"Erro ao enviar notificação: {e}")
        
        getCardapio({'emitir':True, 'carrinho': carrinho})
        
    except Exception as e:
        print(f"Erro ao remover item: {e}")
        emit('Erro', {'erro': f'Falha ao remover: {e}'})
    


@socketio.on('getItemCardapio')
def getItemCardapio(data):
    item = data.get('item')
    carrinho = data.get('carrinho')
    print(item) 
    opcoes = db.execute('SELECT opcoes FROM cardapio WHERE item = ? AND carrinho = ?', item, carrinho)
    if opcoes:
        palavra = ''
        selecionaveis = []
        dados = []
        if opcoes[0]['opcoes'] is None or opcoes[0]['opcoes'] == '':
            emit('respostaGetItemCardapio',{'opcoes':[{'titulo':'','conteudo':[]}]} , broadcast=False)
            return
        for i in opcoes[0]['opcoes']:
            if i == '(':
                nome_selecionavel = palavra
                print(nome_selecionavel)
                palavra = ''
            elif i == '-':
                selecionaveis.append(palavra)
                palavra = ''
            elif i == ')':
                selecionaveis.append(palavra)
                dados.append({'titulo':nome_selecionavel,'conteudo':selecionaveis})
                selecionaveis = []
                palavra = ''
            else:
                palavra += i

        print(dados)
        emit('respostaGetItemCardapio',{'opcoes':dados}, broadcast=False)

def insertAlteracoesTable(tabela,alteracao,tipo,tela,usuario, carrinho):
    hoje = data_brasil_corte_3h()
    horario = datetime.now(pytz.timezone(
        "America/Sao_Paulo")).strftime('%H:%M')
    print(tabela,alteracao,tipo,usuario)
    db.execute('INSERT INTO alteracoes (tabela,alteracao,tipo,usuario,tela,dia,horario, carrinho) VALUES (?,?,?,?,?,?,?,?)',tabela,alteracao,tipo,usuario,tela,hoje,horario, carrinho)
    getAlteracoes({'emitir':True, 'carrinho': carrinho})

@socketio.on('getAlteracoes')
def getAlteracoes(data):
    carrinho = data.get('carrinho')
    emitir = data.get('emitir')
    _register_carrinho_room(carrinho)
    print("Entrou GEtalteracoes")
    if type(emitir)!=bool:
        emiti=emitir.get('emitir')
        change=emitir.get('change')
        hoje = data_brasil_corte_3h() + timedelta(days=int(change))
        dia_mes = hoje.strftime('%d/%m')
    else:
        emiti = emitir
        hoje = data_brasil_corte_3h()
        dia_mes = hoje.strftime('%d/%m')

    data=db.execute("SELECT * FROM alteracoes WHERE dia = ? AND carrinho = ?",hoje, carrinho)
    emit_for_carrinho('respostaAlteracoes', {"alteracoes":data,"hoje":str(dia_mes)}, broadcast=emiti, carrinho=carrinho)

@socketio.on('faturamento_range')
def faturamento_range(data):
    # --------- Entrada / defaults ---------
    date_from = (data or {}).get('date_from') or (data or {}).get('start')
    date_to   = (data or {}).get('date_to')   or (data or {}).get('end')
    emitir    = bool((data or {}).get('emitir', False))
    carrinho  = (data or {}).get('carrinho')

    _register_carrinho_room(carrinho)

    if not date_from or not date_to:
        emit_for_carrinho('faturamento_enviar', {
            'dia': 'Período inválido',
            'faturamento': 0, 'faturamento_previsto': 0,
            'drink': 0, 'porcao': 0, 'restante': 0, 'pedidos': 0,
            'caixinha': 0, 'dezporcento': 0, 'desconto': 0,
            'pix': 0, 'debito': 0, 'credito': 0, 'dinheiro': 0
        }, broadcast=False, carrinho=carrinho)
        return

    # Garante formato AAAA-MM-DD e troca se vier invertido
    # (assume que 'dia' na sua tabela está em TEXT 'YYYY-MM-DD' ou DATE)
    try:
        df = datetime.strptime(date_from, '%Y-%m-%d').date()
        dt = datetime.strptime(date_to,   '%Y-%m-%d').date()
    except ValueError:
        emit_for_carrinho('faturamento_enviar', {
            'dia': 'Formato de data inválido (use YYYY-MM-DD)',
            'faturamento': 0, 'faturamento_previsto': 0,
            'drink': 0, 'porcao': 0, 'restante': 0, 'pedidos': 0,
            'caixinha': 0, 'dezporcento': 0, 'desconto': 0,
            'pix': 0, 'debito': 0, 'credito': 0, 'dinheiro': 0
        }, broadcast=False, carrinho=carrinho)
        return

    if df > dt:
        df, dt = dt, df  # swap
    date_from = df.strftime('%Y-%m-%d')
    date_to   = dt.strftime('%Y-%m-%d')

    # --------- Agregações em PAGAMENTOS ---------
    # Por forma de pagamento
    metodosDict = db.execute("""
        SELECT forma_de_pagamento, SUM(valor) AS valor_total
        FROM pagamentos
        WHERE dia BETWEEN ? AND ? AND carrinho = ?
        GROUP BY forma_de_pagamento
    """, date_from, date_to, carrinho)

    dinheiro = credito = debito = pix = 0
    for row in metodosDict:
        forma = (row.get("forma_de_pagamento") or "").lower()
        val = row.get("valor_total") or 0
        if forma == "dinheiro":
            dinheiro += val
        elif forma == "credito":
            credito += val
        elif forma == "debito":
            debito += val
        elif forma == "pix":
            pix += val

    # Por tipo (caixinha, 10%, desconto, etc.)
    caixinha = db.execute("SELECT COALESCE(SUM(caixinha),0) AS total_caixinha FROM pagamentos WHERE dia BETWEEN ? AND ? AND carrinho = ?", date_from, date_to, carrinho)
    caixinha = caixinha[0]['total_caixinha'] or 0
    dezporcento = db.execute("SELECT COALESCE(SUM(dez_por_cento),0) AS total_dezporcento FROM pagamentos WHERE dia BETWEEN ? AND ? AND carrinho = ?",date_from,date_to, carrinho)
    dezporcento = dezporcento[0]['total_dezporcento'] or 0
    desconto = db.execute("SELECT SUM(valor) AS total_desconto FROM pagamentos WHERE dia BETWEEN ? AND ? AND tipo = ? AND carrinho = ?",date_from,date_to ,'desconto', carrinho)
    desconto = desconto[0]['total_desconto'] or 0

    # Faturamento real = tudo que entrou - descontos
    total_recebimentos = db.execute("SELECT SUM(valor_total) AS total_recebimentos FROM pagamentos WHERE tipo = ? AND dia BETWEEN ? AND ? AND carrinho = ?", 'normal',date_from, date_to, carrinho)
    total_recebimentos = total_recebimentos[0]['total_recebimentos'] or 0
    # --------- Agregações em PEDIDOS ---------
    # Mantive sua lógica de categorias (1=restante, 2=drink, 3=porção)
    pedidosQuantDict = db.execute("""
        SELECT categoria,
               SUM(quantidade) AS quantidade_total,
               SUM(preco_unitario*NULLIF(quantidade,0))      AS preco_total,
               SUM(lucro_unitario*NULLIF(quantidade,0))      AS lucro_total
        FROM pedidos
        WHERE dia BETWEEN ? AND ?
          AND pedido != ? AND carrinho = ?
        GROUP BY categoria
        ORDER BY categoria ASC
    """, date_from, date_to, 'Comanda Aberta', carrinho)
    print('predidosQuantDict', pedidosQuantDict)
    drink = restante = porcao = 0
    faturamento_drink = faturamento_restante = faturamento_porcao = 0
    faturamento_previsto = 0
    lucro_previsto = 0
    lucro_drink = lucro_restante = lucro_porcao = 0
    for row in pedidosQuantDict:
        cat = row.get('categoria')
        qtd = row.get('quantidade_total') or 0
        preco_categoria = row.get('preco_total') or 0
        if cat == '1':
            restante = qtd
            faturamento_restante= preco_categoria
            lucro_restante= row.get('lucro_total') or 0
        elif cat == '2':
            drink = qtd
            faturamento_drink= preco_categoria
            lucro_drink= row.get('lucro_total') or 0
        elif cat == '3':
            porcao = qtd
            faturamento_porcao= preco_categoria
            lucro_porcao= row.get('lucro_total') or 0
        faturamento_previsto += (row.get('preco_total') or 0)
        lucro_previsto += (row.get('lucro_total') or 0)

    pedidos = (drink or 0) + (restante or 0) + (porcao or 0)

    # --------- Rótulo do período (mostrado no front em "Dia base") ---------
    periodo_fmt = f"{df.strftime('%d/%m')} — {dt.strftime('%d/%m')}"
    print(f'Faturamento de {periodo_fmt}: R$ {total_recebimentos:.2f} (previsto R$ {faturamento_previsto:.2f})')
    print(f'  Pedidos: {pedidos} (drink {drink}, porção {porcao}, restante {restante})')
    print(f'  Recebimentos: R$ {total_recebimentos:.2f} (pix R$ {pix:.2f}, débito R$ {debito:.2f}, crédito R$ {credito:.2f}, dinheiro R$ {dinheiro:.2f})')
    print(f'  Caixinha R$ {caixinha:.2f}, 10% R$ {dezporcento:.2f}, Descontos R$ {desconto:.2f})')
    print(f'  (emitir={emitir})')
    # ------------------------------------------
    # --------- Emite no MESMO formato do 'faturamento' ---------
    vendas_user = []
    vendas_user =db.execute('SELECT username, SUM(preco_unitario*NULLIF(quantidade,0)) AS valor_vendido, SUM(quantidade)  AS quant_vendida FROM pedidos WHERE dia BETWEEN ? AND ? AND pedido!= ? AND carrinho = ? GROUP BY username ORDER BY SUM(preco_unitario*NULLIF(quantidade,0)) DESC',date_from,date_to,'Comanda Aberta', carrinho)
    print('vendas_user', vendas_user)

    emit_for_carrinho('faturamento_enviar', {
        'dia': periodo_fmt,
        'faturamento': total_recebimentos,
        'faturamento_previsto': faturamento_previsto,
        'lucro_previsto': lucro_previsto,
        'drink': drink,
        'porcao': porcao,
        "restante": restante,
        "faturamento_drink": faturamento_drink,
        "faturamento_porcao": faturamento_porcao,
        "faturamento_restante": faturamento_restante,
        "lucro_drink": lucro_drink,
        "lucro_porcao": lucro_porcao,
        "lucro_restante": lucro_restante,
        "pedidos": pedidos,
        "caixinha": caixinha,
        "dezporcento": dezporcento,
        "desconto": desconto,
        "pix": pix,
        "debito": debito,
        "credito": credito,
        "dinheiro": dinheiro,
        "vendas_user": vendas_user
    }, broadcast=emitir, carrinho=carrinho)


import re
from flask_socketio import emit  # ou use socketio.emit se preferir

@socketio.on('pagar_itens')
def pagar_itens(data):
    comanda = data.get('comanda')
    itens = data.get('itens')
    forma_de_pagamento = data.get('forma_de_pagamento')
    caixinha = data.get('caixinha', 0)
    caixinha = float(caixinha) if caixinha else 0
    aplicarDez = data.get('aplicarDez', False)
    carrinho = data.get('carrinho')
    ids_quant = []
    dia = data_brasil_corte_3h()
    preco = 0
    for row in itens:
        quantidade = float(row.get('quantidade'))
        item = row.get('pedido')
        ids = db.execute('SELECT id,quantidade,quantidade_paga,preco_unitario FROM pedidos WHERE pedido = ? AND comanda = ? AND ordem = ? AND dia = ? AND carrinho = ?',item,comanda,0,dia, carrinho)
        id_usar = None
        preco_dict = None
        for id in ids:
            if id['quantidade'] - id['quantidade_paga'] >= 1:
                id_usar = id['id']
                preco_dict = id['preco_unitario']
                break
        if id_usar:
            db.execute('''
                    UPDATE pedidos
                    SET quantidade_paga = quantidade_paga + ?
                    WHERE comanda = ?
                    AND id = ?
                    AND ordem = ?
                    AND dia = ?
                    AND carrinho = ?
                ''', quantidade, comanda, id_usar, 0, dia, carrinho)

            if preco_dict:
                preco += float(preco_dict)*quantidade
                ids_quant.append({'id': id_usar, 'quantidade': quantidade})

    if ids:
        dez_por_cento = 0 if not aplicarDez else (preco * 0.1)
        db.execute('INSERT INTO pagamentos (valor,valor_total,caixinha,dez_por_cento,tipo,ordem,dia,forma_de_pagamento,comanda,horario,ids,carrinho) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',preco,preco+caixinha+dez_por_cento,caixinha,dez_por_cento,'normal',0,dia,forma_de_pagamento,comanda,datetime.now(brazil).strftime('%H:%M'),json.dumps(ids_quant),carrinho)
        faturamento({'emitir': True, 'carrinho': carrinho})
    totalComandaDict = db.execute('SELECT SUM(preco_unitario*NULLIF(quantidade,0)) AS total FROM pedidos WHERE comanda = ? AND ordem = ? AND dia = ? AND carrinho = ?', comanda, 0,dia, carrinho)
    valorTotalDict = db.execute('SELECT SUM(valor) as total FROM pagamentos WHERE dia = ? AND comanda = ? AND ordem = ? AND tipo = ? AND carrinho = ?',dia,comanda,0,'normal',carrinho)
    if totalComandaDict and valorTotalDict:
        totalComanda = float(totalComandaDict[0]['total']) if totalComandaDict[0]['total'] else 0
        valorTotal = float(valorTotalDict[0]['total']) if valorTotalDict[0]['total'] else 0
        if totalComanda <= valorTotal:
            handle_delete_comanda({'fcomanda':comanda,'carrinho':carrinho})

    handle_get_cardapio(comanda, carrinho)


@socketio.on('buscar_menu_data')
def buscar_menu_data(payload):
    try:
        print('entrou buscar menu data')

        if isinstance(payload, dict):
            emitir_broadcast = payload.get('emitir', True)
            carrinho = payload.get('carrinho')
        else:
            emitir_broadcast = bool(payload)
            carrinho = None

        if carrinho:
            _register_carrinho_room(carrinho)

        data_geral = db.execute(
            '''
            SELECT id, item, preco,preco_base, categoria_id, image, opcoes, subcategoria
            FROM cardapio
            WHERE usable_on_qr = ? and carrinho = ?
            ORDER BY item ASC
            ''',
            1, carrinho
        )


        data_geral_atualizado = []
        for row in data_geral:
            item_nome = (row.get('item') or '').strip()
            if not item_nome:
                continue

            cat_id = row.get('categoria_id')

            # Classificação
            if (cat_id in (1, 2)) and (item_nome not in ['amendoim', 'milho mostarda e mel', 'Pack de seda', 'cigarro', 'bic', 'dinheiro','castanha de caju']) and not item_nome.startswith('acai'):
                categoria_item = 'bebida'
            elif (cat_id == 3) or (item_nome in ['amendoim', 'milho mostarda e mel','castanha de caju']) or (item_nome.startswith('acai')):
                categoria_item = 'comida'
            else:
                categoria_item = 'outros'
            
            raw = row.get('opcoes')

            if not raw:
                options = []
            elif isinstance(raw, (list, dict)):
                # já é Python list/dict — ótimo
                options = raw
            else:
                try:
                    options = json.loads(raw)  # string JSON válida (aspas duplas)
                except Exception:
                    try:
                        # fallback se veio com aspas simples
                        options = json.loads(raw.replace("'", '"'))
                    except Exception as e:
                        print(f'Erro ao carregar opções para item {item_nome}:', e)
                        options = []

        
            
            data_geral_atualizado.append({
                'id': row['id'],
                'name': item_nome,
                'price': row.get('preco'),
                'original_price': row.get('preco_base'),
                'categoria': categoria_item,
                'subCategoria': row.get('subcategoria','outros'),
                'image': row.get('image') or None,
                'options': options,

            })

        emit_for_carrinho('menuData', data_geral_atualizado, broadcast=emitir_broadcast, carrinho=carrinho)

    except Exception as e:
        print('erro ao buscar_menu_data:', e)

@socketio.on('enviar_pedido_on_qr')
def enviar_pedido_on_qr(data,comanda,token,carrinho='NossoPoint'):
    print(f'enviar pedido on qr:\n {data}')
    print(f'comanda {comanda}')
    cliente = db.execute('SELECT numero FROM clientes WHERE token = ?',token)
    user_number = cliente[0].get('numero') if cliente else None
    if not user_number:
        user_number = 'Desconhecido'
    dia = data_brasil_corte_3h()
    for row in data:
        subcategoria = row.get('subcategoria')
        pedido_dict = db.execute('SELECT item,preco FROM cardapio WHERE id = ?',row.get('id'))
        if pedido_dict:
            pedido = pedido_dict[0].get('item')
            preco_unitario = float(pedido_dict[0].get('preco'))
        preco = float(row.get('price'))
        categoria = row.get('categoria')
        quantidade = row.get('quantity')
        options = row.get('selectedOptions',[])
        if not options:
            options = []
        obs = row.get('observations', None)
        extra = ''
        if categoria=='comida':
            if pedido not in ['amendoim', 'milho','castanha de caju']:
                categoria_id = 1
            elif pedido.startswith('acai'):
                categoria_id = 2
            else :
                categoria_id = 3
        else:
            if subcategoria in ['outros,cervejas']:
                categoria_id = 1
            else:
                categoria_id = 2

        agr = datetime.now()
        hora_min = agr.strftime("%H:%M")
        db.execute('''INSERT INTO pedidos (comanda,pedido,quantidade,extra,preco,preco_unitario,categoria,inicio,estado,nome,ordem,dia,username,opcoes,carrinho)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',comanda,pedido,quantidade,obs, preco,preco_unitario,categoria_id,hora_min,'A Fazer','-1',0,dia,f'Cliente:{user_number}',json.dumps(options),carrinho)



@socketio.on('savePromotion')
def savePromotion(data):
    print('entrou savePromotion')
    try:
        promotionData = data.get('promotionData')
        tipo = data.get('type')
        emitirBroadcast = data.get('emitirBroadcast', True)
        carrinho = data.get('carrinho')
        status = 'active' if promotionData['endDate'] > data_brasil_corte_3h().strftime('%Y-%m-%d') else 'expired'

        if tipo == 'create':
            db.execute('INSERT INTO promotions (name, products, type, value, endDate,status, carrinho) VALUES (?,?,?,?,?,?,?)',promotionData['name'],json.dumps(promotionData['products']),promotionData['type'],float(promotionData['value']),promotionData['endDate'],status, carrinho)
        elif tipo == 'update':
            db.execute('UPDATE promotions SET name = ?, products = ?, type = ?, value = ?, endDate = ?, status = ? WHERE id = ?',promotionData['name'],json.dumps(promotionData['products']),promotionData['type'],float(promotionData['value']),promotionData['endDate'],status,int(promotionData['id']))
        getPromotions({'emitir':True, 'carrinho': carrinho})
        # Aplicar promoção no cardápio
        if status == 'expired':
            for item in promotionData['products']:
                db.execute('UPDATE cardapio SET preco = preco_base WHERE id = ?', item['id'])
        else:
            if promotionData['type'] == 'percentage':
                value = 1.0 - (float(promotionData['value']) / 100)
                sinal = '*'
            else:
                value = float(promotionData['value'])
                sinal = '-'
            for item in promotionData['products']:
                db.execute(f'UPDATE cardapio SET preco = preco_base {sinal} ? WHERE id = ?', round(value, 2),item['id'])
        getCardapio({'emitir':True, 'carrinho': carrinho})


    except Exception as e:
        print('erro ao salvar promoção:', e)

@socketio.on('getPromotions')
def getPromotions(data):
    print('entrou getPromotions')
    emitirBroadcast = data.get('emitir')
    carrinho = data.get('carrinho')
    _register_carrinho_room(carrinho)
    dados = db.execute('SELECT * FROM promotions WHERE carrinho = ?', carrinho)
    emit_for_carrinho('promotionsData', dados, broadcast=emitirBroadcast, carrinho=carrinho)


@socketio.on('register_carrinho')
def handle_register_carrinho(data):
    carrinho = data.get('carrinho')
    if not carrinho:
        return
    join_room(carrinho)
    print(f"[SOCKET] Cliente entrou manualmente na room {carrinho}")
    emit('carrinho_registrado', {'status': 'ok', 'carrinho': carrinho})

@socketio.on('invocar_atendente')
def invocar_antendente(data):
    comanda = data.get('comanda')
    hoje = datetime.now()
    status = data.get('status')
    #horario = hoje.strftime('')
    
    #db.execute('INSERT into invocações_atendentes (comanda,horario,status,dia) VALUES (?,?,?,?)',)
        
    return {'status':'atendente_chamado'},200


    


SEU_CLIENT_ID = "c25a19b3-ca72-4ab3-b390-99e75a90e77d"
SEU_CLIENT_SECRET = "a3eg0gkdgddr6rs8zvlsd2yd4bweu1rj26s8h25w9p96c051y0jcishcz9tvhr1wvves5k5i7pf1x0ojos4dbvp2khct45vf0ug"
TOKEN_URL = "https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token"

_token_cache = {"accessToken": None, "expiresAt": 0.0}
_cache_lock = threading.Lock()

def get_ifood_token():
    """
    Sempre retorna (access_token: str, expires_at: float).
    Renova 60s antes de expirar.
    """
    with _cache_lock:
        now = time.time()
        if _token_cache["accessToken"] and (_token_cache["expiresAt"] - now > 60):
            return _token_cache["accessToken"], _token_cache["expiresAt"]

        if not SEU_CLIENT_ID or not SEU_CLIENT_SECRET:
            raise RuntimeError("IFOOD_CLIENT_ID/IFOOD_CLIENT_SECRET não configurados nas variáveis de ambiente.")

        data = {
            "grantType": "client_credentials",
            "clientId": SEU_CLIENT_ID,
            "clientSecret": SEU_CLIENT_SECRET,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        r = requests.post(TOKEN_URL, data=data, headers=headers, timeout=20)
        r.raise_for_status()
        payload = r.json()

        access_token = payload.get("accessToken") or payload.get("access_token")
        expires_in = int(payload.get("expiresIn") or payload.get("expires_in") or 0)
        if not access_token or not expires_in:
            raise RuntimeError(f"Resposta de token inesperada: {payload}")

        expires_at = now + expires_in
        _token_cache["accessToken"] = access_token
        _token_cache["expiresAt"] = expires_at
        return access_token, expires_at

def fluxo_authentication():
    try:
        token, exp = get_ifood_token()
        return {"ok": True, "accessToken": token, "expiresAt": int(exp)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.route("/ifood/token", methods=["GET"])
def ifood_token_health():
    """Rota utilitária pra testar autenticação rapidamente."""
    res = fluxo_authentication()
    status = 200 if res.get("ok") else 500
    return jsonify(res), status

@app.route('/webhook_ifood', methods=['POST'])
def web_hooks_notifications():
    """
    Webhook do iFood:
    - SEMPRE retornar rapidamente 204 (ou 200) pra evitar reentregas infinitas.
    - Processamento pode ser assíncrono; aqui está direto pra simplificar.
    """
    try:
        print('ENTROUUUUUUU NO WEBHOOOOOK')
        data = request.get_json(silent=True) or {}
        print('data',data)
        # Campos comuns em webhooks do iFood:
        # code: "PLACED" | "CONFIRMED" | ...
        # orderId: "xxxx"
        event_code = data.get("fullCode") or data.get("event") or data.get("eventType")
        
        # Garante token válido
        access_token, _ = get_ifood_token()

        if event_code == "PLACED":
            order_id = data.get("orderId") or data.get("id")
            # Aqui você pode enfileirar para um worker; mantive direto para ficar pronto pra uso.
            pedido_detalhes(order_id, access_token)

        # Responde rápido SEMPRE
        return ("", 204)
    except Exception as e:
        print(f"[webhook_ifood] erro: {e}")
        # Mesmo com erro, devolva 204 pra não gerar loop de reentrega
        return ("", 204)

def pedido_detalhes(order_id: str, access_token: str):
    """Busca detalhes do pedido no endpoint do iFood e faz o parse básico."""
    if not access_token:
        access_token, _ = get_ifood_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    # Detalhes do pedido
    url_order = f"https://merchant-api.ifood.com.br/order/v1.0/orders/{order_id}"
    resp = requests.get(url_order, headers=headers, timeout=20)
    resp.raise_for_status()
    order = resp.json()
    print("[iFood] detalhes do pedido:", order)
    print('/n'*8)
    data = extrair_pedido_ifood(order)
    print(f'Resposta:\n{resp}')
    order_id = data.get('pedido_id')
    produtos = data.get('produtos')
    nome_cliente = data.get('cliente_nome')
    endereco_dict = data.get('endereco')
    endereco = endereco_dict.get('rua')
    endereco+=f" {endereco_dict['numero']}"
    
    orderTiming = data.get('orderTiming')
    pedido_hora = data.get('pedido_hora')
    pedido_data = data.get('pedido_data')
    agendamento_hora = None
    if orderTiming == 'SCHEDULED':
        pedido_data = data.get('agendamento_data')
        agendamento_hora = data.get('agendamento_hora')
    
    for row in produtos:
        pedido = row['produto']
        quantidade = row['quantidade']
        preco = row['preco_total']
        extra = row.get('observacoes','')
        extra+='\n'
        for i in row.get('complementos'):
            extra+=f"{i['quantidade']} {i['nome']},"
        db.execute('INSERT INTO pedidos (pedido,quantidade,preco,categoria,inicio,estado,extra,nome,dia,orderTiming,endereco_entrega,order_id,remetente,horario_para_entrega) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  pedido,quantidade,preco,3,pedido_hora,'A Fazer',extra,nome_cliente,pedido_data,orderTiming,endereco,order_id,'IFOOD',pedido_hora)
    
    # save_order_to_db(order_id, customer_name, customer_phone, parsed_items, sub_total, delivery_fee, order_total)
def parse_iso_br(dt_str: str | None) -> tuple[str | None, str | None]:
    """Converte datetime ISO do iFood para data e hora separadas (em São Paulo)."""
    if not dt_str:
        return None, None
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone(brazil)
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")
    except Exception:
        return None, None

def extrair_pedido_ifood(order: dict) -> dict:
    """
    Retorna informações essenciais do pedido iFood:
    - nome do produto
    - complementos / especificações / observações
    - total com taxas (orderAmount)
    - valor sem taxas (subTotal)
    - endereço formatado
    - horário do pedido (data/hora)
    - se agendado, horário do agendamento (data/hora)
    """
    # Totais
    total_block = order.get("total") or {}
    valor_sem_taxas = total_block.get("subTotal")
    valor_com_taxas = total_block.get("orderAmount")
    print('Totais')

    # Endereço
    delivery = order.get("delivery") or {}
    addr = delivery.get("deliveryAddress") or {}
    endereco = {
        "rua": addr.get("streetName"),
        "numero": addr.get("streetNumber"),
        "bairro": addr.get("neighborhood"),
        "cidade": addr.get("city"),
        "estado": addr.get("state"),
        "cep": addr.get("postalCode"),
        "complemento": addr.get("complement"),
        "referencia": addr.get("reference"),
    }
    print('endereco')

    # Horários
    pedido_data, pedido_hora = parse_iso_br(order.get("createdAt"))
    agendamento_data, agendamento_hora = parse_iso_br(delivery.get("deliveryDateTime"))
    print('horarios')
    # Itens
    itens_extraidos = []
    for it in order.get("items", []):
        item_dict = {
            "produto": it.get("name"),
            "quantidade": it.get("quantity", 1),
            "preco_unit": it.get("unitPrice"),
            "preco_total": it.get("totalPrice"),
            "observacoes": it.get("observations"),
            "complementos": []
        }
        for opt in it.get("options", []):
            comp = {
                "nome": opt.get("name"),
                "grupo": opt.get("groupName"),
                "quantidade": opt.get("quantity", 1),
                "preco": opt.get("price"),
                "customizacoes": []
            }
            for cust in opt.get("customizations", []):
                comp["customizacoes"].append({
                    "nome": cust.get("name"),
                    "grupo": cust.get("groupName"),
                    "quantidade": cust.get("quantity", 1),
                    "preco": cust.get("price"),
                })
            item_dict["complementos"].append(comp)
        itens_extraidos.append(item_dict)
    print('itens')

    return {
        "pedido_id": order.get("id"),
        "cliente_nome": (order.get("customer") or {}).get("name"),
        "produtos": itens_extraidos,
        "valor_sem_taxas": valor_sem_taxas,
        "endereco": endereco,
        "pedido_data": pedido_data,
        "pedido_hora": pedido_hora,
        "orderTiming": order.get('orderTiming'),
        "agendamento_data": agendamento_data,
        "agendamento_hora": agendamento_hora,
    }

def _now_iso():
    return datetime.utcnow().isoformat(timespec="seconds")

_slug_non_alnum = re.compile(r"[^a-z0-9]+")
def slugify(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    s = _slug_non_alnum.sub("-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s

def _get_column_names(table: str):
    try:
        rows = db.execute(f"SELECT name FROM pragma_table_info('{table}')") or []
        return { (r.get("name") or "").strip() for r in rows }
    except Exception:
        return set()

def ensure_schema():
    """
    Garante colunas em `opcoes` e cria auditoria (sem DEFAULT(datetime('now'))).
    Backfill dos slugs a partir de nome_grupo/opcao.
    """
    #analisar
    colnames = _get_column_names("opcoes")

    # Estas três já existem no seu schema, mas mantemos defensivo:
    if "grupo_slug" not in colnames:
        db.execute("ALTER TABLE opcoes ADD COLUMN grupo_slug TEXT")
    if "opcao_slug" not in colnames:
        db.execute("ALTER TABLE opcoes ADD COLUMN opcao_slug TEXT")
    if "updated_at" not in colnames:
        db.execute("ALTER TABLE opcoes ADD COLUMN updated_at TEXT")

    # Auditoria
    db.execute("""
        CREATE TABLE IF NOT EXISTS opcoes_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT (datetime('now')),
            actor TEXT,
            where_json TEXT,
            set_json TEXT,
            dry_run INTEGER,
            matched INTEGER,
            updated INTEGER,
            items_json TEXT
        )
    """)

    # Backfill de slugs (a partir de nome_grupo/opcao)
    rows = db.execute("""
        SELECT rowid, nome_grupo, opcao, grupo_slug, opcao_slug
        FROM opcoes
    """) or []
    to_update = []
    for r in rows:
        gslug = (r.get("grupo_slug") or "").strip()
        oslug = (r.get("opcao_slug") or "").strip()
        if not gslug or not oslug:
            ng = (r.get("nome_grupo") or "").strip()
            op = (r.get("opcao") or "").strip()
            to_update.append({
                "rowid": r["rowid"],
                "g": slugify(ng),
                "o": slugify(op),
            })

    if to_update:
        db.execute("BEGIN")
        try:
            ts = _now_iso()
            for u in to_update:
                db.execute(
                    "UPDATE opcoes SET grupo_slug = :g, opcao_slug = :o, updated_at = :ts WHERE rowid = :rowid",
                    g=u["g"], o=u["o"], ts=ts, rowid=u["rowid"]
                )
            db.execute("COMMIT")
        except Exception:
            db.execute("ROLLBACK")
            raise

def _parse_bool(s):
    if s is None:
        return False
    return str(s).strip().lower() in ("1", "true", "yes", "y")

# ---------- /opcoes/aggregate ----------
@app.route("/opcoes/aggregate", methods=["GET"])
def opcoes_aggregate():
    """
    Params:
      q (opcional) - pesquisa em nome_grupo/opcao/item
      grupo_slug (opcional)
      somente_esgotados (0|1)
      somente_extra_positivo (0|1)
      limit (opcional, padrão 100)
    """
    ensure_schema()

    q = (request.args.get("q") or "").strip()
    grupo_slug = (request.args.get("grupo_slug") or "").strip().lower()
    somente_esgotados = _parse_bool(request.args.get("somente_esgotados"))
    somente_extra_positivo = _parse_bool(request.args.get("somente_extra_positivo"))
    carrinho = (request.args.get("carrinho") or "").strip()
    try:
        limit = int(request.args.get("limit") or 100)
    except Exception:
        limit = 100
    limit = max(1, min(limit, 500))

    # Filtros dinâmicos (base)
    wh = ["carrinho = :carrinho"]
    base_params = {"carrinho":carrinho}

    if grupo_slug:
        wh.append("grupo_slug = :gslug")
        base_params["gslug"] = grupo_slug

    if somente_esgotados:
        wh.append("(esgotado_bool = 1)")

    if somente_extra_positivo:
        wh.append("(COALESCE(valor_extra,0) > 0)")

    if q:
        wh.append("""
          (
            LOWER(COALESCE(nome_grupo,'')) LIKE :q
            OR LOWER(COALESCE(opcao,'')) LIKE :q
            OR LOWER(COALESCE(item,'')) LIKE :q
          )
        """)
        base_params["q"] = f"%{q.lower()}%"

    where_sql = " AND ".join(wh)

    # -------- Agregação (usa :lim) --------
    agg_sql = f"""
        SELECT
          MIN(nome_grupo)  AS grupo,
          grupo_slug       AS grupo_slug,
          MIN(opcao)       AS opcao,
          opcao_slug       AS opcao_slug,
          COUNT(*)         AS ocorrencias,
          SUM(CASE WHEN esgotado_bool = 1 THEN 1 ELSE 0 END) AS esgotados,
          ROUND(AVG(COALESCE(valor_extra,0)), 2) AS media_valor_extra
        FROM opcoes
        WHERE {where_sql}
        GROUP BY grupo_slug, opcao_slug
        ORDER BY MIN(nome_grupo), MIN(opcao)
        LIMIT :lim
    """
    paramsAgg = dict(base_params)
    paramsAgg["lim"] = limit

    clusters = db.execute(agg_sql, **paramsAgg) or []

    # -------- Amostra de itens (NÃO usa :lim) --------
    out = []
    for c in clusters:
        items_sql = f"""
            SELECT
              id_cardapio AS item_id,
              item        AS item_nome,
              valor_extra,
              esgotado_bool
            FROM opcoes
            WHERE {where_sql} AND grupo_slug = :gs AND opcao_slug = :os
            ORDER BY id_cardapio
            LIMIT 30
        """
        paramsItems = dict(base_params)
        paramsItems["gs"] = c["grupo_slug"]
        paramsItems["os"] = c["opcao_slug"]

        items = db.execute(items_sql, **paramsItems) or []

        out.append({
            "grupo": c["grupo"],
            "grupo_slug": c["grupo_slug"],
            "opcao": c["opcao"],
            "opcao_slug": c["opcao_slug"],
            "ocorrencias": c["ocorrencias"],
            "esgotados": c["esgotados"] or 0,
            "media_valor_extra": float(c["media_valor_extra"] or 0),
            "amostra_itens": [
                {
                    "item_id": r["item_id"],
                    "item_nome": r["item_nome"],
                    "valor_extra": float(r["valor_extra"] or 0),
                    "esgotado": int(r["esgotado_bool"] or 0),
                }
                for r in items
            ],
        })

    return jsonify(out)

# ---------- /opcoes/bulk-update ----------
@app.route("/opcoes/bulk-update", methods=["POST"])
def opcoes_bulk_update():
    """
    Body:
    {
      "where": { "grupo_slug": "...", "opcao_slug": "..." },
      "restrict_items": [1,2,3],                  // IDs de cardapio (id_cardapio) - opcional
      "set": { "valor_extra": 22.0, "esgotado": 1 }, // pelo menos um
      "dry_run": true|false
    }
    """
    ensure_schema()

    data = request.get_json(force=True) or {}
    where = data.get("where") or {}
    carrinho = (data.get('carrinho') or "")
    set_ = data.get("set") or {}
    restrict_items = data.get("restrict_items") or []
    dry_run = bool(data.get("dry_run"))

    gslug = (where.get("grupo_slug") or "").strip().lower()
    oslug = (where.get("opcao_slug") or "").strip().lower()
    if not gslug or not oslug:
        return jsonify({"error": "where.grupo_slug e where.opcao_slug são obrigatórios."}), 400

    set_fields = {}
    if "valor_extra" in set_ and set_["valor_extra"] is not None:
        try:
            set_fields["valor_extra"] = float(set_["valor_extra"])
        except Exception:
            return jsonify({"error": "set.valor_extra inválido."}), 400
    if "esgotado" in set_ and set_["esgotado"] is not None:
        v = set_["esgotado"]
        if v in (0, 1, "0", "1", True, False, "true", "false", "True", "False"):
            set_fields["esgotado_bool"] = 1 if str(v).lower() in ("1", "true") else 0
        else:
            return jsonify({"error": "set.esgotado deve ser 0/1/true/false."}), 400

    if not set_fields:
        return jsonify({"error": "Inclua pelo menos um campo em 'set' (valor_extra/esgotado)."}), 400

    # Filtro base
    wh = ["grupo_slug = :gs", "opcao_slug = :os", "carrinho = :carrinho"]
    params = {"gs": gslug, "os": oslug, "carrinho": carrinho}

    # Restrição opcional por itens (id_cardapio)
    ids = []
    if restrict_items:
        ids = [int(x) for x in restrict_items if str(x).isdigit()]
        if not ids:
            return jsonify({"error": "restrict_items inválido/vazio."}), 400
        placeholders = ",".join([f":id{i}" for i in range(len(ids))])
        wh.append(f"id_cardapio IN ({placeholders})")
        for i, v in enumerate(ids):
            params[f"id{i}"] = v

    where_sql = " AND ".join(wh)

    # Impacto
    rows = db.execute(
        f"SELECT id_cardapio FROM opcoes WHERE {where_sql}",
        **params) or []
    matched = len(rows)
    items = sorted(list({r["id_cardapio"] for r in rows}))
    if dry_run:
        return jsonify({
            "matched": matched,
            "would_update": matched,
            "items": items,
            "dry_run": True
        })

    # UPDATE em transação
    set_clauses = []
    set_params = {}
    if "valor_extra" in set_fields:
        set_clauses.append("valor_extra = :nv")
        set_params["nv"] = float(set_fields["valor_extra"])
    if "esgotado_bool" in set_fields:
        set_clauses.append("esgotado_bool = :ne")
        set_params["ne"] = int(set_fields["esgotado_bool"])
    set_clauses.append("updated_at = :ts")
    set_params["ts"] = _now_iso()

    db.execute("BEGIN")
    try:
        sql = f"UPDATE opcoes SET {', '.join(set_clauses)} WHERE {where_sql}"
        db.execute(sql, **set_params, **params)
        updated = matched  # cs50/SQLite não dá rowcount confiável

        actor = request.headers.get("X-User") or "api"
        audit_id = db.execute(
            """
            INSERT INTO opcoes_audit (actor, where_json, set_json, dry_run, matched, updated, items_json, carrinho)
            VALUES (:actor, :w, :s, 0, :m, :u, :items, :carrinho)
            """,
            actor=actor,
            w=json.dumps({"grupo_slug": gslug, "opcao_slug": oslug}, ensure_ascii=False),
            s=json.dumps(set_fields, ensure_ascii=False),
            m=matched,
            u=updated,
            items=json.dumps(items),
            carrinho=carrinho
        )
        getCardapio({'emitir':True,'carrinho': carrinho})  # broadcast atualização do cardápio
        if not audit_id:
            rid = db.execute("SELECT last_insert_rowid() AS id")[0]["id"]
            audit_id = rid

        db.execute("COMMIT")
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({"error": f"Falha ao aplicar: {e}"}), 500

    return jsonify({
        "matched": matched,
        "updated": updated,
        "items": items,
        "audit_id": audit_id,
        "dry_run": False
    })

# ---------- Reconstrução do JSON cardapio.opcoes ----------
def _read_cardapio_props_map(item_id: int):
    """
    Lê cardapio.opcoes e devolve mapa por nome do grupo com props a preservar:
      { "<nome_grupo>": {"ids": ..., "max_selected": ..., "obrigatorio": ...}, ... }
    """
    row = db.execute("SELECT opcoes FROM cardapio WHERE id = :id", id=item_id)
    if not row or not row[0]["opcoes"]:
        return {}
    try:
        data = json.loads(row[0]["opcoes"])
    except Exception:
        return {}
    out = {}
    for g in data if isinstance(data, list) else []:
        nome = (g.get("nome") or "").strip()
        if not nome:
            continue
        out[nome] = {
            "ids": g.get("ids") or "",
            "max_selected": g.get("max_selected", 1),
            "obrigatorio": g.get("obrigatorio", 0),
        }
    return out

def _build_opcoes_json_from_table(item_id: int, carrinho) -> str:
    """
    Monta a estrutura JSON de grupos/opções para um item
    a partir da tabela opcoes (campos: nome_grupo, opcao, valor_extra, esgotado_bool),
    preservando ids/max_selected/obrigatorio do JSON atual.
    """
    rows = db.execute("""
        SELECT nome_grupo, grupo_slug, opcao, valor_extra, esgotado_bool
        FROM opcoes
        WHERE id_cardapio = :id AND carrinho = :carrinho
        ORDER BY nome_grupo, opcao
    """, id=item_id, carrinho=carrinho) or []

    keep = _read_cardapio_props_map(item_id)
    grupos = {}
    for r in rows:
        gnome = (r["nome_grupo"] or "").strip()
        if not gnome:
            continue
        if gnome not in grupos:
            base = keep.get(gnome, {})
            grupos[gnome] = {
                "nome": gnome,
                "ids": base.get("ids", ""),
                "options": [],
                "max_selected": base.get("max_selected", 1),
                "obrigatorio": base.get("obrigatorio", 0),
            }
        grupos[gnome]["options"].append({
            "nome": r["opcao"],
            "valor_extra": float(r["valor_extra"] or 0),
            "esgotado": int(r["esgotado_bool"] or 0),
        })

    out = []
    for gnome in sorted(grupos.keys(), key=lambda s: s.lower()):
        gobj = grupos[gnome]
        gobj["options"] = sorted(gobj["options"], key=lambda x: (str(x["nome"]).lower()))
        out.append(gobj)

    return json.dumps(out, ensure_ascii=False)

# ---------- /opcoes/sync-json ----------
@app.route("/opcoes/sync-json", methods=["POST"])
def opcoes_sync_json():
    """
    Body:
      { "items": [1,2,3] }   // IDs de cardapio (obrigatório)
    Efeito:
      Reescreve cardapio.opcoes de cada item com base na tabela opcoes.
    """
    ensure_schema()

    data = request.get_json(force=True) or {}
    carrinho = data.get('carrinho')
    items = data.get("items")
    if not isinstance(items, list) or not items:
        return jsonify({"error": "Forneça 'items' como lista de IDs (ex.: [1,2,3])."}), 400

    item_ids = sorted(list({int(i) for i in items if str(i).isdigit()}))
    if not item_ids:
        return jsonify({"error": "Lista 'items' inválida."}), 400

    db.execute("BEGIN")
    synced = 0
    try:
        for iid in item_ids:
            new_json = _build_opcoes_json_from_table(iid, carrinho)
            db.execute(
                "UPDATE cardapio SET opcoes = :j WHERE id = :id",
                j=new_json, id=iid
            )
            synced += 1
        db.execute("COMMIT")
        getCardapio(True)  # broadcast atualização do cardápio
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({"error": f"Falha ao sincronizar: {e}"}), 500

    return jsonify({"synced": synced, "items": item_ids})

# ======= /opcoes/group-props-bulk  (editar max_selected, obrigatorio, ids do GRUPO) =======
@app.route("/opcoes/group-props-bulk", methods=["POST"])
def opcoes_group_props_bulk():
    """
    Body:
    {
      "where": { "grupo_slug": "adicionais" },      // obrigatório
      "restrict_items": [1,2,3],                    // opcional (IDs de cardápio)
      "set": { "max_selected": 2, "obrigatorio": 1, "ids": "" },  // pelo menos um
      "dry_run": true|false
    }

    Efeito:
      - Descobre os itens que possuem esse grupo (via tabela `opcoes`).
      - Se dry_run: retorna só o impacto (quantos itens).
      - Se aplicar: reconstrói o JSON de cada item a partir da TABELA `opcoes`,
        e sobrescreve as propriedades do grupo alvo (max_selected / obrigatorio / ids).
    """
    ensure_schema()

    data = request.get_json(force=True) or {}
    where = data.get("where") or {}
    set_ = data.get("set") or {}
    restrict_items = data.get("restrict_items") or []
    dry_run = bool(data.get("dry_run"))
    carrinho = (data.get('carrinho') or "")
    gslug = (where.get("grupo_slug") or "").strip().lower()
    if not gslug:
        return jsonify({"error": "where.grupo_slug é obrigatório."}), 400

    # Valida campos do set
    set_fields = {}
    if "max_selected" in set_ and set_["max_selected"] is not None:
        try:
            ms = int(set_["max_selected"])
            if ms < 0:
                return jsonify({"error": "max_selected deve ser >= 0."}), 400
            set_fields["max_selected"] = ms
        except Exception:
            return jsonify({"error": "max_selected inválido (inteiro)."}), 400
    if "obrigatorio" in set_ and set_["obrigatorio"] is not None:
        v = set_["obrigatorio"]
        if v in (0, 1, "0", "1", True, False, "true", "false", "True", "False"):
            set_fields["obrigatorio"] = 1 if str(v).lower() in ("1", "true") else 0
        else:
            return jsonify({"error": "obrigatorio deve ser 0/1/true/false."}), 400
    if "ids" in set_ and set_["ids"] is not None:
        # Campo livre string
        set_fields["ids"] = str(set_["ids"])

    if not set_fields:
        return jsonify({"error": "Inclua pelo menos um campo em 'set' (max_selected/obrigatorio/ids)."}), 400

    # Monta filtro base para descobrir itens que possuem esse grupo
    wh = ["grupo_slug = :gs", "carrinho = :carrinho"]
    params = {"gs": gslug, "carrinho": carrinho}

    ids = []
    if restrict_items:
        ids = [int(x) for x in restrict_items if str(x).isdigit()]
        if not ids:
            return jsonify({"error": "restrict_items inválido/vazio."}), 400
        placeholders = ",".join([f":id{i}" for i in range(len(ids))])
        wh.append(f"id_cardapio IN ({placeholders})")
        for i, v in enumerate(ids):
            params[f"id{i}"] = v

    where_sql = " AND ".join(wh)

    # Coleta itens distintos que possuem esse grupo
    item_rows = db.execute(
        f"""
        SELECT DISTINCT id_cardapio
        FROM opcoes
        WHERE {where_sql}
        ORDER BY id_cardapio
        """,
        **params
    ) or []
    items = [r["id_cardapio"] for r in item_rows]
    matched = len(items)

    if dry_run:
        return jsonify({
            "matched": matched,
            "would_update": matched,
            "items": items,
            "dry_run": True
        })

    # Aplica nos JSONs de cada item
    db.execute("BEGIN")
    try:
        for iid in items:
            # Nome do grupo desse item (para casar com JSON)
            gr = db.execute(
                "SELECT MIN(nome_grupo) AS nome FROM opcoes WHERE id_cardapio = :id AND grupo_slug = :gs AND carrinho = :carrinho",
                id=iid, gs=gslug, carrinho = carrinho
            )
            group_name = (gr[0]["nome"] if gr and gr[0]["nome"] else "").strip()
            if not group_name:
                # não deve ocorrer, pois o item veio da opcoes com esse grupo_slug
                continue

            # Reconstrói JSON a partir da tabela (garante que grupos/opções estejam atualizados)
            json_str = _build_opcoes_json_from_table(iid, carrinho)
            try:
                data_json = json.loads(json_str) if json_str else []
            except Exception:
                data_json = []

            # Sobrescreve props do grupo alvo
            changed = False
            for g in data_json:
                if (g.get("nome") or "").strip() == group_name:
                    if "max_selected" in set_fields:
                        g["max_selected"] = int(set_fields["max_selected"])
                        changed = True
                    if "obrigatorio" in set_fields:
                        g["obrigatorio"] = int(set_fields["obrigatorio"])
                        changed = True
                    if "ids" in set_fields:
                        g["ids"] = set_fields["ids"]
                        changed = True
                    break

            if changed:
                new_str = json.dumps(data_json, ensure_ascii=False)
                db.execute("UPDATE cardapio SET opcoes = :j WHERE id = :id AND carrinho = :carrinho", j=new_str, id=iid, carrinho=carrinho)
                getCardapio(True)  # broadcast atualização do cardápio

        # Auditoria (reuso da tabela existente)
        actor = request.headers.get("X-User") or "api"
        audit_id = db.execute(
            """
            INSERT INTO opcoes_audit (actor, where_json, set_json, dry_run, matched, updated, items_json, carrinho)
            VALUES (:actor, :w, :s, 0, :m, :u, :items, :carrinho)
            """,
            actor=actor,
            w=json.dumps({"grupo_slug": gslug, "type": "group_props"}, ensure_ascii=False),
            s=json.dumps(set_fields, ensure_ascii=False),
            m=matched,
            u=matched,
            items=json.dumps(items),
            carrinho=carrinho
        )
        if not audit_id:
            rid = db.execute("SELECT last_insert_rowid() AS id")[0]["id"]
            audit_id = rid

        db.execute("COMMIT")
    except Exception as e:
        db.execute("ROLLBACK")
        return jsonify({"error": f"Falha ao aplicar propriedades do grupo: {e}"}), 500

    return jsonify({
        "matched": matched,
        "updated": matched,
        "items": items,
        "audit_id": audit_id,
        "dry_run": False
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)

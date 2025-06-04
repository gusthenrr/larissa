# backend.py

from flask import Flask, request, jsonify, url_for
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from cs50 import SQL
from datetime import datetime
from pytz import timezone
import os

var=True
import shutil
if var:
    DATABASE_PATH = "/data/dados.db"
    if not os.path.exists(DATABASE_PATH):
        shutil.copy("dados.db", DATABASE_PATH)
    db = SQL("sqlite:///" + DATABASE_PATH)
else:
    db=SQL('sqlite:///data/dados.db')

app = Flask(
    __name__,
    static_folder='static',      # pasta que vai servir arquivos
    static_url_path='/static'    # endereço para acessar esses arquivos
)

app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui'  # Use uma chave real em produção!

UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

brazil = timezone('America/Sao_Paulo')
# Inicializa o Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")  # "*" aceita conexões de qualquer origem



@app.route('/upload-item-photo', methods=['POST'])
def upload_item_photo():
    if 'photo' not in request.files:
        return jsonify({'error': 'Nenhuma foto enviada'}), 400

    file = request.files['photo']
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # gera URL pública completa
    image_url = url_for(
        'static',
        filename=f'uploads/{filename}',
        _external=True
    )
    return jsonify({'imageUrl': image_url}), 200

@app.route('/items-json')
def items_json():
    # busca tudo da tabela itens e retorna como JSON
    registros = db.execute("SELECT * FROM itens")
    return jsonify(registros)


@socketio.on("getDados")
def getDados():
    print('get dados')
    todos_dados=db.execute("SELECT * FROM itens")
    print("todos os dados",todos_dados)
    emit("RespostaPesquisa",todos_dados,broadcast=True)

@socketio.on("getDadosPedidos")
def getDadosPedidos():
    print('get dados')
    todos_dados=db.execute("SELECT * FROM pedidos")
    print("todos os dados",todos_dados)
    emit("RespostaPedidos",todos_dados,broadcast=True)

@socketio.on('SaveAlteracoesPedidos')
def save_alteracoes_pedidos(data):
    id = data.get('id', '')
    item = data.get('item', '')
    preco = data.get('preco_de_venda', '')
    link = data.get('link', '')
    nome_loja = data.get('loja')
    categoria = data.get('categoria', '')
    imagem = data.get('imagem', '')
    endereco = data.get('endereco', '')
    dia_da_compra = data.get('dia_da_compra', '')
    previsao_entrega = data.get('previsao_entrega')
    db.execute('UPDATE pedidos SET item=?,preco=?,link=?,loja=?,categoria=?,imagem=?,endereco=?,dia_da_compra=?,previsao_entrega=?',item,preco,link,nome_loja,categoria,imagem,endereco,dia_da_compra,previsao_entrega)
    getDadosPedidos()
    
@socketio.on("SaveAlteracoes")
def saveAlteracoese(data):
    id=data['id']
    item=data['item']
    preco=data.get('preco_de_venda', '')
    link=data['link']
    nomeLoja=data['loja']
    categoria=data['categoria']
    imagem=data['imagem']
    db.execute("UPDATE itens SET item=?,preco_de_venda=?,link=?,loja=?,categoria=?,imagem=? WHERE id=?",item,preco,link,nomeLoja,categoria,imagem,id)

@socketio.on("ExcluirPedido")
def ExcluirPedido(data):
    id=data['id']
    db.execute("DELETE FROM pedidos WHERE id=?", id)
    print(f"excluir o pedido  {data['item']} de {data['nome_comprador']}")
    getDadosPedidos()

@socketio.on("ExcluirItem")
def ExcluirPedido(data):
    id=data['id']
    db.execute("DELETE FROM itens WHERE id=?", id)
    print(f"excluir o pedido  {data['item']} de {data['nome_comprador']}")
    getDados()

@socketio.on('AdicionarNovoPedido')
def adicionar_novo_pedido(data):
    print('entrou adicionar novo pedido')
    agora = datetime.now(brazil).date()
    dia = agora.strftime('%d-%m-%Y')
    itemCompleto = data.get('itemOriginal',{})
    item = itemCompleto.get('item', '')
    preco=itemCompleto.get('preco','')
    categoria = itemCompleto.get('categoria', '')
    loja = itemCompleto.get('loja', '')
    imagem=itemCompleto.get('imagem','')
    link = itemCompleto.get('link', '')
    comprador = data.get('comprador', '')
    telefone = data.get('telefone', '')
    endereco = data.get('endereco','')
    previsao=data.get('previsao','')
    db.execute('INSERT INTO pedidos (item,nome_comprador,numero_telefone,dia_da_compra,categoria,loja,link,previsao_entrega,endereco,imagem,preco) VALUES (?,?,?,?,?,?,?,?,?,?,?)',item,comprador,telefone,dia,categoria,loja,link,previsao,endereco,imagem,preco)
    getDadosPedidos()

@socketio.on("GetCategoriaLoja")
def getCategoriaLojas():
    print("entrou no gett")
    dados=db.execute("SELECT categoria,loja FROM itens")
    print("dados:",dados)
    emit("RespostaCategoriaLoja",dados)

@socketio.on('AdicionarItem')
def adicionarItem(data):
    print('entrouuuuu')
    item=data['item']
    link=data['link']
    nomeLoja=data['selectedLoja']
    categoria=data['selectedCategoria']
    imagem=data.get("imagem",'')
    preco_de_venda = data.get('preco', '')
    db.execute("INSERT INTO itens (item, preco_de_venda, link, loja, categoria, imagem) VALUES (?, ?, ?, ?, ?, ?)",item,preco_de_venda,link,nomeLoja,categoria,imagem)
    print("item guardado")
    getDados()


if __name__ == '__main__':
    # Rode o servidor com suporte a WebSocket
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

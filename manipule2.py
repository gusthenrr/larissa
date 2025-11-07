from cs50 import SQL
import shutil
import os
from datetime import datetime

var = True

if var:
    DATABASE_PATH = "/data/dados.db"
    if not os.path.exists(DATABASE_PATH):
        shutil.copy("dados.db", DATABASE_PATH)
    db = SQL("sqlite:///" + DATABASE_PATH)
else:
    DATABASE_PATH = "data/dados.db"
    db=SQL("sqlite:///" + DATABASE_PATH)
insert_sql = """
INSERT INTO cardapio
(item,preco,categoria_id,opcoes,instrucoes,image,preco_base,usable_on_qr,subcategoria,subsubcategoria,carrinho)
VALUES (?,?,?,?,?,?,?,?,?,?,?)
"""

dados = [
    {'item':'alho','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 12.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 41.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 63.90, "esgotado": 0},], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'calabresa','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 13.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 37.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 57.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'}, 
    {'item':'frango com catupiry','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 17.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 53.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 81.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'marguerita','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 17.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 40.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 62.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'mussarela','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 14.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 38.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 59.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'napolitana','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 13.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 42.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 65.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'paulista','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 13.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 53.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 82.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'portuguesa','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 19.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 58.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 90.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'3 queijos','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 15.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 49.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 75.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'4 queijos','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 16.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 56.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 86.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'5 queijos','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 17.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 63.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 97.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'queijo coalho','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 17.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 63.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 97.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'atum','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 14.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 52.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 80.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'caipira','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 16.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 53.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 82.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'carne seca','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 16.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 55.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 84.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'lombo','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 16.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 51.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 79.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'romana','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 17.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 57.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 87.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'abobrinha','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 15.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 45.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 69.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'rucula','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 17.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 46.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 71.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'vegana','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 12.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 39.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 60.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'brocolis','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 15.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 49.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 74.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'alho poro','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 17.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 56.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 86.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'a moda','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 18.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 62.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 95.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'camarao','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 17.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 57.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 88.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'italiana','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 14.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 42.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 65.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'jardineira','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 20.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 50.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 77.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'pepperoni','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 17.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 50.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 77.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'santista','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 22.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 74.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 114.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'shimeji','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 16.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 55.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 84.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'brigadeiro','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 16.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 34.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 52.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'casadinha','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 17.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 35.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 54.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'banana nevada','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 18.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 40.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 61.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'pistache com nutella','preco':0,'categoria_id':3,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Pedaco", "valor_extra": 19.90, "esgotado": 0},
                                {"nome": "Broto", "valor_extra": 42.90, "esgotado": 0},
                                 {"nome": "Grande", "valor_extra": 65.90, "esgotado": 0}], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'heineken long 330ml','preco':13.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'corona long 330ml','preco':13.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'estrella galicia 330ml','preco':13.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'heineken 0 330ml','preco':13.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'original 600ml','preco':18.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'teresopolis 600ml','preco':18.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'estrella galicia 600ml','preco':18.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'heineken 600ml','preco':18.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'coca cola lata','preco':7.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'coca cola zero lata','preco':7.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'coca cola 600ml','preco':11.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'coca cola zero 600ml','preco':11.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'suco del vale pessego lata','preco':7.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'suco de laranja natural','preco':15.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'suco de limao natural','preco':15.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'guarana','preco':7.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'agua','preco':5.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'tonica','preco':7.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'limoneto','preco':7.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'agua com gas','preco':6.90,'categoria_id':1,'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'vinho merlot','preco':0,'categoria_id':1,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Taca", "valor_extra": 29.90, "esgotado": 0},
                                {"nome": "Garrafa", "valor_extra": 109.90, "esgotado": 0},], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'vinho cabernet sauvignon','preco':0,'categoria_id':1,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Taca", "valor_extra": 39.90, "esgotado": 0},
                                {"nome": "Garrafa", "valor_extra": 139.90, "esgotado": 0},], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'vinho pinot noir','preco':0,'categoria_id':1,'opcoes':'''[
                                {"nome": "Tamanho", "ids": "",
                                 "options": [{"nome": "Taca", "valor_extra": 44.90, "esgotado": 0},
                                {"nome": "Garrafa", "valor_extra": 159.90, "esgotado": 0},], "max_selected": 1, "obrigatorio": 1}]''',
                                 'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},
    {'item':'1/2 broto','preco':0,'categoria_id':3,'opcoes':'''[
  {"nome": "Sabor", "ids": "",
   "options": [
     {"nome": "Alho", "valor_extra": 25.90, "esgotado": 0},
     {"nome": "Calabresa", "valor_extra": 22.90, "esgotado": 0},
     {"nome": "Frango com Catupiry", "valor_extra": 32.90, "esgotado": 0},
     {"nome": "Marguerita", "valor_extra": 24.90, "esgotado": 0},
     {"nome": "Mussarela", "valor_extra": 23.90, "esgotado": 0},
     {"nome": "Napolitana", "valor_extra": 25.90, "esgotado": 0},
     {"nome": "Paulista", "valor_extra": 32.90, "esgotado": 0},
     {"nome": "Portuguesa", "valor_extra": 35.90, "esgotado": 0},
     {"nome": "3 Queijos", "valor_extra": 30.90, "esgotado": 0},
     {"nome": "4 Queijos", "valor_extra": 34.90, "esgotado": 0},
     {"nome": "5 Queijos", "valor_extra": 38.90, "esgotado": 0},
     {"nome": "Queijo Coalho", "valor_extra": 38.90, "esgotado": 0},
     {"nome": "Atum", "valor_extra": 31.90, "esgotado": 0},
     {"nome": "Caipira", "valor_extra": 32.90, "esgotado": 0},
     {"nome": "Carne Seca", "valor_extra": 33.90, "esgotado": 0},
     {"nome": "Lombo", "valor_extra": 31.90, "esgotado": 0},
     {"nome": "Romana", "valor_extra": 34.90, "esgotado": 0},
     {"nome": "Abobrinha", "valor_extra": 27.90, "esgotado": 0},
     {"nome": "Rucula", "valor_extra": 28.90, "esgotado": 0},
     {"nome": "Vegana", "valor_extra": 24.90, "esgotado": 0},
     {"nome": "Brocolis", "valor_extra": 30.90, "esgotado": 0},
     {"nome": "Alho Poro", "valor_extra": 34.90, "esgotado": 0},
     {"nome": "A Moda", "valor_extra": 37.90, "esgotado": 0},
     {"nome": "Camarao", "valor_extra": 34.90, "esgotado": 0},
     {"nome": "Italiana", "valor_extra": 25.90, "esgotado": 0},
     {"nome": "Jardineira", "valor_extra": 30.90, "esgotado": 0},
     {"nome": "Pepperoni", "valor_extra": 30.90, "esgotado": 0},
     {"nome": "Santista", "valor_extra": 45.90, "esgotado": 0},
     {"nome": "Shimeji", "valor_extra": 33.90, "esgotado": 0},
     {"nome": "Brigadeiro", "valor_extra": 21.90, "esgotado": 0},
     {"nome": "Casadinha", "valor_extra": 21.90, "esgotado": 0},
     {"nome": "Banana Nevada", "valor_extra": 24.90, "esgotado": 0},
     {"nome": "Pistache com Nutella", "valor_extra": 25.90, "esgotado": 0}
   ],
   "max_selected": 2, "obrigatorio": 2
  }
]''',
'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'},

{'item':'1/2 grande','preco':0,'categoria_id':3,'opcoes':'''[
  {"nome": "Sabor", "ids": "",
   "options": [
     {"nome": "Alho", "valor_extra": 38.90, "esgotado": 0},
     {"nome": "Calabresa", "valor_extra": 34.90, "esgotado": 0},
     {"nome": "Frango com Catupiry", "valor_extra": 49.90, "esgotado": 0},
     {"nome": "Marguerita", "valor_extra": 37.90, "esgotado": 0},
     {"nome": "Mussarela", "valor_extra": 36.90, "esgotado": 0},
     {"nome": "Napolitana", "valor_extra": 39.90, "esgotado": 0},
     {"nome": "Paulista", "valor_extra": 49.90, "esgotado": 0},
     {"nome": "Portuguesa", "valor_extra": 54.90, "esgotado": 0},
     {"nome": "3 Queijos", "valor_extra": 45.90, "esgotado": 0},
     {"nome": "4 Queijos", "valor_extra": 52.90, "esgotado": 0},
     {"nome": "5 Queijos", "valor_extra": 58.90, "esgotado": 0},
     {"nome": "Queijo Coalho", "valor_extra": 58.90, "esgotado": 0},
     {"nome": "Atum", "valor_extra": 48.90, "esgotado": 0},
     {"nome": "Caipira", "valor_extra": 49.90, "esgotado": 0},
     {"nome": "Carne Seca", "valor_extra": 51.90, "esgotado": 0},
     {"nome": "Lombo", "valor_extra": 48.90, "esgotado": 0},
     {"nome": "Romana", "valor_extra": 52.90, "esgotado": 0},
     {"nome": "Abobrinha", "valor_extra": 42.90, "esgotado": 0},
     {"nome": "Rucula", "valor_extra": 43.90, "esgotado": 0},
     {"nome": "Vegana", "valor_extra": 36.90, "esgotado": 0},
     {"nome": "Brocolis", "valor_extra": 45.90, "esgotado": 0},
     {"nome": "Alho Poro", "valor_extra": 52.90, "esgotado": 0},
     {"nome": "A Moda", "valor_extra": 57.90, "esgotado": 0},
     {"nome": "Camarao", "valor_extra": 53.90, "esgotado": 0},
     {"nome": "Italiana", "valor_extra": 39.90, "esgotado": 0},
     {"nome": "Jardineira", "valor_extra": 46.90, "esgotado": 0},
     {"nome": "Pepperoni", "valor_extra": 46.90, "esgotado": 0},
     {"nome": "Santista", "valor_extra": 69.90, "esgotado": 0},
     {"nome": "Shimeji", "valor_extra": 51.90, "esgotado": 0},
     {"nome": "Brigadeiro", "valor_extra": 31.90, "esgotado": 0},
     {"nome": "Casadinha", "valor_extra": 33.90, "esgotado": 0},
     {"nome": "Banana Nevada", "valor_extra": 37.90, "esgotado": 0},
     {"nome": "Pistache com Nutella", "valor_extra": 39.90, "esgotado": 0}
   ],
   "max_selected": 2, "obrigatorio": 2
  }
]''',
'instrucoes': None, 'image': None, 'preco_base':0,'usable_on_qr':None,'carrinho':'SlicePizza'}

]

db.execute("BEGIN")
try:
    for d in dados:
        params = [
            d["item"].strip(),
            float(d.get("preco", 0) or 0),
            int(d.get("categoria_id", 0) or 0),
            d.get("opcoes"),                 # <- string, vai como está
            d.get("instrucoes"),
            d.get("image"),
            float(d.get("preco_base", 0) or 0),
            1 if d.get("usable_on_qr") is None else int(bool(d.get("usable_on_qr"))),
            d.get("subcategoria"),
            d.get("subsubcategoria"),
            d.get("carrinho"),
        ]
        db.execute(insert_sql, *params)

    db.execute("COMMIT")
    print("[DONE] Inserção concluída.")
except Exception as e:
    db.execute("ROLLBACK")

    raise

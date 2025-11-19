# -*- coding: utf-8 -*-
from cs50 import SQL
import shutil
import os
from datetime import datetime

# caminhos do banco
DB_PATH = "sqlite:///data/dados.db"
RAW_PATH = "data/dados.db"

# 1. backup rápido antes de mexer
if os.path.exists(RAW_PATH): 
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"data/dados.backup.{ts}.db"
    shutil.copyfile(RAW_PATH, backup_path)
    print(f"[OK] Backup criado em {backup_path}")

db = SQL(DB_PATH)
insert_sql = """
INSERT INTO cardapio
(item,preco,categoria_id,opcoes,instrucoes,image,preco_base,usable_on_qr,subcategoria,subsubcategoria,carrinho)
VALUES (?,?,?,?,?,?,?,?,?,?,?)
"""
# ----------------------------
# Itens simples do cardápio
# ----------------------------
# categoria_id = 1  -> produtos simples
# subcategoria  -> grupo grande (Bebidas)
# subsubcategoria -> tipo (Água, Refrigerante, Cerveja)

db.execute("INSERT INTO usuarios (username,senha,carrinho, cargo, liberado) VALUES (?,?,?,?,?)", 'teste_summer', 'senha123', 'SummerDrinks', 'Dono', 1)

dados = [
    #-----------BEBIDAS SIMPLES---------------(CATEGORIA_ID = 1)
    {'item': 'agua','preco': 5.00,'categoria_id': 1,
     'instrucoes': None, 'image': None, 'preco_base': 5.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks'},

    {'item': 'agua com gas','preco': 6.00,'categoria_id': 1,
     'instrucoes': None, 'image': None, 'preco_base': 6.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks'},

    {'item': 'coca cola','preco': 7.00,'categoria_id': 1,
     'instrucoes': None, 'image': None, 'preco_base': 7.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks'},

    {'item': 'coca cola zero','preco': 7.00,'categoria_id': 1,
     'instrucoes': None, 'image': None, 'preco_base': 7.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks'},

    {'item': 'guarana','preco': 7.00,'categoria_id': 1,
     'instrucoes': None, 'image': None, 'preco_base': 7.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks'},

    {'item': 'skol','preco': 7.00,'categoria_id': 1,
     'instrucoes': None, 'image': None, 'preco_base': 7.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks'},

    {'item': 'brahma duplo malte','preco': 8.00,'categoria_id': 1,
     'instrucoes': None, 'image': None, 'preco_base': 8.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks'},

    {'item': 'heineken','preco': 10.00,'categoria_id': 1,
     'instrucoes': None, 'image': None, 'preco_base': 10.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks'},
 
     #-----------DRINKS E BATIDAS---------------(CATEGORIA_ID = 2)
    {'item': 'suco natural', 'preco': 15.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 15.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Sabor", "ids": "","options": [{"nome": "Morango", "valor_extra": 0, "esgotado": 0},
     {"nome": "Limao", "valor_extra": 0, "esgotado": 0},{"nome": "Maracuja", "valor_extra": 0, "esgotado": 0},
     {"nome": "Abacaxi", "valor_extra": 0, "esgotado": 0},{"nome": "Abacaxi com hortela", "valor_extra": 0, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}]'''},

    {'item': 'caipirinha c/ velho barreiro', 'preco': 20.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 20.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[
     {"nome": "Frutas", "ids": "","options": [{"nome": "Limao", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Maracuja", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Morango", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Abacaxi", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Kiwi", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
     {"nome": "Frutas extras","ids": "","options": [{"nome": "Limao","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Maracuja","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Morango","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Abacaxi","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Kiwi","valor_extra": 3.00,"esgotado": 0}
     ],"max_selected": 2,"obrigatorio": 0}
     ]'''},
    {'item': 'caipirinha c/ smirnof', 'preco': 25.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 25.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[
     {"nome": "Frutas", "ids": "","options": [{"nome": "Limao", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Maracuja", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Morango", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Abacaxi", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Kiwi", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
     {"nome": "Frutas extras","ids": "","options": [{"nome": "Limao","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Maracuja","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Morango","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Abacaxi","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Kiwi","valor_extra": 3.00,"esgotado": 0}
     ],"max_selected": 2,"obrigatorio": 0}
     ]'''},

    {'item': 'batida com velho barreiro', 'preco': 20.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 20.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[
     {"nome": "Frutas", "ids": "","options": [{"nome": "Limao", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Maracuja", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Morango", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Abacaxi", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Kiwi", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
     {"nome": "Frutas extras","ids": "","options": [{"nome": "Limao","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Maracuja","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Morango","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Abacaxi","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Kiwi","valor_extra": 3.00,"esgotado": 0}
     ],"max_selected": 2,"obrigatorio": 0}
     ]'''},
    {'item': 'batida com smirnoff', 'preco': 25.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 25.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[
     {"nome": "Frutas", "ids": "","options": [{"nome": "Limao", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Maracuja", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Morango", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Abacaxi", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Kiwi", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
     {"nome": "Frutas extras","ids": "","options": [{"nome": "Limao","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Maracuja","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Morango","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Abacaxi","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Kiwi","valor_extra": 3.00,"esgotado": 0}
     ],"max_selected": 2,"obrigatorio": 0}
     ]'''},
    {'item': 'saquerita', 'preco': 25.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 25.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[
     {"nome": "Frutas", "ids": "","options": [{"nome": "Limao", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Maracuja", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Morango", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Abacaxi", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Kiwi", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
     {"nome": "Frutas extras","ids": "","options": [{"nome": "Limao","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Maracuja","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Morango","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Abacaxi","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Kiwi","valor_extra": 3.00,"esgotado": 0}
     ],"max_selected": 2,"obrigatorio": 0}
     ]'''},
    {'item': 'espanhola', 'preco': 25.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 25.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[
     {"nome": "Frutas", "ids": "","options": [{"nome": "Limao", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Maracuja", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Morango", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Abacaxi", "valor_extra": 0.00, "esgotado": 0},
        {"nome": "Kiwi", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
     {"nome": "Frutas extras","ids": "","options": [{"nome": "Limao","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Maracuja","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Morango","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Abacaxi","valor_extra": 3.00,"esgotado": 0},
        {"nome": "Kiwi","valor_extra": 3.00,"esgotado": 0}
     ],"max_selected": 2,"obrigatorio": 0}
     ]'''},
    {'item': 'baicara', 'preco': 30.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 30.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [{"nome": "Cachaca", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Vodka", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Saque", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},
    {'item': 'mangacuja', 'preco': 30.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 30.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [{"nome": "Cachaca", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Vodka", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Saque", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},
    {'item': 'brisa tropical', 'preco': 30.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 30.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [{"nome": "Cachaca", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Vodka", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Saque", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},
    {'item': 'kiwi fresh', 'preco': 30.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 30.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [{"nome": "Cachaca", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Vodka", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Saque", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},
    {'item': 'doce mare', 'preco': 30.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 30.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [{"nome": "Cachaca", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Vodka", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Saque", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},
    {'item': 'brisa de frutas vermelhas', 'preco': 30.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 30.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [{"nome": "Cachaca", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Vodka", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Saque", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},
    {'item': 'juruloka', 'preco': 30.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 30.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [{"nome": "Cachaca", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Vodka", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Saque", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},
    {'item': 'tropical de coco', 'preco': 30.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 30.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [{"nome": "Cachaca", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Vodka", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Saque", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},
    {'item': 'jurumar', 'preco': 30.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 30.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [{"nome": "Cachaca", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Vodka", "valor_extra": 0.00, "esgotado": 0},
     {"nome": "Saque", "valor_extra": 0.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},
    {'item': 'sex on the beach', 'preco': 00.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [
     {"nome": "Vodka", "valor_extra": 30.00, "esgotado": 0},
     {"nome": "Gin", "valor_extra": 35.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},
    {'item': 'aperol tropical', 'preco': 00.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [
     {"nome": "Vodka", "valor_extra": 30.00, "esgotado": 0},
     {"nome": "Gin", "valor_extra": 35.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},
    {'item': 'festa na praia', 'preco': 00.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [
     {"nome": "Vodka", "valor_extra": 30.00, "esgotado": 0},
     {"nome": "Gin", "valor_extra": 35.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},
    {'item': 'berry beach', 'preco': 00.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [
     {"nome": "Vodka", "valor_extra": 30.00, "esgotado": 0},
     {"nome": "Gin", "valor_extra": 35.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},
    {'item': 'onda de kiwi', 'preco': 00.00, 'categoria_id': 2,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Destilados", "ids": "","options": [
     {"nome": "Vodka", "valor_extra": 30.00, "esgotado": 0},
     {"nome": "Gin", "valor_extra": 35.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1}
     ]'''},

    #-----------PORCOES---------------(CATEGORIA_ID = 3)
    {'item': 'fritas', 'preco': 00.00, 'categoria_id': 3,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Tamanhos", "ids": "","options": [
     {"nome": "P(300g)", "valor_extra": 44.00, "esgotado": 0},
     {"nome": "M(500g)", "valor_extra": 65.00, "esgotado": 0},
     {"nome": "G(1kg)", "valor_extra": 119.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
     {"nome": "Adicionais", "ids": "","options": [
     {"nome": "Cheddar + Bacon", "valor_extra": 23.00, "esgotado": 0},
     {"nome": "Cebola empanada", "valor_extra": 20.00, "esgotado": 0}
     ],"max_selected": 2, "obrigatorio": 0}
     ]'''},
    {'item': 'calabresa acebolada', 'preco': 00.00, 'categoria_id': 3,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Tamanhos", "ids": "","options": [
     {"nome": "P(300g)", "valor_extra": 58.00, "esgotado": 0},
     {"nome": "M(500g)", "valor_extra": 86.00, "esgotado": 0},
     {"nome": "G(1kg)", "valor_extra": 138.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
     {"nome": "Adicionais", "ids": "","options": [
     {"nome": "Cheddar + Bacon", "valor_extra": 23.00, "esgotado": 0},
     {"nome": "Cebola empanada", "valor_extra": 20.00, "esgotado": 0}
     ],"max_selected": 2, "obrigatorio": 0}
     ]'''},
    {'item': 'frango', 'preco': 00.00, 'categoria_id': 3,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Tamanhos", "ids": "","options": [
     {"nome": "P(300g)", "valor_extra": 65.00, "esgotado": 0},
     {"nome": "M(500g)", "valor_extra": 98.00, "esgotado": 0},
     {"nome": "G(1kg)", "valor_extra": 187.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
    {"nome": "Adicionais", "ids": "","options": [
     {"nome": "Cheddar + Bacon", "valor_extra": 23.00, "esgotado": 0},
     {"nome": "Cebola empanada", "valor_extra": 20.00, "esgotado": 0}
     ],"max_selected": 2, "obrigatorio": 0}
     ]'''},
    {'item': 'isca de peixe', 'preco': 00.00, 'categoria_id': 3,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Tamanhos", "ids": "","options": [
     {"nome": "P(300g)", "valor_extra": 72.00, "esgotado": 0},
     {"nome": "M(500g)", "valor_extra": 112.00, "esgotado": 0},
     {"nome": "G(1kg)", "valor_extra": 213.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
    {"nome": "Adicionais", "ids": "","options": [
     {"nome": "Cheddar + Bacon", "valor_extra": 23.00, "esgotado": 0},
     {"nome": "Cebola empanada", "valor_extra": 20.00, "esgotado": 0}
     ],"max_selected": 2, "obrigatorio": 0}
     ]'''},
    {'item': 'porquinho', 'preco': 00.00, 'categoria_id': 3,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Tamanhos", "ids": "","options": [
     {"nome": "P(300g)", "valor_extra": 72.00, "esgotado": 0},
     {"nome": "M(500g)", "valor_extra": 112.00, "esgotado": 0},
     {"nome": "G(1kg)", "valor_extra": 213.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
     {"nome": "Adicionais", "ids": "","options": [
     {"nome": "Cheddar + Bacon", "valor_extra": 23.00, "esgotado": 0},
     {"nome": "Cebola empanada", "valor_extra": 20.00, "esgotado": 0}
     ],"max_selected": 2, "obrigatorio": 0}
     ]'''},
    {'item': 'isca de contra acebolado', 'preco': 00.00, 'categoria_id': 3,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Tamanhos", "ids": "","options": [
     {"nome": "P(300g)", "valor_extra": 78.00, "esgotado": 0},
     {"nome": "M(500g)", "valor_extra": 129.00, "esgotado": 0},
     {"nome": "G(1kg)", "valor_extra": 241.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
    {"nome": "Adicionais", "ids": "","options": [
     {"nome": "Cheddar + Bacon", "valor_extra": 23.00, "esgotado": 0},
     {"nome": "Cebola empanada", "valor_extra": 20.00, "esgotado": 0}
     ],"max_selected": 2, "obrigatorio": 0}
     ]'''},
    {'item': 'camarao', 'preco': 00.00, 'categoria_id': 3,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Tamanhos", "ids": "","options": [
     {"nome": "P(300g)", "valor_extra": 86.00, "esgotado": 0},
     {"nome": "M(500g)", "valor_extra": 133.00, "esgotado": 0},
     {"nome": "G(1kg)", "valor_extra": 255.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
    {"nome": "Adicionais", "ids": "","options": [
     {"nome": "Cheddar + Bacon", "valor_extra": 23.00, "esgotado": 0},
     {"nome": "Cebola empanada", "valor_extra": 20.00, "esgotado": 0}
     ],"max_selected": 2, "obrigatorio": 0}
     ]'''},
    {'item': 'lula', 'preco': 00.00, 'categoria_id': 3,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[{"nome": "Tamanhos", "ids": "","options": [
     {"nome": "P(300g)", "valor_extra": 87.00, "esgotado": 0},
     {"nome": "M(500g)", "valor_extra": 135.00, "esgotado": 0},
     {"nome": "G(1kg)", "valor_extra": 259.00, "esgotado": 0}
     ],"max_selected": 1, "obrigatorio": 1},
    {"nome": "Adicionais", "ids": "","options": [
     {"nome": "Cheddar + Bacon", "valor_extra": 23.00, "esgotado": 0},
     {"nome": "Cebola empanada", "valor_extra": 20.00, "esgotado": 0}
     ],"max_selected": 2, "obrigatorio": 0}
     ]'''},

     #-----------PORCOES MISTAS(1kg)---------------(CATEGORIA_ID = 3)
    {'item': 'mista de 1kg(500g cada)', 'preco': 00.00, 'categoria_id': 3,
     'instrucoes': None,'image': None,'preco_base': 00.00,
     'usable_on_qr': None,'carrinho': 'SummerDrinks',
     'opcoes': '''[
     {"nome": "Sabores", "ids": "",
     "options": [
     {"nome": "Fritas + calabresa", "valor_extra": 133.00, "esgotado": 0},
     {"nome": "Fritas + frango", "valor_extra": 147.00, "esgotado": 0},
    {"nome": "Fritas + peixe", "valor_extra": 159.00, "esgotado": 0},
    {"nome": "Calabresa + frango", "valor_extra": 166.00, "esgotado": 0},
    {"nome": "Calabresa + peixe", "valor_extra": 180.00, "esgotado": 0},
    {"nome": "Fritas + camarao", "valor_extra": 180.00, "esgotado": 0},
    {"nome": "Fritas + carne", "valor_extra": 180.00, "esgotado": 0},
    {"nome": "Fritas + lula", "valor_extra": 184.00, "esgotado": 0},
    {"nome": "Calabresa + carne", "valor_extra": 201.00, "esgotado": 0},
    {"nome": "Camarao + peixe", "valor_extra": 227.00, "esgotado": 0},
    {"nome": "Lula + peixe", "valor_extra": 230.00, "esgotado": 0},
    {"nome": "Camarao + lula", "valor_extra": 236.00, "esgotado": 0}
     ],
     "max_selected": 1, 
     "obrigatorio": 1
     },
    {"nome": "Adicionais", "ids": "","options": [
     {"nome": "Cheddar + Bacon", "valor_extra": 23.00, "esgotado": 0},
     {"nome": "Cebola empanada", "valor_extra": 20.00, "esgotado": 0}
     ],"max_selected": 2, "obrigatorio": 0}
     ]'''},

    #-----------PORCOES MISTAS(900g(300g cada))---------------(CATEGORIA_ID = 3)
    {'item': 'mista de 900g(300g cada)', 'preco': 0.00, 'categoria_id': 3,
    'instrucoes': None,'image': None,'preco_base': 0.00,
    'usable_on_qr': None,'carrinho': 'SummerDrinks',
    'opcoes': '''[
    {"nome": "Sabores","ids": "",
    "options": [
      {"nome": "Fritas + contra + calabresa", "valor_extra": 166.00, "esgotado": 0},
      {"nome": "Fritas + peixe + frango", "valor_extra": 166.00, "esgotado": 0},
      {"nome": "Fritas + camarao + frango", "valor_extra": 180.00, "esgotado": 0},
      {"nome": "Fritas + frango + lula", "valor_extra": 184.00, "esgotado": 0},
      {"nome": "Fritas + camarao + peixe", "valor_extra": 187.00, "esgotado": 0},
      {"nome": "Fritas + peixe + lula", "valor_extra": 190.00, "esgotado": 0},
      {"nome": "Fritas + camarao + lula", "valor_extra": 196.00, "esgotado": 0},
      {"nome": "Camarao + frango + peixe", "valor_extra": 201.00, "esgotado": 0},
      {"nome": "Camarao + frango + lula", "valor_extra": 206.00, "esgotado": 0},
      {"nome": "Camarao + lula + peixe", "valor_extra": 213.00, "esgotado": 0}
    ],
    "max_selected": 1,
    "obrigatorio": 1
  },
  {
    "nome": "Adicionais",
    "ids": "",
    "options": [
      {"nome": "Cheddar + Bacon", "valor_extra": 23.00, "esgotado": 0},
      {"nome": "Cebola empanada", "valor_extra": 20.00, "esgotado": 0}
    ],
    "max_selected": 2,
    "obrigatorio": 0
  }
]'''
    },

    #----------PORCOES MISTAS(1,5kg(500g cada))---------------(CATEGORIA_ID = 3)
    {'item': 'mista de 1,5kg(500g cada)', 'preco': 0.00, 'categoria_id': 3,
    'instrucoes': None,'image': None,'preco_base': 0.00,
    'usable_on_qr': None,'carrinho': 'SummerDrinks',
    'opcoes': '''[{"nome": "Sabores","ids": "",
    "options": [
      {"nome": "Fritas + contra + calabresa", "valor_extra": 272.00, "esgotado": 0},
      {"nome": "Fritas + peixe + frango", "valor_extra": 272.00, "esgotado": 0},
      {"nome": "Fritas + camarao + frango", "valor_extra": 281.00, "esgotado": 0},
      {"nome": "Fritas + frango + lula", "valor_extra": 282.00, "esgotado": 0},
      {"nome": "Fritas + camarao + peixe", "valor_extra": 295.00, "esgotado": 0},
      {"nome": "Fritas + peixe + lula", "valor_extra": 299.00, "esgotado": 0},
      {"nome": "Fritas + camarao + lula", "valor_extra": 309.00, "esgotado": 0},
      {"nome": "Camarao + frango + peixe", "valor_extra": 334.00, "esgotado": 0},
      {"nome": "Camarao + frango + lula", "valor_extra": 335.00, "esgotado": 0},
      {"nome": "Camarao + lula + peixe", "valor_extra": 356.00, "esgotado": 0}
    ],
    "max_selected": 1,
    "obrigatorio": 1
  },
  {"nome": "Adicionais","ids": "",
    "options": [
      {"nome": "Cheddar + Bacon", "valor_extra": 23.00, "esgotado": 0},
      {"nome": "Cebola empanada", "valor_extra": 20.00, "esgotado": 0}
    ],
    "max_selected": 2,
    "obrigatorio": 0
  }
]'''
    },

    #----------PORCOES MISTAS(1,2kg(300g cada))---------------(CATEGORIA_ID = 3)
    {'item': 'mista de 1,2kg(300g cada)', 'preco': 0.00, 'categoria_id': 3,
    'instrucoes': None,'image': None,'preco_base': 0.00,
    'usable_on_qr': None,'carrinho': 'SummerDrinks',
    'opcoes': '''[{"nome": "Sabores","ids": "",
    "options": [
      {"nome": "Fritas + camarao + frango + peixe", "valor_extra": 248.00, "esgotado": 0},
      {"nome": "Fritas + frango + lula + peixe", "valor_extra": 253.00, "esgotado": 0},
      {"nome": "Fritas + camarao + frango + lula", "valor_extra": 253.00, "esgotado": 0},
      {"nome": "Fritas + camarao + lula + peixe", "valor_extra": 260.00, "esgotado": 0},
      {"nome": "Camarao + frango + lula + peixe", "valor_extra": 281.00, "esgotado": 0}
    ],
    "max_selected": 1,
    "obrigatorio": 1
  },
  {"nome": "Adicionais","ids": "",
    "options": [
      {"nome": "Cheddar + Bacon", "valor_extra": 23.00, "esgotado": 0},
      {"nome": "Cebola empanada", "valor_extra": 20.00, "esgotado": 0}
    ],
    "max_selected": 2,
    "obrigatorio": 0
  }
]'''
    },
    
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
    raise
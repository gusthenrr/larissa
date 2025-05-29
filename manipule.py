from cs50 import SQL
from datetime import datetime
from pytz import timezone

db = SQL('sqlite:///data/dados.db')
brazil = timezone('America/Sao_Paulo')


dia = datetime.now(brazil).date()
print(db.execute("SELECT * FROM itens"))
print(db.execute("SELECT * FROM pedidos"))


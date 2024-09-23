from flask import Flask, render_template, request, redirect, url_for 
import sqlite3
from datetime import datetime, timedelta
app = Flask(__name__)


def conectar_banco():
    return sqlite3.connect('sistema_vendas.db')


def inicializar_banco():
    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        data_de_registro DATE NOT NULL,
        proxima_data_pagamento DATE NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        preco REAL NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER,
        id_produto INTEGER,
        quantidade INTEGER,
        data_pedido DATE NOT NULL,
        FOREIGN KEY(id_cliente) REFERENCES clientes(id),
        FOREIGN KEY(id_produto) REFERENCES produtos(id)
    )
    ''')

    conexao.commit()
    conexao.close()

@app.route('/')
def index():
    conexao = conectar_banco()
    cursor = conexao.cursor()

 
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

  
    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

   
    valor_devido = {}
    extratos = {}

    for cliente in clientes:
        cliente_id = cliente[0]

        
        cursor.execute('''
            SELECT SUM(p.preco * pe.quantidade) 
            FROM pedidos pe
            JOIN produtos p ON pe.id_produto = p.id
            WHERE pe.id_cliente = ?
        ''', (cliente_id,))
        valor = cursor.fetchone()[0]
        valor_devido[cliente_id] = valor if valor is not None else 0

        
        cursor.execute('''
            SELECT p.preco * pe.quantidade, pe.data_pedido
            FROM pedidos pe
            JOIN produtos p ON pe.id_produto = p.id
            WHERE pe.id_cliente = ?
            ORDER BY pe.data_pedido
        ''', (cliente_id,))
        extratos[cliente_id] = cursor.fetchall()

   
    clientes_com_valor = [(c[0], c[1], valor_devido.get(c[0], 0), extratos.get(c[0], [])) for c in clientes]

    conexao.close()
    return render_template('index.html', clientes=clientes_com_valor, produtos=produtos)



@app.route('/adicionar_cliente', methods=['POST'])
def adicionar_cliente():
    nome_cliente = request.form['nome']
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    proxima_data_pagamento = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')  # 14 dias a partir de hoje
    
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO clientes (nome, data_de_registro, proxima_data_pagamento) VALUES (?, ?, ?)", 
                   (nome_cliente, data_hoje, proxima_data_pagamento))
    conexao.commit()
    conexao.close()

    return redirect(url_for('index'))


@app.route('/adicionar_produto', methods=['POST'])
def adicionar_produto():
    nome_produto = request.form['nome_produto']
    preco_produto = float(request.form['preco_produto'])
    
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome_produto, preco_produto))
    conexao.commit()
    conexao.close()

    return redirect(url_for('index'))



@app.route('/registrar_pedido', methods=['POST'])
def registrar_pedido():
    id_cliente = request.form['id_cliente']
    id_produto = request.form.getlist('id_produto[]')  
    quantidade = request.form.getlist('quantidade[]')  
    
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    
    conexao = conectar_banco()
    cursor = conexao.cursor()
    
   
    if len(id_produto) != len(quantidade):
        return "Erro: O número de produtos e quantidades não correspondem.", 400
    
    for i in range(len(id_produto)):
        cursor.execute("INSERT INTO pedidos (id_cliente, id_produto, quantidade, data_pedido) VALUES (?, ?, ?, ?)", 
                       (id_cliente, id_produto[i], quantidade[i], data_hoje))
    
    conexao.commit()
    conexao.close()
    
    return redirect(url_for('index'))


@app.route('/excluir_cliente/<int:id_cliente>', methods=['POST'])
def excluir_cliente(id_cliente):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (id_cliente,))
    conexao.commit()
    conexao.close()
    return redirect(url_for('clientes'))



@app.route('/excluir_produto/<int:id_produto>', methods=['POST'])
def excluir_produto(id_produto):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (id_produto,))
    conexao.commit()
    conexao.close()
    return redirect(url_for('produtos'))

@app.route('/excluir_valor_devido/<int:id_cliente>', methods=['POST'])
def excluir_valor_devido(id_cliente):
    conexao = conectar_banco()
    cursor = conexao.cursor()

    cursor.execute("DELETE FROM pedidos WHERE id_cliente = ?", (id_cliente,))
    
    conexao.commit()
    conexao.close()

    return redirect(url_for('valor_devido'))

@app.route('/clientes')
def clientes():
    conexao = conectar_banco()
    cursor = conexao.cursor()
        
    search = request.args.get('search', '')

    if search:
        
        cursor.execute("SELECT * FROM clientes WHERE nome LIKE ?", ('%' + search + '%',))
    else:
        cursor.execute("SELECT * FROM clientes")

    clientes = cursor.fetchall()
    conexao.close()
    return render_template('clientes.html', clientes=clientes)

@app.route('/produtos')
def produtos():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    search = request.args.get('search', '')

    if search:
        
        cursor.execute("SELECT * FROM produtos WHERE nome LIKE ?", ('%' + search + '%',))
    else:
        cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()
    conexao.close()
    return render_template('produtos.html', produtos=produtos)

@app.route('/valor_devido', methods=['GET'])
def valor_devido():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    search = request.args.get('search', '')

    if search:
    
        cursor.execute("SELECT * FROM clientes WHERE nome LIKE ?", ('%' + search + '%',))
    else:
        cursor.execute("SELECT * FROM clientes")

    clientes = cursor.fetchall()

    valor_devido = {}
    extratos = {}

    for cliente in clientes:
        cliente_id = cliente[0]
    
        cursor.execute('''
            SELECT SUM(p.preco * pe.quantidade)
            FROM pedidos pe
            JOIN produtos p ON pe.id_produto = p.id
            WHERE pe.id_cliente = ?
        ''', (cliente_id,))
        valor = cursor.fetchone()[0]
        valor_devido[cliente_id] = valor if valor is not None else 0

        cursor.execute('''
            SELECT GROUP_CONCAT(p.nome, ', '), SUM(p.preco * pe.quantidade), 
                   pe.data_pedido, date(pe.data_pedido, '+14 days') as data_vencimento
            FROM pedidos pe
            JOIN produtos p ON pe.id_produto = p.id
            WHERE pe.id_cliente = ?
            GROUP BY pe.data_pedido
            ORDER BY pe.data_pedido
        ''', (cliente_id,))
        extratos[cliente_id] = cursor.fetchall()

    clientes_com_valor = [(c[0], c[1], valor_devido.get(c[0], 0), extratos.get(c[0], [])) for c in clientes]

    conexao.close()
    return render_template('valor_devido.html', clientes=clientes_com_valor)



if __name__ == '__main__':
    inicializar_banco()
    app.run(debug=True)  
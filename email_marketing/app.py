from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import csv

# Configuração inicial
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 📦 Configuração do Banco de Dados
# Usando variável de ambiente DATABASE_URL (para PostgreSQL no Render)
# ou SQLite local como padrão
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///email_marketing.db'
)

# ⚠️ Correção do prefixo caso Render gere postgres://
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace(
        'postgres://', 'postgresql://', 1
    )

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 🎯 Modelos do Banco de Dados
class EmailList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)

class SendData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campanha = db.Column(db.String(100))
    abertos = db.Column(db.Integer)
    clicados = db.Column(db.Integer)

class Excluded(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)

# 🚩 Página Inicial
@app.route('/')
def index():
    return render_template('index.html')

# 🚩 Página Lista de Clientes
@app.route('/lista-clientes', methods=['GET', 'POST'])
def lista_clientes():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # Limpa a tabela antes de adicionar os novos
            EmailList.query.delete()
            db.session.commit()

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            with open(filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    novo = EmailList(nome=row['Nome'], email=row['Email'])
                    db.session.add(novo)
                db.session.commit()

            os.remove(filepath)
            return redirect(url_for('lista_clientes'))

    emails = EmailList.query.all()
    return render_template('lista_clientes.html', emails=emails)

# 🚩 Página E-mails Excluídos
@app.route('/excluidos')
def excluidos():
    emails = Excluded.query.all()
    return render_template('excluidos.html', emails=emails)

@app.route('/download-excluidos')
def download_excluidos():
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'excluidos.csv')
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Nome', 'Email']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for email in Excluded.query.all():
            writer.writerow({'Nome': email.nome, 'Email': email.email})
    return send_file(filepath, as_attachment=True)

# 🚩 Página Dados dos Envios
@app.route('/dados-envios')
def dados_envios():
    dados = SendData.query.all()
    return render_template('dados_envios.html', dados=dados)

# 🚩 Página Enviar Campanha
@app.route('/enviar-campanha', methods=['GET', 'POST'])
def enviar_campanha():
    if request.method == 'POST':
        campanha = request.form['campanha']
        assunto = request.form['assunto']
        remetente_nome = request.form['remetente_nome']
        remetente_email = request.form['remetente_email']
        conteudo = request.form['conteudo']

        emails = EmailList.query.all()
        abertos = 0
        clicados = 0

        for email in emails:
            # Aqui pode ser integrado o envio real via SMTP
            print(f"Enviando para: {email.email}")
            print(f"Assunto: {assunto}")
            print(f"De: {remetente_nome} <{remetente_email}>")
            print(f"Conteúdo: {conteudo}")

        registro = SendData(campanha=campanha, abertos=abertos, clicados=clicados)
        db.session.add(registro)
        db.session.commit()

        return redirect(url_for('dados_envios'))

    return render_template('enviar_campanha.html')

# 🚩 Cancelar Subscrição
@app.route('/cancelar/<email>')
def cancelar(email):
    cliente = EmailList.query.filter_by(email=email).first()
    if cliente:
        excluido = Excluded(nome=cliente.nome, email=cliente.email)
        db.session.add(excluido)
        db.session.delete(cliente)
        db.session.commit()
    return "Seu e-mail foi removido com sucesso."

# 🚀 Inicialização
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas se não existirem
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    if __name__ == '__main__':
    app.run(debug=True)




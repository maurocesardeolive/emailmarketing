import os
from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import csv

# Configuração da aplicação Flask
app = Flask(__name__, instance_relative_config=True)

# Caminho para o banco de dados dentro da pasta instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'email_marketing.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'uploads')

# Garante que as pastas existam
os.makedirs(app.instance_path, exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializa o banco de dados
db = SQLAlchemy(app)

# Modelos (Tabelas)
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

# ---------------------------
# Rotas da aplicação
# ---------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lista-clientes', methods=['GET', 'POST'])
def lista_clientes():
    if request.method == 'POST':
        file = request.files['file']
        if file:
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

@app.route('/excluidos')
def excluidos():
    emails = Excluded.query.all()
    return render_template('emails_excluidos.html', emails=emails)

@app.route('/download-excluidos')
def download_excluidos():
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'excluidos.csv')
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Nome', 'Email'])
        for email in Excluded.query.all():
            writer.writerow([email.nome, email.email])
    return send_file(filepath, as_attachment=True)

@app.route('/dados-envios')
def dados_envios():
    dados = SendData.query.all()
    return render_template('dados_envios.html', dados=dados)

@app.route('/enviar-campanha', methods=['GET', 'POST'])
def enviar_campanha():
    if request.method == 'POST':
        campanha = request.form['campanha']
        assunto = request.form['assunto']
        remetente_nome = request.form['remetente_nome']
        remetente_email = request.form['remetente_email']
        conteudo = request.form['conteudo']

        emails = EmailList.query.all()

        for email in emails:
            print(f"Enviando para: {email.email}")
            print(f"Assunto: {assunto}")
            print(f"De: {remetente_nome} <{remetente_email}>")
            print(f"Conteúdo: {conteudo}")

        registro = SendData(campanha=campanha, abertos=0, clicados=0)
        db.session.add(registro)
        db.session.commit()

        return redirect(url_for('dados_envios'))

    return render_template('enviar_campanha.html')

@app.route('/cancelar/<email>')
def cancelar(email):
    cliente = EmailList.query.filter_by(email=email).first()
    if cliente:
        excluido = Excluded(nome=cliente.nome, email=cliente.email)
        db.session.add(excluido)
        db.session.delete(cliente)
        db.session.commit()
    return "Seu e-mail foi removido com sucesso."

# ---------------------------

if __name__ == '__main__':
    app.run(debug=True)

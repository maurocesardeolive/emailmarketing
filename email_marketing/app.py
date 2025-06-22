from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import csv
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///email_marketing.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)

# Banco de dados
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

# Página Inicial
@app.route('/')
def index():
    return render_template('index.html')

# Página Lista de Clientes
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
            with open(filepath, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    novo = EmailList(nome=row['Nome'], email=row['Email'])
                    db.session.add(novo)
                db.session.commit()
            os.remove(filepath)
            return redirect(url_for('lista_clientes'))
    emails = EmailList.query.all()
    return render_template('lista_clientes.html', emails=emails)

# Página E-mails Excluídos
@app.route('/excluidos')
def excluidos():
    emails = Excluded.query.all()
    return render_template('excluidos.html', emails=emails)

@app.route('/download-excluidos')
def download_excluidos():
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'excluidos.csv')
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = ['Nome', 'Email']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for email in Excluded.query.all():
            writer.writerow({'Nome': email.nome, 'Email': email.email})
    return send_file(filepath, as_attachment=True)

# Página Dados dos Envios
@app.route('/dados-envios')
def dados_envios():
    dados = SendData.query.all()
    return render_template('dados_envios.html', dados=dados)

# Página Enviar Campanhas (Simples)
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
            # Simulação de envio de e-mail (implementar SMTP real)
            print(f"Enviando para: {email.email}")
            print(f"Assunto: {assunto}")
            print(f"De: {remetente_nome} <{remetente_email}>")
            print(f"Conteúdo: {conteudo}")

        registro = SendData(campanha=campanha, abertos=abertos, clicados=clicados)
        db.session.add(registro)
        db.session.commit()

        return redirect(url_for('dados_envios'))

    return render_template('enviar_campanha.html')

# Cancelar Subscrição
@app.route('/cancelar/<email>')
def cancelar(email):
    cliente = EmailList.query.filter_by(email=email).first()
    if cliente:
        excluido = Excluded(nome=cliente.nome, email=cliente.email)
        db.session.add(excluido)
        db.session.delete(cliente)
        db.session.commit()
    return "Seu e-mail foi removido com sucesso."

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db.create_all()
    app.run(debug=True)
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def enviar_email(destinatario, assunto, conteudo, remetente_nome, remetente_email, senha):
    msg = MIMEMultipart()
    msg['From'] = f"{remetente_nome} <{remetente_email}>"
    msg['To'] = destinatario
    msg['Subject'] = assunto

    msg.attach(MIMEText(conteudo, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(remetente_email, senha)
            servidor.send_message(msg)
            print(f'E-mail enviado para {destinatario}')
    except Exception as e:
        print(f'Erro ao enviar para {destinatario}: {e}')
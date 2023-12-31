from flask import Flask
from flask import render_template
from flask_mysqldb import MySQL
from flask import request
from flask import session
from dotenv import load_dotenv
import os
import openai
import uuid
import ast
import json

#
#app.config['MYSQL_HOST'] = 'tws_bd.mysql.dbaas.com.br'
#app.config['MYSQL_USER'] = 'tws_bd'
#app.config['MYSQL_PASSWORD'] = os.getenv('PI_DB_PASSWORD')
#app.config['MYSQL_DB'] = 'tws_bd'

load_dotenv()
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'curric1.mysql.pythonanywhere-services.com'
app.config['MYSQL_USER'] = 'curric1'
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD_PW')
app.config['MYSQL_DB'] = 'curric1$default'
mysql = MySQL(app)
openai.api_key = os.getenv('OPENIA_KEY')
app.secret_key = str(uuid.uuid4())


###### Funções de operação
def openai_chat_completion(prompt, temperature):
    response = openai.Completion.create(model="gpt-3.5-turbo-instruct",
                                        prompt=prompt,
                                        max_tokens=1000,
                                        temperature=temperature)
    reponse_text = response["choices"][0]["text"]
    return reponse_text


####### Funções de GET ou POST
@app.route("/")
def index_html():
    return render_template("index.html")


@app.route("/form-html")
def form_html():
    return render_template("cv_form.html")


@app.route("/blog")
def blog():
    query_skus = f'''SELECT id, title, image FROM pi_blog ORDER BY datecreated DESC'''
    cur = mysql.connection.cursor()
    cur.execute(query_skus)
    data = cur.fetchall()
    cur.close()
    return render_template("blog_itens.html", data=data)


@app.route("/publi")
def publi():
    id = request.args.get('id')
    query_skus = f'''SELECT title, content, author, image, datecreated FROM pi_blog WHERE ID = {id}'''
    cur = mysql.connection.cursor()
    cur.execute(query_skus)
    data = cur.fetchone()
    cur.close()
    return render_template("publi.html", data=data)


@app.route('/get-recommendations', methods=['POST'])
def get_recoommendations():
    # Armazenando as variaveis do formulário na sessão
    session['nome'] = request.form.get('nome').title()
    session['idade'] = request.form.get('age')
    session['email'] = request.form.get('email')
    session['telefone'] = request.form.get('telefone')
    session['escolaridade'] = request.form.get('escolaridade')
    session['institution'] = request.form.get('institution')
    session['qualidades'] = request.form.get('mensagem')

    # abre o arquivo com o prompt e substitui as variaveis
    # necessidade block try except por bug no pythoanywhere
    try:
        prompt = open(f'prompts/get_qualifications.txt', encoding='utf-8').read()
    except:
        prompt = open(f'pi2/prompts/get_qualifications.txt', encoding='utf-8').read()

    prompt = prompt.format(qualidades=session.get('qualidades'))

    # faz requisção pegando possíveis qualificações profissionais
    qualifications = openai_chat_completion(prompt=prompt,
                                            temperature=0)

    return render_template('get_reccommedations.html',
                           qualifications=ast.literal_eval(qualifications))


@app.route('/cvmaker', methods=['POST'])
def cv_maker():
    # Pega as variáveis da sessão para montar o cv e criar o segundo prompt cv_maker
    nome = str(session.get('nome')).title()
    idade = session.get('idade')
    email = session.get('email')
    telefone = session.get('telefone')
    escolaridade = session.get('escolaridade')
    institution = session.get('institution')
    qualidades = session.get('mensagem')

    # pega apenas as competencias selecionadas e transforma em uma string separado por virgula
    competencias_selecionadas = request.form.getlist('competencias')
    competencias_string = ', '.join(competencias_selecionadas)

    # abre o arquivo com o prompt e substitui as variaveis
    # necessidade block try except por bug no pythoanywhere
    try:
        prompt = open(f'prompts/cv_maker.txt', encoding='utf-8').read()
    except:
        prompt = open(f'pi2/prompts/cv_maker.txt', encoding='utf-8').read()

    prompt = prompt.format(nome=nome,
                           idade=idade,
                           escolaridade=escolaridade,
                           qualidades=qualidades,
                           competencias_string=competencias_string)

    # É solicitado no prompt acima que o modelo retorne os dados em um JSON
    # Dessa forma podemos criar dois conteúdos em um único prompt
    # Neste caso estamos criando o campo RESUMO e OBJETIVOS
    json_string = openai_chat_completion(prompt=prompt, temperature=0.5)
    json_data = json.loads(json_string)

    return render_template('cv_model.html',
                           nome=nome,
                           idade=idade,
                           email=email,
                           telefone=telefone,
                           escolaridade=escolaridade,
                           institution=institution,
                           resume=json_data['resumo'],
                           goals=json_data['objetivos'],
                           competencias=competencias_string)


if __name__ == "__main__":
    app.run(debug=True)

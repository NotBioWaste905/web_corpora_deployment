from search import Searcher
s = Searcher()
from flask import Flask
from flask import url_for, render_template, request, redirect
from flask_bootstrap import Bootstrap
app = Flask(__name__)
bootstrap = Bootstrap(app)

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == "POST":
        query_ = request.form["query"]

        if query_ == '':
            return render_template('base.html', title="Reviews")

        return redirect(url_for(f'results', query=query_))
    return render_template('base.html', title="Reviews")

@app.route('/request=<query>', methods=['POST', 'GET'])
def results(query=None):
    if request.method == "POST":
        query_ = request.form["query"]
        return redirect(url_for(f'results', query=query_))
    res = s.search(query)
    return render_template('base.html', title="Reviews", result=res, query=query)

@app.route('/texts=<id>', methods=['POST', 'GET'])
def texts(id=None):
    return render_template('text.html', meta=s.get_meta(int(id)))

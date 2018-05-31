from flask import Flask
from flask_graphql import GraphQLView
from schema import Schema

view_func = GraphQLView.as_view('graphql', schema=Schema, graphiql=True)

app = Flask(__name__)
app.add_url_rule('/', view_func=view_func)

if __name__ == '__main__':
    app.run()
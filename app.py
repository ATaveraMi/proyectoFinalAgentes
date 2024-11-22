from flask import Flask
from models import IntersectionModel

app = Flask(__name__)
model = IntersectionModel()

@app.route("/")
def index():
    pass


@app.route("/positions")
def positions():
    model.step()
    return ({ "x": 1, "y": 2 })


@app.route("/semaphores")
def semaphores():
    pass
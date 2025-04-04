from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    user_text = request.form.get("user_input")
    return f"You entered: {user_text}"

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, jsonify
from similarity import path_similarity, autocomplete_words


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        w1 = request.form["word1"]
        w2 = request.form["word2"]

        sim = path_similarity(w1, w2)

        if not sim:
            result = {"error": f"No path found between '{w1}' and '{w2}'."}
        else:
            result = sim

    return render_template("index.html", result=result)

@app.route("/autocomplete")
def autocomplete():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    suggestions = autocomplete_words(q)
    return jsonify(suggestions)



if __name__ == "__main__":
    app.run(debug=True)

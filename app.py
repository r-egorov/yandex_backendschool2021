from flask import Flask, request, jsonify
from serializers import CourierSerializer

app = Flask(__name__)


@app.route('/')
def index():
    return "Hello World!"


@app.route("/couriers", methods=["POST"])
def import_couriers():
    content = request.get_json()
    if content.get("data") is None:
        return jsonify({"validation_error": "no data key"}), 400
    serializer = CourierSerializer(content["data"])
    if serializer.is_valid():
        serializer.save()
        return jsonify(serializer.response()), 201
    return jsonify(serializer.response()), 400



if __name__ == "__main__":
    app.run(host="127.0.0.1", port="8000", debug=True)
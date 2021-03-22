from flask import Flask, request, jsonify
from serializers import CourierSerializer, OrderSerializer

app = Flask(__name__)


@app.route('/')
def index():
    return "Hello World!"


@app.route("/couriers", methods=["POST"])
def import_couriers():
    content = request.get_json()
    if content.get("data") is None:
        return jsonify({"validation_error": "no data key"}), 400
    serializer = CourierSerializer(content["data"], many=True)
    if serializer.is_valid():
        serializer.save()
        return jsonify(serializer.import_response()), 201
    return jsonify(serializer.import_response()), 400


@app.route("/couriers/<int:courier_id>", methods=["PATCH"])
def patch_courier(courier_id):
    content = request.get_json()
    serializer = CourierSerializer(content)
    serializer.patch_courier(courier_id)
    response = serializer.patch_response(courier_id)
    if serializer.invalid:
        return jsonify(response), 400
    return jsonify(response), 200


@app.route("/orders", methods=["POST"])
def import_orders():
    content = request.get_json()
    if content.get("data") is None:
        return jsonify({"validation_error": "no data key"}), 400
    serializer = OrderSerializer(content["data"], many=True)
    if serializer.is_valid():
        serializer.save()
        return jsonify(serializer.import_response()), 201
    return jsonify(serializer.import_response()), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port="8000", debug=True)

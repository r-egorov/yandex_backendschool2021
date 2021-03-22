from flask import Flask, request, jsonify
from serializers import CourierSerializer, OrderSerializer
from datetime import time
import re

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


def create_time(hours_list):
    time_list = []
    for timestr in hours_list:
        time_search = re.search("^(\d{2}:\d{2})-(\d{2}:\d{2})$", timestr)
        start = time_search.group(1)
        end = time_search.group(2)
        time_list.append((start, end))
    print(time_list)


@app.route("/orders/assign", methods=["POST"])
def assign_orders():
    content = request.get_json()
    order_serializer = OrderSerializer(content, many=True)
    order_serializer.get_orders()

    courier = CourierSerializer.get_courier(content["courier_id"])
    working_hours = time.fromisoformat("09:00")
    for order in order_serializer.valid:
        print("DH", order.delivery_hours)
        create_time(order.delivery_hours)

    return "GOOD", 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port="8000", debug=True)

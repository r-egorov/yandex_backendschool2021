from flask import Flask, request, jsonify
from serializers import CourierSerializer,\
    OrderSerializer, TimePeriod, OrderHandler


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


def assignable(order, courier):
    working_hours = [TimePeriod(timestr) for timestr in courier.working_hours]
    courier.working_hours = working_hours
    delivery_time_list = [
        TimePeriod(timestr) for timestr in order.delivery_hours
    ]
    order.delivery_hours = delivery_time_list
    for delivery_period in order.delivery_hours:
        if delivery_period in courier.working_hours:
            return True


@app.route("/couriers/<int:courier_id>", methods=["PATCH"])
def patch_courier(courier_id):
    content = request.get_json()
    courier_serializer = CourierSerializer(content)
    courier_serializer.patch_courier(courier_id)
    response = courier_serializer.patch_response(courier_id)
    if courier_serializer.invalid:
        return jsonify(response), 400

    order_serializer = OrderSerializer(many=True)
    order_serializer.get_assigned_orders(courier_id)

    courier = courier_serializer.get_courier(courier_id)
    courier.hours_to_periods()

    invalid_orders = []
    for order in order_serializer.valid:
        order.hours_to_periods()
        if order.weight > courier.lift_capacity or \
                order.region not in courier.regions or \
                not order.assignable(courier):
            invalid_orders.append(order)

    if invalid_orders:
        dismisser = OrderHandler(courier, orders_to_dismiss=invalid_orders)
        dismisser.dismiss_orders()

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


@app.route("/orders/assign", methods=["POST"])
def assign_orders():
    content = request.get_json()
    order_serializer = OrderSerializer(content, many=True)
    order_serializer.get_free_orders()
    courier = CourierSerializer.get_courier(content["courier_id"])
    if courier is None:
        response = {"error": "No courier with such id"}
        return jsonify(response), 400

    courier.hours_to_periods()

    orders_to_assign = []
    for order in order_serializer.valid:
        order.hours_to_periods()
        if order.weight <= courier.lift_capacity:
            if order.region in courier.regions:
                if order.assignable(courier):
                    orders_to_assign.append(order)

    assigner = OrderHandler(courier, orders_to_assign=orders_to_assign)
    assigner.assign_orders()
    response = assigner.response()
    return jsonify(response), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port="8000", debug=True)

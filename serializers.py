import json
import db
import re

from abc import ABC, abstractmethod
from datetime import time, datetime


class Courier:
    def __init__(self, data):
        self.id = data.get("courier_id")
        if self.id is None:
            self.id = data.get("id")
        self.type = data.get("courier_type")
        self.regions = data.get("regions")
        self.working_hours = data.get("working_hours")
        self.rating = 0.0
        self.earning = 0

    @property
    def lift_capacity(self):
        if self.type == "foot":
            return 10
        elif self.type == "bike":
            return 15
        else:
            return 50

    def hours_to_periods(self):
        working_hours = [TimePeriod(timestr) for timestr in self.working_hours]
        self.working_hours = working_hours


class Order:
    def __init__(self, data):
        self.id = data.get("order_id")
        if self.id is None:
            self.id = data.get("id")
        self.weight = data.get("weight")
        self.region = data.get("region")
        self.delivery_hours = data.get("delivery_hours")
        self.assigned = data.get("assigned")
        self.completed = data.get("completed")

    def hours_to_periods(self):
        delivery_hours = [TimePeriod(timestr) for timestr in self.delivery_hours]
        self.delivery_hours = delivery_hours

    def assignable(self, courier):
        for delivery_period in self.delivery_hours:
            if delivery_period in courier.working_hours:
                return True


class TimePeriod:
    def __init__(self, timestr):
        time_search = re.search(r"^(\d{2}:\d{2})-(\d{2}:\d{2})$", timestr)
        self.start = time.fromisoformat(time_search.group(1))
        self.end = time.fromisoformat(time_search.group(2))

    def __repr__(self):
        return str(self.start) + " - " + str(self.end)

    def __eq__(self, other):
        return self.start < other.end and self.end > other.start


class OrderHandler:
    def __init__(self, courier, orders_to_assign=None, orders_to_dismiss=None):
        self.courier = courier
        self.to_assign = orders_to_assign
        self.to_dismiss = orders_to_dismiss
        self.timestamp = datetime.now()

    def assign_orders(self):
        timestamp = datetime.strftime(self.timestamp, "%Y-%m-%d %H:%M:%S")
        db.assign_orders(self.courier.id, self.to_assign, timestamp)

    def dismiss_orders(self):
        db.dismiss_orders(self.to_dismiss)

    def response(self):
        orders_response = [{"id": order.id} for order in self.to_assign]
        if orders_response:
            timestamp = self.timestamp.isoformat()[:-4] + "Z"
            response = {
                "orders": orders_response,
                "assign_time": timestamp
            }
        else:
            response = {
                "orders": orders_response
            }
        return response


class AbstractSerializer(ABC):
    def __init__(self, data=None, many=False):
        self.data = data
        self.many = many
        self.valid = []
        self.invalid = []

    def no_duplicates(self, existing_elements):
        i = 0
        while i < len(self.valid):
            order = self.valid[i]
            if order.id in existing_elements:
                self.valid.remove(order)
                i -= 1
                self.invalid.append(order.id)
            i += 1
        if self.invalid:
            return False
        return True

    @staticmethod
    def validate_hours(working_hours):
        if not working_hours:
            return None
        for period in working_hours:
            if not re.match(r"^\d{2}:\d{2}-\d{2}:\d{2}$", period):
                return None
        return working_hours

    @abstractmethod
    def is_valid(self):
        self.to_internal_value()
        pass

    @abstractmethod
    def to_internal_value(self):
        pass

    @abstractmethod
    def import_response(self):
        pass

    @abstractmethod
    def save(self):
        pass


class CourierSerializer(AbstractSerializer):
    """
    A class used to serialize data received in JSON-format
    """

    def make_courier(self, data=None):
        courier_id = data.get("courier_id")
        courier_type = self.validate_type(data.get("courier_type"))
        regions = self.validate_regions(data.get("regions"))
        working_hours = self.validate_hours(data.get("working_hours"))
        if not courier_id or \
                not courier_type or \
                not regions or \
                not working_hours:
            self.invalid.append(courier_id)
        else:
            courier = Courier(data)
            self.valid.append(courier)

    def to_internal_value(self):
        if self.many:
            for element in self.data:
                self.make_courier(element)
        else:
            self.make_courier(self.data)

    @staticmethod
    def validate_type(courier_type):
        if not courier_type:
            return None
        if courier_type in ("foot", "bike", "auto"):
            return courier_type
        return courier_type

    @staticmethod
    def validate_regions(regions):
        if not regions:
            return None
        for region in regions:
            if not isinstance(region, int):
                return None
        return regions

    def import_response(self):
        couriers_dict = {"couriers": []}
        if self.invalid:
            for courier_id in self.invalid:
                couriers_dict["couriers"].append({"id": courier_id})
            return {"validation_error": couriers_dict}
        for courier in self.valid:
            couriers_dict["couriers"].append({"id": courier.id})
        return couriers_dict

    def is_valid(self):
        self.to_internal_value()
        existing_couriers = db.get_ids("couriers")
        return self.no_duplicates(existing_couriers)

    def patch_courier(self, courier_id):
        existing_couriers = db.get_ids("couriers")
        if courier_id not in existing_couriers:
            self.invalid.append(courier_id)
            return
        for key in list(self.data):
            if key == "regions":
                self.data[key] = self.validate_regions(self.data[key])
                if self.data[key] is not None:
                    self.data["regions"] = json.dumps(self.data["regions"])
            elif key == "working_hours":
                self.data[key] = self.validate_hours(self.data[key])
                if self.data[key] is not None:
                    self.data["working_hours"] = json.dumps(self.data["working_hours"])
            elif key == "courier_type":
                self.data["type"] = self.validate_type(self.data.pop(key))
                key = "type"
            else:
                self.invalid.append(courier_id)
                return
            if not self.data[key]:
                self.invalid.append(courier_id)
                return
        db.update("couriers", courier_id, self.data)

    def patch_response(self, courier_id):
        if self.invalid:
            return {"patch_error": {"couriers": [{"id": courier_id}]}}
        courier_row = db.get_id("couriers", courier_id)
        response = {
            "courier_id": courier_row[0],
            "courier_type": courier_row[1],
            "regions": json.loads(courier_row[2]),
            "working_hours": json.loads(courier_row[3])
        }
        return response

    def save(self):
        to_save = [("id", "type", "regions", "working_hours")]
        for courier in self.valid:
            to_save.append((
                courier.id,
                courier.type,
                json.dumps(courier.regions),
                json.dumps(courier.working_hours),
            ))
        db.insert_many("couriers", to_save)

    @staticmethod
    def get_courier(courier_id):
        courier_row = db.get_id("couriers", courier_id)
        if courier_row is None:
            return None
        data = {
            "courier_id": courier_row[0],
            "courier_type": courier_row[1],
            "regions": json.loads(courier_row[2]),
            "working_hours": json.loads(courier_row[3])
        }
        return Courier(data)


class OrderSerializer(AbstractSerializer):
    def __init__(self, data=None, many=False):
        super().__init__(data, many)

    @staticmethod
    def validate_weight(weight):
        if not weight or weight < 0.01 or weight > 50:
            return None
        return weight

    def make_order(self, data):
        order_id = data.get("order_id")
        if order_id is None:
            order_id = data.get("id")
        weight = self.validate_weight(data.get("weight"))
        region = data.get("region")
        delivery_hours = self.validate_hours(data.get("delivery_hours"))
        if not order_id or \
                not weight or \
                not region or \
                not delivery_hours:
            self.invalid.append(order_id)
        else:
            order = Order(data)
            self.valid.append(order)

    def to_internal_value(self):
        if self.many:
            for element in self.data:
                self.make_order(element)
        else:
            self.make_order(self.data)

    def is_valid(self):
        self.to_internal_value()
        existing_orders = db.get_ids("orders")
        return self.no_duplicates(existing_orders)

    def import_response(self):
        orders_dict = {"orders": []}
        if self.invalid:
            for order_id in self.invalid:
                orders_dict["orders"].append({"id": order_id})
            return {"validation_error": orders_dict}
        for order in self.valid:
            orders_dict["orders"].append({"id": order.id})
        return orders_dict

    def get_orders(self):
        self.data = db.get_all(
            "orders", [
                "id",
                "weight",
                "region",
                "delivery_hours",
                "assigned",
                "completed"
            ]
        )
        for order in self.data:
            order["delivery_hours"] = json.loads(order["delivery_hours"])
        self.to_internal_value()

    def get_free_orders(self):
        self.data = db.get_free_orders()
        for order in self.data:
            order["delivery_hours"] = json.loads(order["delivery_hours"])
        self.to_internal_value()

    def get_assigned_orders(self, courier_id):
        self.data = db.get_assigned_orders(courier_id)
        for order in self.data:
            order["delivery_hours"] = json.loads(order["delivery_hours"])
        self.to_internal_value()

    def save(self):
        to_save = [("id", "weight", "region", "delivery_hours")]
        for order in self.valid:
            to_save.append((
                order.id,
                order.weight,
                order.region,
                json.dumps(order.delivery_hours),
            ))
        db.insert_many("orders", to_save)

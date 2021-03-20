import json
import db
import re


class Courier:
    def __init__(self, data):
        self.id = data["courier_id"]
        self.type = data["courier_type"]
        self.regions = data["regions"]
        self.working_hours = data["working_hours"]
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


class CourierSerializer:
    """
    A class used to serialize data received in JSON-format
    """

    def __init__(self, data):
        self.couriers = []
        self.invalid = []
        self.data = data

    def to_internal_value(self):
        for element in self.data:
            courier_id = element.get("courier_id")
            courier_type = self.validate_type(element.get("courier_type"))
            regions = self.validate_regions(element.get("regions"))
            working_hours = self.validate_hours(element.get("working_hours"))
            if not courier_id or \
                    not courier_type or \
                    not regions or \
                    not working_hours:
                self.invalid.append(courier_id)
            else:
                courier = Courier(element)
                self.couriers.append(courier)

    @staticmethod
    def validate_hours(working_hours):
        if working_hours is None:
            return None
        for period in working_hours:
            if not re.match(r"^\d{2}:\d{2}-\d{2}:\d{2}$", period):
                return None
        return working_hours

    @staticmethod
    def validate_type(courier_type):
        if courier_type is None:
            return None
        if courier_type in ("foot", "bike", "auto"):
            return courier_type
        return courier_type

    @staticmethod
    def validate_regions(regions):
        if regions is None:
            return None
        for region in regions:
            if not isinstance(region, int):
                return None
        return regions

    def response(self):
        couriers_dict = {"couriers": []}
        if self.invalid:
            for courier_id in self.invalid:
                couriers_dict["couriers"].append({"id": courier_id})
            return {"validation_error": couriers_dict}
        for courier in self.couriers:
            couriers_dict["couriers"].append({"id": courier.id})
        return couriers_dict

    def is_valid(self):
        self.to_internal_value()
        existing_couriers = db.get_courier_ids()
        i = 0
        while i < len(self.couriers):
            courier = self.couriers[i]
            if courier.id in existing_couriers:
                self.couriers.remove(courier)
                i -= 1
                self.invalid.append(courier.id)
            i += 1
        if self.invalid:
            return False
        return True

    def save(self):
        to_save = [("id", "type", "regions", "working_hours")]
        for courier in self.couriers:
            to_save.append((
                courier.id,
                courier.type,
                json.dumps(courier.regions),
                json.dumps(courier.working_hours),
            ))
        db.insert_many("couriers", to_save)

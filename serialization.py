from marshmallow import Schema, fields, ValidationError, RAISE, post_load
from datetime import date


class CitizenSchema(Schema):
    citizen_id = fields.Integer(required=True)
    town = fields.String(required=True)
    street = fields.String(required=True)
    building = fields.String(required=True)
    apartment = fields.Integer(required=True)
    name = fields.String(required=True)
    birth_date = fields.DateTime("%d.%m.%Y", required=True, validate=lambda x: x.date() < date.today())
    gender = fields.String(required=True, validate=lambda x: (x == 'male') or (x == 'female'))
    relatives = fields.List(fields.Integer, required=True)

    class Meta:
        strict = True
        unknown = RAISE
        ordered = True


class CitizenSchemaPatch(Schema):
    town = fields.String()
    street = fields.String()
    building = fields.String()
    apartment = fields.Integer()
    name = fields.String()
    birth_date = fields.DateTime("%d.%m.%Y", validate=lambda x: x.date() < date.today())
    gender = fields.String(validate=lambda x: (x == 'male') or (x == 'female'))
    relatives = fields.List(fields.Integer)

    class Meta:
        strict = True
        unknown = RAISE
        ordered = True


class Serializer:

    def deserialize_citizens(self, citizens):
        schema = CitizenSchema(many=True)
        result = self.list_to_dict(schema.loads(citizens))
        self._validate_relatives(result)
        return result

    def deserialize_patch_data(self, data):
        schema = CitizenSchemaPatch()
        result = schema.loads(data)
        if "relatives" in result:
            if len(set(result["relatives"])) != len(result["relatives"]):
                raise ValidationError("Error in relatives")
        return result

    def list_to_dict(self, data):
        result = dict()
        for elem in data:
            if elem["citizen_id"] in result:
                raise ValidationError("citizen_id is not unique")
            else:
                result[elem["citizen_id"]] = elem
        return result

    def _validate_relatives(self, data):
        for citizen in data:
            for relative in data[citizen]["relatives"]:
                if citizen not in data[relative]["relatives"]:
                    raise ValidationError("relatives are not consistent")


if __name__ == '__main__':
    serializer = Serializer()
    serializer.deserialize_citizens()

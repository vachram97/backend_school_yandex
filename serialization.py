from marshmallow import Schema, fields, ValidationError, RAISE


class CitizenSchema(Schema):
    citizen_id = fields.Integer(required=True)
    town = fields.String(required=True)
    street = fields.String(required=True)
    building = fields.String(required=True)
    appartement = fields.Integer(required=True)
    name = fields.String(required=True)
    birth_date = fields.DateTime("%d.%m.%Y", required=True)
    gender = fields.String(required=True, validate=lambda x: (x == 'male') or (x == 'female'))
    relatives = fields.List(fields.Integer, required=True)

    class Meta:
        strict = True
        unknown = RAISE


class Serializer:

    def serialize_citizens(self, citizens):
        schema = CitizenSchema(many=True)
        result = schema.loads(citizens)
        return result


if __name__ == '__main__':
    serializer = Serializer()
    serializer.serialize_citizens()

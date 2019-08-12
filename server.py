from aiohttp import web
import serialization
import citizen_db
from marshmallow import ValidationError
from MySQLdb import ProgrammingError
import keyring

MYSQL_TABLE_NOT_EXIST = '(1146'


async def post_import(request):
    ser = serialization.Serializer()
    try:
        import_id = db.get_next_id()
        db.fill_import("import_" + str(import_id), ser.deserialize_citizens(await request.text()))
    except ValidationError as e:
        return web.json_response({"error": e.messages}, status=400)
    return web.json_response({"data": {"import_id": import_id}}, status=201)


async def patch_info(request):
    ser = serialization.Serializer()
    try:
        result = db.patch_user_data(request.match_info["import_id"], request.match_info["citizen_id"],
                                    ser.deserialize_patch_data(await request.text()))
    except ValidationError as e:
        return web.json_response({"error": e.messages}, status=400)
    except ProgrammingError as e:
        if str(e).startswith(MYSQL_TABLE_NOT_EXIST):
            return web.json_response({"error": "import_id doesn't exist"}, status=400)
        else:
            raise
    except Exception:
        return web.json_response({"error": "import_id doesn't exist"}, status=418)
    return web.json_response({"data": result}, status=200)


async def get_info(request):
    try:
        result = db.get_info(request.match_info['import_id'])
    except ProgrammingError as e:
        if str(e).startswith(MYSQL_TABLE_NOT_EXIST):
            return web.json_response({"error": "import_id doesn't exist"}, status=400)
    return web.json_response({"data": result}, status=200)


async def get_birthdays(request):
    try:
        result = db.get_birthdays_info(request.match_info['import_id'])
    except ProgrammingError as e:
        if str(e).startswith(MYSQL_TABLE_NOT_EXIST):
            return web.json_response({"error": "import_id doesn't exist"}, status=400)
    return web.json_response({"data": result}, status=200)


async def get_statistics(request):
    try:
        result = db.get_statistics(request.match_info['import_id'])
    except ProgrammingError as e:
        if str(e).startswith(MYSQL_TABLE_NOT_EXIST):
            return web.json_response({"error": "import_id doesn't exist"}, status=400)
    return web.json_response({"data": result}, status=200)


if __name__ == "__main__":
    app = web.Application(client_max_size=1024**3)
    user = "root"
    passwd = keyring.get_password("system", user)
    db = citizen_db.CitizenDB(user, passwd, "citizens")
    app.add_routes([web.post(r'/imports', post_import),
                    web.patch(r'/imports/{import_id:\d+}/citizens/{citizen_id:\d+}', patch_info),
                    web.get(r'/imports/{import_id:\d+}/citizens', get_info),
                    web.get(r'/imports/{import_id:\d+}/citizens/birthdays', get_birthdays),
                    web.get(r'/imports/{import_id:\d+}/citizens/towns/stat/percentile/age', get_statistics)
                    ])

    web.run_app(app)

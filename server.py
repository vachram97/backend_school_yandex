from aiohttp import web
import serialization
import citizen_db


async def post_import(request):
    ser = serialization.Serializer()
    print(ser.serialize_citizens(await request.text()))
    return web.Response(status=418)


async def patch_info(request):
    print('got patch')
    return web.Response(status=418)


async def get_info(request):
    print('got get info')
    return web.Response(status=418)


async def get_birthdays(request):
    print('got get birth')
    return web.Response(status=418)


async def get_statistics(request):
    print('got get stats')
    return web.Response(status=418)


app = web.Application()
app.add_routes([web.post(r'/imports', post_import),
                web.patch(r'/imports/{import_id:\d+}/citizens/{citizen_id:\d+}', patch_info),
                web.get(r'/imports/{import_id:\d+}/citizens/', get_info),
                web.get(r'/imports/{import_id:\d+}/citizens/birthdays', get_birthdays),
                web.get(r'/imports/{import_id:\d+}/citizens/towns/stat/percentile/age', get_statistics)
                ])

web.run_app(app)

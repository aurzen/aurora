import aiohttp.web
routes = aiohttp.web.RouteTableDef()

@routes.post("/")
async def register_shortlink(request : aiohttp.web.Request):

    pass

app = aiohttp.web.Application()
app.add_routes(routes)
aiohttp.web.run_app(app)




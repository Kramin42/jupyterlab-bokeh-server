from tornado import web
import sys
import time

from custom_bokeh_server import get_server_custom

print('Loading Bokeh Dashboards...')

routes = {
}

from os.path import dirname, basename, isfile, join
import glob
import importlib.util
dashboard_modules = glob.glob(join('dashboards', '*.py'))
for file_path in dashboard_modules:
    file_name = basename(file_path)
    module_name = file_name.replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    routes['/'+module_name] = module.main
#from dashboards import temperature


class RouteIndex(web.RequestHandler):
    """ A JSON index of all routes present on the Bokeh Server """

    def get(self):
        self.write({route: route.strip("/").replace('_',' ').title() for route in routes})


if __name__ == "__main__":
    from tornado.ioloop import IOLoop
    server = get_server_custom(routes, port=int(sys.argv[1]), websocket_origin="*")
    server.start()

    server._tornado.add_handlers(
        r".*", [(server.prefix + "/" + "index.json", RouteIndex, {})]
    )

    IOLoop.current().start()

from tornado import web
import sys
import time
from tornado.ioloop import IOLoop

from custom_bokeh_server import get_server_custom

print('Loading Bokeh Dashboards...')

routes = {
}

import sys
sys.path.append('/home/xilinx/pylib')
from os.path import dirname, basename, isfile, join
import glob
import importlib.util

def load_dashboards():
    routes = {}
    dashboard_modules = glob.glob(join('dashboards', '*.py'))
    for file_path in dashboard_modules:
        file_name = basename(file_path)
        module_name = file_name.replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        routes['/'+module_name] = module.main
    return routes



class RouteIndex(web.RequestHandler):
    """ A JSON index of all routes present on the Bokeh Server """

    def get(self):
        self.write({route: route.strip("/").replace('_',' ') for route in routes})

class ReloadDashboards(web.RequestHandler):
    """ Trigger dashboards to reload"""
    
    def get(self):
        global g_restart_on_exit
        g_restart_on_exit = True
        ioloop = IOLoop.current()
        ioloop.current().add_callback(ioloop.stop)
        self.write({'status': 'success'})


if __name__ == "__main__":
    g_restart_on_exit = True
    while g_restart_on_exit:
        g_restart_on_exit = False
        routes = load_dashboards()
        server = get_server_custom(routes, port=int(sys.argv[1]), websocket_origin="*")
        server.start()

        server._tornado.add_handlers(
            r".*", [
                (server.prefix + "/" + "index.json", RouteIndex, {}),
                (server.prefix + "/" + "reload", ReloadDashboards, {})
            ]
        )

        IOLoop.current().start()
        server.stop()

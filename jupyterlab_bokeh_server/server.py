from bokeh.server.server import Server
from bokeh.plotting import figure, ColumnDataSource
from tornado import web

import random
import sys
import time

import numpy as np

import threading
from functools import partial
from tornado import gen
from microspec_api import system_api

import signal
import uuid
from functools import partial
from types import FunctionType

from bokeh.server.server import Server
from panel.io import state
from panel.io.server import INDEX_HTML

def _eval_panel(panel, server_id, title, doc):
    from panel.template import Template
    from panel.pane import panel as as_panel

    if isinstance(panel, Template):
        return panel._modify_doc(server_id, title, doc)
    elif isinstance(panel, FunctionType):
        panel = panel(doc)
    return as_panel(panel)._modify_doc(server_id, title, doc)

def get_server_custom(panel, port=0, websocket_origin=None, loop=None,
                      show=False, start=False, title=None, verbose=False, **kwargs):
    """
    Returns a Server instance with this panel attached as the root
    app.
    Arguments
    ---------
    panel: Viewable, function or {str: Viewable}
      A Panel object, a function returning a Panel object or a
      dictionary mapping from the URL slug to either.
    port: int (optional, default=0)
      Allows specifying a specific port
    websocket_origin: str or list(str) (optional)
      A list of hosts that can connect to the websocket.
      This is typically required when embedding a server app in
      an external web site.
      If None, "localhost" is used.
    loop : tornado.ioloop.IOLoop (optional, default=IOLoop.current())
      The tornado IOLoop to run the Server on
    show : boolean (optional, default=False)
      Whether to open the server in a new browser tab on start
    start : boolean(optional, default=False)
      Whether to start the Server
    title: str (optional, default=None)
      An HTML title for the application
    verbose: boolean (optional, default=False)
      Whether to report the address and port
    kwargs: dict
      Additional keyword arguments to pass to Server instance
    Returns
    -------
    server : bokeh.server.server.Server
      Bokeh Server instance running this panel
    """
    from tornado.ioloop import IOLoop

    server_id = kwargs.pop('server_id', uuid.uuid4().hex)
    if isinstance(panel, dict):
        apps = {slug if slug.startswith('/') else '/'+slug:
                partial(_eval_panel, p, server_id, title)
                for slug, p in panel.items()}
    else:
        apps = {'/': partial(_eval_panel, panel, server_id, title)}

    opts = dict(kwargs)
    if loop:
        loop.make_current()
        opts['io_loop'] = loop
    else:
        opts['io_loop'] = IOLoop.current()

    if 'index' not in opts:
        opts['index'] = INDEX_HTML

    if websocket_origin:
        if not isinstance(websocket_origin, list):
            websocket_origin = [websocket_origin]
        opts['allow_websocket_origin'] = websocket_origin

    server = Server(apps, port=port, **opts)
    if verbose:
        address = server.address or 'localhost'
        print("Launching server at http://%s:%s" % (address, server.port))

    state._servers[server_id] = (server, panel, [])

    if show:
        def show_callback():
            server.show('/')
        server.io_loop.add_callback(show_callback)

    def sig_exit(*args, **kwargs):
        server.io_loop.add_callback_from_signal(do_stop)

    def do_stop(*args, **kwargs):
        server.io_loop.stop()

    try:
        signal.signal(signal.SIGINT, sig_exit)
    except ValueError:
        pass # Can't use signal on a thread

    if start:
        server.start()
        try:
            server.io_loop.start()
        except RuntimeError:
            pass
    return server

routes = {
}

import sys
sys.path.append('/home/xilinx/dashlib')
from os.path import dirname, basename, isfile, join
import glob
import importlib.util
dashboard_modules = glob.glob(join('/home/xilinx/dashboards', '*.py'))
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

import {
  ILabShell,
  ILayoutRestorer,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { WidgetTracker, ICommandPalette } from '@jupyterlab/apputils';

import { BokehDashboard, BokehDashboardLauncher, IDashboardItem } from './dashboard';

import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

import '../style/index.css';

const LAUNCH_COMMAND_ID = 'bokeh-server:launch-document';
const RELOAD_COMMAND_ID = 'bokeh-server:reload';

/**
 * Initialization data for the jupyterlab-bokeh-server extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab-bokeh-server',
  autoStart: true,
  requires: [ILabShell, ICommandPalette],
  optional: [ILayoutRestorer],
  activate: (
    app: JupyterFrontEnd,
    labShell: ILabShell,
    palette: ICommandPalette,
    restorer: ILayoutRestorer | null
  ) => {

    const sidebar = new BokehDashboardLauncher({
      launchItem: (item: IDashboardItem) => {
        app.commands.execute(LAUNCH_COMMAND_ID, item);
      }
    });
    sidebar.id = 'bokeh-dashboard-launcher';
    sidebar.title.iconClass ='bokeh-ChartIcon jp-SideBar-tabIcon';
    sidebar.title.caption = 'Dashboard Apps';
    labShell.add(sidebar, 'left');

    // An instance tracker which is used for state restoration.
    const tracker = new WidgetTracker<BokehDashboard>({
      namespace: 'bokeh-dashboard-launcher'
    });

    app.commands.addCommand(LAUNCH_COMMAND_ID, {
      label: 'Open Dashboard App',
      execute: args => {
        const item = args as IDashboardItem;
        // If we already have a dashboard open to this url, activate it
        // but don't create a duplicate.
        const w = tracker.find(w => {
          return !!(w && w.item && w.item.route === item.route);
        });
        if (w) {
          if (!w.isAttached) {
            labShell.add(w, 'main');
          }
          labShell.activateById(w.id);
          return;
        }

        const widget = new BokehDashboard();
        widget.title.label = item.label;
        widget.title.icon = 'bokeh-ChartIcon';
        widget.item = item;
        labShell.add(widget, 'main');
        tracker.add(widget);
      }
    });

    app.commands.addCommand(RELOAD_COMMAND_ID, {
      label: 'Reload Dashboards',
      execute: () => {
        console.log(`Reloading Dashboards`);
        let connection = ServerConnection.makeSettings({});
        ServerConnection.makeRequest(
          URLExt.join(connection.baseUrl, '/bokeh-dashboard/reload'),
          {},
          connection
        ).then(response => {
          response.json().then((data: { [x: string]: string }) => {
            console.log(`reloading status: ${data.status}`);
          });
        });
      }
    });

    palette.addItem({
      command: RELOAD_COMMAND_ID,
      category: 'dashboards',
      args: {}
    });

    if (restorer) {
      // Add state restoration for the dashboard items.
      restorer.add(sidebar, sidebar.id);
      restorer.restore(tracker, {
        command: LAUNCH_COMMAND_ID,
        args: widget => widget.item || {},
        name: widget => (widget.item && widget.item.route) || ''
      });
    }

    labShell.add(sidebar, 'left', { rank: 200 });

  }
};

export default extension;

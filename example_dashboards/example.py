import panel as pn
from bokeh.plotting import figure
import numpy as np

print("loading example dashboard...")

def main(doc):
    print('running example dashboard...')
    x = np.linspace(0, 4*np.pi, 100)
    y = np.sin(x)
    fig = figure(title="Example", sizing_mode="stretch_both")
    fig.line(x, y, legend_label="sin(x)")
    return pn.Column(fig, sizing_mode='stretch_both')

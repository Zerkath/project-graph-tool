import json

import ipywidgets as widgets
import networkx as nx
from ipysigma import Sigma
from IPython.display import display

with open("class_graph.json", encoding="utf-8") as f:
    data = json.load(f)

G = nx.DiGraph()
for node in data["nodes"]:
    G.add_node(node["key"], **node["attributes"])
for edge in data["edges"]:
    G.add_edge(edge["source"], edge["target"], **edge["attributes"])

output = widgets.Output()


def render(gravity, scaling_ratio, slow_down, barnes_hut_theta, edge_weight_influence, strong_gravity, barnes_hut, lin_log, outbound_attraction, adjust_sizes):
    output.clear_output(wait=True)
    with output:
        display(
            Sigma(
                G,
                node_color="kind",
                node_label="label",
                node_size=G.degree,
                edge_color="rel",
                edge_label="rel",
                node_metrics=["louvain"],
                start_layout=5,
                height=1080,
                layout_settings={
                    "barnesHutOptimize": barnes_hut,
                    "barnesHutTheta": barnes_hut_theta,
                    "gravity": gravity,
                    "scalingRatio": scaling_ratio,
                    "strongGravityMode": strong_gravity,
                    "slowDown": slow_down,
                    "edgeWeightInfluence": edge_weight_influence,
                    "linLogMode": lin_log,
                    "outboundAttractionDistribution": outbound_attraction,
                    "adjustSizes": adjust_sizes,
                },
            )
        )


_slider_layout = widgets.Layout(width="800px")
_slider_style = {"description_width": "180px"}

controls = widgets.interactive(
    render,
    {"manual": True, "manual_name": "Apply layout"},
    gravity=widgets.FloatSlider(
        value=0.4, min=0, max=20, step=0.01, description="gravity",
        layout=_slider_layout, style=_slider_style, readout_format=".2f",
    ),
    scaling_ratio=widgets.FloatSlider(
        value=5, min=1, max=250, step=0.5, description="scalingRatio",
        layout=_slider_layout, style=_slider_style,
    ),
    slow_down=widgets.FloatSlider(
        value=1, min=1, max=40, step=0.1, description="slowDown",
        layout=_slider_layout, style=_slider_style,
    ),
    barnes_hut_theta=widgets.FloatSlider(
        value=0.2, min=0, max=1.5, step=0.01, description="barnesHutTheta",
        layout=_slider_layout, style=_slider_style, readout_format=".2f",
    ),
    edge_weight_influence=widgets.FloatSlider(
        value=1, min=0, max=5, step=0.01, description="edgeWeightInfluence",
        layout=_slider_layout, style=_slider_style, readout_format=".2f",
    ),
    strong_gravity=widgets.Checkbox(value=False, description="strongGravityMode"),
    barnes_hut=widgets.Checkbox(value=False, description="barnesHutOptimize"),
    lin_log=widgets.Checkbox(value=False, description="linLogMode"),
    outbound_attraction=widgets.Checkbox(value=False, description="outboundAttractionDistribution"),
    adjust_sizes=widgets.Checkbox(value=False, description="adjustSizes"),
)

display(controls, output)
render(
    gravity=1,
    scaling_ratio=10,
    slow_down=5,
    barnes_hut_theta=0.5,
    edge_weight_influence=1,
    strong_gravity=False,
    barnes_hut=True,
    lin_log=False,
    outbound_attraction=False,
    adjust_sizes=False,
)

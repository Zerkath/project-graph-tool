import json

import networkx as nx
from ipysigma import Sigma

with open("class_graph.json", encoding="utf-8") as f:
    data = json.load(f)

G = nx.DiGraph()
for node in data["nodes"]:
    G.add_node(node["key"], **node["attributes"])
for edge in data["edges"]:
    G.add_edge(edge["source"], edge["target"], **edge["attributes"])

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
        "barnesHutOptimize": True,
        "gravity": 1,
        "scalingRatio": 10,
        "strongGravityMode": False,
        "slowDown": 5,
    },
)

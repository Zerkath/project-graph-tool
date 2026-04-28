# Project Graph Tool

Simple python utility that scans source directories and produces a class graph as a [graphology](https://graphology.github.io/serialization.html) JSON file (`class_graph.json`).

The output is consumable by [sigma.js](https://www.sigmajs.org/) for rendering in the browser.

Possible to use [Gephi Lite 1.0.1](https://lite.gephi.org/v1.0.1/)

[Currently open issue preventing use of 1.0.2](https://github.com/gephi/gephi-lite/issues/290)
[Pending 1.1.0 release](https://github.com/gephi/gephi-lite/milestone/2)

![Vizualization of this project](/images/vizualization.jpg)
![Vizualization of my Chess Engine](/images/rosemary.jpg)

```sh
uvx --from git+ssh://git@github.com/Zerkath/project-graph-tool.git visualize-project
```

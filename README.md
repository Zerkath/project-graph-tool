# Project Graph Tool

Simple python utility that scans source directories and produces a class graph as a
[graphology] JSON file (`class_graph.json`).

The output is consumable by [sigma.js] for rendering in the browser.

> [!TIP]
> Usage:
> 
> ```sh
> uvx --from git+ssh://git@github.com/Zerkath/project-graph-tool.git visualize-project
> ```

# Contributing

At this time this project is meant for demonstration and occasional internal use.
I do not intend to have others contribute to the setup.

## Demonstration

Examples rendered using:

[Gephi Lite 1.0.1](https://lite.gephi.org/v1.0.1/)

- [Currently open issue preventing use of 1.0.2](https://github.com/gephi/gephi-lite/issues/290)
- [Pending 1.1.0 release](https://github.com/gephi/gephi-lite/milestone/2)

### This Project

![Vizualization of this project](/images/vizualization.jpg)

### [Rosemary Chess]

Past school project built on Java.

![Vizualization of my Chess Engine](/images/rosemary.jpg)


[Rosemary Chess]: https://github.com/Zerkath/rosemary-chess
[graphology]: https://graphology.github.io/serialization.html
[sigma.js]: https://www.sigmajs.org/

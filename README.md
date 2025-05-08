# Toying with displaying dispatch dependency in IREE

We can dump dispatch graph from IREE, using `--iree-flow-dump-dispatch-graph`
flag. However, it is not efficient at model level in terms of display, because
it has too many nodes. This is a toy script to display the graph in a browser.

To display the graph in HTML, run this script,

```bash
iree-compile ... \
  --iree-flow-dump-dispatch-graph \
  --iree-flow-dump-dispatch-graph-output-file=dispatch.dot
./dot_to_html.py dispatch.dot graph.html
```

Then you can open the `graph.html` in your browser.

## Graph Interaction Features
- Move the graph: Click and drag the background to move the entire graph.
- Zoom In/Out: Use your mouse wheel to zoom in and out smoothly.
- Scroll with Wheel: Use the scroll wheel to pan vertically across the graph.
    (similar to tracy profile)
- Drag Nodes: Nodes can be repositioned by dragging them directly.

## TODO

- Search the node with given dispatch name.
- Display the dispatch content somehow.

## Note

The script is not maintained actively. It is just a toy. Any contribution is
welcome.

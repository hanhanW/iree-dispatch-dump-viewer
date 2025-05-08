#!/usr/bin/env python3
import json
import re

def parse_dot(dot_file):
    """
    Returns a pair of (nodes, edges) from the dot_file. edges is a list of
    dictionary that describes the edges. An edge could have additional
    roperties depending on the dot file. E.g.,
      [ {'source': 'v0', 'target': 'v1'},
        {'source', 'v1', 'target': 'v2', 'endArrow': True,
          'style': {'stroke': '#ccc'} }
      ]
    """
    with open(dot_file, 'r') as f:
        lines = f.readlines()

    nodes = {}
    edges = []
    inside_subgraph = False
    for line in lines:
        # Remove comments
        line = re.sub(r"//.*", "", line).strip()

        if re.match(r"^subgraph\s+cluster_\d+\s*{$", line):
            inside_subgraph = True
            continue
        if line == "}":
            inside_subgraph = False
            continue

        # Match node definitions with attributes (e.g., A [shape = ellipse, label = "Start"];)
        match = re.match(r"^([a-zA-Z0-9_]+)\s*\[(.*)\];$", line)
        if match:
            node_id = match.group(1)
            attributes_str = match.group(2)

            # Split attributes by commas, but avoid breaking on commas inside
            # quotes. It basically maps to SSA form in MLIR.
            attributes = re.findall(r'(\w+)\s*=\s*"([^"]+)"', attributes_str)
            node_attrs = {}
            for key, value in attributes:
                node_attrs[key.strip()] = value.strip().replace('\\n', '\n')
            nodes[node_id] = node_attrs

        # Match edges (e.g., A -> B [style = solid, label = ""];)
        match_edge = re.match(r"^([a-zA-Z0-9_]+)\s*->\s*([a-zA-Z0-9_]+)\s*\[([^\]]+)\];$", line)
        if match_edge:
            source = match_edge.group(1)
            dest = match_edge.group(2)
            edge_attrs_str = match_edge.group(3)

            # Split edge attributes by commas, but avoid breaking on commas
            # inside quotes.
            edge_properties = {}
            for key, value in re.findall(r'(\w+)\s*=\s*"([^"]+)"', edge_attrs_str):
                edge_properties[key.strip] = value.strip().strip('"')
            edge = {
                "source": source,
                "target": dest,
                "endArrow": True,
                "style": {"stroke": "#ccc"}  # Default stroke style
            }
            if "style" in edge_properties:
                if "solid" in edge_properties["style"]:
                    edge["style"]["lineType"] = "solid"
            if "label" in edge_properties and edge_properties["label"]:
                edge["label"] = edge_properties["label"]
            edges.append(edge)

    return (nodes, edges)

def convert_to_g6_graph(nodes, edges):
    g6_graph = {
        "nodes": [
            {"id": node_id,
             "label": nodes[node_id].get("label", node_id),
             "shape": nodes[node_id].get("shape", "rect")}
            for node_id in nodes
        ],
        "edges": edges
    }
    return g6_graph

JS = """
      function highlightMultiEdgeNodes(data) {
        const outCount = {};

        // Count in and out edges
        data.edges.forEach(edge => {
          outCount[edge.source] = (outCount[edge.source] || 0) + 1;
        });

        // Update node styles
        data.nodes.forEach(node => {
          const outgoing = outCount[node.id] || 0;
          if (outgoing > 1) {
            node.style = {
              fill: '#FFD591', // Highlight color
              stroke: '#FA8C16',
              lineWidth: 2
            };
          }
        });

        return data;
      }
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Dispatch DAG - G6 Layout</title>
    <script src="https://gw.alipayobjects.com/os/lib/antv/g6/4.8.17/dist/g6.min.js"></script>
    <style>
      html, body, #container {{
        width: 100%;
        height: 100%;
        margin: 0;
        overflow: hidden;
      }}
    </style>
  </head>
  <body>
    <div id="container"></div>
    <script>
      {js}

      const graph = new G6.Graph({{
        container: 'container',
        width: window.innerWidth,
        height: window.innerHeight,
        layout: {{
          type: 'dagre',
          rankdir: 'TB',      // Top to Bottom
          nodesep: 40,
          ranksep: 100
        }},
        defaultNode: {{
          type: 'rect',
          size: [160, 40],     // Wider nodes for labels
          style: {{
            fill: '#9EC9FF',
            stroke: '#5B8FF9',
            radius: 4
          }},
          labelCfg: {{
            style: {{
              fontSize: 12,
              fill: '#000',
              overflow: 'clip'
            }}
          }}
        }},
        defaultEdge: {{
          style: {{
            stroke: '#ccc',
            endArrow: true
          }}
        }},
        modes: {{
          default: ['drag-canvas', 'zoom-canvas', 'drag-node']
        }},
        fitView: true,
        animate: true,
      }});

      const data = {graph};

      adjustedData = highlightMultiEdgeNodes(data);

      graph.data(adjustedData);
      graph.render();
    </script>
  </body>
</html>
""".strip()

def save_to_html(output_file, g6_graph):
    graph = json.dumps(g6_graph, indent=2)
    html = HTML_TEMPLATE.format(graph=graph, js=JS)
    with open(output_file, 'w') as f:
        f.write(html)
    print(f"HTML successfully saved to {output_file}")

def main(dot_file, output_file):
    print(f"Parsing {dot_file}...")
    (nodes, edges) = parse_dot(dot_file)
    print(f"Converting parsed graph to g6_graph...")
    g6_graph = convert_to_g6_graph(nodes, edges)
    save_to_html(output_file, g6_graph)

if __name__ == "__main__":
    # Example: python dot_to_g6.py input.dot output.json
    import sys
    if len(sys.argv) != 3:
        print("Usage: python dot_to_html.py <input.dot> <output.html>")
        sys.exit(1)

    input_dot_file = sys.argv[1]
    output_json_file = sys.argv[2]

    main(input_dot_file, output_json_file)

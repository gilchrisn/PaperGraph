import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

/**
 * Build a tree structure from the given { nodes, links } graph.
 * The data is already given in BFS/DFS order from the server, so we just:
 * 1) Create a map of nodeId -> node
 * 2) For each link, attach the child to the parent's children[] if not already visited
 * 3) Return the node corresponding to `rootId`
 *
 * This way, we ensure a node is only "attached" once, preventing duplicates.
 */
function buildHierarchyNoDuplicates(nodes, links, rootId) {
  // 1) Create a map of nodes => { ...node, children: [] }
  const nodeMap = new Map(
    nodes.map((n) => [n.id, { ...n, children: [] }])
  );

  // 2) Keep track of child IDs we've already attached to a parent
  const attachedChildren = new Set();

  // 3) Attach children based on links
  //    The server traversal ensures a node likely appears in correct BFS/DFS order.
  links.forEach((link) => {
    const parent = nodeMap.get(link.source);
    const child = nodeMap.get(link.target);

    // If both parent & child exist AND we haven't attached the child yet
    if (parent && child && !attachedChildren.has(child.id)) {
      parent.children.push(child);
      attachedChildren.add(child.id);
    }
  });

  // 4) Return the "root" node object, or null if missing
  return nodeMap.get(rootId) || null;
}

const TreeVisualization = ({ graph, rootId, onNodeClick }) => {
  const svgRef = useRef(null);
  const gRef = useRef(null);

  useEffect(() => {
    // Guard: if no nodes or if we can't find the root node
    if (!graph.nodes.length) return;

    // Build a hierarchy from the already-traversed data
    const rootData = buildHierarchyNoDuplicates(graph.nodes, graph.links, rootId);
    if (!rootData) {
      console.warn(`Could not build hierarchy: no root found for id=${rootId}`);
      return;
    }

    // Convert our "plain object" tree into a D3 hierarchy, then run d3.tree()
    const root = d3.hierarchy(rootData);
    d3.tree().size([1500, 800])(root);

    // We'll need a quick lookup from node ID => { x, y } for drawing links
    const allNodes = root.descendants();
    const nodeById = {};
    allNodes.forEach((d) => {
      nodeById[d.data.id] = d;
    });

    // Prepare the <svg> with zoom
    const svg = d3
      .select(svgRef.current)
      .attr("width", 1500)
      .attr("height", 800)
      .style("border", "1px solid black")
      .call(
        d3.zoom().on("zoom", (event) => {
          d3.select(gRef.current).attr("transform", event.transform);
        })
      );

    const g = d3.select(gRef.current);

    // ========== Draw Links ==========
    g.selectAll(".link")
      // Bind all incoming links (regardless of BFS/DFS) 
      // but only render if their source/target is in the hierarchy
      .data(graph.links, (d) => `${d.source}-${d.target}`)
      .join(
        (enter) =>
          enter
            .append("line")
            .attr("class", "link")
            .attr("stroke", "#999")
            .attr("stroke-width", 2)
            // Start both ends at the source's position (for a "grow" effect)
            .attr("x1", (d) => nodeById[d.source]?.x ?? 0)
            .attr("y1", (d) => nodeById[d.source]?.y ?? 0)
            .attr("x2", (d) => nodeById[d.source]?.x ?? 0)
            .attr("y2", (d) => nodeById[d.source]?.y ?? 0)
            .transition()
            .duration(500)
            .attr("x2", (d) => nodeById[d.target]?.x ?? 0)
            .attr("y2", (d) => nodeById[d.target]?.y ?? 0),
        (update) =>
          update
            .attr("x1", (d) => nodeById[d.source]?.x ?? 0)
            .attr("y1", (d) => nodeById[d.source]?.y ?? 0)
            .attr("x2", (d) => nodeById[d.target]?.x ?? 0)
            .attr("y2", (d) => nodeById[d.target]?.y ?? 0),
        (exit) => exit.remove()
      );

    // ========== Draw Nodes ==========
    g.selectAll(".node")
      // We bind the *hierarchy-based* nodes, so only once per unique node
      .data(allNodes, (d) => d.data.id)
      .join(
        (enter) =>
          enter
            .append("circle")
            .attr("class", "node")
            .attr("fill", (d) => {
              const colorScale = d3
                .scaleLinear()
                .domain([0, 0.33, 0.66, 1])
                .range(["red", "orange", "yellow", "green"]);
              return colorScale(d.data.similarity_score || 0);
            })
            .attr("r", 0) // start with r=0 for an animation effect
            .attr("cx", (d) => d.x)
            .attr("cy", (d) => d.y)
            .on("click", (event, d) => onNodeClick?.(d.data))
            .transition()
            .duration(500)
            .attr("r", 30), // final radius
        (update) =>
          update
            .attr("cx", (d) => d.x)
            .attr("cy", (d) => d.y),
        (exit) => exit.remove()
      );

    // ========== Draw Labels ==========
    g.selectAll(".label")
      .data(allNodes, (d) => d.data.id)
      .join(
        (enter) =>
          enter
            .append("text")
            .attr("class", "label")
            .attr("text-anchor", "middle")
            .style("font-size", "14px")
            .attr("x", (d) => d.x)
            .attr("y", (d) => d.y - 35)
            .text((d) => d.data.title || d.data.label || "No Label"),
        (update) =>
          update
            .attr("x", (d) => d.x)
            .attr("y", (d) => d.y - 35)
            .text((d) => d.data.title || d.data.label || "No Label"),
        (exit) => exit.remove()
      );
  }, [graph, rootId, onNodeClick]);

  return (
    <div style={{ position: "relative" }}>
      <svg ref={svgRef}>
        <g ref={gRef}></g>
      </svg>
    </div>
  );
};

export default TreeVisualization;

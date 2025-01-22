import React, { useEffect, useRef, useCallback } from "react";
import * as d3 from "d3";
import PropTypes from "prop-types";

/**
 * TREE VISUALIZATION COMPONENT
 * - Runs an up/down BFS layering from rootId.
 * - Zoom/pan support.
 * - Color-coded edges (downward vs. upward).
 * - Root node in red, others in green.
 * - Nielsen's heuristics: clear feedback, easy zoom/pan, consistent coloring.
 */
const TreeVisualization = ({
  graph,
  rootId,
  onNodeClick,
  downwardData,
  upwardData,
  width = 800,
  height = 600
}) => {
  const svgRef = useRef();
  const tooltipRef = useRef();

  // Colors for edges and nodes
  const COLORS = {
    downward: "#4daf4a", // green
    upward: "#377eb8",   // blue
    root: "#e41a1c",     // red
    nodeDefault: "#69b3a2", 
    text: "#333",
    background: "#f5f5f5"
  };

  /**
   * 1. Combine the `graph` with phase info from `downwardData` & `upwardData`.
   *    We'll label edges as "downward" or "upward" based on membership in downwardData.
   */
  const processGraphData = useCallback(() => {
    if (!graph || !graph.nodes || !graph.links) {
      return { nodes: [], links: [] };
    }
    const nodeMap = {};
    graph.nodes.forEach((n) => {
      nodeMap[n.id] = n;
    });

    // Collect downward link IDs for quick lookup
    const downLinkSet = new Set(
      downwardData.links.map((l) => `${l.source}-${l.target}`)
    );

    // Mark each link with a "type"
    const finalLinks = graph.links.map((link) => {
      const key = `${link.source}-${link.target}`;
      const isDownward = downLinkSet.has(key);
      return {
        ...link,
        type: isDownward ? "downward" : "upward"
      };
    });

    return {
      nodes: graph.nodes,
      links: finalLinks
    };
  }, [graph, downwardData]);

  /**
   * 2. BFS LAYERING:
   *    - adjacencyDown for source->target
   *    - adjacencyUp for target->source
   *    - BFS down => nonnegative levels
   *    - BFS up => negative levels
   *    - Combine & shift so top-most is level 0 or keep root at 0. We'll keep top-most at 0 for clarity.
   */
  const computePositions = (nodes, links) => {
    if (!nodes.length) return { positions: {}, displayedLinks: [] };

    // Build adjacency for downward & upward
    const adjacencyDown = {};
    const adjacencyUp = {};
    const nodeSet = new Set(nodes.map((n) => n.id));
    nodes.forEach((n) => {
      adjacencyDown[n.id] = [];
      adjacencyUp[n.id] = [];
    });
    links.forEach((l) => {
      if (nodeSet.has(l.source) && nodeSet.has(l.target)) {
        adjacencyDown[l.source].push(l.target);
        adjacencyUp[l.target].push(l.source);
      }
    });

    // BFS helper
    function bfs(start, adjacency) {
      const queue = [start];
      const levels = { [start]: 0 };
      while (queue.length > 0) {
        const current = queue.shift();
        const curLevel = levels[current];
        (adjacency[current] || []).forEach((nbr) => {
          if (levels[nbr] === undefined) {
            levels[nbr] = curLevel + 1;
            queue.push(nbr);
          }
        });
      }
      return levels;
    }

    // 1. BFS downward from root => levelsDown
    const levelsDown = bfs(rootId, adjacencyDown);
    // 2. BFS upward from root => levelsUp
    const rawUp = bfs(rootId, adjacencyUp);
    // Convert upward BFS to negative levels
    const levelsUp = {};
    Object.entries(rawUp).forEach(([nid, dist]) => {
      levelsUp[nid] = -dist;
    });

    // 3. Combine BFS results
    const finalLevels = {};
    // Start with downward
    Object.entries(levelsDown).forEach(([nid, dist]) => {
      finalLevels[nid] = dist;
    });
    // Merge upward
    Object.entries(levelsUp).forEach(([nid, upLvl]) => {
      if (finalLevels[nid] === undefined) {
        finalLevels[nid] = upLvl;
      } else {
        // if discovered in both BFS, pick whichever is "closer" to root
        const existing = finalLevels[nid];
        if (Math.abs(upLvl) < Math.abs(existing)) {
          finalLevels[nid] = upLvl;
        }
      }
    });

    // 4. Determine min & max levels => shift so min is 0
    const allLvls = Object.values(finalLevels);
    const minLvl = d3.min(allLvls);
    const maxLvl = d3.max(allLvls) || 0;
    const levelOffset = -minLvl; // e.g. if minLvl is -2 => offset = 2 => top row becomes 0

    // Group nodes by final layer after offset
    const layerGroups = {};
    Object.entries(finalLevels).forEach(([nid, lvl]) => {
      const newLvl = lvl + levelOffset; 
      if (!layerGroups[newLvl]) layerGroups[newLvl] = [];
      layerGroups[newLvl].push(nid);
    });

    // 5. Assign x,y positions
    const positions = {};
    const verticalGap = 120;
    const horizontalGap = 90;

    const sortedLayers = Object.keys(layerGroups).map(Number).sort((a, b) => a - b);
    sortedLayers.forEach((layer) => {
      const nodeIds = layerGroups[layer];
      const count = nodeIds.length;
      const totalWidth = (count - 1) * horizontalGap;
      nodeIds.forEach((nid, i) => {
        const x = width / 2 - totalWidth / 2 + i * horizontalGap;
        const y = 50 + layer * verticalGap;
        positions[nid] = { x, y };
      });
    });

    // 6. Filter links to only those whose both endpoints are placed
    const displayedLinks = links.filter((l) => positions[l.source] && positions[l.target]);

    return { positions, displayedLinks };
  };

  /**
   * 3. Main rendering logic (zoom, edges, nodes, tooltip, legend)
   */
  const renderVisualization = useCallback(() => {
    const { nodes, links } = processGraphData();
    if (!nodes.length) return;

    // Build BFS-based positions
    const { positions, displayedLinks } = computePositions(nodes, links);

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Zoom container
    const zoomG = svg.append("g");

    // Zoom/pan setup
    const zoomBehavior = d3
      .zoom()
      .scaleExtent([0.5, 5])
      .on("zoom", (event) => {
        zoomG.attr("transform", event.transform);
      });

    svg.call(zoomBehavior).on("dblclick.zoom", null);

    // Draw edges
    zoomG
      .selectAll(".link")
      .data(displayedLinks)
      .join("line")
      .attr("class", "link")
      .attr("stroke", (d) => (d.type === "downward" ? COLORS.downward : COLORS.upward))
      .attr("stroke-width", 1.5)
      .attr("x1", (d) => positions[d.source].x)
      .attr("y1", (d) => positions[d.source].y)
      .attr("x2", (d) => positions[d.target].x)
      .attr("y2", (d) => positions[d.target].y);

    // Draw nodes
    const nodeGroups = zoomG
      .selectAll(".node")
      .data(nodes)
      .join("g")
      .attr("class", "node")
      .filter((d) => positions[d.id]) // only if we have a position
      .attr("transform", (d) => {
        const { x, y } = positions[d.id];
        return `translate(${x},${y})`;
      })
      .on("click", (event, d) => {
        event.stopPropagation();
        onNodeClick?.(d);
      })
      .on("mouseover", function (event, d) {
        d3.select(this).select("circle").attr("r", 14);
        showTooltip(event, d);
      })
      .on("mouseout", function () {
        d3.select(this).select("circle").attr("r", 10);
        hideTooltip();
      });

    nodeGroups
      .append("circle")
      .attr("r", 10)
      .attr("fill", (d) => (d.id === rootId ? COLORS.root : COLORS.nodeDefault));

    nodeGroups
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", -18)
      .style("font-size", "12px")
      .style("fill", COLORS.text)
      .text((d) => d.title || d.id);

    // Legend
    const legendData = [
      { label: "Downward", color: COLORS.downward },
      { label: "Upward", color: COLORS.upward },
      { label: "Root", color: COLORS.root }
    ];
    const legend = zoomG
      .append("g")
      .attr("transform", "translate(20,20)")
      .selectAll(".legend-item")
      .data(legendData)
      .join("g")
      .attr("class", "legend-item")
      .attr("transform", (_, i) => `translate(0, ${i * 20})`);

    legend
      .append("rect")
      .attr("width", 15)
      .attr("height", 15)
      .attr("fill", (d) => d.color);

    legend
      .append("text")
      .attr("x", 20)
      .attr("y", 12)
      .style("font-size", "12px")
      .text((d) => d.label);
  }, [processGraphData, onNodeClick]);

  /**
   * 4. Tooltip show/hide
   */
  const showTooltip = (event, node) => {
    const tooltip = d3.select(tooltipRef.current);
    tooltip
      .style("opacity", 1)
      .style("left", `${event.pageX + 12}px`)
      .style("top", `${event.pageY + 12}px`)
      .html(`
        <strong>${node.title ?? node.id}</strong><br/>
        Similarity: ${node.similarity_score?.toFixed(2) ?? "N/A"}<br/>
        ${node.remarks ? `Remarks: ${node.remarks}` : ""}
      `);
  };

  const hideTooltip = () => {
    d3.select(tooltipRef.current).style("opacity", 0);
  };

  /**
   * 5. Render on every relevant change
   */
  useEffect(() => {
    renderVisualization();
    return () => {
      d3.select(svgRef.current).selectAll("*").remove();
    };
  }, [renderVisualization]);

  /**
   * Final JSX
   */
  return (
    <div style={{ position: "relative" }}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{
          border: "1px solid #ddd",
          borderRadius: "8px",
          backgroundColor: COLORS.background
        }}
      />
      {/* Tooltip */}
      <div
        ref={tooltipRef}
        style={{
          position: "absolute",
          opacity: 0,
          padding: "8px",
          background: "#fff",
          border: "1px solid #ccc",
          borderRadius: "4px",
          pointerEvents: "none",
          boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
          zIndex: 999
        }}
      />
    </div>
  );
};

TreeVisualization.propTypes = {
  graph: PropTypes.shape({
    nodes: PropTypes.array.isRequired,
    links: PropTypes.array.isRequired
  }),
  rootId: PropTypes.string.isRequired,
  onNodeClick: PropTypes.func,
  downwardData: PropTypes.object,
  upwardData: PropTypes.object,
  width: PropTypes.number,
  height: PropTypes.number
};

export default TreeVisualization;

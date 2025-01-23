import React, { useEffect, useRef, useCallback } from "react";
import * as d3 from "d3";
import PropTypes from "prop-types";

const TreeVisualization = ({
  graph,
  rootId,
  onNodeClick,
  downwardData,
  upwardData,
  width = 800,
  height = 600,
  similarityThreshold = 0
}) => {
  const svgRef = useRef();
  const tooltipRef = useRef();

  // Colors for edges and nodes
  const COLORS = {
    downward: "#4d8f4a", // green
    upward:   "#377eb8", // blue
    root:     "#e41a1c", // red
    nodeDefault: "#69b3a2",
    text: "#333",
    background: "#f5f5f5"
  };

  //////////////////////////////////////////////////////////
  // 1) Classify links as downward/upward from data
  //////////////////////////////////////////////////////////
  const processGraphData = useCallback(() => {
    if (!graph || !graph.nodes || !graph.links) {
      return { nodes: [], links: [] };
    }

    // Create sets for quick membership checks
    const downLinkSet = new Set(
      (downwardData?.links || []).map((l) => `${l.source}-${l.target}`)
    );
    const upLinkSet = new Set(
      (upwardData?.links || []).map((l) => `${l.source}-${l.target}`)
    );

    // Mark each link with "downward" or "upward"
    const finalLinks = graph.links.map((link) => {
      const key = `${link.source}-${link.target}`;
      if (downLinkSet.has(key)) {
        return { ...link, type: "downward" };
      } else if (upLinkSet.has(key)) {
        return { ...link, type: "upward" };
      } else {
        return { ...link, type: "downward" };
      }
    });

    return {
      nodes: graph.nodes,
      links: finalLinks
    };
  }, [graph, downwardData, upwardData]);

  //////////////////////////////////////////////////////////
  // 2) BFS helper
  //////////////////////////////////////////////////////////
  const bfs = (startId, adjacency) => {
    const dist = { [startId]: 0 };
    const queue = [startId];
    while (queue.length) {
      const current = queue.shift();
      const curDist = dist[current];
      for (const nbr of adjacency[current] || []) {
        if (dist[nbr] === undefined) {
          dist[nbr] = curDist + 1;
          queue.push(nbr);
        }
      }
    }
    return dist;
  };

  //////////////////////////////////////////////////////////
  // 3) Combine BFS logic to place nodes above or below
  //////////////////////////////////////////////////////////
  const computePositionsCenterRoot = (nodes, links, rootId, width, height) => {
    // 3A) Build adjacencyDown / adjacencyUp
    if (!nodes.length || !links.length) {
      return { positions: {}, displayedLinks: [] };
    }

    const adjacencyDown = {};
    const adjacencyUp = {};

    for (const n of nodes) {
      adjacencyDown[n.id] = [];
      adjacencyUp[n.id] = [];
    }

    // If link.type === "downward": adjacencyDown[source].push(target)
    // If link.type === "upward":   adjacencyUp[source].push(target)  (child -> parent)
    links.forEach((l) => {
      const { source, target, type } = l;
      if (type === "upward") {
        // child -> parent
        adjacencyUp[source].push(target);
      } else {
        // downward
        adjacencyDown[source].push(target);
      }
    });

    // 3B) BFS downward from root => distanceDown
    const distanceDown = bfs(rootId, adjacencyDown);

    // finalLevels[nodeId] = numeric level (root=0, child=+d, parent=-d)
    const finalLevels = {};
    finalLevels[rootId] = 0;

    // record BFS-down results
    Object.entries(distanceDown).forEach(([nid, dist]) => {
      if (finalLevels[nid] === undefined) {
        finalLevels[nid] = dist; // place below root
      } else {
        finalLevels[nid] = Math.min(finalLevels[nid], dist);
      }
    });

    // 3C) For each node discovered downward, BFS up from that node
    for (const [nodeId, downDist] of Object.entries(distanceDown)) {
      const distUp = bfs(nodeId, adjacencyUp);
      // If distUp[parent] = k, then parent is (downDist - k)
      // That might be above the root if k> downDist, or still below root if k < downDist
      for (const [parentId, k] of Object.entries(distUp)) {
        if (parentId === nodeId) continue;
        const candidateLevel = downDist - k;
        if (finalLevels[parentId] === undefined) {
          finalLevels[parentId] = candidateLevel;
        } else {
          finalLevels[parentId] = Math.min(finalLevels[parentId], candidateLevel);
        }
      }
    }

    // Now finalLevels has all nodes discovered either by BFS down or BFS up from discovered nodes

    // 3D) Filter nodes to those discovered in finalLevels
    const discoveredNodeIds = new Set(Object.keys(finalLevels));
    const filteredNodes = nodes.filter((n) => discoveredNodeIds.has(n.id));

    // 3E) Filter links to only those whose endpoints are discovered
    // Also skip edges if finalLevels[source] === finalLevels[target]
    const filteredLinks = links.filter((l) => {
      const ls = finalLevels[l.source];
      const lt = finalLevels[l.target];
      if (ls === undefined || lt === undefined) return false;
      if (ls === lt) return false; // no same-level edges
      return true;
    });

    // 3F) Assign (x,y) based on finalLevels
    const positions = {};
    const yRoot = height / 2;
    const verticalGap = 100;
    const horizontalGap = 80;

    // group by finalLevels
    const levelGroups = {};
    filteredNodes.forEach((n) => {
      const lvl = finalLevels[n.id];
      if (!levelGroups[lvl]) levelGroups[lvl] = [];
      levelGroups[lvl].push(n.id);
    });

    // sort levels ascending
    const sortedLevels = Object.keys(levelGroups)
      .map(Number)
      .sort((a, b) => a - b);

    // place each level
    sortedLevels.forEach((lvl) => {
      const nodeIds = levelGroups[lvl];
      const totalWidth = (nodeIds.length - 1) * horizontalGap;
      nodeIds.forEach((nid, i) => {
        const x = width / 2 - totalWidth / 2 + i * horizontalGap;
        const y = yRoot + lvl * verticalGap;
        positions[nid] = { x, y };
      });
    });

    return { positions, displayedNodes: filteredNodes, displayedLinks: filteredLinks };
  };

  //////////////////////////////////////////////////////////
  // 4) Main rendering
  //////////////////////////////////////////////////////////
  const renderVisualization = useCallback(() => {
    const { nodes, links } = processGraphData();
    if (!nodes.length) return;

    // Combine BFS logic => positions + filtered (nodes/links)
    const { positions, displayedNodes, displayedLinks } = computePositionsCenterRoot(
      nodes,
      links,
      rootId,
      width,
      height
    );

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Zoom container
    const zoomG = svg.append("g");

    // Zoom/pan
    const zoomBehavior = d3
      .zoom()
      .scaleExtent([0.5, 5])
      .on("zoom", (event) => {
        zoomG.attr("transform", event.transform);
      });
    svg.call(zoomBehavior).on("dblclick.zoom", null);

    // Build a map for quick node lookups
    const nodeMap = {};
    displayedNodes.forEach((n) => {
      nodeMap[n.id] = n;
    });

    // Edges
    zoomG
      .selectAll(".link")
      .data(displayedLinks)
      .join("line")
      .attr("class", "link")
      .attr("x1", (d) => positions[d.source].x)
      .attr("y1", (d) => positions[d.source].y)
      .attr("x2", (d) => positions[d.target].x)
      .attr("y2", (d) => positions[d.target].y)
      .attr("stroke", (d) => {
        const targetNode = nodeMap[d.target];
        const score = targetNode?.similarity_score || 0;
        const baseColor = d.type === "downward" ? COLORS.downward : COLORS.upward;
        return score > similarityThreshold
          ? d3.color(baseColor).brighter(0.5)
          : baseColor;
      })
      .attr("stroke-width", (d) => {
        const targetNode = nodeMap[d.target];
        return (targetNode?.similarity_score || 0) > similarityThreshold ? 3 : 1;
      });

    // Nodes
    const nodeGroups = zoomG
      .selectAll(".node")
      .data(displayedNodes)
      .join("g")
      .attr("class", "node")
      .attr("transform", (d) => {
        const { x, y } = positions[d.id];
        return `translate(${x},${y})`;
      })
      // Dim nodes below threshold
      .attr("opacity", (d) => ((d.similarity_score || 0) > similarityThreshold ? 1 : 0.5))
      .on("click", (event, d) => {
        event.stopPropagation();
        onNodeClick?.(d);
      })
      .on("mouseover", function (event, d) {
        // Make bigger on hover
        d3.select(this).select("circle").attr("r", 14);
        showTooltip(event, d);
      })
      .on("mouseout", function () {
        d3.select(this)
          .select("circle")
          .attr("r", (d) => ((d.similarity_score || 0) > similarityThreshold ? 14 : 5));
        hideTooltip();
      });

    nodeGroups
      .append("circle")
      .attr("r", (d) => ((d.similarity_score || 0) > similarityThreshold ? 14 : 5))
      .attr("fill", (d) => {
        const baseColor = d.id === rootId ? COLORS.root : COLORS.nodeDefault;
        return (d.similarity_score || 0) > similarityThreshold
          ? d3.color(baseColor).brighter(0.3)
          : baseColor;
      });

    // Only render text for high-similarity nodes
    nodeGroups
      .filter((d) => (d.similarity_score || 0) > similarityThreshold)
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
  }, [
    processGraphData,
    bfs,
    rootId,
    width,
    height,
    similarityThreshold,
    onNodeClick
  ]);

  //////////////////////////////////////////////////////////
  // 5) Tooltip show/hide
  //////////////////////////////////////////////////////////
  const showTooltip = (event, node) => {
    d3.select(tooltipRef.current)
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

  //////////////////////////////////////////////////////////
  // 6) useEffect to render
  //////////////////////////////////////////////////////////
  useEffect(() => {
    renderVisualization();
    return () => {
      d3.select(svgRef.current).selectAll("*").remove();
    };
  }, [renderVisualization]);

  //////////////////////////////////////////////////////////
  // 7) Return JSX
  //////////////////////////////////////////////////////////
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
  downwardData: PropTypes.shape({
    links: PropTypes.array
  }),
  upwardData: PropTypes.shape({
    links: PropTypes.array
  }),
  onNodeClick: PropTypes.func,
  width: PropTypes.number,
  height: PropTypes.number,
  similarityThreshold: PropTypes.number
};

export default TreeVisualization;

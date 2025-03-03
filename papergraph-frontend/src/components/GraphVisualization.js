import React, { useEffect, useRef, useCallback } from "react";
import * as d3 from "d3";
import PropTypes from "prop-types";

/**
 * GraphVisualization
 * Renders the paper network using a force-directed graph layout.
 */
const GraphVisualization = ({
  graph,
  rootId,
  onNodeClick,
  downwardData,
  upwardData,
  width = 800,
  height = 600,
  similarityThreshold = 0,
  viewMode = "combined",
}) => {
  const svgRef = useRef(null);
  const tooltipRef = useRef(null);

  // Colors for edges and nodes
  const COLORS = {
    downward: "#4d8f4a", // green
    upward: "#377eb8",   // blue
    root: "#e41a1c",     // red
    nodeDefault: "#69b3a2",
    text: "#333",
    background: "#f5f5f5",
  };

  /**
   * Filter nodes/links based on the current viewMode
   */
  const filterByViewMode = useCallback((allNodes, allLinks) => {
    if (viewMode === "downward") {
      // Only show the downwardData set
      const downLinksSet = new Set(
        (downwardData?.links || []).map((l) => `${l.source}-${l.target}`)
      );
      const downNodeIds = new Set((downwardData?.nodes || []).map((n) => n.id));

      const filteredNodes = allNodes.filter((n) => downNodeIds.has(n.id));
      const filteredLinks = allLinks.filter((l) =>
        downLinksSet.has(`${l.source}-${l.target}`)
      );
      return { nodes: filteredNodes, links: filteredLinks };
    } else if (viewMode === "upward") {
      // Only show the upwardData set
      const upLinksSet = new Set(
        (upwardData?.links || []).map((l) => `${l.source}-${l.target}`)
      );
      const upNodeIds = new Set((upwardData?.nodes || []).map((n) => n.id));

      const filteredNodes = allNodes.filter((n) => upNodeIds.has(n.id));
      const filteredLinks = allLinks.filter((l) =>
        upLinksSet.has(`${l.source}-${l.target}`)
      );
      return { nodes: filteredNodes, links: filteredLinks };
    } else if (viewMode === "threshold") {
      // Only show nodes with similarity > threshold
      const validIds = new Set(
        allNodes
          .filter((n) => (n.relevance_score || 0) > similarityThreshold)
          .map((n) => n.id)
      );

      const filteredNodes = allNodes.filter((n) => validIds.has(n.id));
      const filteredLinks = allLinks.filter(
        (l) => validIds.has(l.source) && validIds.has(l.target)
      );
      return { nodes: filteredNodes, links: filteredLinks };
    } else {
      // "combined" => show everything
      return { nodes: allNodes, links: allLinks };
    }
  }, [downwardData, upwardData, similarityThreshold, viewMode]);

  /**
   * Process the graph data:
   * - Mark links as downward or upward (same as in TreeVisualization)
   */
  const processGraphData = useCallback(() => {
    if (!graph || !graph.nodes || !graph.links) {
      return { nodes: [], links: [] };
    }

    const downLinkSet = new Set(
      (downwardData?.links || []).map((l) => `${l.source}-${l.target}`)
    );
    const upLinkSet = new Set(
      (upwardData?.links || []).map((l) => `${l.source}-${l.target}`)
    );

    const finalLinks = graph.links.map((link) => {
      const key = `${link.source}-${link.target}`;
      if (downLinkSet.has(key)) {
        return { ...link, type: "downward" };
      } else if (upLinkSet.has(key)) {
        return { ...link, type: "upward" };
      } else {
        // default to downward if unknown
        return { ...link, type: "downward" };
      }
    });

    return {
      nodes: graph.nodes,
      links: finalLinks,
    };
  }, [graph, downwardData, upwardData]);

  /**
   * Show tooltip
   */
  const showTooltip = (event, node) => {
    d3.select(tooltipRef.current)
      .style("opacity", 1)
      .style("left", `${event.pageX + 12}px`)
      .style("top", `${event.pageY + 12}px`)
      .html(`
        <strong>${node.title ?? node.id}</strong><br/>
        Similarity: ${node.relevance_score?.toFixed(2) ?? "N/A"}<br/>
        ${node.remarks ? `Remarks: ${node.remarks}` : ""}
      `);
  };

  /**
   * Hide tooltip
   */
  const hideTooltip = () => {
    d3.select(tooltipRef.current).style("opacity", 0);
  };

  /**
   * Main rendering logic using D3 force layout
   */
  const renderVisualization = useCallback(() => {
    const { nodes: rawNodes, links: rawLinks } = processGraphData();
    if (!rawNodes.length) return;

    // Filter nodes/links by viewMode
    const { nodes, links } = filterByViewMode(rawNodes, rawLinks);

    // If no nodes or links after filtering, clear
    if (!nodes.length) {
      d3.select(svgRef.current).selectAll("*").remove();
      return;
    }

    // Clear existing
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Setup root <g> for zoom
    const zoomG = svg.append("g");

    // Zoom behavior
    const zoomBehavior = d3
      .zoom()
      .scaleExtent([0.1, 5])
      .on("zoom", (event) => {
        zoomG.attr("transform", event.transform);
      });
    svg.call(zoomBehavior);

    // Create simulation
    const simulation = d3
      .forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d) => d.id).distance(150))
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // Build link elements
    const linkSelection = zoomG
      .selectAll(".link")
      .data(links)
      .enter()
      .append("line")
      .attr("class", "link")
      .attr("stroke", (d) => {
        const baseColor = d.type === "downward" ? COLORS.downward : COLORS.upward;
        // We'll color by target's similarity score
        const targetNode = nodes.find((n) => n.id === d.target);
        const score = targetNode?.relevance_score || 0;
        return score > similarityThreshold
          ? d3.color(baseColor).brighter(0.5)
          : baseColor;
      })
      .attr("stroke-width", (d) => {
        const targetNode = nodes.find((n) => n.id === d.target);
        return (targetNode?.relevance_score || 0) > similarityThreshold ? 3 : 1;
      });

    // Build node groups
    const nodeGroup = zoomG
      .selectAll(".node")
      .data(nodes)
      .enter()
      .append("g")
      .attr("class", "node")
      .on("mouseover", function (event, d) {
        // Make bigger on hover
        d3.select(this).select("circle").attr("r", 14);
        showTooltip(event, d);
      })
      .on("mouseout", function (event, d) {
        d3.select(this)
          .select("circle")
          .attr("r", (n) => ((n.relevance_score || 0) > similarityThreshold ? 14 : 8));
        hideTooltip();
      })
      .on("click", (event, d) => {
        event.stopPropagation();
        onNodeClick?.(d);
      });

    // Append circles
    nodeGroup
      .append("circle")
      .attr("r", (d) => ((d.relevance_score || 0) > similarityThreshold ? 14 : 8))
      .attr("fill", (d) => {
        if (d.id === rootId) {
          return COLORS.root;
        }
        const baseColor = COLORS.nodeDefault;
        return (d.relevance_score || 0) > similarityThreshold
          ? d3.color(baseColor).brighter(0.3)
          : baseColor;
      })
      .attr("opacity", (d) => ((d.relevance_score || 0) > similarityThreshold ? 1 : 0.7));

    // Optionally render text for high-similarity nodes
    nodeGroup
      .filter((d) => (d.relevance_score || 0) > similarityThreshold)
      .append("text")
      .text((d) => d.title || d.id)
      .attr("x", 16)
      .attr("y", 4)
      .style("font-size", "12px")
      .style("fill", COLORS.text);

    // Update positions on each tick
    simulation.on("tick", () => {
      linkSelection
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      nodeGroup.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });
  }, [
    processGraphData,
    filterByViewMode,
    rootId,
    similarityThreshold,
    width,
    height,
    onNodeClick,
  ]);

  useEffect(() => {
    renderVisualization();
    return () => {
      d3.select(svgRef.current).selectAll("*").remove();
    };
  }, [renderVisualization]);

  return (
    <div style={{ position: "relative" }}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{
          border: "1px solid #ddd",
          borderRadius: "8px",
          backgroundColor: COLORS.background,
        }}
      />
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
          zIndex: 999,
        }}
      />
    </div>
  );
};

GraphVisualization.propTypes = {
  graph: PropTypes.shape({
    nodes: PropTypes.array.isRequired,
    links: PropTypes.array.isRequired,
  }),
  rootId: PropTypes.string.isRequired,
  downwardData: PropTypes.shape({
    links: PropTypes.array,
    nodes: PropTypes.array,
  }),
  upwardData: PropTypes.shape({
    links: PropTypes.array,
    nodes: PropTypes.array,
  }),
  onNodeClick: PropTypes.func,
  width: PropTypes.number,
  height: PropTypes.number,
  similarityThreshold: PropTypes.number,
  viewMode: PropTypes.string,
};

export default GraphVisualization;

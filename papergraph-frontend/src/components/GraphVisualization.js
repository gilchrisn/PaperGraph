import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const GraphVisualization = ({ nodes, links, onNodeClick, width = 800, height = 600 }) => {
    const svgRef = useRef();

    useEffect(() => {
        const svg = d3.select(svgRef.current);
        // Clear any old render
        svg.selectAll("*").remove();

        // Force simulation
        const simulation = d3
            .forceSimulation(nodes)
            .force("link", d3.forceLink(links).id((d) => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2));

        // Draw links
        const link = svg
            .append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("stroke", "#999")
            .attr("stroke-width", 1.5);

        // Draw nodes
        const node = svg
            .append("g")
            .selectAll("circle")
            .data(nodes)
            .join("circle")
            .attr("r", 10)
            .attr("fill", "#69b3a2")
            .call(drag(simulation))
            .on("click", (event, d) => {
                if (onNodeClick) onNodeClick(d);
            });

        // Add labels near nodes
        const label = svg
            .append("g")
            .selectAll("text")
            .data(nodes)
            .join("text")
            .attr("dy", -15)
            .attr("text-anchor", "middle")
            .style("font-size", "12px")
            .text((d) => d.title ?? d.id);

        // Update positions on each tick
        simulation.on("tick", () => {
            link
                .attr("x1", (d) => d.source.x)
                .attr("y1", (d) => d.source.y)
                .attr("x2", (d) => d.target.x)
                .attr("y2", (d) => d.target.y);

            node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);

            label.attr("x", (d) => d.x).attr("y", (d) => d.y);
        });

        // Cleanup
        return () => simulation.stop();
    }, [nodes, links, onNodeClick, width, height]);

    return <svg ref={svgRef} width={width} height={height} style={{ border: "1px solid black" }} />;
};

// Drag behavior
const drag = (simulation) => {
    function dragStarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragEnded(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    return d3
        .drag()
        .on("start", dragStarted)
        .on("drag", dragged)
        .on("end", dragEnded);
};

export default GraphVisualization;

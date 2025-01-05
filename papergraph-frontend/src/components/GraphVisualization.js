import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const GraphVisualization = ({ nodes, links }) => {
    const svgRef = useRef(); // Reference to the SVG container

    useEffect(() => {
        const svg = d3.select(svgRef.current); // Select the SVG container
        const width = 800; // Width of the SVG
        const height = 600; // Height of the SVG
        
        // Define a force simulation for layout
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id((d) => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2));

        // Remove old elements before drawing new ones
        svg.selectAll("*").remove();

        // Draw links
        const link = svg
            .append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("stroke", "#999")
            .attr("stroke-width", 2);

        // Draw nodes
        const node = svg
            .append("g")
            .selectAll("circle")
            .data(nodes)
            .join("circle")
            .attr("r", 10)
            .attr("fill", "#69b3a2")
            .call(drag(simulation));

        // Add labels to nodes
        const labels = svg
            .append("g")
            .selectAll("text")
            .data(nodes)
            .join("text")
            .attr("dy", -15)
            .attr("text-anchor", "middle")
            .text((d) => d.label)
            .style("font-size", "12px");

        // Update positions on every tick
        simulation.on("tick", () => {
            link
                .attr("x1", (d) => d.source.x)
                .attr("y1", (d) => d.source.y)
                .attr("x2", (d) => d.target.x)
                .attr("y2", (d) => d.target.y);

            node
                .attr("cx", (d) => d.x)
                .attr("cy", (d) => d.y);

            labels
                .attr("x", (d) => d.x)
                .attr("y", (d) => d.y);
        });

        // Cleanup on unmount
        return () => simulation.stop();
    }, [nodes, links]);

    return (
        <svg
            ref={svgRef}
            width="800"
            height="600"
            style={{ border: "1px solid black" }}
        ></svg>
    );
};

// Drag behavior for nodes
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

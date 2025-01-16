import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const MeshVisualization = ({ data, onNodeClick }) => {
    const svgRef = useRef();
    const gRef = useRef();

    useEffect(() => {
        const width = 1500;
        const height = 800;

        const svg = d3
            .select(svgRef.current)
            .attr("width", width)
            .attr("height", height)
            .style("border", "1px solid black");

        const g = d3.select(gRef.current);

        // **Clear previous content**
        g.selectAll("*").remove();

        // Nodes and links from data
        const nodes = data.nodes;
        const links = data.links;

        // Simulation with forces
        const simulation = d3
            .forceSimulation(nodes)
            .force(
                "link",
                d3
                    .forceLink(links)
                    .id((d) => d.id)
                    .distance(100)
            )
            .force("charge", d3.forceManyBody().strength(-500))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force(
                "y",
                d3.forceY((d) => d.layer * 150) // Vertical alignment by layer
                    .strength(1)
            )
            .on("tick", ticked);

        // Draw links
        const link = g
            .selectAll(".link")
            .data(links)
            .join("line")
            .attr("class", "link")
            .attr("stroke", "#999")
            .attr("stroke-width", 2);

        // Draw nodes
        const node = g
            .selectAll(".node")
            .data(nodes)
            .join("circle")
            .attr("class", "node")
            .attr("r", 20)
            .attr("fill", (d) => {
                const colorScale = d3.scaleLinear()
                    .domain([0, 0.33, 0.66, 1])
                    .range(["red", "orange", "yellow", "green"]);
                return colorScale(d.similarity_score || 0);
            })
            .call(d3.drag()
                .on("start", (event, d) => {
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                })
                .on("drag", (event, d) => {
                    d.fx = event.x;
                    d.fy = event.y;
                })
                .on("end", (event, d) => {
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                })
            )
            .on("click", (event, d) => onNodeClick && onNodeClick(d));

        // Add labels
        const labels = g
            .selectAll(".label")
            .data(nodes)
            .join("text")
            .attr("class", "label")
            .attr("text-anchor", "middle")
            .attr("dy", -30)
            .text((d) => d.label);

        // Update positions on each simulation tick
        function ticked() {
            link
                .attr("x1", (d) => d.source.x)
                .attr("y1", (d) => d.source.y)
                .attr("x2", (d) => d.target.x)
                .attr("y2", (d) => d.target.y);

            node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);

            labels.attr("x", (d) => d.x).attr("y", (d) => d.y - 30);
        }
    }, [data]);

    return (
        <div style={{ position: "relative" }}>
            <svg ref={svgRef}>
                <g ref={gRef}></g>
            </svg>
        </div>
    );
};

export default MeshVisualization;

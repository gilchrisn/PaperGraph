import React, { useState, useEffect, useRef } from "react";
import * as d3 from "d3";

const TreeVisualization = ({ data, onNodeClick }) => {
    const svgRef = useRef();
    const gRef = useRef();

    const [existingNodeIds, setExistingNodeIds] = useState(new Set());
    const [existingLinkIds, setExistingLinkIds] = useState(new Set());

    useEffect(() => {
        const width = 1500;
        const height = 800;

        // Select the SVG container
        const svg = d3
            .select(svgRef.current)
            .attr("width", width)
            .attr("height", height)
            .style("border", "1px solid black")
            .call(
                d3.zoom().on("zoom", (event) => {
                    d3.select(gRef.current).attr("transform", event.transform);
                })
            );

        const g = d3.select(gRef.current);

        // **Clear all existing content in the <g> group**
        g.selectAll("*").remove();

        // Define tree layout
        const treeLayout = d3.tree().size([height * 5, width]);
        const root = d3.hierarchy(data);
        treeLayout(root);

        const nodes = root.descendants();
        const links = root.links();

        // Identify new nodes and links
        const currentNodeIds = new Set(nodes.map((node) => node.data.id));
        const newNodes = nodes.filter((node) => !existingNodeIds.has(node.data.id));

        const currentLinkIds = new Set(
            links.map((link) => `${link.source.data.id}-${link.target.data.id}`)
        );
        const newLinks = links.filter(
            (link) =>
                !existingLinkIds.has(`${link.source.data.id}-${link.target.data.id}`)
        );

        // Draw existing links without animation
        g.selectAll(".link-existing")
            .data(links.filter((link) => !newLinks.includes(link)), (d) =>
                `${d.source.data.id}-${d.target.data.id}`
            )
            .join(
                (enter) =>
                    enter
                        .append("line")
                        .attr("class", "link-existing")
                        .attr("stroke", "#999")
                        .attr("stroke-width", 5)
                        .attr("x1", (d) => d.source.x)
                        .attr("y1", (d) => d.source.y)
                        .attr("x2", (d) => d.target.x)
                        .attr("y2", (d) => d.target.y)
            );

        // Stagger new links animation
        newLinks.forEach((link, index) => {
            d3.timeout(() => {
                g.append("line")
                    .attr("class", "link-new")
                    .attr("stroke", "#999")
                    .attr("stroke-width", 5)
                    .attr("x1", link.source.x)
                    .attr("y1", link.source.y)
                    .attr("x2", link.source.x)
                    .attr("y2", link.source.y)
                    .transition()
                    .duration(500)
                    .attr("x2", link.target.x)
                    .attr("y2", link.target.y);
            }, index * 100); // Delay animation based on index
        });


        // Draw existing nodes without animation
        g.selectAll(".node-existing")
            .data(nodes.filter((node) => !newNodes.includes(node)), (d) => d.data.id)
            .join(
                (enter) =>
                    enter
                        .append("circle")
                        .attr("class", "node-existing")
                        .attr("fill", (d) => {
                            const colorScale = d3.scaleLinear()
                                .domain([0, 0.33, 0.66, 1])
                                .range(["red", "orange", "yellow", "green"]);
                            return colorScale(d.data.similarity_score || 0);
                        })
                        .attr("r", 50)
                        .attr("cx", (d) => d.x)
                        .attr("cy", (d) => d.y)
                        .on("click", (event, d) => onNodeClick && onNodeClick(d.data))
            );

        // Stagger new nodes animation
        newNodes.forEach((node, index) => {
            d3.timeout(() => {
                g.append("circle")
                    .attr("class", "node-new")
                    .attr("r", 0)
                    .attr("fill", () => {
                        const colorScale = d3.scaleLinear()
                            .domain([0, 0.33, 0.66, 1])
                            .range(["red", "orange", "yellow", "green"]);
                        return colorScale(node.data.similarity_score || 0);
                    })
                    .attr("cx", node.parent ? node.parent.x : node.x)
                    .attr("cy", node.parent ? node.parent.y : node.y)
                    .on("click", (event) => onNodeClick && onNodeClick(node.data))
                    .transition()
                    .duration(500)
                    .attr("r", 50)
                    .attr("cx", node.x)
                    .attr("cy", node.y);

                // Append label after node
                g.append("text")
                    .attr("class", "label")
                    .attr("text-anchor", "middle")
                    .style("font-size", "14px")
                    .attr("x", node.x)
                    .attr("y", node.y - 10)
                    .text(node.data.label);
            }, index * 100); // Delay animation based on index
        });



        // Draw labels
        g.selectAll(".label-existing")
            .data(nodes.filter((node) => !newNodes.includes(node)), (d) => d.data.id)
            .join(
                (enter) =>
                    enter
                        .append("text")
                        .attr("class", "label-existing")
                        .attr("text-anchor", "middle")
                        .style("font-size", "14px")
                        .attr("x", (d) => d.x)
                        .attr("y", (d) => d.y - 10)
                        .text((d) => d.data.label)
            );


        // Update the sets of existing node and link IDs
        setExistingNodeIds(new Set([...existingNodeIds, ...currentNodeIds]));
        setExistingLinkIds(new Set([...existingLinkIds, ...currentLinkIds]));
    }, [data]);

    return (
        <div style={{ position: "relative" }}>
            <svg ref={svgRef}>
                <g ref={gRef}></g>
            </svg>
        </div>
    );
};

export default TreeVisualization;

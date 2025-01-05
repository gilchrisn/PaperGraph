import React, { useState, useEffect, useRef } from "react";
import * as d3 from "d3";
import Tooltip from "./Tooltip";


const TreeVisualization = ({ data }) => {
    const svgRef = useRef();
    const gRef = useRef();

    const [tooltip, setTooltip] = useState({
        visible: false,
        x: 0,
        y: 0,
        node: null,
    });

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
        const treeLayout = d3.tree().size([height * 10, width * 2]);
        const root = d3.hierarchy(data);
        treeLayout(root);

        // Links
        const links = root.links();

    
        g.selectAll(".link")
            .data(links, (d) => `${d.source.data.id}-${d.target.data.id}`)
            .join(
                (enter) =>
                    enter
                        .append("line")
                        .attr("class", "link")
                        .attr("stroke", "#999")
                        .attr("stroke-width", 5)
                        .attr("x1", (d) => d.source.x)
                        .attr("y1", (d) => d.source.y)
                        .attr("x2", (d) => d.source.x)
                        .attr("y2", (d) => d.source.y)
                        .transition()
                        .duration(500)
                        .attr("x2", (d) => d.target.x)
                        .attr("y2", (d) => d.target.y)
            );

        // Nodes
        const nodes = root.descendants();

        // Print all x and y values of nodes
        
        g.selectAll(".node")
            .data(nodes, (d) => d.data.id)
            .join(
                (enter) =>
                    enter
                        .append("circle")
                        .attr("class", "node")
                        .attr("r", 0)
                        .attr("fill", (d) => {
                            // Define a color scale
                            const colorScale = d3.scaleLinear()
                                .domain([0, 0.33, 0.66, 1]) // Dynamic domain based on length of range
                                .range(["red", "orange", "yellow", "green"]); // Output range: colors
        
                            return colorScale(d.data.similarity_score || 0); // Apply color based on similarity score
                        })
                        .attr("cx", (d) => (d.parent ? d.parent.x : d.x))
                        .attr("cy", (d) => (d.parent ? d.parent.y : d.y))
                        .on("click", (event, d) => {
                            setTooltip({
                                visible: true,
                                x: event.pageX, // Use event.pageX/Y for positioning
                                y: event.pageY,
                                node: d.data,
                            })
                        })
                        // .on("click", (event, d) => {
                        //     console.log(`Node clicked: ${d.data.id}`);
                        //     const url = `/paper/${d.data.id}`; // Construct the URL
                        //     window.open(url, "_blank"); // Open the URL in a new tab
                        // })
                        .transition()
                        .duration(500)
                        .attr("r", 100) // Increase node size
                        .attr("cx", (d) => d.x) // Update node position
                        .attr("cy", (d) => d.y)
                        
            );

        // Labels
        g.selectAll(".label")
            .data(nodes, (d) => d.data.id)
            .join(
                (enter) =>
                    enter
                        .append("text")
                        .attr("class", "label")
                        .attr("text-anchor", "middle")
                        .style("font-size", "14px") // Slightly larger font
                        .attr("x", (d) => (d.parent ? d.parent.x : d.x))
                        .attr("y", (d) => (d.parent ? d.parent.y : d.y)) // Offset labels
                        .text((d) => d.data.label)
                        .transition()
                        .duration(500)
                        .attr("x", (d) => d.x)
                        .attr("y", (d) => d.y)
            );
    }, [data]);

    return (
        <div style={{ position: "relative" }}>
            <svg ref={svgRef}>
                <g ref={gRef}></g>
            </svg>

            {tooltip.visible && (
                <Tooltip
                    x={tooltip.x}
                    y={tooltip.y}
                    node={tooltip.node}
                    onClose={() => setTooltip({ visible: false })}
                />
            )}
        </div>
    );
};

export default TreeVisualization;

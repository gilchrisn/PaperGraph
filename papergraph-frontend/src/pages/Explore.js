import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { createWebSocket } from "../utils/websocket";
import TreeVisualization from "../components/TreeVisualization";

const Explore = () => {
    const { id } = useParams(); // Get paper ID from the route

    // Root node and tree structure
    const [treeData, setTreeData] = useState({
        id: id,
        label: "Root Paper",
        similarity_score: 1.0,
        children: [],
    });

    useEffect(() => {
        // Merge new nodes and links into the tree structure
        const mergeIntoTree = (tree, newNodes, newLinks) => {
            // Flatten tree into a map for quick lookup
            const nodeMap = {};
            const flattenTree = (node) => {
                nodeMap[node.id] = node;
                if (node.children) {
                    node.children.forEach(flattenTree);
                }
            };
            flattenTree(tree);

            // Add new nodes
            newNodes.forEach((node) => {
                if (!nodeMap[node.id]) {
                    nodeMap[node.id] = { ...node, children: [] };
                }
            });

            // Establish parent-child relationships using links
            newLinks.forEach(({ source, target }) => {
                if (nodeMap[source] && nodeMap[target]) {
                    const parent = nodeMap[source];
                    const child = nodeMap[target];
                    if (!parent.children.find((c) => c.id === child.id)) {
                        parent.children.push(child);
                    }
                }
            });

            return { ...tree }; // Return updated tree
        };

        // Handle incoming WebSocket data
        const handleMessage = (data) => {
            setTreeData((prevTree) => mergeIntoTree(prevTree, data.nodes, data.links));
        };

        // Establish WebSocket connection
        const socket = createWebSocket(id, handleMessage);

        // Clean up WebSocket on component unmount
        return () => {
            socket.close();
        };
    }, [id]);

    return (
        <div>
            <h1>Exploring References for Paper: {id}</h1>
            <div id="tree-container">
                {/* Render the tree dynamically */}
                <TreeVisualization data={treeData} />
            </div>
        </div>
    );
};

export default Explore;

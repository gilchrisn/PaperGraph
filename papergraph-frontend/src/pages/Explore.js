import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { createWebSocket } from "../utils/websocket";
import TreeVisualization from "../components/TreeVisualization";
import PaperDetails from "../components/PaperDetails";

const Explore = () => {
    const { id } = useParams(); // Get paper ID from the route

    // Root node and tree structure
    const [treeData, setTreeData] = useState({
        id: id,
        label: "Root Paper",
        similarity_score: 1.0,
        children: [],
    });

    const [inputThreshold, setInputThreshold] = useState(0.7); // Input box value
    const [selectedPaper, setSelectedPaper] = useState(null); // Selected paper for details
    const [nodes, setNodes] = useState([]); // For storing all nodes
    const [similarNodes, setSimilarNodes] = useState([]); // For storing similar nodes

    const handleUpdateThreshold = () => {
        const filteredNodes = Object.values(nodes).filter(
            (node) => node.similarity_score >= inputThreshold
        );
        
        setSimilarNodes(filteredNodes);
    };

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
            setNodes(Object.values(nodeMap));

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
            handleUpdateThreshold();
        };

        // Establish WebSocket connection
        const socket = createWebSocket(id, handleMessage);

        // Clean up WebSocket on component unmount
        return () => {
            socket.close();
        };
    }, [id]);

    

    return (
        <div style={{ display: "flex", height: "100vh" }}>
            {/* Main Section: Tree Visualization and Similar Papers */}
            <div style={{ flex: 2, padding: "10px", borderRight: "1px solid #ccc" }}>
                <h1>Exploring References for Paper: {id}</h1>

                <div id="tree-container">
                    <TreeVisualization data={treeData} onNodeClick={(node) => setSelectedPaper(node)} />
                </div>

                {/* Similar Papers Section */}
                <div style={{ marginTop: "20px" }}>
                    <h3>Set Similarity Score Threshold</h3>
                    <input
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        value={inputThreshold}
                        onChange={(e) => setInputThreshold(e.target.value)}
                    />
                    <button onClick={handleUpdateThreshold}>Update Threshold</button>
                    <h2>Similar Papers</h2>
                    {similarNodes.length > 0 ? (
                        <ul>
                            {similarNodes.map((node) => (
                                <li
                                    key={node.id}
                                    style={{ cursor: "pointer", color: "blue", textDecoration: "underline" }}
                                    onClick={() => setSelectedPaper(node)}
                                >
                                    {node.label} (Score: {node.similarity_score.toFixed(2)})
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p>No nodes found with similarity score ≥ {inputThreshold}.</p>
                    )}
                </div>
            </div>

            {/* Right Section: Paper Details */}
            <div style={{ flex: 1, padding: "10px" }}>
                <h2>Paper Details</h2>
                {selectedPaper ? (
                    <PaperDetails paper={selectedPaper} />
                ) : (
                    <p>Select a paper from the list to view details.</p>
                )}
            </div>
        </div>
    );
};

export default Explore;

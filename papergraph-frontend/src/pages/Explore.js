import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { createWebSocket } from "../utils/websocket";
import TreeVisualization from "../components/TreeVisualization";
import PaperDetails from "../components/PaperDetails";

const Explore = () => {
    const { id } = useParams(); // Get paper ID from the route

    const [treeData, setTreeData] = useState({
        id: id,
        label: "Root Paper",
        similarity_score: 1.0,
        children: [],
    });
    
    const [selectedPaper, setSelectedPaper] = useState(null); // Selected paper for details
    const [nodes, setNodes] = useState([]); // For storing all nodes
    const [similarNodes, setSimilarNodes] = useState([]); // For storing similar nodes
    const [maxDepth, setMaxDepth] = useState(5); // Maximum depth to render
    const [similarityThreshold, setSimilarityThreshold] = useState(0.88); // Similarity threshold
    const [traversalType, setTraversalType] = useState("bfs"); // Traversal type
    const [loading, setLoading] = useState(false);

    const [tempMaxDepth, setTempMaxDepth] = useState(maxDepth);
    const [tempSimilarityThreshold, setTempSimilarityThreshold] = useState(similarityThreshold);   
    const [tempTraversalType, setTempTraversalType] = useState(traversalType);


    
    // Recalculate similarNodes when nodes or similarityThreshold changes
    useEffect(() => {
        const filteredNodes = nodes.filter(
            (node) => node.similarity_score >= similarityThreshold && node.id !== id
        );
        setSimilarNodes(filteredNodes);
    }, [nodes, similarityThreshold]);

    useEffect(() => {
        // Clear the tree data to force a refresh
        setTreeData({
            id: id,
            title: "Root Paper",
            similarity_score: 1.0,
            relationship_type: "baseline",
            remarks: "This is the root paper.",
            children: [],
            
        });
        
        // Merge new nodes and links into the tree structure
        const mergeIntoTree = (tree, newNodes, newLinks) => {
            const nodeMap = {};
            const flattenTree = (node) => {
                nodeMap[node.id] = node;
                if (node.children) {
                    node.children.forEach(flattenTree);
                }
            };
            flattenTree(tree);

            // Update existing nodes
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

        const handleMessage = (data) => {
            console.log("WebSocket message received:", data);
            if (data.status && data.status === "Max exploration depth reached") {
                console.log("Tree construction complete.");
                return;
            }
            setTreeData((prevTree) => mergeIntoTree(prevTree, data.nodes, data.links));
            setLoading(false);
        };

        // Establish WebSocket connection
        const socket = createWebSocket(id, handleMessage, maxDepth, similarityThreshold, traversalType);

        // Clean up WebSocket on component unmount
        return () => {
            socket.close();
        };
    }, [id, maxDepth, similarityThreshold, traversalType]);

    const handleParameterChange = () => {
        setMaxDepth(tempMaxDepth);
        setSimilarityThreshold(tempSimilarityThreshold);
        setTraversalType(tempTraversalType);
    };

    return (
        <div style={{ display: "flex", height: "100vh" }}>
            <div style={{ flex: 2, padding: "10px", borderRight: "1px solid #ccc" }}>
                <h1>Exploring References for Paper: {id}</h1>

                <div>
                    {loading && <p>Loading tree...</p>}
                </div>

                <div id="tree-container">
                <TreeVisualization 
                    key={`${id}-${similarityThreshold}-${maxDepth}`} 
                    data={treeData} 
                    onNodeClick={(node) => setSelectedPaper(node)} 
                />

                </div>

                <div style={{ marginTop: "20px" }}>
                    <h3>Set Parameters</h3>
                    <label>
                        Similarity Threshold:
                        <input
                            type="number"
                            step="0.01"
                            min="0"
                            max="1"
                            value={tempSimilarityThreshold}
                            onChange={(e) => setTempSimilarityThreshold(Number(e.target.value))}
                        />
                    </label>
                    <br />
                    <label>
                        Max Depth:
                        <input
                            type="number"
                            min="1"
                            value={tempMaxDepth}
                            onChange={(e) => setTempMaxDepth(Number(e.target.value))}
                        />
                    </label>
                    <br />
                    <label>
                        Traversal Type:
                        <select
                            value={tempTraversalType}
                            onChange={(e) => setTempTraversalType(e.target.value)}
                        >
                            <option value="bfs">Breadth-First Search</option>
                            <option value="dfs">Depth-First Search</option>
                            <option value="djikstra">Djikstra's Algorithm</option>
                        </select>
                    </label>
                    <br />
                    <button onClick={handleParameterChange}>Apply Changes</button>
                </div>

                <h2>Similar Papers</h2>
                {similarNodes.length > 0 ? (
                    <ul>
                        {similarNodes.map((node) => (
                            <li
                                key={node.id}
                                style={{ cursor: "pointer", color: "blue", textDecoration: "underline" }}
                                onClick={() => setSelectedPaper(node)}
                            >
                                {node.title} (Score: {node.similarity_score.toFixed(2)})
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p>No nodes found with similarity score ≥ {similarityThreshold}.</p>
                )}
            </div>

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

import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { createWebSocket } from "../utils/websocket";
import TreeVisualization from "../components/TreeVisualization";
import PaperDetails from "../components/PaperDetails";
import { max } from "d3";

const Explore = () => {
    const { id } = useParams(); // Paper ID from the route

    // Master graph state: always up-to-date with new data from WebSocket
    const [graph, setGraph] = useState({ nodes: [], links: [] });

    const [selectedPaper, setSelectedPaper] = useState(null);
    const [similarNodes, setSimilarNodes] = useState([]);
    const [maxDepth, setMaxDepth] = useState(5);
    const [similarityThreshold, setSimilarityThreshold] = useState(0.88);
    const [traversalType, setTraversalType] = useState("bfs");

    // Temp states for the form
    const [tempMaxDepth, setTempMaxDepth] = useState(maxDepth);
    const [tempSimilarityThreshold, setTempSimilarityThreshold] = useState(similarityThreshold);
    const [tempTraversalType, setTempTraversalType] = useState(traversalType);

    // Recalculate similarNodes whenever graph or similarityThreshold changes
    useEffect(() => {
        // We only consider nodes that meet threshold
        const filteredAndSorted = graph.nodes
            .filter((n) => n.similarity_score >= similarityThreshold && n.id !== id)
            .sort((a, b) => b.similarity_score - a.similarity_score);
        setSimilarNodes(filteredAndSorted);
    }, [graph, similarityThreshold, id]);

    // On mount (or when parameters change), open WebSocket
    useEffect(() => {
        setGraph({ nodes: [], links: [] }); // Clear the graph

        const handleMessage = (data) => {

            if (data.status === "Max exploration depth reached") {
                console.log("Tree construction complete.");
                return;
            }

            // Merge incoming data into our master `graph`
            setGraph((prevGraph) => {
                // Merge nodes
                const existingNodeIds = new Set(prevGraph.nodes.map((n) => n.id));
                const newNodes = data.nodes.filter((n) => !existingNodeIds.has(n.id));
                const mergedNodes = [...prevGraph.nodes, ...newNodes];

                // Merge links
                const existingLinks = new Set(
                    prevGraph.links.map((l) => `${l.source}-${l.target}`)
                );
                const newLinks = data.links.filter(
                    (l) => !existingLinks.has(`${l.source}-${l.target}`)
                );
                const mergedLinks = [...prevGraph.links, ...newLinks];

                return { nodes: mergedNodes, links: mergedLinks };
            });
        };

        const socket = createWebSocket(
            id,
            handleMessage,
            maxDepth,
            similarityThreshold,
            traversalType
        );

        socket.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        // Clean up when component unmounts
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
            {/* Left Section */}
            <div
                style={{
                    flex: 3,
                    padding: "10px",
                    borderRight: "1px solid #ccc",
                    overflowY: "auto",
                }}
            >
                <h1>Exploring References for Paper: {id}</h1>

                <div id="tree-container" style={{ marginBottom: "20px" }}>
                    {/* Pass the entire merged graph to TreeVisualization */}
                    <TreeVisualization
                        graph={graph}
                        rootId={id} // We'll treat the current paper as the tree's root
                        onNodeClick={(node) => setSelectedPaper(node)}
                        id={similarityThreshold + traversalType + maxDepth}
                    />
                </div>

                {/* Parameter Controls */}
                <div style={{ marginBottom: "20px" }}>
                    <h3>Set Parameters</h3>
                    <label>
                        Similarity Threshold:
                        <input
                            type="number"
                            step="0.01"
                            min="0"
                            max="1"
                            value={tempSimilarityThreshold}
                            onChange={(e) => setTempSimilarityThreshold(+e.target.value)}
                        />
                    </label>
                    <br />
                    <label>
                        Max Depth:
                        <input
                            type="number"
                            min="1"
                            value={tempMaxDepth}
                            onChange={(e) => setTempMaxDepth(+e.target.value)}
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
                            <option value="priority">Dijkstra's Algorithm</option>
                        </select>
                    </label>
                    <br />
                    <button onClick={handleParameterChange}>Apply Changes</button>
                </div>

                {/* Similar Papers List */}
                <h2>Similar Papers</h2>
                {similarNodes.length > 0 ? (
                    <ol>
                        {similarNodes.map((node) => (
                            <li
                                key={node.id}
                                style={{
                                    cursor: "pointer",
                                    color: "blue",
                                    textDecoration: "underline",
                                }}
                                onClick={() => setSelectedPaper(node)}
                            >
                                {node.title} (Score: {node.similarity_score.toFixed(2)})
                            </li>
                        ))}
                    </ol>
                ) : (
                    <p>
                        No nodes found with similarity ≥ {similarityThreshold}.
                    </p>
                )}
            </div>

            {/* Right Section: Paper Details */}
            <div style={{ flex: 1, padding: "10px", overflowY: "auto" }}>
                <h2>Paper Details</h2>
                {selectedPaper ? (
                    <PaperDetails paper={selectedPaper} />
                ) : (
                    <p>Select a paper from the list or tree to view details.</p>
                )}
            </div>
        </div>
    );
};

export default Explore;

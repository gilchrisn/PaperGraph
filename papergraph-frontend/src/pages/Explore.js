import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { createWebSocket } from "../utils/websocket";
import PaperDetails from "../components/PaperDetails";
import TreeVisualization from "../components/TreeVisualization"; // <-- Changed
import PropTypes from "prop-types";

/**
 * EXPLORE PAPER COMPONENT
 * Main component for exploring paper relationships
 * Implements Nielsen's heuristics through:
 * - Clear system status (loading/errors)
 * - Match between system and real world (natural language)
 * - Consistency and standards
 * - Error prevention
 */
const ExplorePaper = () => {
  const { id: paperId } = useParams(); // Get paper ID from URL

  // Main graph state
  const [graph, setGraph] = useState({ nodes: [], links: [] });
  const [graphPhases, setGraphPhases] = useState({
    downward: { nodes: [], links: [] },
    upward: { nodes: [], links: [] }
  });

  // UI States
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [similarNodes, setSimilarNodes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Exploration Parameters
  const [params, setParams] = useState({
    maxDepth: 5,
    similarityThreshold: 0.88,
    traversalType: "bfs"
  });

  // Temporary form state
  const [draftParams, setDraftParams] = useState({ ...params });

  // Update similar papers when graph or threshold changes
  useEffect(() => {
    const threshold = params.similarityThreshold;
    const filtered = graph.nodes.filter(
      (node) => node.similarity_score >= threshold && node.id !== paperId
    );
    setSimilarNodes(filtered.sort((a, b) => b.similarity_score - a.similarity_score));
  }, [graph, params.similarityThreshold, paperId]);

  // WebSocket management
  useEffect(() => {
    setIsLoading(true);
    setError(null);
    setGraph({ nodes: [], links: [] });
    setGraphPhases({
      downward: { nodes: [], links: [] },
      upward: { nodes: [], links: [] }
    });

    const handleWebSocketMessage = (data) => {
      // Handle system messages
      if (data.status) {
        if (data.status === "error") {
          setError(data.message);
          setIsLoading(false);
        }
        return;
      }

      // Handle graph updates
      if (data.phase && data.nodes && data.links) {
        setGraphPhases((prev) => ({
          ...prev,
          [data.phase]: {
            nodes: [...prev[data.phase].nodes, ...data.nodes],
            links: [...prev[data.phase].links, ...data.links]
          }
        }));

        // Merge all phases for full visualization
        setGraph((prevGraph) => {
            // 1) Deduplicate nodes
            const existingNodeIds = new Set(prevGraph.nodes.map((n) => n.id));
            const dedupedNewNodes = data.nodes.filter((n) => !existingNodeIds.has(n.id));
            const mergedNodes = [...prevGraph.nodes, ...dedupedNewNodes];
          
            // 2) Deduplicate links
            // For links, a good “unique” signature is `${source}-${target}` or similar
            const existingLinks = new Set(
              prevGraph.links.map((l) => `${l.source}-${l.target}`)
            );
            const dedupedNewLinks = data.links.filter(
              (l) => !existingLinks.has(`${l.source}-${l.target}`)
            );
            const mergedLinks = [...prevGraph.links, ...dedupedNewLinks];
          
            return { nodes: mergedNodes, links: mergedLinks };
          });
      }
    };

    // Initialize WebSocket connection
    const socket = createWebSocket(
      paperId,
      handleWebSocketMessage,
      params.maxDepth,
      params.similarityThreshold,
      params.traversalType
    );

    socket.onopen = () => setIsLoading(false);
    socket.onerror = (err) => {
      setError("Connection failed. Please try again.");
      setIsLoading(false);
    };

    return () => socket.close();
  }, [paperId, params]);

  // Handle parameter changes with validation
  const handleParamChange = (field, value) => {
    let processedValue = value;

    if (field === "similarityThreshold") {
      processedValue = Math.min(1, Math.max(0, Number(value)));
    }

    setDraftParams((prev) => ({ ...prev, [field]: processedValue }));
  };

  const applyNewParams = () => {
    if (draftParams.similarityThreshold > 1 || draftParams.similarityThreshold < 0) {
      setError("Similarity must be between 0 and 1");
      return;
    }
    setParams({ ...draftParams });
  };

  // RENDERING
  return (
    <div className="explore-container">
      {/* Loading/Error Overlay */}
      {isLoading && <div className="status-banner">Loading paper network...</div>}
      {error && <div className="status-banner error">{error}</div>}

      <div className="content-wrapper">
        {/* Visualization Panel */}
        <section className="visualization-panel">
          <h1>Exploring Connections for Paper: {paperId}</h1>

          <TreeVisualization
            graph={graph}
            rootId={paperId}
            onNodeClick={setSelectedPaper}
            downwardData={graphPhases.downward}
            upwardData={graphPhases.upward}
            width={800}
            height={600}
          />

          {/* Parameter Controls */}
          <div className="parameter-controls">
            <h2>Exploration Settings</h2>
            <div className="input-group">
              <label>
                Similarity Threshold (0-1):
                <input
                  type="number"
                  step="0.01"
                  value={draftParams.similarityThreshold}
                  onChange={(e) => handleParamChange("similarityThreshold", e.target.value)}
                  min="0"
                  max="1"
                />
              </label>
            </div>

            <div className="input-group">
              <label>
                Search Depth:
                <input
                  type="number"
                  value={draftParams.maxDepth}
                  onChange={(e) => handleParamChange("maxDepth", e.target.value)}
                  min="1"
                  max="10"
                />
              </label>
            </div>

            <div className="input-group">
              <label>
                Exploration Method:
                <select
                  value={draftParams.traversalType}
                  onChange={(e) => handleParamChange("traversalType", e.target.value)}
                >
                  <option value="bfs">Breadth-First Search</option>
                  <option value="dfs">Depth-First Search</option>
                  <option value="priority">Priority (Similarity)</option>
                </select>
              </label>
            </div>

            <button onClick={applyNewParams} disabled={isLoading}>
              {isLoading ? "Applying..." : "Update Exploration"}
            </button>
          </div>
        </section>

        {/* Similar Papers List */}
        <section className="similar-papers">
          <h2>Highly Similar Papers</h2>
          {similarNodes.length > 0 ? (
            <ul className="paper-list">
              {similarNodes.map((node) => (
                <li
                  key={node.id}
                  onClick={() => setSelectedPaper(node)}
                  className="paper-item"
                >
                  <span className="paper-title">{node.title}</span>
                  <span className="similarity-score">
                    {node.similarity_score.toFixed(2)}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-state">
              No papers meet the similarity threshold ({params.similarityThreshold})
            </p>
          )}
        </section>

        {/* Paper Details Sidebar */}
        <section className="details-sidebar">
          <h2>Paper Details</h2>
          {selectedPaper ? (
            <PaperDetails paper={selectedPaper} />
          ) : (
            <p className="instruction">
              ← Select a paper from the graph or list to view details
            </p>
          )}
        </section>
      </div>
    </div>
  );
};

ExplorePaper.propTypes = {};

export default ExplorePaper;

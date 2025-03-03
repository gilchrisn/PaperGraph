import React from "react";
import "./RemarksOverlay.css"; // Custom CSS for the overlay

const RemarksOverlay = ({ remarks, onClose }) => {
  // Safely parse the remarks JSON
  let remarksData = {};
  try {
    remarksData = JSON.parse(remarks) || {};
  } catch (error) {
    console.error("Invalid JSON in remarks:", error);
  }

  // Extract the criteria for table display
  const criteriaEntries = remarksData.criteria ? Object.entries(remarksData.criteria) : [];

  return (
    <div className="overlay">
      <div className="overlay-content">
        <button className="close-btn" onClick={onClose}>
          Close
        </button>

        <h2>Remarks Details</h2>

        {/* If we have criteria data, show the table, otherwise show a fallback. */}
        {criteriaEntries.length > 0 ? (
          <table
            border="1"
            style={{ width: "100%", borderCollapse: "collapse" }}
          >
            <thead>
              <tr>
                <th>Criterion</th>
                <th>Source Paper</th>
                <th>Cited Paper</th>
                <th>Relevance Score</th>
                <th>Explanation</th>
              </tr>
            </thead>
            <tbody>
              {criteriaEntries.map(([criterionKey, details]) => (
                <tr key={criterionKey}>
                  <td>{criterionKey.replace(/_/g, " ")}</td>
                  <td>{details.source_paper || "N/A"}</td>
                  <td>{details.cited_paper || "N/A"}</td>
                  <td>{details.relevance_score}</td>
                  <td>{details.explanation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No detailed criteria found.</p>
        )}

        {/* Relationship Type */}
        <p>
          <strong>Relationship Type:</strong>{" "}
          {remarksData.relationship_type || "N/A"}
        </p>

        {/* Similarity Score */}
        <p>
          <strong>Similarity Score:</strong>{" "}
          {remarksData.similarity_score !== undefined
            ? remarksData.similarity_score.toFixed(2)
            : "N/A"}
        </p>

        {/* Conclusion */}
        <p>
          <strong>Conclusion:</strong> {remarksData.conclusion || "N/A"}
        </p>
      </div>
    </div>
  );
};

export default RemarksOverlay;

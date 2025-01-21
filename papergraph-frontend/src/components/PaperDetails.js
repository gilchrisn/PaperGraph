import React, { useState } from "react";
import RemarksOverlay from "./RemarksOverlay.js"; // Import the overlay component

const PaperDetails = ({ paper }) => {
    const [showRemarks, setShowRemarks] = useState(false);

    return (
        <div>
            <h3>{paper.title}</h3>
            <p>
                <strong>ID:</strong> {paper.id}
            </p>
            <p>
                <strong>Similarity Score:</strong> {paper.similarity_score.toFixed(2)}
            </p>
            <p>
                <strong>Relationship Type:</strong> {paper.relationship_type}
            </p>
            <button
                onClick={() => setShowRemarks(true)}
                style={{ marginTop: "10px" }}
            >
                View Remarks
            </button>
            <button
                onClick={() => window.open(`/papers/${paper.id}`, "_blank")}
                style={{ marginTop: "10px" }}
            >
                Open Paper Page
            </button>

            {/* Show remarks as an overlay */}
            {showRemarks && (
                <RemarksOverlay
                    remarks={paper.remarks} // Pass remarks to the overlay
                    onClose={() => setShowRemarks(false)} // Close overlay handler
                />
            )}
        </div>
    );
};

export default PaperDetails;

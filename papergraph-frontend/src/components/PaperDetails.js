import React from "react";

const PaperDetails = ({ paper }) => {
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
                <strong>relationship_type: {paper.relationship_type}</strong>
            </p>
            <p>
                <strong>remarks:</strong> {paper.remarks}
            </p>
            <button
                onClick={() => window.open(`/papers/${paper.id}`, "_blank")}
                style={{ marginTop: "10px" }}
            >
                Open Paper Page
            </button>
        </div>
    );
};

export default PaperDetails;

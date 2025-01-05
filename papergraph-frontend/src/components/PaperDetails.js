import React from "react";

const PaperDetails = ({ paper }) => {
    return (
        <div>
            <h3>{paper.label}</h3>
            <p>
                <strong>ID:</strong> {paper.id}
            </p>
            <p>
                <strong>Similarity Score:</strong> {paper.similarity_score.toFixed(2)}
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

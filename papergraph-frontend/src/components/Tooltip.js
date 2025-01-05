import React from "react";

const Tooltip = ({ x, y, node, onClose }) => {
    if (!node) return null; // Render nothing if no node data is provided

    return (
        <div
            style={{
                position: "absolute",
                top: y,
                left: x,
                backgroundColor: "white",
                border: "1px solid black",
                padding: "10px",
                borderRadius: "5px",
                zIndex: 10,
            }}
        >
            <p><strong>ID:</strong> {node.id}</p>
            <p><strong>Similarity Score:</strong> {node.similarity_score}</p>
            <button
                style={{
                    padding: "5px 10px",
                    cursor: "pointer",
                    backgroundColor: "#69b3a2",
                    color: "white",
                    border: "none",
                    borderRadius: "3px",
                }}
                onClick={() => window.open(`/paper/${node.id}`, "_blank")}
            >
                Go to Node Page
            </button>
            <button
                style={{
                    marginLeft: "5px",
                    padding: "5px 10px",
                    cursor: "pointer",
                    backgroundColor: "red",
                    color: "white",
                    border: "none",
                    borderRadius: "3px",
                }}
                onClick={onClose}
            >
                Close
            </button>
        </div>
    );
};

export default Tooltip;

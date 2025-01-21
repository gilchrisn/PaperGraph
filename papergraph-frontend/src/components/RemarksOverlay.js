// import React from "react";
// import "./RemarksOverlay.css"; // Custom CSS for the overlay

// const RemarksOverlay = ({ remarks, onClose }) => {
//     const remarksData = JSON.parse(remarks || "{}"); // Parse remarks JSON

//     return (
//         <div className="overlay">
//             <div className="overlay-content">
//                 <button className="close-btn" onClick={onClose}>
//                     Close
//                 </button>
//                 <h2>Remarks Details</h2>
//                 <table border="1" style={{ width: "100%", borderCollapse: "collapse" }}>
//                     <thead>
//                         <tr>
//                             <th>Criterion</th>
//                             <th>Source Paper</th>
//                             <th>Cited Paper</th>
//                             <th>Relevance Score</th>
//                             <th>Explanation</th>
//                         </tr>
//                     </thead>
//                     <tbody>
//                         {Object.entries(remarksData.criteria || {}).map(([criterion, details]) => (
//                             <tr key={criterion}>
//                                 <td>{criterion.replace(/_/g, " ")}</td>
//                                 <td>{details.source_paper}</td>
//                                 <td>{details.cited_paper}</td>
//                                 <td>{details.relevance_score}</td>
//                                 <td>{details.explanation}</td>
//                             </tr>
//                         ))}
//                     </tbody>
//                 </table>
//                 <p>
//                     <strong>Relationship Type:</strong> {remarksData.relationship_type}
//                 </p>
//                 <p>
//                     <strong>Similarity Score:</strong> {remarksData.similarity_score.toFixed(2)}
//                 </p>
//                 <p>
//                     <strong>Conclusion:</strong> {remarksData.conclusion}
//                 </p>
//             </div>
//         </div>
//     );
// };

// export default RemarksOverlay;

import React, { useState } from "react";
import "./RemarksOverlay.css"; // Custom CSS for the overlay

const RemarksOverlay = ({ onClose }) => {
    const [hoveredText, setHoveredText] = useState(""); // Text to display
    const [hoverStyle, setHoverStyle] = useState({}); // Style for the hover box

    // Dummy remarks data for testing
    const dummyRemarks = JSON.stringify({
        criteria: {
            problem_alignment: {
                source_paper: "Paper A discusses the challenges of X in Y domain.",
                cited_paper: "Paper B explores X in a similar Y domain.",
                relevance_score: 3,
                explanation: "Both papers address the same challenges, indicating strong alignment."
            },
            methodological_overlap: {
                source_paper: "Paper A uses a neural network for task Z.",
                cited_paper: "Paper B also implements a neural network with enhancements for task Z.",
                relevance_score: 3,
                explanation: "There is a strong overlap in methodology with some differences."
            },
            dataset_experimental_overlap: {
                source_paper: "Paper A evaluates on dataset Q.",
                cited_paper: "Paper B uses dataset Q and introduces additional benchmarks.",
                relevance_score: 2,
                explanation: "There is moderate overlap in experimental setup with some extensions in Paper B."
            }
        },
        relationship_type: "baseline",
        similarity_score: 0.85,
        conclusion: "Paper B is a strong candidate as a baseline for Paper A due to significant methodological overlap and problem alignment."
    });

    const remarksData = JSON.parse(dummyRemarks);

    const handleMouseEnter = (text, event) => {
        const rect = event.target.getBoundingClientRect();
        setHoveredText(text);
        setHoverStyle({
            top: rect.top + window.scrollY + rect.height + 5 + "px", // Position below the cell
            left: rect.left + "px", // Align with the left of the cell
            width: rect.width + "px" // Match the width of the cell
        });
    };

    const handleMouseLeave = () => {
        setHoveredText("");
    };

    return (
        <div className="overlay">
            <div className="overlay-content">
                <button className="close-btn" onClick={onClose}>
                    Close
                </button>
                <h2>Remarks Details</h2>
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
                        {Object.entries(remarksData.criteria || {}).map(
                            ([criterion, details]) => (
                                <tr key={criterion}>
                                    <td
                                        onMouseEnter={(e) =>
                                            handleMouseEnter(
                                                criterion.replace(/_/g, " "),
                                                e
                                            )
                                        }
                                        onMouseLeave={handleMouseLeave}
                                    >
                                        {criterion.replace(/_/g, " ")}
                                    </td>
                                    <td
                                        onMouseEnter={(e) =>
                                            handleMouseEnter(
                                                details.source_paper,
                                                e
                                            )
                                        }
                                        onMouseLeave={handleMouseLeave}
                                    >
                                        {details.source_paper}
                                    </td>
                                    <td
                                        onMouseEnter={(e) =>
                                            handleMouseEnter(
                                                details.cited_paper,
                                                e
                                            )
                                        }
                                        onMouseLeave={handleMouseLeave}
                                    >
                                        {details.cited_paper}
                                    </td>
                                    <td
                                        onMouseEnter={(e) =>
                                            handleMouseEnter(
                                                `Score: ${details.relevance_score}`,
                                                e
                                            )
                                        }
                                        onMouseLeave={handleMouseLeave}
                                    >
                                        {details.relevance_score}
                                    </td>
                                    <td
                                        onMouseEnter={(e) =>
                                            handleMouseEnter(
                                                details.explanation,
                                                e
                                            )
                                        }
                                        onMouseLeave={handleMouseLeave}
                                    >
                                        {details.explanation}
                                    </td>
                                </tr>
                            )
                        )}
                    </tbody>
                </table>
                {hoveredText && (
                    <div className="hover-text-box" style={hoverStyle}>
                        {hoveredText}
                    </div>
                )}
                <p>
                    <strong>Relationship Type:</strong> {remarksData.relationship_type}
                </p>
                <p>
                    <strong>Similarity Score:</strong>{" "}
                    {remarksData.similarity_score.toFixed(2)}
                </p>
                <p>
                    <strong>Conclusion:</strong> {remarksData.conclusion}
                </p>
            </div>
        </div>
    );
};

export default RemarksOverlay;

import React from "react";
import { useNavigate } from "react-router-dom";

const PaperCard = ({ paper }) => {
    const navigate = useNavigate();

    return (
        <div className="paper-card">
            <h3>{paper.title}</h3>
            <p>{paper.abstract.slice(0, 100)}...</p>
            <button onClick={() => navigate(`/papers/${paper.id}`)}>
                View Details
            </button>
        </div>
    );
};

export default PaperCard;

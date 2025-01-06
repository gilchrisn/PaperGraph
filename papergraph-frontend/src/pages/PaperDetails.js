import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { searchPaperById } from "../api";
import { useNavigate } from "react-router-dom";

const PaperDetails = () => {
    const { id } = useParams();
    const [paper, setPaper] = useState(null);

    useEffect(() => {
        searchPaperById(id)
            .then((data) => setPaper(data.paper))
            .catch((err) => console.error("Error fetching paper:", err));
    }, [id]);
    
    const navigate = useNavigate();

    const handleExplore = () => {
        // Redirect the user to the exploration page
        navigate(`/papers/${id}/explore`);
    };

    if (!paper) return <div>Loading...</div>;

    return (
        <div>
            <h1>{paper.title}</h1>
            <p><strong>Authors:</strong> {paper.authors.join(", ")}</p>
            <a
                href={`http://localhost:8000/papers/${encodeURIComponent(paper.id)}/pdf`}
                target="_blank"
                rel="noopener noreferrer"
            >
                <button>Open PDF</button>
            </a>
            <button onClick={handleExplore}>Explore References</button>
        </div>
    );
};

export default PaperDetails;

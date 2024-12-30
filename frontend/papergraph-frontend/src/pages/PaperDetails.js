import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { searchPaperById, exploreReferences } from "../api";

const PaperDetails = () => {
    const { id } = useParams();
    const [paper, setPaper] = useState(null);

    useEffect(() => {
        searchPaperById(id)
            .then((data) => setPaper(data.paper))
            .catch((err) => console.error("Error fetching paper:", err));
    }, [id]);
    
    const handleExplore = () => {
        exploreReferences(id).then((res) => {
            console.log("Exploration result:", res.data);
        });
    };

    if (!paper) return <div>Loading...</div>;

    return (
        <div>
            <h1>{paper.title}</h1>
            <p><strong>Abstract:</strong> {paper.abstract}</p>
            <p><strong>Authors:</strong> {paper.authors.join(", ")}</p>
            <a href={paper.filepath} target="_blank" rel="noopener noreferrer">
                <button>Open PDF</button>
            </a>
            <button onClick={handleExplore}>Explore References</button>
        </div>
    );
};

export default PaperDetails;

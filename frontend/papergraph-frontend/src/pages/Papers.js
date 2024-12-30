import { fetchAllPapers } from "../api";
import React, { useState, useEffect } from "react";
import PaperCard from "../components/PaperCard";

const Papers = () => {
    const [papers, setPapers] = useState([]);

    useEffect(() => {
        fetchAllPapers()
            .then((data) => setPapers(data.papers)) // `data.papers` is directly available
            .catch((err) => console.error("Error fetching papers:", err.message));
    }, []);

    return (
        <div>
            <h2>All Papers</h2>
            {papers.map((paper) => (
                <PaperCard key={paper.id} paper={paper} />
            ))}
        </div>
    );
};

export default Papers;
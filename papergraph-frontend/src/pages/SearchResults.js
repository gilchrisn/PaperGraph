// src/components/SearchResults.jsx

import React, { useState, useEffect } from "react";
import { useLocation, Link } from "react-router-dom";
import { searchPaperByTitle } from "../api";

const SearchResults = () => {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const location = useLocation();
  // Extract the 'title' query parameter from the URL
  const queryParams = new URLSearchParams(location.search);
  const title = queryParams.get("title");

  useEffect(() => {
    const fetchPapers = async () => {
      try {
        setLoading(true);
        setError("");
        // Call the backend API to search papers by title
        const result = await searchPaperByTitle(title);
        console.log("API Response:", result);
        if (!result.papers || result.papers.length === 0) {
          setError(`No papers found for title "${title}"`);
        } else {
          setPapers(result.papers);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (title) {
      fetchPapers();
    } else {
      setError("No title provided.");
      setLoading(false);
    }
  }, [title]);

  return (
    <div className="container mt-5">
      <h1>Search Results for "{title}"</h1>
      {loading && <p>Loading...</p>}
      {error && <div className="alert alert-danger">{error}</div>}
      {!loading && papers.length > 0 && (
        <ul className="list-group">
          {papers.map((paper) => (
            <li key={paper.semantic_id} className="list-group-item">
              {/* Link to PaperDetails using the paper's semantic_id */}
              <Link to={`/papers/${paper.paperId}`}>
                <strong>{paper.title}</strong>
              </Link>
              {paper.year && <span> ({paper.year})</span>}
              {paper.venue && <span> - {paper.venue}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SearchResults;

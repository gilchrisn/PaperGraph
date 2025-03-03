// src/components/SearchBox.jsx

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const SearchBox = () => {
  const [title, setTitle] = useState("");
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    // Navigate to the search results page with the title as a query parameter
    navigate(`/search?title=${encodeURIComponent(title)}`);
  };

  return (
    <div className="search-box container mt-5">
      <h3>Search Paper by Title</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="paperTitle">Paper Title:</label>
          <input
            type="text"
            id="paperTitle"
            className="form-control"
            placeholder="Enter paper title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="btn btn-primary mt-2">
          Search
        </button>
      </form>
    </div>
  );
};

export default SearchBox;

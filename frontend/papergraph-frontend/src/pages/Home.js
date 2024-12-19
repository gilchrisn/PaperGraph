import React from "react";
import { useNavigate } from "react-router-dom";

const Home = () => {
    const navigate = useNavigate();

    return (
        <div className="home-container">
            <h1>Welcome to Paper Explorer</h1>
            <p>Find and analyze research papers effortlessly.</p>
            <button onClick={() => navigate("/papers")}>Get Started</button>
        </div>
    );
};

export default Home;

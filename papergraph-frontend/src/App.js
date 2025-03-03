import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Papers from "./pages/Papers";
import PaperDetails from "./pages/PaperDetails";
import Explore from "./pages/Explore";
import SearchResults from "./pages/SearchResults";

function App() {
    return (
        <Router>  
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/papers" element={<Papers />} />
                <Route path="/papers/:id" element={<PaperDetails />} />
                <Route path="/papers/:id/explore" element={<Explore />} />
                <Route path="/search" element={<SearchResults />} />
            </Routes>
        </Router>
    );
}

export default App;

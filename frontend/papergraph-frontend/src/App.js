import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Papers from "./pages/Papers";
import PaperDetails from "./pages/PaperDetails";

function App() {
    return (
        <Router>  
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/papers" element={<Papers />} />
                <Route path="/papers/:id" element={<PaperDetails />} />
            </Routes>
        </Router>
    );
}

export default App;

import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000"; // Backend URL

// Helper function for consistent error handling
const apiRequest = async (method, url, params = {}, data = {}) => {
    try {
        const response = await axios({
            method,
            url: `${API_BASE_URL}${url}`,
            params,
            data,
        });
        return response.data; // Return the response data directly
    } catch (error) {
        console.error(`API Request Failed: ${method.toUpperCase()} ${url}`, error.message);
        throw error; // Re-throw the error for handling in components
    }
};

// Fetch all papers
export const fetchAllPapers = async () => {
    return apiRequest("GET", "/papers/");
};

// Fetch a single paper by ID
export const searchPaperById = async (id) => {
    return apiRequest("GET", `/papers/${id}/`);
};

// Search for a paper by title
export const searchPaperByTitle = async (title) => {
    return apiRequest("GET", "/papers/search/", { title });
};

// Explore references for a given paper ID
export const exploreReferences = async (paperId) => {
    return apiRequest("GET", `/papers/${paperId}/explore/`);
};

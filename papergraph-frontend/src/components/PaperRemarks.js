import React from "react";

const PaperRemarks = ({ location }) => {
    // Dummy data for testing purposes
    const dummyRemarks = JSON.stringify({
        criteria: {
            problem_alignment: {
                source_paper: "Paper A discusses the challenges of X in Y domain.",
                cited_paper: "Paper B explores X in a similar Y domain.",
                relevance_score: 3,
                explanation: "Both papers address the same challenges, indicating strong alignment."
            },
            methodological_overlap: {
                source_paper: "Paper A uses a neural network for task Z.",
                cited_paper: "Paper B also implements a neural network with enhancements for task Z.",
                relevance_score: 3,
                explanation: "There is a strong overlap in methodology with some differences."
            },
            dataset_experimental_overlap: {
                source_paper: "Paper A evaluates on dataset Q.",
                cited_paper: "Paper B uses dataset Q and introduces additional benchmarks.",
                relevance_score: 2,
                explanation: "There is moderate overlap in experimental setup with some extensions in Paper B."
            },
            performance_metrics_comparability: {
                source_paper: "Paper A reports F1 scores and precision.",
                cited_paper: "Paper B reports F1 scores, precision, and recall.",
                relevance_score: 2,
                explanation: "Metrics are comparable but not identical."
            },
            novelty_claims: {
                source_paper: "Paper A introduces a new architecture for task Z.",
                cited_paper: "Paper B proposes improvements to existing architectures, including Paper A's.",
                relevance_score: 3,
                explanation: "Paper B builds on and critiques Paper A's contributions."
            },
            references_citation_network: {
                source_paper: "Paper A cites foundational works in Y.",
                cited_paper: "Paper B cites similar works but adds additional key references.",
                relevance_score: 2,
                explanation: "There is some overlap in citations but Paper B broadens the scope."
            },
            temporal_context: {
                source_paper: "Published in 2022.",
                cited_paper: "Published in 2021.",
                relevance_score: 3,
                explanation: "Paper B predates Paper A, making it feasible to be a baseline."
            }
        },
        relationship_type: "baseline",
        similarity_score: 0.85,
        conclusion: "Paper B is a strong candidate as a baseline for Paper A due to significant methodological overlap and problem alignment."
    });

    // Simulate location.state.remarks with dummy data
    const remarksData = JSON.parse(dummyRemarks);

    return (
        <div>
            <h2>Remarks Details</h2>
            <table border="1" style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                    <tr>
                        <th>Criterion</th>
                        <th>Source Paper</th>
                        <th>Cited Paper</th>
                        <th>Relevance Score</th>
                        <th>Explanation</th>
                    </tr>
                </thead>
                <tbody>
                    {Object.entries(remarksData.criteria || {}).map(([criterion, details]) => (
                        <tr key={criterion}>
                            <td>{criterion.replace(/_/g, " ")}</td>
                            <td>{details.source_paper}</td>
                            <td>{details.cited_paper}</td>
                            <td>{details.relevance_score}</td>
                            <td>{details.explanation}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
            <p>
                <strong>Relationship Type:</strong> {remarksData.relationship_type}
            </p>
            <p>
                <strong>Similarity Score:</strong> {remarksData.similarity_score.toFixed(2)}
            </p>
            <p>
                <strong>Conclusion:</strong> {remarksData.conclusion}
            </p>
        </div>
    );
};

export default PaperRemarks;

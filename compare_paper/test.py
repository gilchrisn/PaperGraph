from paper_embedding import create_paper_metrics, generate_paper_embeddings, generate_combined_embedding
from similarity_computation import compute_similarity, compute_overall_similarity
from sklearn.metrics.pairwise import cosine_similarity

paper_1_metrics = {
    "problem": "Simulates the formation and evolution of galaxies in the early universe.",
    "methods": "Uses smoothed particle hydrodynamics (SPH) combined with adaptive mesh refinement for high-resolution galaxy simulations.",
    "applications": "Astrophysics research, cosmic evolution studies, and understanding dark matter distribution.",
    "datasets": "Cosmological datasets generated from observations like the Sloan Digital Sky Survey (SDSS).",
    "results": "Produces highly accurate models of galaxy formation that align with real-world observational data.",
    "citations/references": "References key astrophysics works such as the Lambda-CDM model and prior SPH simulation techniques.",
    "key_contributions": "Introduces a hybrid SPH-mesh refinement model for galaxy simulations at unprecedented resolution.",
    "assumptions": "Assumes standard cosmological parameters and initial conditions for dark matter distribution.",
    "evaluation_metrics": "Measures galaxy clustering, stellar distribution, and alignment with observed large-scale structures.",
    "theoretical_vs_practical": "Primarily theoretical with practical implications for astrophysics modeling.",
    "baselines": "Compares against prior cosmological simulation frameworks like Gadget and Ramses.",
    "domain": "Astrophysics"
}

paper_2_metrics = {
    "problem": "Analyzes the impact of progressive taxation policies on income inequality in developing countries.",
    "methods": "Uses a dynamic stochastic general equilibrium (DSGE) model to simulate policy effects over time.",
    "applications": "Economic policy evaluation, poverty reduction strategies, and fiscal planning.",
    "datasets": "Socioeconomic datasets collected from World Bank and IMF reports.",
    "results": "Shows that progressive taxation can reduce inequality without significantly affecting economic growth.",
    "citations/references": "References economic modeling frameworks such as DSGE and studies on inequality by Piketty and others.",
    "key_contributions": "Introduces a novel parameterization of labor elasticity to better model developing economies.",
    "assumptions": "Assumes steady-state conditions and a closed economy for the simulation period.",
    "evaluation_metrics": "Measures income inequality (Gini coefficient), GDP growth, and government revenue over time.",
    "theoretical_vs_practical": "Balances theoretical modeling with practical policy recommendations.",
    "baselines": "Compares against flat taxation models and prior inequality-focused DSGE implementations.",
    "domain": "Economics"
}

if __name__ == '__main__':
    # Ensure the local model path is used in paper_embedding.py
    print("Generating embeddings...")
    embeddings_paper_1 = generate_paper_embeddings(paper_1_metrics)
    embeddings_paper_2 = generate_paper_embeddings(paper_2_metrics)

    # Compute similarity scores
    print("Computing similarity...")
    similarity_scores = compute_similarity(embeddings_paper_1, embeddings_paper_2)

    # Define weights for metrics (if desired)
    metric_weights = {
        "problem": 2.0,
        "methods": 2.0,
        "applications": 1.5,
        "datasets": 1.0,
        "results": 2.0,
        "citations/references": 1.0,
        "key_contributions": 1.5,
        "assumptions": 1.0,
        "evaluation_metrics": 1.5,
        "theoretical_vs_practical": 1.0,
        "baselines": 1.0
    }

    # Compute overall similarity
    overall_similarity = compute_overall_similarity(similarity_scores, metric_weights)

    # Display results
    print("Similarity Scores by Metric:")
    for metric, score in similarity_scores.items():
        print(f"{metric}: {score:.2f}")
    print(f"\nOverall Similarity: {overall_similarity:.2f}")
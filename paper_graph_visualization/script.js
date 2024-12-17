// Example data for the tree
const treeData = {
    id: "root",
    title: "Root Paper",
    similarity_score: 1.0,
    children: [
        {
            id: "child_1",
            title: "Child Paper 1",
            similarity_score: 0.8,
            children: []
        },
        {
            id: "child_2",
            title: "Child Paper 2",
            similarity_score: 0.5,
            children: []
        }
    ]
};

// Set up the SVG canvas
const svgWidth = 1000;
const svgHeight = 800;
const margin = { top: 20, right: 90, bottom: 30, left: 90 };
const width = svgWidth - margin.left - margin.right;
const height = svgHeight - margin.top - margin.bottom;

const svg = d3.select("svg")
    .attr("width", svgWidth)
    .attr("height", svgHeight);

const g = svg.append("g")
    .attr("transform", `translate(${margin.left}, ${margin.top})`);

// Create a tree layout
const treeLayout = d3.tree().size([height, width]);

// Generate the hierarchical data
const root = d3.hierarchy(treeData);
treeLayout(root);

// Add links
const links = g.selectAll(".link")
    .data(root.links())
    .enter()
    .append("path")
    .attr("class", "link")
    .attr("d", d3.linkHorizontal()
        .x(d => d.y)
        .y(d => d.x))
    .attr("stroke", d => d.target.data.similarity_score >= 0.8 ? "green"
        : d.target.data.similarity_score >= 0.5 ? "orange" : "gray");

// Add nodes
const nodes = g.selectAll(".node")
    .data(root.descendants())
    .enter()
    .append("g")
    .attr("class", "node")
    .attr("transform", d => `translate(${d.y}, ${d.x})`);

nodes.append("circle")
    .attr("r", 5)
    .attr("fill", d => d.data.similarity_score >= 0.8 ? "green"
        : d.data.similarity_score >= 0.5 ? "orange" : "gray");

nodes.append("text")
    .attr("dx", 10)
    .attr("dy", 3)
    .text(d => d.data.title);

// Add click event to display metadata
nodes.on("click", (event, d) => {
    alert(`Title: ${d.data.title}\nSimilarity: ${d.data.similarity_score}`);
});

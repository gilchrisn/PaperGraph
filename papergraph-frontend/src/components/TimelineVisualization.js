import React from "react";
import PropTypes from "prop-types";
import "./TimelineVisualization.css"; // optional: for styling

const TimelineVisualization = ({ nodes, onNodeClick }) => {
  // Sort nodes by year (assumes each node has a numeric "year" property)
  const sortedNodes = [...nodes].sort((a, b) => a.year - b.year);

  return (
    <div className="timeline-container">
      {sortedNodes.map((node) => (
        <div
          key={node.id}
          className="timeline-node"
          onClick={() => onNodeClick(node)}
          title={`${node.title} (${node.year})`}
        >
          <div className="timeline-node-circle" />
          <div className="timeline-node-label">
            {node.title} ({node.year})
          </div>
        </div>
      ))}
    </div>
  );
};

TimelineVisualization.propTypes = {
  nodes: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string,
      year: PropTypes.number,
    })
  ).isRequired,
  onNodeClick: PropTypes.func.isRequired,
};

export default TimelineVisualization;

import React from 'react';
import styles from '../../styles/DataVisualization.module.css';

export interface StatCardProps {
  title: string;
  value: string | number;
  type?: 'users' | 'success' | 'activity' | 'contacts';
  data?: any;
  history?: {
    labels: string[];
    values: number[];
  };
}

interface DataVisualizationProps {
  stats: StatCardProps[];
}

// Activity updates component
const ActivityUpdates: React.FC<{ data?: { updates: { text: string, time: string }[] } }> = ({ data = { updates: [] } }) => {
  return (
    <ul className={styles.activityList}>
      {data.updates.map((update, index) => (
        <li key={index} className={styles.activityItem}>
          {update.text}
          <div className={styles.activityTime}>{update.time}</div>
        </li>
      ))}
    </ul>
  );
};

// Updated LineGraph component with black line and adjusted scaling
const LineGraph: React.FC<{ history: { labels: string[], values: number[] } }> = ({ history }) => {
  // We know the last value is the highest since users always grow
  const maxValue = history.values[history.values.length - 1];
  // Set minimum to 0 or slightly lower than the lowest value for better visualization
  const minValue = 0;
  const range = maxValue - minValue;
  
  // Calculate points for the line graph
  const points = history.values.map((value, index) => {
    // X position based on index (evenly spaced)
    const x = (index / (history.values.length - 1)) * 100;
    // Y position (inverted because SVG coordinates)
    // Scale to use only the lower half of the available space (50%)
    const y = 100 - ((value - minValue) / (range || 1)) * 50;
    return { x, y, value };
  });
  
  // Generate SVG path string for the line
  const pathD = points.map((point, i) => 
    `${i === 0 ? 'M' : 'L'} ${point.x} ${point.y}`
  ).join(' ');
  
  return (
    <div className={styles.lineGraphContainer}>
      <svg className={styles.svgGraph} viewBox="0 0 100 100" preserveAspectRatio="none">
        {/* Draw the line */}
        <path 
          d={pathD} 
          className={styles.graphLine}
          fill="none"
        />
        
        {/* Draw points on the line */}
        {points.map((point, i) => (
          <circle 
            key={i}
            cx={point.x} 
            cy={point.y} 
            r="1.5" 
            className={styles.graphPoint}
          />
        ))}
      </svg>
      
      {/* X-axis labels */}
      <div className={styles.graphLabels}>
        {history.labels.map((label, index) => (
          <div 
            key={index} 
            className={styles.graphLabel}
            style={{ left: `${(index / (history.labels.length - 1)) * 100}%` }}
          >
            {label}
          </div>
        ))}
      </div>
    </div>
  );
};

const StatCard: React.FC<StatCardProps> = ({ 
  title, 
  value, 
  type = 'users',
  data,
  history
}) => {
  return (
    <div className={`${styles.statCard} ${styles[type]}`}>
      <div className={styles.statHeader}>
        <h3 className={styles.statTitle}>{title}</h3>
      </div>
      
      {(type === 'users' || type === 'success' || type === 'contacts') && (
        <div className={styles.statValue}>{value}</div>
      )}
      
      {type === 'activity' && <ActivityUpdates data={data} />}
    </div>
  );
};

const DataVisualization: React.FC<DataVisualizationProps> = ({ stats = [] }) => {
  // Find stat by type or return default
  const getStatByType = (type: string): StatCardProps => {
    const found = stats.find(stat => stat.type === type);
    return found || { title: type, value: '0', type: type as any };
  };

  return (
    <div className={styles.visualizationContainer}>
      <div className={styles.newLayout}>
        <div className={styles.leftColumn}>
          <div className={styles.usersCard}>
            <StatCard {...getStatByType('users')} />
          </div>
          <div className={styles.successCard}>
            <StatCard {...getStatByType('success')} />
          </div>
        </div>
        <div className={styles.rightColumn}>
          <div className={styles.activityCard}>
            <StatCard {...getStatByType('activity')} />
          </div>
        </div>
        <div className={styles.bottomRow}>
          <div className={styles.contactsCard}>
            <StatCard {...getStatByType('contacts')} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataVisualization;

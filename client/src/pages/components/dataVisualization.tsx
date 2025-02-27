import React from 'react';
import styles from '../../styles/DataVisualization.module.css';

export interface StatCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  type?: 'default' | 'graph' | 'activity' | 'languages';
  size?: 'small' | 'medium' | 'large' | 'tall' | 'wide';
  data?: any;
}

interface DataVisualizationProps {
  stats: StatCardProps[];
}

// Generate user network growth graph
const UserNetworkGraph: React.FC<{ data?: { values: number[], target: number } }> = ({ data = { values: [], target: 100 } }) => {
  return (
    <div className={styles.graph}>
      {data.values.map((value, index) => (
        <div 
          key={index} 
          className={styles.graphBar} 
          style={{
            height: `${(value / data.target) * 100}%`,
            left: `${(index / Math.max(data.values.length - 1, 1)) * 100}%`,
            opacity: 0.7 + (index / Math.max(data.values.length - 1, 1)) * 0.3
          }}
        />
      ))}
      <div className={styles.graphLabels}>
        <span>0</span>
        <span>{data.target}</span>
      </div>
    </div>
  );
};

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

// Programming languages chart
const LanguagesChart: React.FC<{ data?: { languages: { name: string, value: number }[] } }> = ({ data = { languages: [] } }) => {
  // Find maximum value for percentage calculation
  const maxValue = data.languages.length ? Math.max(...data.languages.map(lang => lang.value)) : 1;
  
  return (
    <div>
      {data.languages.map((language, index) => (
        <div key={index} className={styles.languageBar}>
          <div className={styles.languageName}>{language.name}</div>
          <div 
            className={styles.languageValue} 
            style={{ width: `${(language.value / maxValue) * 100}%` }}
          />
          <div className={styles.languagePercent}>{language.value}</div>
        </div>
      ))}
    </div>
  );
};

const StatCard: React.FC<StatCardProps> = ({ 
  title, 
  value, 
  icon, 
  trend, 
  trendValue, 
  type = 'default',
  size = 'small',
  data 
}) => {
  return (
    <div className={`${styles.statCard} ${styles[size]}`}>
      <div className={styles.statHeader}>
        <h3 className={styles.statTitle}>{title}</h3>
        {icon && <div className={styles.statIcon}>{icon}</div>}
      </div>
      
      {type === 'default' && (
        <>
          <div className={styles.statValue}>{value}</div>
        </>
      )}
      
      {type === 'graph' && <UserNetworkGraph data={data} />}
      {type === 'activity' && <ActivityUpdates data={data} />}
      {type === 'languages' && <LanguagesChart data={data} />}
    </div>
  );
};

const DataVisualization: React.FC<DataVisualizationProps> = ({ stats = [] }) => {
  return (
    <div className={styles.visualizationContainer}>
      <div className={styles.gridWrapper}>
        <div className={styles.statsGrid}>
          {stats.map((stat, index) => (
            <StatCard key={index} {...stat} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default DataVisualization;

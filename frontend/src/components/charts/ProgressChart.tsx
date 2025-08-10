import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface ProgressData {
  date: string;
  progress: number;
  milestone?: string;
}

interface ProgressChartProps {
  data: ProgressData[];
  title?: string;
  projectName?: string;
}

export const ProgressChart: React.FC<ProgressChartProps> = ({
  data,
  title = "Project Progress Over Time",
  projectName = "Project"
}) => {
  const chartData = {
    labels: data.map(item => new Date(item.date)),
    datasets: [
      {
        label: `${projectName} Progress`,
        data: data.map(item => item.progress),
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#3B82F6',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: title,
        font: {
          size: 16,
          weight: 'bold' as const,
        },
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const dataPoint = data[context.dataIndex];
            let label = `Progress: ${context.parsed.y}%`;
            if (dataPoint.milestone) {
              label += `\nMilestone: ${dataPoint.milestone}`;
            }
            return label;
          },
          title: function(context: any) {
            const date = new Date(context[0].label);
            return date.toLocaleDateString('en-ZA', {
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            });
          }
        },
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: 'month' as const,
          displayFormats: {
            month: 'MMM yyyy'
          }
        },
        title: {
          display: true,
          text: 'Timeline',
          font: {
            weight: 'bold' as const,
          },
        },
      },
      y: {
        beginAtZero: true,
        max: 100,
        title: {
          display: true,
          text: 'Progress (%)',
          font: {
            weight: 'bold' as const,
          },
        },
        ticks: {
          callback: function(value: any) {
            return value + '%';
          }
        }
      },
    },
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
  };

  return (
    <div className="w-full">
      <div className="h-80">
        <Line data={chartData} options={options} />
      </div>
      
      {/* Progress milestones */}
      <div className="mt-6">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Key Milestones</h4>
        <div className="space-y-2">
          {data.filter(item => item.milestone).map((item, index) => (
            <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                <span className="text-sm text-gray-800">{item.milestone}</span>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-blue-600">{item.progress}%</div>
                <div className="text-xs text-gray-500">
                  {new Date(item.date).toLocaleDateString('en-ZA')}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

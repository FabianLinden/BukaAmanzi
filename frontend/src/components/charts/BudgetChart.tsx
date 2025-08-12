import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface BudgetData {
  allocated: number;
  spent: number;
  remaining: number;
}

interface BudgetChartProps {
  data: BudgetData;
  title?: string;
  type?: 'bar' | 'doughnut';
  currency?: string;
}

export const BudgetChart: React.FC<BudgetChartProps> = ({ 
  data, 
  title = "Project Budget", 
  type = 'doughnut',
  currency = 'ZAR' 
}) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatCompactCurrency = (amount: number) => {
    // Ensure we're working with a valid number
    const validAmount = Number(amount) || 0;
    
    if (validAmount >= 1000000000) {
      return `R${(validAmount / 1000000000).toFixed(1)}B`;
    } else if (validAmount >= 1000000) {
      return `R${(validAmount / 1000000).toFixed(1)}M`;
    } else if (validAmount >= 1000) {
      return `R${(validAmount / 1000).toFixed(1)}K`;
    }
    return formatCurrency(validAmount);
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
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
            const label = context.label || '';
            const value = context.parsed || context.raw;
            return `${label}: ${formatCurrency(value)}`;
          }
        }
      }
    },
  };

  if (type === 'doughnut') {
    const doughnutData = {
      labels: ['Spent', 'Remaining'],
      datasets: [
        {
          data: [data.spent, data.remaining],
          backgroundColor: [
            '#EF4444', // Red for spent
            '#10B981', // Green for remaining
          ],
          borderColor: [
            '#DC2626',
            '#059669',
          ],
          borderWidth: 2,
        },
      ],
    };

    return (
      <div className="w-full h-full">
        <div className="h-64">
          <Doughnut data={doughnutData} options={chartOptions} />
        </div>
        <div className="mt-4 grid grid-cols-3 gap-4 text-center">
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="text-sm text-blue-600 font-medium">Allocated</div>
            <div className="text-lg font-bold text-blue-800">
              {formatCompactCurrency(data.allocated)}
            </div>
          </div>
          <div className="bg-red-50 p-3 rounded-lg">
            <div className="text-sm text-red-600 font-medium">Spent</div>
            <div className="text-lg font-bold text-red-800">
              {formatCompactCurrency(data.spent)}
            </div>
          </div>
          <div className="bg-green-50 p-3 rounded-lg">
            <div className="text-sm text-green-600 font-medium">Remaining</div>
            <div className="text-lg font-bold text-green-800">
              {formatCompactCurrency(data.remaining)}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Bar chart version
  const barData = {
    labels: ['Budget'],
    datasets: [
      {
        label: 'Allocated',
        data: [data.allocated],
        backgroundColor: '#3B82F6',
        borderColor: '#2563EB',
        borderWidth: 1,
      },
      {
        label: 'Spent',
        data: [data.spent],
        backgroundColor: '#EF4444',
        borderColor: '#DC2626',
        borderWidth: 1,
      },
    ],
  };

  const barOptions = {
    ...chartOptions,
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value: any) {
            return formatCompactCurrency(value);
          }
        }
      }
    },
  };

  return (
    <div className="w-full h-64">
      <Bar data={barData} options={barOptions} />
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { ProgressBar } from './ui/ProgressBar';

interface Budget {
  id: string;
  project_id: string;
  budget_type: 'allocated' | 'revised' | 'spent';
  amount: number;
  currency: string;
  financial_year: string;
  quarter?: number;
  source: string;
  created_at: string;
}

interface BudgetSummary {
  project_id: string;
  financial_year?: string;
  budget_allocated: number;
  budget_revised: number;
  budget_final: number;
  amount_spent: number;
  amount_remaining: number;
  spent_percentage: number;
  budget_records: number;
}

interface Props {
  projectId?: string;
  showCreateForm?: boolean;
  onBudgetCreated?: (budget: Budget) => void;
}

export const BudgetManagement: React.FC<Props> = ({ 
  projectId, 
  showCreateForm = false,
  onBudgetCreated 
}) => {
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [budgetSummary, setBudgetSummary] = useState<BudgetSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFinancialYear, setSelectedFinancialYear] = useState<string>('');
  const [filters, setFilters] = useState({
    budget_type: '',
    financial_year: '',
    quarter: ''
  });

  // Create budget form state
  const [showForm, setShowForm] = useState(showCreateForm);
  const [formData, setFormData] = useState({
    project_id: projectId || '',
    budget_type: 'allocated' as Budget['budget_type'],
    amount: '',
    currency: 'ZAR',
    financial_year: '2024/2025',
    quarter: '',
    source: 'manual_entry'
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchBudgets = async () => {
    try {
      const params = new URLSearchParams();
      if (projectId) params.append('project_id', projectId);
      if (filters.budget_type) params.append('budget_type', filters.budget_type);
      if (filters.financial_year) params.append('financial_year', filters.financial_year);
      if (filters.quarter) params.append('quarter', filters.quarter);
      
      const response = await fetch(`/api/v1/budgets?${params}`);
      if (!response.ok) throw new Error('Failed to fetch budgets');
      const data = await response.json();
      setBudgets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const fetchBudgetSummary = async () => {
    if (!projectId) return;
    
    try {
      const params = new URLSearchParams();
      if (selectedFinancialYear) params.append('financial_year', selectedFinancialYear);
      
      const response = await fetch(`/api/v1/budgets/project/${projectId}/summary?${params}`);
      if (!response.ok) {
        if (response.status === 404) {
          setBudgetSummary(null);
          return;
        }
        throw new Error('Failed to fetch budget summary');
      }
      const data = await response.json();
      setBudgetSummary(data);
    } catch (err) {
      console.error('Error fetching budget summary:', err);
      setBudgetSummary(null);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchBudgets(), fetchBudgetSummary()]);
      setLoading(false);
    };

    loadData();
  }, [projectId, filters, selectedFinancialYear]);

  const handleCreateBudget = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const response = await fetch('/api/v1/budgets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          amount: parseFloat(formData.amount),
          quarter: formData.quarter ? parseInt(formData.quarter) : null
        }),
      });

      if (!response.ok) throw new Error('Failed to create budget');
      
      const newBudget = await response.json();
      await fetchBudgets();
      await fetchBudgetSummary();
      
      if (onBudgetCreated) onBudgetCreated(newBudget);
      
      // Reset form
      setFormData({
        project_id: projectId || '',
        budget_type: 'allocated',
        amount: '',
        currency: 'ZAR',
        financial_year: '2024/2025',
        quarter: '',
        source: 'manual_entry'
      });
      setShowForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setSubmitting(false);
    }
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 1e9) {
      return `R${(amount / 1e9).toFixed(1)}B`;
    } else if (amount >= 1e6) {
      return `R${(amount / 1e6).toFixed(1)}M`;
    } else {
      return `R${amount.toLocaleString()}`;
    }
  };

  const getBudgetTypeColor = (type: string) => {
    switch (type) {
      case 'allocated': return 'bg-blue-100 text-blue-800';
      case 'revised': return 'bg-yellow-100 text-yellow-800';
      case 'spent': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Budget Summary */}
      {budgetSummary && (
        <Card>
          <div className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Budget Summary</h3>
              <select
                value={selectedFinancialYear}
                onChange={(e) => setSelectedFinancialYear(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">All Years</option>
                <option value="2024/2025">2024/2025</option>
                <option value="2023/2024">2023/2024</option>
                <option value="2022/2023">2022/2023</option>
              </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {formatCurrency(budgetSummary.budget_final)}
                </div>
                <div className="text-sm text-blue-600">Final Budget</div>
                {budgetSummary.budget_revised > 0 && (
                  <div className="text-xs text-gray-600">
                    (Revised from {formatCurrency(budgetSummary.budget_allocated)})
                  </div>
                )}
              </div>

              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {formatCurrency(budgetSummary.amount_spent)}
                </div>
                <div className="text-sm text-green-600">Amount Spent</div>
                <div className="text-xs text-gray-600">
                  {budgetSummary.spent_percentage.toFixed(1)}% of budget
                </div>
              </div>

              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">
                  {formatCurrency(budgetSummary.amount_remaining)}
                </div>
                <div className="text-sm text-orange-600">Remaining</div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-gray-600">
                  {budgetSummary.budget_records}
                </div>
                <div className="text-sm text-gray-600">Budget Records</div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Budget Utilization</span>
                <span>{budgetSummary.spent_percentage.toFixed(1)}%</span>
              </div>
              <ProgressBar progress={budgetSummary.spent_percentage} className="h-3" />
            </div>
          </div>
        </Card>
      )}

      {/* Filters and Controls */}
      <Card>
        <div className="p-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <h3 className="text-lg font-semibold">Budget Records</h3>
            
            <div className="flex flex-wrap gap-3">
              {/* Filters */}
              <select
                value={filters.budget_type}
                onChange={(e) => setFilters({...filters, budget_type: e.target.value})}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option value="">All Types</option>
                <option value="allocated">Allocated</option>
                <option value="revised">Revised</option>
                <option value="spent">Spent</option>
              </select>

              <select
                value={filters.financial_year}
                onChange={(e) => setFilters({...filters, financial_year: e.target.value})}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option value="">All Years</option>
                <option value="2024/2025">2024/2025</option>
                <option value="2023/2024">2023/2024</option>
                <option value="2022/2023">2022/2023</option>
              </select>

              <Button
                onClick={() => setShowForm(!showForm)}
                variant="primary"
                size="sm"
              >
                {showForm ? 'Cancel' : 'Add Budget'}
              </Button>
            </div>
          </div>

          {/* Create Budget Form */}
          {showForm && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium mb-3">Add Budget Record</h4>
              <form onSubmit={handleCreateBudget} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Budget Type
                  </label>
                  <select
                    value={formData.budget_type}
                    onChange={(e) => setFormData({...formData, budget_type: e.target.value as Budget['budget_type']})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                  >
                    <option value="allocated">Allocated</option>
                    <option value="revised">Revised</option>
                    <option value="spent">Spent</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Amount
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.amount}
                    onChange={(e) => setFormData({...formData, amount: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="0.00"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Financial Year
                  </label>
                  <select
                    value={formData.financial_year}
                    onChange={(e) => setFormData({...formData, financial_year: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="2024/2025">2024/2025</option>
                    <option value="2023/2024">2023/2024</option>
                    <option value="2022/2023">2022/2023</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Quarter (Optional)
                  </label>
                  <select
                    value={formData.quarter}
                    onChange={(e) => setFormData({...formData, quarter: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">All Quarters</option>
                    <option value="1">Q1</option>
                    <option value="2">Q2</option>
                    <option value="3">Q3</option>
                    <option value="4">Q4</option>
                  </select>
                </div>

                <div className="lg:col-span-4 flex justify-end gap-2">
                  <Button
                    type="button"
                    onClick={() => setShowForm(false)}
                    variant="secondary"
                    size="sm"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={submitting}
                    variant="primary"
                    size="sm"
                  >
                    {submitting ? 'Creating...' : 'Create Budget'}
                  </Button>
                </div>
              </form>
            </div>
          )}

          {/* Budget Records */}
          <div className="mt-6">
            {budgets.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-lg mb-2">No budget records found</div>
                <div className="text-sm">Add a budget record to get started</div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Amount
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Financial Year
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quarter
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Source
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {budgets.map((budget) => (
                      <tr key={budget.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getBudgetTypeColor(budget.budget_type)}`}>
                            {budget.budget_type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {formatCurrency(budget.amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {budget.financial_year}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {budget.quarter ? `Q${budget.quarter}` : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {budget.source}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(budget.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};

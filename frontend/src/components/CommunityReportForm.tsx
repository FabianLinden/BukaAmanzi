import React, { useState } from 'react';
import { Button } from './ui/Button';

interface CommunityReportFormProps {
  projectId: string;
  projectName: string;
  onSubmit: (reportData: ReportFormData) => Promise<void>;
  onCancel: () => void;
  isOpen: boolean;
}

interface ReportFormData {
  projectId: string;
  title: string;
  description: string;
  reportType: string;
  location?: string;
  address?: string;
  contributorName?: string;
  contributor?: {
    name?: string;
    email?: string;
    organization?: string;
  };
  photos?: string[];
}

const reportTypes = [
  { value: 'progress_update', label: 'Progress Update', description: 'Share updates on project progress' },
  { value: 'issue', label: 'Report Issue', description: 'Report problems or concerns' },
  { value: 'completion', label: 'Completion Report', description: 'Report project completion' },
  { value: 'quality_concern', label: 'Quality Concern', description: 'Report quality issues' },
];

export const CommunityReportForm: React.FC<CommunityReportFormProps> = ({
  projectId,
  projectName,
  onSubmit,
  onCancel,
  isOpen
}) => {
  const [formData, setFormData] = useState<ReportFormData>({
    projectId,
    title: '',
    description: '',
    reportType: 'progress_update',
    location: '',
    address: '',
    contributorName: '',
    contributor: {
      name: '',
      email: '',
      organization: ''
    },
    photos: []
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [includeContact, setIncludeContact] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (formData.description.trim().length < 20) {
      newErrors.description = 'Description must be at least 20 characters long';
    }

    if (includeContact) {
      if (!formData.contributor?.email?.trim()) {
        newErrors.email = 'Email is required when providing contact information';
      } else if (!/\S+@\S+\.\S+/.test(formData.contributor.email)) {
        newErrors.email = 'Please enter a valid email address';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      const reportData = {
        ...formData,
        contributor: includeContact ? formData.contributor : undefined
      };
      
      await onSubmit(reportData);
      
      // Reset form
      setFormData({
        projectId,
        title: '',
        description: '',
        reportType: 'progress_update',
        location: '',
        address: '',
        contributorName: '',
        contributor: {
          name: '',
          email: '',
          organization: ''
        },
        photos: []
      });
      setIncludeContact(false);
      setErrors({});
    } catch (error) {
      console.error('Failed to submit report:', error);
      setErrors({ submit: 'Failed to submit report. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof ReportFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleContributorChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      contributor: {
        ...prev.contributor,
        [field]: value
      }
    }));
    
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Submit Community Report</h2>
              <p className="text-gray-600 mt-1">Share your observations about: {projectName}</p>
            </div>
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              disabled={isSubmitting}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Report Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">Report Type</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {reportTypes.map((type) => (
                  <label
                    key={type.value}
                    className={`
                      relative flex cursor-pointer rounded-lg border p-4 focus:outline-none
                      ${formData.reportType === type.value 
                        ? 'border-blue-600 ring-2 ring-blue-600 bg-blue-50' 
                        : 'border-gray-300 hover:border-gray-400'
                      }
                    `}
                  >
                    <input
                      type="radio"
                      name="reportType"
                      value={type.value}
                      className="sr-only"
                      checked={formData.reportType === type.value}
                      onChange={(e) => handleInputChange('reportType', e.target.value)}
                    />
                    <div className="flex flex-col">
                      <div className={`text-sm font-medium ${
                        formData.reportType === type.value ? 'text-blue-900' : 'text-gray-900'
                      }`}>
                        {type.label}
                      </div>
                      <div className={`text-sm ${
                        formData.reportType === type.value ? 'text-blue-700' : 'text-gray-500'
                      }`}>
                        {type.description}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                Report Title *
              </label>
              <input
                type="text"
                id="title"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                className={`
                  w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:border-transparent
                  ${errors.title ? 'border-red-300 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}
                `}
                placeholder="Brief, descriptive title for your report"
                disabled={isSubmitting}
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600">{errors.title}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                Description *
              </label>
              <textarea
                id="description"
                rows={4}
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                className={`
                  w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:border-transparent
                  ${errors.description ? 'border-red-300 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}
                `}
                placeholder="Provide detailed information about your observation or concern (minimum 20 characters)"
                disabled={isSubmitting}
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600">{errors.description}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                {formData.description.length}/20 characters minimum
              </p>
            </div>

            {/* Location */}
            <div>
              <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-2">
                Specific Location (Optional)
              </label>
              <input
                type="text"
                id="address"
                value={formData.address || ''}
                onChange={(e) => handleInputChange('address', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Specific address or location details"
                disabled={isSubmitting}
              />
            </div>

            {/* Contributor Name (always shown) */}
            <div>
              <label htmlFor="contributorName" className="block text-sm font-medium text-gray-700 mb-2">
                Your Name (Optional - for attribution)
              </label>
              <input
                type="text"
                id="contributorName"
                value={formData.contributorName || ''}
                onChange={(e) => handleInputChange('contributorName', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="How you'd like to be credited in the report"
                disabled={isSubmitting}
              />
            </div>

            {/* Contact Information Toggle */}
            <div className="border-t border-gray-200 pt-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeContact}
                  onChange={(e) => setIncludeContact(e.target.checked)}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  disabled={isSubmitting}
                />
                <span className="ml-2 text-sm text-gray-700">
                  Include contact information for follow-up (optional)
                </span>
              </label>
            </div>

            {/* Contact Information (conditional) */}
            {includeContact && (
              <div className="bg-gray-50 p-4 rounded-lg space-y-4">
                <h4 className="text-sm font-medium text-gray-900">Contact Information</h4>
                
                <div>
                  <label htmlFor="contactName" className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    id="contactName"
                    value={formData.contributor?.name || ''}
                    onChange={(e) => handleContributorChange('name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Your full name"
                    disabled={isSubmitting}
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address *
                  </label>
                  <input
                    type="email"
                    id="email"
                    value={formData.contributor?.email || ''}
                    onChange={(e) => handleContributorChange('email', e.target.value)}
                    className={`
                      w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:border-transparent
                      ${errors.email ? 'border-red-300 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}
                    `}
                    placeholder="your.email@example.com"
                    disabled={isSubmitting}
                  />
                  {errors.email && (
                    <p className="mt-1 text-sm text-red-600">{errors.email}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="organization" className="block text-sm font-medium text-gray-700 mb-2">
                    Organization (Optional)
                  </label>
                  <input
                    type="text"
                    id="organization"
                    value={formData.contributor?.organization || ''}
                    onChange={(e) => handleContributorChange('organization', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Your organization or affiliation"
                    disabled={isSubmitting}
                  />
                </div>
              </div>
            )}

            {/* Error Display */}
            {errors.submit && (
              <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded">
                {errors.submit}
              </div>
            )}

            {/* Form Actions */}
            <div className="flex items-center justify-end space-x-4 pt-6 border-t border-gray-200">
              <Button
                type="button"
                variant="secondary"
                onClick={onCancel}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Submitting...
                  </>
                ) : (
                  'Submit Report'
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

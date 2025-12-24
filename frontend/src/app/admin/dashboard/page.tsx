'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface AdminStats {
  total_categories: number;
  total_indicators: number;
  total_data_points: number;
  categories: string[];
  indicators: Array<{
    id: number;
    name: string;
    slug: string;
    category: string;
    data_points: number;
    date_range: string | null;
  }>;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [showCreateNew, setShowCreateNew] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [selectedIndicator, setSelectedIndicator] = useState('');
  const [selectedIndicatorSeries, setSelectedIndicatorSeries] = useState<Array<{series_type: string, label: string}>>([]);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSeriesType, setUploadSeriesType] = useState('historical');
  const [customUploadSeriesType, setCustomUploadSeriesType] = useState('');
  const [isNewSeries, setIsNewSeries] = useState(true);
  const [editingIndicator, setEditingIndicator] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  
  // New indicator form
  const [newIndicator, setNewIndicator] = useState({
    name: '',
    slug: '',
    category: 'market-indexes',
    description: '',
    unit: 'Index',
    frequency: 'daily',
  });
  
  // Multiple file uploads for new indicator
  const [fileUploads, setFileUploads] = useState<Array<{
    file: File | null;
    series_type: string;
    custom_series_type: string;
  }>>([
    { file: null, series_type: 'historical', custom_series_type: '' }
  ]);
  
  // Edit indicator form
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    unit: '',
    frequency: 'daily',
    source: ''
  });
  
  const router = useRouter();

  const getToken = () => localStorage.getItem('admin_token');

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    const token = getToken();
    if (!token) {
      router.push('/admin');
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/stats?admin_token=${token}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        router.push('/admin');
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadIndicatorSeries = async (slug: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/indicators/${slug}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setSelectedIndicatorSeries(data.series || []);
      }
    } catch (error) {
      console.error('Error loading indicator series:', error);
      setSelectedIndicatorSeries([]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!selectedIndicator) {
      setUploadStatus('❌ Please select an indicator first');
      return;
    }
    
    if (!uploadFile) {
      setUploadStatus('❌ Please select a CSV file to upload');
      return;
    }
    
    if (isNewSeries && uploadSeriesType === 'other' && !customUploadSeriesType.trim()) {
      setUploadStatus('❌ Please provide a custom series type name');
      return;
    }

    const token = getToken();
    const formData = new FormData();
    formData.append('file', uploadFile);
    const seriesTypeToUpload = (isNewSeries && uploadSeriesType === 'other') ? customUploadSeriesType : uploadSeriesType;
    formData.append('series_type', seriesTypeToUpload);
    formData.append('admin_token', token || '');

    setIsUploading(true);
    setUploadStatus(isNewSeries ? '⏳ Adding new series...' : '⏳ Updating series data...');

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/upload-csv/${selectedIndicator}`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (response.ok) {
        const result = await response.json();
        if (isNewSeries) {
          setUploadStatus(`✅ Success! Added new series with ${result.added} data points`);
        } else {
          setUploadStatus(`✅ Success! Updated series: Added ${result.added}, Updated ${result.updated} data points`);
        }
        loadStats(); // Reload stats
        loadIndicatorSeries(selectedIndicator); // Reload series list
        
        // Redirect to indicator page after 1.5 seconds
        setTimeout(() => {
          router.push(`/indicator/${selectedIndicator}`);
        }, 1500);
      } else {
        const error = await response.json();
        setUploadStatus(`❌ Error: ${error.detail}`);
      }
    } catch (error) {
      setUploadStatus('❌ Error uploading file');
    } finally {
      setIsUploading(false);
    }
  };

  const handleCreateNew = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Form submitted');
    console.log('fileUploads:', fileUploads);
    console.log('newIndicator:', newIndicator);
    
    // Validate at least one file is uploaded
    const validUploads = fileUploads.filter(u => u.file !== null);
    console.log('validUploads count:', validUploads.length);
    
    if (validUploads.length === 0) {
      setUploadStatus('❌ Please select at least one CSV file');
      return;
    }
    
    if (!newIndicator.name || !newIndicator.slug) {
      setUploadStatus('❌ Please fill in indicator name and slug');
      return;
    }

    // Validate custom series types are filled in
    for (const upload of validUploads) {
      if (upload.series_type === 'other' && !upload.custom_series_type.trim()) {
        setUploadStatus('❌ Please provide a custom series type name for all "Other" selections');
        return;
      }
    }

    const token = getToken();
    if (!token) {
      setUploadStatus('❌ Admin token not found. Please log in again.');
      return;
    }
    
    setIsUploading(true);
    setUploadStatus('⏳ Creating indicator...');

    try {
      // Step 1: Create indicator with first file
      const firstUpload = validUploads[0];
      const formData = new FormData();
      formData.append('file', firstUpload.file!);
      formData.append('name', newIndicator.name);
      formData.append('slug', newIndicator.slug);
      formData.append('category_slug', newIndicator.category);
      formData.append('description', newIndicator.description);
      formData.append('unit', newIndicator.unit);
      formData.append('frequency', newIndicator.frequency);
      const firstSeriesType = firstUpload.series_type === 'other' ? firstUpload.custom_series_type : firstUpload.series_type;
      formData.append('series_type', firstSeriesType);
      formData.append('admin_token', token || '');

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/create-indicator-from-csv`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        const error = await response.json();
        console.error('Error creating indicator:', error);
        const errorMsg = error.detail || 'Unknown error occurred';
        if (errorMsg.includes('already exists')) {
          setUploadStatus(`❌ Error: Slug "${newIndicator.slug}" is already in use. Please choose a different slug.`);
        } else {
          setUploadStatus(`❌ Error: ${errorMsg}`);
        }
        return;
      }

      const result = await response.json();
      let totalAdded = result.data_added;

      // Step 2: Upload additional files if any
      if (validUploads.length > 1) {
        setUploadStatus(`⏳ Created indicator. Uploading ${validUploads.length - 1} additional series...`);
        for (let i = 1; i < validUploads.length; i++) {
          const upload = validUploads[i];
          const additionalFormData = new FormData();
          additionalFormData.append('file', upload.file!);
          const seriesType = upload.series_type === 'other' ? upload.custom_series_type : upload.series_type;
          additionalFormData.append('series_type', seriesType);
          additionalFormData.append('admin_token', token || '');

          console.log(`Uploading additional file ${i}: ${upload.file!.name} with series type: ${seriesType}`);

          const additionalResponse = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/upload-csv/${newIndicator.slug}`,
            {
              method: 'POST',
              body: additionalFormData,
            }
          );

          if (additionalResponse.ok) {
            const additionalResult = await additionalResponse.json();
            totalAdded += additionalResult.added;
            console.log(`Added ${additionalResult.added} data points from file ${i}`);
          } else {
            const error = await additionalResponse.json();
            console.error(`Error uploading file ${i}:`, error);
          }
        }
      }

      setUploadStatus(`✅ Success! Created "${result.indicator.name}" with ${validUploads.length} series and ${totalAdded} total data points`);
      loadStats(); // Reload stats
      setTimeout(() => {
        setShowCreateNew(false);
        setUploadStatus('');
        setFileUploads([{ file: null, series_type: 'historical', custom_series_type: '' }]);
        setNewIndicator({
          name: '',
          slug: '',
          category: 'market-indexes',
          description: '',
          unit: 'Index',
          frequency: 'daily',
        });
      }, 3000);
    } catch (error) {
      console.error('Error creating indicator:', error);
      setUploadStatus(`❌ Error creating indicator: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (slug: string, name: string) => {
    const token = getToken();
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/indicators/${slug}?admin_token=${token}`,
        { method: 'DELETE' }
      );
      
      if (response.ok) {
        setUploadStatus(`✅ Successfully deleted "${name}"`);
        setDeleteConfirm(null);
        setShowDelete(false);
        loadStats();
        setTimeout(() => setUploadStatus(''), 3000);
      } else {
        const error = await response.json();
        setUploadStatus(`❌ Error: ${error.detail}`);
      }
    } catch (error) {
      setUploadStatus('❌ Error deleting indicator');
    }
  };

  const handleEdit = async (slug: string) => {
    const token = getToken();
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/indicators/${slug}?admin_token=${token}&name=${encodeURIComponent(editForm.name)}&description=${encodeURIComponent(editForm.description)}&unit=${encodeURIComponent(editForm.unit)}&frequency=${editForm.frequency}&source=${encodeURIComponent(editForm.source)}`,
        { method: 'PUT' }
      );
      
      if (response.ok) {
        setUploadStatus('Indicator updated successfully');
        setEditingIndicator(null);
        loadStats();
        setTimeout(() => setUploadStatus(''), 3000);
      } else {
        const error = await response.json();
        setUploadStatus(`Error: ${error.detail}`);
      }
    } catch (error) {
      setUploadStatus('Error updating indicator');
    }
  };

  const startEdit = (indicator: any) => {
    setEditingIndicator(indicator.slug);
    setEditForm({
      name: indicator.name,
      description: '',
      unit: '',
      frequency: 'daily',
      source: ''
    });
    setShowUpload(false);
    setShowCreateNew(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    router.push('/admin');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <div className="text-xl text-gray-600">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
            <div className="flex gap-4">
              <a href="/" className="text-blue-600 hover:text-blue-800">
                View Site
              </a>
              <button
                onClick={handleLogout}
                className="text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Status Message - Fixed at top */}
      {uploadStatus && (
        <div className="sticky top-[73px] z-40 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className={`p-4 rounded-md shadow-lg ${
              uploadStatus.includes('Success') || uploadStatus.includes('deleted') || uploadStatus.includes('updated') 
                ? 'bg-green-50 text-green-800 border-2 border-green-300' 
                : uploadStatus.includes('⏳')
                ? 'bg-blue-50 text-blue-800 border-2 border-blue-300'
                : 'bg-red-50 text-red-800 border-2 border-red-300'
            }`}>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  {isUploading && (
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  )}
                  {!isUploading && (uploadStatus.includes('Success') || uploadStatus.includes('deleted') || uploadStatus.includes('updated')) && (
                    <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                  {!isUploading && uploadStatus.includes('❌') && (
                    <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                  <span className="font-medium">{uploadStatus}</span>
                </div>
                {!isUploading && (
                  <button 
                    onClick={() => setUploadStatus('')}
                    className="text-gray-500 hover:text-gray-700 font-bold text-lg"
                  >
                    ✕
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Total Categories</h3>
            <p className="text-3xl font-bold text-gray-900 mt-2">{stats?.total_categories}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Total Indicators</h3>
            <p className="text-3xl font-bold text-gray-900 mt-2">{stats?.total_indicators}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Total Data Points</h3>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {stats?.total_data_points.toLocaleString()}
            </p>
          </div>
        </div>

        {/* Upload/Create Section */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-900">Manage Data</h2>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setShowCreateNew(!showCreateNew);
                  setShowUpload(false);
                  setShowDelete(false);
                }}
                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
              >
                {showCreateNew ? 'Cancel' : 'Create New Indicator'}
              </button>
              <button
                onClick={() => {
                  setShowUpload(!showUpload);
                  setShowCreateNew(false);
                  setShowDelete(false);
                }}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                {showUpload ? 'Cancel' : 'Update Existing'}
              </button>
              <button
                onClick={() => {
                  setShowDelete(!showDelete);
                  setShowUpload(false);
                  setShowCreateNew(false);
                }}
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
              >
                {showDelete ? 'Cancel' : 'Delete'}
              </button>
            </div>
          </div>

          {showCreateNew && (
            <form onSubmit={handleCreateNew} className="space-y-4 border-t pt-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Create New Indicator</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Indicator Name *
                  </label>
                  <input
                    type="text"
                    value={newIndicator.name}
                    onChange={(e) => setNewIndicator({...newIndicator, name: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md"
                    placeholder="e.g., Gold Price"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Slug (URL-friendly) *
                  </label>
                  <input
                    type="text"
                    value={newIndicator.slug}
                    onChange={(e) => setNewIndicator({...newIndicator, slug: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md"
                    placeholder="e.g., gold-price"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Category *
                  </label>
                  <select
                    value={newIndicator.category}
                    onChange={(e) => setNewIndicator({...newIndicator, category: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md"
                    required
                  >
                    {stats?.categories.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Unit
                  </label>
                  <input
                    type="text"
                    value={newIndicator.unit}
                    onChange={(e) => setNewIndicator({...newIndicator, unit: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md"
                    placeholder="e.g., USD, Index, %"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Frequency
                  </label>
                  <select
                    value={newIndicator.frequency}
                    onChange={(e) => setNewIndicator({...newIndicator, frequency: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={newIndicator.description}
                    onChange={(e) => setNewIndicator({...newIndicator, description: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md"
                    rows={3}
                    placeholder="Brief description of the indicator..."
                  />
                </div>
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-between items-center mb-4">
                  <label className="block text-sm font-medium text-gray-700">
                    CSV Files (must have &apos;date&apos; and &apos;value&apos; columns) *
                  </label>
                  <button
                    type="button"
                    onClick={() => setFileUploads([...fileUploads, { file: null, series_type: 'historical', custom_series_type: '' }])}
                    className="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
                  >
                    + Add Another CSV
                  </button>
                </div>

                {fileUploads.map((upload, index) => (
                  <div key={index} className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex justify-between items-center mb-3">
                      <h4 className="text-sm font-medium text-gray-700">Series #{index + 1}</h4>
                      {fileUploads.length > 1 && (
                        <button
                          type="button"
                          onClick={() => setFileUploads(fileUploads.filter((_, i) => i !== index))}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          Remove
                        </button>
                      )}
                    </div>

                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Series Type
                        </label>
                        <select
                          value={upload.series_type}
                          onChange={(e) => {
                            const updated = [...fileUploads];
                            updated[index].series_type = e.target.value;
                            setFileUploads(updated);
                          }}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        >
                          <option value="historical">Historical</option>
                          <option value="inflation_adjusted">Adjusted for Inflation</option>
                          <option value="annual_change">Annual % Change</option>
                          <option value="annual_average">Annual Average</option>
                          <option value="other">Other (Custom)</option>
                        </select>
                      </div>

                      {upload.series_type === 'other' && (
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            Custom Series Type Name *
                          </label>
                          <input
                            type="text"
                            value={upload.custom_series_type}
                            onChange={(e) => {
                              const updated = [...fileUploads];
                              updated[index].custom_series_type = e.target.value;
                              setFileUploads(updated);
                            }}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                            placeholder="e.g., quarterly_avg, rolling_12m"
                            required
                          />
                        </div>
                      )}

                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          CSV File
                        </label>
                        <input
                          type="file"
                          accept=".csv"
                          onChange={(e) => {
                            const updated = [...fileUploads];
                            updated[index].file = e.target.files?.[0] || null;
                            setFileUploads(updated);
                            console.log('File selected:', e.target.files?.[0]?.name);
                          }}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        />
                        {upload.file && (
                          <p className="text-xs text-green-600 mt-1">
                            ✓ {upload.file.name}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                
                <p className="text-xs text-gray-500 mt-2">
                  CSV format: date,value (e.g., 2024-01-01,100.50). You can upload multiple CSVs with different series types.
                </p>
              </div>

              <button
                type="submit"
                disabled={isUploading}
                className="w-full bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isUploading && (
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                )}
                {isUploading ? 'Uploading...' : 'Create Indicator and Import Data'}
              </button>
            </form>
          )}

          {showUpload && (
            <form onSubmit={handleUpload} className="space-y-4 border-t pt-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Update Existing Indicator</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Indicator
                </label>
                <select
                  value={selectedIndicator}
                  onChange={(e) => {
                    setSelectedIndicator(e.target.value);
                    if (e.target.value) {
                      loadIndicatorSeries(e.target.value);
                    } else {
                      setSelectedIndicatorSeries([]);
                    }
                    setIsNewSeries(true);
                    setUploadSeriesType('historical');
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md"
                  required
                >
                  <option value="">Choose an indicator...</option>
                  {stats?.indicators.map((ind) => (
                    <option key={ind.slug} value={ind.slug}>
                      {ind.name} ({ind.category})
                    </option>
                  ))}
                </select>
              </div>

              {selectedIndicator && selectedIndicatorSeries.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <h4 className="text-sm font-semibold text-blue-900 mb-2">
                    Existing Series for this Indicator:
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedIndicatorSeries.map((series) => (
                      <span 
                        key={series.series_type}
                        className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {series.label}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedIndicator && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Action
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center">
                        <input
                          type="radio"
                          checked={isNewSeries}
                          onChange={() => {
                            setIsNewSeries(true);
                            setUploadSeriesType('historical');
                          }}
                          className="mr-2"
                        />
                        <span className="text-sm">Add a new series type</span>
                      </label>
                      {selectedIndicatorSeries.length > 0 && (
                        <label className="flex items-center">
                          <input
                            type="radio"
                            checked={!isNewSeries}
                            onChange={() => {
                              setIsNewSeries(false);
                              setUploadSeriesType(selectedIndicatorSeries[0]?.series_type || 'historical');
                            }}
                            className="mr-2"
                          />
                          <span className="text-sm">Update an existing series type (replace data)</span>
                        </label>
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Series Type
                    </label>
                    {!isNewSeries && selectedIndicatorSeries.length > 0 ? (
                      <select
                        value={uploadSeriesType}
                        onChange={(e) => setUploadSeriesType(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-md"
                        required
                      >
                        {selectedIndicatorSeries.map((series) => (
                          <option key={series.series_type} value={series.series_type}>
                            {series.label} (Update existing)
                          </option>
                        ))}
                      </select>
                    ) : (
                      <>
                        <select
                          value={uploadSeriesType}
                          onChange={(e) => setUploadSeriesType(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-md"
                          required
                        >
                          <option value="historical">Historical</option>
                          <option value="inflation_adjusted">Adjusted for Inflation</option>
                          <option value="annual_change">Annual % Change</option>
                          <option value="annual_average">Annual Average</option>
                          <option value="other">Other (Custom)</option>
                        </select>
                        <p className="text-xs text-gray-500 mt-1">
                          Select which series type this data belongs to
                        </p>
                      </>
                    )}
                  </div>

                  {isNewSeries && uploadSeriesType === 'other' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Custom Series Type Name *
                      </label>
                      <input
                        type="text"
                        value={customUploadSeriesType}
                        onChange={(e) => setCustomUploadSeriesType(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-md"
                        placeholder="e.g., quarterly_avg, rolling_12m"
                        required
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Enter a unique identifier for this series type (use lowercase with underscores)
                      </p>
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      CSV File (must have &apos;date&apos; and &apos;value&apos; columns)
                    </label>
                    <input
                      type="file"
                      accept=".csv"
                      onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-md"
                      required
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isUploading}
                    className="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {isUploading && (
                      <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    )}
                    {isUploading ? 'Uploading...' : (isNewSeries ? 'Add New Series' : 'Update Series Data')}
                  </button>
                </>
              )}
            </form>
          )}

          {showDelete && (
            <div className="space-y-4 border-t pt-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Delete Indicator</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Indicator to Delete
                </label>
                <select
                  value={deleteConfirm || ''}
                  onChange={(e) => setDeleteConfirm(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md"
                >
                  <option value="">Choose an indicator...</option>
                  {stats?.indicators.map((ind) => (
                    <option key={ind.slug} value={ind.slug}>
                      {ind.name} ({ind.category}) - {ind.data_points.toLocaleString()} points
                    </option>
                  ))}
                </select>
              </div>

              {deleteConfirm && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4">
                  <p className="text-red-800 mb-4">
                    ⚠️ Are you sure you want to delete <strong>{stats?.indicators.find(i => i.slug === deleteConfirm)?.name}</strong>? 
                    This will permanently remove all {stats?.indicators.find(i => i.slug === deleteConfirm)?.data_points.toLocaleString()} data points.
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={() => {
                        const indicator = stats?.indicators.find(i => i.slug === deleteConfirm);
                        if (indicator) {
                          handleDelete(indicator.slug, indicator.name);
                        }
                      }}
                      className="bg-red-600 text-white px-6 py-2 rounded-md hover:bg-red-700 font-medium"
                    >
                      Yes, Delete Permanently
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(null)}
                      className="bg-gray-200 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Indicators Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">All Indicators</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Data Points
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date Range
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {stats?.indicators.map((indicator) => (
                  <tr key={indicator.id} className={editingIndicator === indicator.slug ? 'bg-blue-50' : ''}>
                    <td className="px-6 py-4">
                      <a 
                        href={`/indicator/${indicator.slug}`}
                        target="_blank"
                        className="block hover:bg-gray-50 transition-colors"
                      >
                        <div className="text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline">{indicator.name}</div>
                        <div className="text-sm text-gray-500">{indicator.slug}</div>
                      </a>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {indicator.category}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {indicator.data_points.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {editingIndicator === indicator.slug ? (
                        <div className="space-y-2">
                          <input
                            type="text"
                            value={editForm.description}
                            onChange={(e) => setEditForm({...editForm, description: e.target.value})}
                            className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
                            placeholder="Description"
                          />
                          <input
                            type="text"
                            value={editForm.unit}
                            onChange={(e) => setEditForm({...editForm, unit: e.target.value})}
                            className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
                            placeholder="Unit"
                          />
                          <select
                            value={editForm.frequency}
                            onChange={(e) => setEditForm({...editForm, frequency: e.target.value})}
                            className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
                          >
                            <option value="daily">Daily</option>
                            <option value="weekly">Weekly</option>
                            <option value="monthly">Monthly</option>
                            <option value="quarterly">Quarterly</option>
                            <option value="yearly">Yearly</option>
                          </select>
                        </div>
                      ) : (
                        indicator.date_range || 'N/A'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

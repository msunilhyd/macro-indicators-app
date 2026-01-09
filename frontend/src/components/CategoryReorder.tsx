'use client';

import { useState, useEffect } from 'react';
import { ArrowUp, ArrowDown, Save, X, Settings } from 'lucide-react';

interface Indicator {
  id: number;
  name: string;
  slug: string;
  unit: string | null;
  latest_value: number | null;
  latest_date: string | null;
  previous_value: number | null;
  change_percent: number | null;
}

interface CategoryReorderProps {
  categorySlug: string;
  initialIndicators: Indicator[];
}

export default function CategoryReorder({ categorySlug, initialIndicators }: CategoryReorderProps) {
  const [isAdmin, setIsAdmin] = useState(false);
  const [showReorder, setShowReorder] = useState(false);
  const [indicators, setIndicators] = useState<Indicator[]>(initialIndicators);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    // Check if user is admin
    const token = localStorage.getItem('admin_token');
    setIsAdmin(!!token);
  }, []);

  useEffect(() => {
    setIndicators(initialIndicators);
  }, [initialIndicators]);

  const moveIndicator = (index: number, direction: 'up' | 'down') => {
    const newIndicators = [...indicators];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;

    if (targetIndex >= 0 && targetIndex < newIndicators.length) {
      [newIndicators[index], newIndicators[targetIndex]] = [
        newIndicators[targetIndex],
        newIndicators[index],
      ];
      setIndicators(newIndicators);
    }
  };

  const saveOrder = async () => {
    const token = localStorage.getItem('admin_token');
    if (!token) {
      setMessage('❌ Admin token not found');
      return;
    }

    setIsSaving(true);
    setMessage('⏳ Saving order...');

    try {
      // Fetch all indicators to get their current display_order
      const allIndicatorsResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/stats?admin_token=${token}`
      );

      if (!allIndicatorsResponse.ok) {
        throw new Error('Failed to fetch indicators');
      }

      const statsData = await allIndicatorsResponse.json();
      const allIndicators = statsData.indicators;

      // Create a map of current indicators with their new positions
      const reorderedSlugs = indicators.map((ind) => ind.slug);
      const updatedIndicators = [...allIndicators];

      // Find the current indicators in the full list and update their order
      let baseOrder = 0;
      reorderedSlugs.forEach((slug, newIndex) => {
        const indicatorIndex = updatedIndicators.findIndex((ind: any) => ind.slug === slug);
        if (indicatorIndex !== -1) {
          updatedIndicators[indicatorIndex].display_order = baseOrder + newIndex;
        }
      });

      // Prepare order data for all indicators
      const orderData = updatedIndicators.map((ind: any) => ({
        slug: ind.slug,
        display_order: ind.display_order,
      }));

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/reorder-indicators?admin_token=${token}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(orderData),
        }
      );

      if (response.ok) {
        setMessage('✅ Order saved successfully! Refreshing...');
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        const error = await response.json();
        setMessage(`❌ Error: ${error.detail}`);
      }
    } catch (error) {
      setMessage('❌ Error saving order');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isAdmin) {
    return null;
  }

  return (
    <div className="mb-6">
      {!showReorder ? (
        <button
          onClick={() => setShowReorder(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm font-medium"
        >
          <Settings className="h-4 w-4" />
          Reorder Indicators
        </button>
      ) : (
        <div className="bg-white rounded-lg shadow-lg p-6 border-2 border-purple-200">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Reorder Indicators</h3>
            <div className="flex gap-2">
              <button
                onClick={saveOrder}
                disabled={isSaving}
                className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
              >
                <Save className="h-4 w-4" />
                {isSaving ? 'Saving...' : 'Save Order'}
              </button>
              <button
                onClick={() => {
                  setShowReorder(false);
                  setIndicators(initialIndicators);
                  setMessage('');
                }}
                className="inline-flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 text-sm font-medium"
              >
                <X className="h-4 w-4" />
                Cancel
              </button>
            </div>
          </div>

          {message && (
            <div
              className={`mb-4 p-3 rounded-md text-sm ${
                message.includes('✅')
                  ? 'bg-green-50 text-green-800 border border-green-200'
                  : message.includes('⏳')
                  ? 'bg-blue-50 text-blue-800 border border-blue-200'
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}
            >
              {message}
            </div>
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4 text-sm text-blue-800">
            💡 Use the ↑↓ arrows to reorder indicators. Changes will be reflected immediately after saving.
          </div>

          <div className="space-y-2 max-h-[500px] overflow-y-auto">
            {indicators.map((indicator, index) => (
              <div
                key={indicator.slug}
                className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-md p-3 hover:bg-gray-100"
              >
                <div className="flex items-center gap-3 flex-1">
                  <div className="text-sm font-medium text-gray-500 w-8">#{index + 1}</div>
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{indicator.name}</div>
                    <div className="text-xs text-gray-500">
                      {indicator.latest_value !== null && indicator.unit
                        ? `Latest: ${indicator.latest_value.toLocaleString()} ${indicator.unit}`
                        : 'No recent data'}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => moveIndicator(index, 'up')}
                    disabled={index === 0}
                    className="p-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    title="Move up"
                  >
                    <ArrowUp className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => moveIndicator(index, 'down')}
                    disabled={index === indicators.length - 1}
                    className="p-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    title="Move down"
                  >
                    <ArrowDown className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

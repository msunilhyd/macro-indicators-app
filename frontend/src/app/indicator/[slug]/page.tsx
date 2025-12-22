import Link from 'next/link';
import { getIndicator, formatValue, formatDate } from '@/lib/api';
import ChartWithFilters from '@/components/ChartWithFilters';
import { ArrowLeft } from 'lucide-react';

interface PageProps {
  params: { slug: string };
}

export default async function IndicatorPage({ params }: PageProps) {
  let indicator = null;

  try {
    indicator = await getIndicator(params.slug, 5000);
  } catch (error) {
    console.error('Failed to fetch indicator:', error);
  }

  if (!indicator) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <p className="text-gray-500">Indicator not found or backend unavailable.</p>
        <Link href="/" className="text-blue-600 hover:underline mt-4 inline-block">
          ← Back to Home
        </Link>
      </div>
    );
  }

  const latestValue = indicator.data_points.length > 0 
    ? indicator.data_points[indicator.data_points.length - 1] 
    : null;
  
  const previousValue = indicator.data_points.length > 1 
    ? indicator.data_points[indicator.data_points.length - 2] 
    : null;

  let changePercent = null;
  if (latestValue && previousValue && previousValue.value !== 0) {
    changePercent = ((latestValue.value - previousValue.value) / Math.abs(previousValue.value)) * 100;
  }

  const isPositive = changePercent !== null && changePercent > 0;
  const isNegative = changePercent !== null && changePercent < 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <Link href="/" className="inline-flex items-center text-blue-600 hover:underline mb-6">
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to Dashboard
      </Link>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">{indicator.name}</h1>
        {indicator.description && (
          <p className="text-gray-600 mb-4">{indicator.description}</p>
        )}

        <div className="flex flex-wrap gap-4 mt-4">
          {latestValue && (
            <div className="bg-white rounded-lg shadow px-6 py-4">
              <p className="text-sm text-gray-500 mb-1">Latest Value</p>
              <p className="text-3xl font-bold text-gray-900">
                {formatValue(latestValue.value, indicator.unit)}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {formatDate(latestValue.date)}
              </p>
            </div>
          )}

          {changePercent !== null && (
            <div className="bg-white rounded-lg shadow px-6 py-4">
              <p className="text-sm text-gray-500 mb-1">Change</p>
              <p className={`text-3xl font-bold ${
                isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-900'
              }`}>
                {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
              </p>
              <p className="text-sm text-gray-500 mt-1">vs previous</p>
            </div>
          )}

          <div className="bg-white rounded-lg shadow px-6 py-4">
            <p className="text-sm text-gray-500 mb-1">Data Points</p>
            <p className="text-3xl font-bold text-gray-900">
              {indicator.data_points.length.toLocaleString()}
            </p>
            <p className="text-sm text-gray-500 mt-1">{indicator.frequency}</p>
          </div>

          <div className="bg-white rounded-lg shadow px-6 py-4">
            <p className="text-sm text-gray-500 mb-1">Source</p>
            <p className="text-xl font-semibold text-gray-900">{indicator.source}</p>
            <p className="text-sm text-gray-500 mt-1">Unit: {indicator.unit || 'N/A'}</p>
          </div>
        </div>
      </div>

      {indicator.data_points.length > 0 ? (
        <ChartWithFilters 
          data={indicator.data_points} 
          name={indicator.name} 
          unit={indicator.unit}
          series={indicator.series || []}
        />
      ) : (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-500">No data available for this indicator.</p>
        </div>
      )}

      {/* Data Table */}
      <div className="mt-8">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Recent Data</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Value
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {indicator.data_points.slice(-20).reverse().map((dp, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-3 text-gray-600">
                    {formatDate(dp.date)}
                  </td>
                  <td className="px-6 py-3 text-right font-medium text-gray-900">
                    {formatValue(dp.value, indicator.unit)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

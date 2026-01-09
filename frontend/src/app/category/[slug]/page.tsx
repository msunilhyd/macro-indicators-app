import Link from 'next/link';
import { getCategory, formatValue, formatDate } from '@/lib/api';
import { ArrowLeft, TrendingUp, TrendingDown } from 'lucide-react';

interface PageProps {
  params: { slug: string };
}

export default async function CategoryPage({ params }: PageProps) {
  let category = null;

  try {
    category = await getCategory(params.slug);
  } catch (error) {
    console.error('Failed to fetch category:', error);
  }

  if (!category) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <p className="text-gray-500">Category not found or backend unavailable.</p>
        <Link href="/" className="text-blue-600 hover:underline mt-4 inline-block">
          ← Back to Home
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <Link href="/" className="inline-flex items-center text-blue-600 hover:underline mb-6">
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to Dashboard
      </Link>

      <h1 className="text-3xl font-bold text-gray-800 mb-2">{category.name}</h1>
      {category.description && (
        <p className="text-gray-600 mb-8">{category.description}</p>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                #
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Indicator
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Latest Value
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Change
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {category.indicators.map((indicator, index) => {
              const isPositive = indicator.change_percent !== null && indicator.change_percent > 0;
              const isNegative = indicator.change_percent !== null && indicator.change_percent < 0;

              return (
                <tr key={indicator.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-800 text-sm font-medium">
                      {index + 1}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <Link
                      href={`/indicator/${indicator.slug}`}
                      className="text-blue-600 hover:underline font-medium"
                    >
                      {indicator.name}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-right font-semibold text-gray-900">
                    {formatValue(indicator.latest_value, indicator.unit)}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {indicator.change_percent !== null && (
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded text-sm font-medium ${
                          isPositive
                            ? 'bg-green-100 text-green-700'
                            : isNegative
                            ? 'bg-red-100 text-red-700'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {isPositive && <TrendingUp className="h-3 w-3 mr-1" />}
                        {isNegative && <TrendingDown className="h-3 w-3 mr-1" />}
                        {isPositive ? '+' : ''}
                        {indicator.change_percent.toFixed(2)}%
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right text-gray-500 text-sm">
                    {formatDate(indicator.latest_date)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {category.indicators.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-500">No indicators found in this category.</p>
        </div>
      )}
    </div>
  );
}

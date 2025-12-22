import Link from 'next/link';
import { getDashboard, getSummary } from '@/lib/api';
import IndicatorCard from '@/components/IndicatorCard';
import { TrendingUp, Database, BarChart3, Calendar } from 'lucide-react';

export default async function Home() {
  let dashboard: Awaited<ReturnType<typeof getDashboard>> = [];
  let summary: Awaited<ReturnType<typeof getSummary>> | null = null;

  try {
    dashboard = await getDashboard();
    summary = await getSummary();
  } catch (error) {
    console.error('Failed to fetch data:', error);
  }

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-16">
        <div className="max-w-7xl mx-auto px-4">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Macro Economic Indicators
          </h1>
          <p className="text-xl text-blue-100 max-w-2xl">
            Real-time macroeconomic data and historical trends for informed financial decisions.
          </p>

          {summary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
              <div className="bg-white/10 rounded-lg p-4">
                <div className="flex items-center space-x-2 text-blue-200 mb-1">
                  <BarChart3 className="h-4 w-4" />
                  <span className="text-sm">Indicators</span>
                </div>
                <p className="text-2xl font-bold">{summary.total_indicators}</p>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="flex items-center space-x-2 text-blue-200 mb-1">
                  <Database className="h-4 w-4" />
                  <span className="text-sm">Data Points</span>
                </div>
                <p className="text-2xl font-bold">{summary.total_data_points?.toLocaleString()}</p>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="flex items-center space-x-2 text-blue-200 mb-1">
                  <TrendingUp className="h-4 w-4" />
                  <span className="text-sm">Categories</span>
                </div>
                <p className="text-2xl font-bold">{summary.total_categories}</p>
              </div>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="flex items-center space-x-2 text-blue-200 mb-1">
                  <Calendar className="h-4 w-4" />
                  <span className="text-sm">Data Since</span>
                </div>
                <p className="text-2xl font-bold">
                  {summary.data_range?.oldest ? new Date(summary.data_range.oldest).getFullYear() : 'N/A'}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Key Indicators */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Key Indicators</h2>

        {dashboard.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {dashboard.map((indicator) => (
              <IndicatorCard
                key={indicator.id}
                name={indicator.name}
                slug={indicator.slug}
                categorySlug={indicator.category_slug}
                unit={indicator.unit}
                latestValue={indicator.latest_value}
                latestDate={indicator.latest_date}
                changePercent={indicator.change_percent}
                sparkline={indicator.sparkline}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500 mb-4">
              No data available. Make sure the backend is running and the database is seeded.
            </p>
            <p className="text-sm text-gray-400">
              Run: <code className="bg-gray-100 px-2 py-1 rounded">cd backend && python seed_data.py</code>
            </p>
          </div>
        )}

        {/* Categories Section */}
        <h2 className="text-2xl font-bold text-gray-800 mb-6 mt-12">Browse Categories</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[
            { name: 'Market Indexes', slug: 'market-indexes', icon: '📈', desc: 'S&P 500, Dow Jones, NASDAQ' },
            { name: 'Precious Metals', slug: 'precious-metals', icon: '🥇', desc: 'Gold, Silver, Platinum' },
            { name: 'Energy', slug: 'energy', icon: '⛽', desc: 'Oil, Natural Gas prices' },
            { name: 'Commodities', slug: 'commodities', icon: '🌾', desc: 'Agricultural commodities' },
            { name: 'Exchange Rates', slug: 'exchange-rates', icon: '💱', desc: 'Currency exchange rates' },
            { name: 'Interest Rates', slug: 'interest-rates', icon: '🏦', desc: 'Fed rates, Treasury yields' },
            { name: 'Economy', slug: 'economy', icon: '📊', desc: 'GDP, Unemployment, Inflation' },
          ].map((cat) => (
            <Link key={cat.slug} href={`/category/${cat.slug}`}>
              <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer border border-gray-100">
                <span className="text-3xl mb-3 block">{cat.icon}</span>
                <h3 className="font-semibold text-gray-800 mb-1">{cat.name}</h3>
                <p className="text-sm text-gray-500">{cat.desc}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

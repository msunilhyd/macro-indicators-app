'use client';

import { useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  BarChart,
  Bar,
} from 'recharts';
import { DataPoint, DataSeries } from '@/lib/api';

interface ChartWithFiltersProps {
  data: DataPoint[];
  name: string;
  unit: string | null;
  series?: DataSeries[];
}

type TimeRange = '5Y' | '10Y' | '20Y' | '30Y' | '50Y' | 'ALL';

const TIME_RANGES: { label: TimeRange; years: number | null }[] = [
  { label: '5Y', years: 5 },
  { label: '10Y', years: 10 },
  { label: '20Y', years: 20 },
  { label: '30Y', years: 30 },
  { label: '50Y', years: 50 },
  { label: 'ALL', years: null },
];

export default function ChartWithFilters({ data, name, unit, series = [] }: ChartWithFiltersProps) {
  const [selectedRange, setSelectedRange] = useState<TimeRange>('ALL');
  const [selectedSeries, setSelectedSeries] = useState<string>('historical');

  // Use series data if available, otherwise fall back to data prop
  const currentSeriesData = useMemo(() => {
    if (series.length > 0) {
      const found = series.find(s => s.series_type === selectedSeries);
      return found?.data_points || data;
    }
    return data;
  }, [series, selectedSeries, data]);

  const currentSeriesLabel = useMemo(() => {
    if (series.length > 0) {
      const found = series.find(s => s.series_type === selectedSeries);
      return found?.label || name;
    }
    return name;
  }, [series, selectedSeries, name]);

  // Determine unit based on series type
  const currentUnit = useMemo(() => {
    if (selectedSeries === 'annual_change') return '%';
    return unit;
  }, [selectedSeries, unit]);

  const filteredData = useMemo(() => {
    if (selectedRange === 'ALL' || currentSeriesData.length === 0) {
      return currentSeriesData;
    }

    const range = TIME_RANGES.find(r => r.label === selectedRange);
    if (!range || !range.years) return currentSeriesData;

    const cutoffDate = new Date();
    cutoffDate.setFullYear(cutoffDate.getFullYear() - range.years);

    return currentSeriesData.filter(dp => new Date(dp.date) >= cutoffDate);
  }, [currentSeriesData, selectedRange]);

  const chartData = useMemo(() => {
    return filteredData.map((dp) => ({
      date: new Date(dp.date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
      }),
      value: dp.value,
      fullDate: dp.date,
    }));
  }, [filteredData]);

  const formatYAxis = (value: number) => {
    if (currentUnit === '%') return `${value}%`;
    if (currentUnit?.includes('USD')) return `$${value.toLocaleString()}`;
    return value.toLocaleString();
  };

  // Check if we should use bar chart (for annual change)
  const useBarChart = selectedSeries === 'annual_change';

  // Calculate min/max for better Y-axis scaling
  const minValue = Math.min(...filteredData.map(d => d.value));
  const maxValue = Math.max(...filteredData.map(d => d.value));
  const padding = (maxValue - minValue) * 0.1;

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      {/* Series Type Tabs */}
      {series.length > 1 && (
        <div className="flex flex-wrap gap-2 mb-4 pb-4 border-b border-gray-200">
          {series.map((s) => (
            <button
              key={s.series_type}
              onClick={() => setSelectedSeries(s.series_type)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedSeries === s.series_type
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}

      {/* Time Range Filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        {TIME_RANGES.map((range) => (
          <button
            key={range.label}
            onClick={() => setSelectedRange(range.label)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedRange === range.label
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {range.label}
          </button>
        ))}
      </div>

      {/* Data range info */}
      <div className="text-sm text-gray-500 mb-4">
        Showing {filteredData.length.toLocaleString()} data points
        {filteredData.length > 0 && (
          <span>
            {' '}from {new Date(filteredData[0].date).toLocaleDateString('en-US', { year: 'numeric', month: 'short' })}
            {' '}to {new Date(filteredData[filteredData.length - 1].date).toLocaleDateString('en-US', { year: 'numeric', month: 'short' })}
          </span>
        )}
      </div>

      {/* Chart */}
      <div className="w-full h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
              interval="preserveStartEnd"
            />
            <YAxis
              tickFormatter={formatYAxis}
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
              domain={[minValue - padding, maxValue + padding]}
            />
            <Tooltip
              formatter={(value) => [formatYAxis(value as number), currentSeriesLabel]}
              labelFormatter={(label) => `Date: ${label}`}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="value"
              name={currentSeriesLabel}
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

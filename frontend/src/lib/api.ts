// API base URL - uses environment variable or defaults to localhost
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  display_order: number;
}

export interface IndicatorSummary {
  id: number;
  name: string;
  slug: string;
  unit: string | null;
  latest_value: number | null;
  latest_date: string | null;
  previous_value: number | null;
  change_percent: number | null;
}

export interface CategoryWithIndicators extends Category {
  indicators: IndicatorSummary[];
}

export interface DataPoint {
  date: string;
  value: number;
}

export interface DataSeries {
  series_type: string;
  label: string;
  data_points: DataPoint[];
}

export interface IndicatorWithData {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  unit: string | null;
  frequency: string;
  category_id: number;
  source: string;
  data_points: DataPoint[];
  series: DataSeries[];
}

export interface DashboardIndicator {
  id: number;
  name: string;
  slug: string;
  category_slug: string;
  unit: string | null;
  latest_value: number | null;
  latest_date: string | null;
  change_percent: number | null;
  sparkline: number[];
}

export async function getCategories(): Promise<Category[]> {
  const res = await fetch(`${API_BASE}/api/categories`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch categories');
  return res.json();
}

export async function getCategory(slug: string): Promise<CategoryWithIndicators> {
  const res = await fetch(`${API_BASE}/api/categories/${slug}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch category');
  return res.json();
}

export async function getIndicator(slug: string, limit = 500): Promise<IndicatorWithData> {
  const res = await fetch(`${API_BASE}/api/indicators/${slug}?limit=${limit}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch indicator');
  return res.json();
}

export async function getDashboard(): Promise<DashboardIndicator[]> {
  const res = await fetch(`${API_BASE}/api/dashboard`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch dashboard');
  return res.json();
}

export async function getSummary(): Promise<{
  total_indicators: number;
  total_data_points: number;
  total_categories: number;
  data_range: { oldest: string; newest: string };
}> {
  const res = await fetch(`${API_BASE}/api/dashboard/summary`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch summary');
  return res.json();
}

export function formatValue(value: number | null, unit: string | null): string {
  if (value === null) return 'N/A';
  
  if (unit === '%') {
    return `${value.toFixed(2)}%`;
  } else if (unit === 'USD' || unit === 'USD/oz' || unit === 'USD/bbl') {
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  } else if (unit === 'Index' || unit === 'Ratio') {
    return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'N/A';
  const date = new Date(dateStr);
  
  // If date is January 1st, show only the year (year-only data)
  if (date.getMonth() === 0 && date.getDate() === 1) {
    return date.getFullYear().toString();
  }
  
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// Bootstrap 4 jQuery modal augmentation
interface JQuery {
  modal(action: 'show' | 'hide' | 'toggle' | 'dispose'): JQuery;
  modal(options?: Record<string, unknown>): JQuery;
}

// Chart.js (loaded via CDN)
interface ChartTickOptions {
  autoSkip?: boolean;
  maxTicksLimit?: number;
  stepSize?: number;
}

interface ChartScaleOptions {
  type?: string;
  ticks?: ChartTickOptions;
  grid?: {
    color?: string | ((ctx: ChartScaleContext) => string);
    lineWidth?: number | ((ctx: ChartScaleContext) => number);
  };
  min?: number;
  max?: number;
  beginAtZero?: boolean;
}

interface ChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  animation?: { duration?: number; easing?: string };
  plugins?: {
    title?: { display?: boolean; text?: string };
    legend?: { display?: boolean; position?: string };
  };
  scales?: {
    x?: ChartScaleOptions;
    y?: ChartScaleOptions;
  };
}

interface ChartDataset {
  label?: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  fill?: boolean;
  tension?: number;
  pointRadius?: number;
  pointHoverRadius?: number;
  borderDash?: number[];
  order?: number;
}

interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

interface ChartConfig {
  type: string;
  data: ChartData;
  options?: ChartOptions;
}

interface ChartScaleContext {
  tick: { value: number };
}

declare class Chart {
  data: ChartData;
  options: ChartOptions;
  constructor(ctx: CanvasRenderingContext2D, config: ChartConfig);
  update(mode?: string): void;
}

// Window extensions
interface Window {
  memoMarkdownRender?: (text: string) => string;
  markdownit?: (options?: object) => { render: (text: string) => string };
}

// Global chart data variables (set via Django template script tags)
declare const categoryData: ChartData | undefined;
declare const expenseData: ChartData | undefined;
declare const balanceData: ChartData | undefined;
declare const majorCategoryData: ChartData | undefined;

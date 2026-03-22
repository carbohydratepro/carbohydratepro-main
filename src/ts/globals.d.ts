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

interface ChartTooltipCallbacks {
  label?: (context: ChartTooltipContext) => string;
  title?: (items: ChartTooltipContext[]) => string;
}

interface ChartTooltipContext {
  dataset: ChartDataset;
  datasetIndex: number;
  dataIndex: number;
  parsed: { x: number; y: number };
  formattedValue: string;
  label: string;
}

interface ChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  animation?: { duration?: number; easing?: string };
  interaction?: {
    mode?: 'index' | 'nearest' | 'point' | 'dataset' | 'x' | 'y';
    intersect?: boolean;
    axis?: 'x' | 'y' | 'xy';
  };
  plugins?: {
    title?: { display?: boolean; text?: string };
    legend?: { display?: boolean; position?: string };
    tooltip?: {
      enabled?: boolean;
      mode?: string;
      intersect?: boolean;
      callbacks?: ChartTooltipCallbacks;
    };
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

// Global functions from app.ts
declare function isInteractiveTarget(target: EventTarget | null): boolean;
declare function initLongPressDelete(container?: HTMLElement): void;
declare function getCookie(name: string): string | null;

// Global functions from transaction.ts
declare function toggleWeekendColor(): void;

// Global chart data variables (set via Django template script tags)
declare const categoryData: ChartData | undefined;
declare const expenseData: ChartData | undefined;
declare const balanceData: ChartData | undefined;
declare const majorCategoryData: ChartData | undefined;
declare const monthlyData: ChartData | undefined;

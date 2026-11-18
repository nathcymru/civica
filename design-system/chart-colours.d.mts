export type ChartMode = 'light' | 'dark';
export interface ChartColourOptions { mode?: ChartMode }
export type ChartPattern = 'solid' | 'diagonal' | 'reverse-diagonal' | 'cross' | 'horizontal' | 'vertical' | 'dots';
export interface ChartSeriesStyle { color: string; pattern: ChartPattern; lineDash: number[]; symbol: string; index: number }
export interface ChartCategoricalColour { id: string; name: string; hex: string }
export const CHART_COLOUR_SPEC: Readonly<{
  schemaVersion: number; algorithmVersion: string;
  categorical: readonly Readonly<ChartCategoricalColour>[];
  axesAndLines: Readonly<ChartCategoricalColour>;
  labels: Readonly<Record<ChartMode, Readonly<ChartCategoricalColour>>>;
  roles: Readonly<Record<string, Readonly<{ colour: string; pattern: ChartPattern; index: number }>>>;
  patterns: readonly ChartPattern[];
  exampleKeys: readonly Readonly<{ key: string; label: string }>[];
  [key: string]: unknown;
}>;
export function chartColour(key: string, options?: ChartColourOptions): string;
export function chartSeriesStyle(key: string, options?: ChartColourOptions): ChartSeriesStyle;
export function chartSlotColour(slot: number, options?: ChartColourOptions): string;
export function chartLabelColour(mode?: ChartMode): string;
export function chartAxisColour(): string;
export function chartContrast(one: string, two: string): number;

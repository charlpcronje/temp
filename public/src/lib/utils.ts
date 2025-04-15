import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatFileSize(bytes: number): string {
  if (isNaN(bytes) || bytes < 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const exponent = Math.floor(Math.log10(bytes) / 3);
  const value = bytes / Math.pow(1024, exponent);

  return `${value.toFixed(2)} ${units[exponent]}`;
}
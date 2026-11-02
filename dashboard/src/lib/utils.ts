import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency: string = "MAD"): string {
  return new Intl.NumberFormat("fr-MA", {
    style: "currency",
    currency: currency,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(dateString: string): string {
  try {
    const d = new Date(dateString);
    return d.toLocaleString("fr-MA", {
      dateStyle: "short",
      timeStyle: "medium",
    });
  } catch {
    return dateString;
  }
}


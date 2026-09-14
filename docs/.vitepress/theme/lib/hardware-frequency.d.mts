export type HardwareSource = { work_id: string; title: string; first_public_date?: string; first_public_date_precision?: string; original_url: string; usages: any[] }
export type HardwareFrequency = { hardware_id: string; name: string; category: string; identity_level: string; work_count: number; real_work_count: number; simulation_work_count: number; baseline_work_count: number; calibration_work_count: number; source_count: number; sources: HardwareSource[]; [key: string]: any }
export function hardwareMonth(work: any): string
export function hardwareEvidenceUrl(usage: any): string
export function hardwareFrequency(devices?: any[], works?: any[], filters?: { category?: string; device?: string; setting?: string; role?: string; month?: string }): { models: HardwareFrequency[]; unresolved: HardwareFrequency[] }

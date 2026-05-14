export const percent = (value: number) => `${Math.round(value * 100)}%`

export const formatDate = (date: string) =>
  new Intl.DateTimeFormat('en', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(date))

export const titleFromText = (text: string) =>
  text
    .split(/[.\n]/)
    .find((line) => line.trim().length > 0)
    ?.trim()
    .slice(0, 96) ?? 'Untitled analysis'

export const tokenKey = (token: string) =>
  token
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()

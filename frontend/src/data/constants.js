// constants.js — Shared UI constants for the dashboard

export const classLabels = {
  industrial_fire: 'Industrial Fire',
  wildfire: 'Wildfire',
  crop_burning: 'Crop Burning',
  gas_flare: 'Gas Flare',
  mining: 'Mining',
};

export const statusLabels = {
  new: 'New',
  recurring: 'Recurring',
  persistent: 'Persistent',
  escalated: 'Escalated',
};

export const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'new', label: 'New' },
  { value: 'recurring', label: 'Recurring' },
  { value: 'persistent', label: 'Persistent' },
  { value: 'escalated', label: 'Escalated' },
];

export const classOptions = [
  { value: '', label: 'All Classes' },
  { value: 'industrial_fire', label: 'Industrial Fire' },
  { value: 'wildfire', label: 'Wildfire' },
  { value: 'crop_burning', label: 'Crop Burning' },
  { value: 'gas_flare', label: 'Gas Flare' },
  { value: 'mining', label: 'Mining' },
];

export function getClassBadgeClass(cls) {
  return `badge-class-${cls}`;
}

export function getStatusBadgeClass(status) {
  return `badge-status-${status}`;
}
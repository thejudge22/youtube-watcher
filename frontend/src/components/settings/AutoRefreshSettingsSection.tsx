import { useState, useEffect } from 'react';
import { Button } from '../common/Button';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import {
  useAutoRefreshSettings,
  useUpdateAutoRefreshSettings,
  useAutoRefreshStatus
} from '../../hooks/useAutoRefresh';
import { useRefreshAllChannels } from '../../hooks/useChannels';
import type { AutoRefreshSettings } from '../../types';

export function AutoRefreshSettingsSection() {
  const { data: settings, isLoading } = useAutoRefreshSettings();
  const { data: status } = useAutoRefreshStatus();
  const updateSettings = useUpdateAutoRefreshSettings();
  const refreshAll = useRefreshAllChannels();

  const [formData, setFormData] = useState<AutoRefreshSettings>({
    auto_refresh_enabled: false,
    auto_refresh_interval: '6h',
  });

  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  const handleChange = (field: keyof AutoRefreshSettings, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    updateSettings.mutate(formData);
  };

  const handleRefreshNow = async () => {
    await refreshAll.mutateAsync(undefined);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
  };

  const intervalLabels: Record<string, string> = {
    '1h': 'Every hour',
    '6h': 'Every 6 hours',
    '12h': 'Every 12 hours',
    '24h': 'Every day',
  };

  if (isLoading) {
    return <div className="text-text-secondary">Loading auto-refresh settings...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-text-primary mb-2">Auto-Refresh</h2>
        <p className="text-text-secondary text-sm mb-4">
          Automatically check your channels for new videos on a schedule.
        </p>
      </div>

      {/* Enable/Disable Toggle */}
      <div className="flex items-center justify-between">
        <div>
          <label className="text-text-primary font-medium">Enable Auto-Refresh</label>
          <p className="text-text-secondary text-sm">Refresh all channels automatically</p>
        </div>
        <button
          onClick={() => handleChange('auto_refresh_enabled', !formData.auto_refresh_enabled)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            formData.auto_refresh_enabled ? 'bg-accent-blue' : 'bg-bg-elevated'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              formData.auto_refresh_enabled ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      {/* Interval Selection */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1">
          Refresh Interval
        </label>
        <select
          value={formData.auto_refresh_interval}
          onChange={(e) => handleChange('auto_refresh_interval', e.target.value)}
          className="w-full bg-bg-tertiary border border-border text-text-primary rounded-lg px-3 py-2"
          disabled={!formData.auto_refresh_enabled}
        >
          {Object.entries(intervalLabels).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={handleSave}
          isLoading={updateSettings.isPending}
        >
          Save Auto-Refresh Settings
        </Button>
      </div>

      {/* Status Section */}
      <div className="border-t border-border pt-4 mt-6">
        <h3 className="text-md font-medium text-text-primary mb-3">Refresh Status</h3>

        <div className="bg-bg-tertiary/50 rounded-lg p-4 space-y-2">
          <div className="flex justify-between">
            <span className="text-text-secondary">Auto-Refresh:</span>
            <span className={status?.auto_refresh_enabled ? 'text-accent-green' : 'text-text-secondary'}>
              {status?.auto_refresh_enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-secondary">Last Refresh:</span>
            <span className="text-text-primary">{formatDate(status?.last_refresh_at ?? null)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-secondary">Status:</span>
            <span className={
              status?.last_refresh_status === 'success'
                ? 'text-accent-green'
                : status?.last_refresh_status === 'failed'
                ? 'text-accent-red'
                : 'text-text-secondary'
            }>
              {status?.last_refresh_status === 'success' ? 'Success' : status?.last_refresh_status === 'failed' ? 'Failed' : 'No refresh yet'}
            </span>
          </div>
          {status?.last_refresh_error && (
            <div className="text-accent-red text-sm mt-2">
              Error: {status.last_refresh_error}
            </div>
          )}
        </div>

        {/* Manual Refresh Button */}
        <div className="mt-4">
          <Button
            variant="secondary"
            onClick={handleRefreshNow}
            isLoading={refreshAll.isPending}
          >
            <ArrowPathIcon className={`w-4 h-4 mr-1.5 ${refreshAll.isPending ? 'animate-spin' : ''}`} />
            Refresh Now
          </Button>
        </div>
      </div>
    </div>
  );
}
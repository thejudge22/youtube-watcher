import { useState, useEffect } from 'react';
import { Button } from '../common/Button';
import {
  useBackupSettings,
  useUpdateBackupSettings,
  useBackupStatus,
  useBackupList,
  useRunBackup
} from '../../hooks/useBackup';
import type { BackupSettings } from '../../types';

export function BackupSettingsSection() {
  const { data: settings, isLoading } = useBackupSettings();
  const { data: status } = useBackupStatus();
  const { data: backupList } = useBackupList();
  const updateSettings = useUpdateBackupSettings();
  const runBackup = useRunBackup();

  const [formData, setFormData] = useState<BackupSettings>({
    backup_enabled: false,
    backup_schedule: 'daily',
    backup_time: '02:00',
    backup_format: 'json',
    backup_retention_days: 30,
  });

  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  const handleChange = (field: keyof BackupSettings, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    updateSettings.mutate(formData);
  };

  const handleRunBackup = () => {
    runBackup.mutate(formData.backup_format);
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
  };

  if (isLoading) {
    return <div className="text-gray-400">Loading backup settings...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-white mb-2">Scheduled Backups</h2>
        <p className="text-gray-400 text-sm mb-4">
          Configure automatic backups to protect your data.
        </p>
      </div>

      {/* Enable/Disable Toggle */}
      <div className="flex items-center justify-between">
        <div>
          <label className="text-white font-medium">Enable Automatic Backups</label>
          <p className="text-gray-400 text-sm">Run backups on a schedule</p>
        </div>
        <button
          onClick={() => handleChange('backup_enabled', !formData.backup_enabled)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            formData.backup_enabled ? 'bg-blue-600' : 'bg-gray-600'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              formData.backup_enabled ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      {/* Schedule Options */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Schedule
          </label>
          <select
            value={formData.backup_schedule}
            onChange={(e) => handleChange('backup_schedule', e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2"
            disabled={!formData.backup_enabled}
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly (Sunday)</option>
            <option value="monthly">Monthly (1st)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Time
          </label>
          <input
            type="time"
            value={formData.backup_time}
            onChange={(e) => handleChange('backup_time', e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2"
            disabled={!formData.backup_enabled}
          />
        </div>
      </div>

      {/* Format Options */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Backup Format
          </label>
          <select
            value={formData.backup_format}
            onChange={(e) => handleChange('backup_format', e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2"
          >
            <option value="json">JSON Export</option>
            <option value="database">Database Copy</option>
            <option value="both">Both</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Keep backups for
          </label>
          <select
            value={formData.backup_retention_days}
            onChange={(e) => handleChange('backup_retention_days', parseInt(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2"
          >
            <option value="7">7 days</option>
            <option value="14">14 days</option>
            <option value="30">30 days</option>
            <option value="60">60 days</option>
            <option value="90">90 days</option>
          </select>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={handleSave}
          isLoading={updateSettings.isPending}
        >
          Save Backup Settings
        </Button>
      </div>

      {/* Status Section */}
      <div className="border-t border-gray-700 pt-4 mt-6">
        <h3 className="text-md font-medium text-white mb-3">Backup Status</h3>

        <div className="bg-gray-700/50 rounded-lg p-4 space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-400">Last Backup:</span>
            <span className="text-white">{formatDate(status?.last_backup_at ?? null)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Status:</span>
            <span className={
              status?.last_backup_status === 'success'
                ? 'text-green-400'
                : status?.last_backup_status === 'failed'
                ? 'text-red-400'
                : 'text-gray-400'
            }>
              {status?.last_backup_status || 'No backups yet'}
            </span>
          </div>
          {status?.last_backup_error && (
            <div className="text-red-400 text-sm mt-2">
              Error: {status.last_backup_error}
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-gray-400">Total Backups:</span>
            <span className="text-white">
              {backupList?.total_count ?? 0} ({formatBytes(backupList?.total_size_bytes ?? 0)})
            </span>
          </div>
        </div>

        {/* Manual Backup Button */}
        <div className="mt-4">
          <Button
            variant="secondary"
            onClick={handleRunBackup}
            isLoading={runBackup.isPending}
          >
            Run Backup Now
          </Button>
        </div>
      </div>
    </div>
  );
}

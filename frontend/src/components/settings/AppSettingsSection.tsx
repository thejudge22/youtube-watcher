import { useState, useEffect } from 'react';
import { useSettings, useUpdateSettings } from '../../hooks/useSettings';
import { Button } from '../common/Button';

export default function AppSettingsSection() {
  const { data: settings, isLoading, error } = useSettings();
  const updateSettings = useUpdateSettings();
  const [httpTimeout, setHttpTimeout] = useState('10.0');
  const [isDirty, setIsDirty] = useState(false);

  // Update local state when settings load
  useEffect(() => {
    if (settings) {
      setHttpTimeout(settings.http_timeout.toString());
    }
  }, [settings]);

  const handleSave = async () => {
    const timeout = parseFloat(httpTimeout);
    if (isNaN(timeout) || timeout < 1 || timeout > 300) {
      alert('HTTP timeout must be between 1 and 300 seconds');
      return;
    }
    await updateSettings.mutateAsync({ http_timeout: timeout });
    setIsDirty(false);
  };

  const handleReset = () => {
    setHttpTimeout(settings?.http_timeout?.toString() || '10.0');
    setIsDirty(false);
  };

  const handleInputChange = (value: string) => {
    setHttpTimeout(value);
    setIsDirty(true);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-text-primary">Application Settings</h2>

      {isLoading ? (
        <div className="text-text-secondary">Loading settings...</div>
      ) : error ? (
        <div className="text-accent-red">Failed to load settings</div>
      ) : (
        <div className="bg-bg-secondary rounded-lg p-6 space-y-6">
          {/* HTTP Timeout Setting */}
          <div className="space-y-3">
            <div>
              <label htmlFor="http-timeout" className="block text-sm font-medium text-text-primary mb-2">
                HTTP Request Timeout
              </label>
              <p className="text-sm text-text-secondary mb-3">
                Maximum time (in seconds) to wait for YouTube/RSS API responses.
                Increase if you experience timeout errors on slow connections.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <input
                id="http-timeout"
                type="number"
                min="1"
                max="300"
                step="1"
                value={httpTimeout}
                onChange={(e) => handleInputChange(e.target.value)}
                className="w-32 px-3 py-2 bg-bg-tertiary border border-border rounded-md text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
                disabled={updateSettings.isPending}
              />
              <span className="text-text-secondary text-sm">seconds (1-300)</span>
            </div>
            <div className="flex gap-2">
              <Button
                variant="primary"
                onClick={handleSave}
                isLoading={updateSettings.isPending}
                disabled={!isDirty || updateSettings.isPending}
              >
                Save Changes
              </Button>
              <Button
                variant="secondary"
                onClick={handleReset}
                disabled={!isDirty || updateSettings.isPending}
              >
                Reset
              </Button>
            </div>
          </div>

          {/* Info Box */}
          <div className="bg-accent-blue/10 border border-accent-blue/30 rounded-lg p-4">
            <p className="text-sm text-accent-blue">
              <strong>Tip:</strong> If you frequently see timeout errors when adding channels or refreshing,
              try increasing this value. The default is 10 seconds. Values between 15-30 seconds are recommended
              for slower connections.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

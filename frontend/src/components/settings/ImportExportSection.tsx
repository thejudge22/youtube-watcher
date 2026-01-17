import { useState, useRef } from 'react';
import {
  useExportChannels,
  useExportSavedVideos,
  useExportAll,
  useImportChannels,
  useImportVideos,
  useImportVideoUrls,
} from '../../hooks/useImportExport';
import { ExportData, ImportResult } from '../../api/client';
import { Button } from '../common/Button';

export default function ImportExportSection() {
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const urlFileInputRef = useRef<HTMLInputElement>(null);

  const exportChannels = useExportChannels();
  const exportSavedVideos = useExportSavedVideos();
  const exportAll = useExportAll();
  const importChannels = useImportChannels();
  const importVideos = useImportVideos();
  const importVideoUrls = useImportVideoUrls();

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
    type: 'channels' | 'videos' | 'all'
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setImportResult(null);
    setImportError(null);

    try {
      const text = await file.text();
      const data: ExportData = JSON.parse(text);

      let result: ImportResult;

      if (type === 'channels' || type === 'all') {
        if (data.channels && data.channels.length > 0) {
          result = await importChannels.mutateAsync(data.channels);
          setImportResult(result);
        }
      }

      if (type === 'videos' || type === 'all') {
        if (data.saved_videos && data.saved_videos.length > 0) {
          result = await importVideos.mutateAsync(data.saved_videos);
          setImportResult(prev => prev ? {
            total: prev.total + result.total,
            imported: prev.imported + result.imported,
            skipped: prev.skipped + result.skipped,
            errors: [...prev.errors, ...result.errors],
          } : result);
        }
      }
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Failed to parse file');
    }

    // Reset input
    event.target.value = '';
  };

  const handleUrlFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setImportResult(null);
    setImportError(null);

    try {
      const text = await file.text();
      const urls = text
        .split('\n')
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('#'));

      if (urls.length === 0) {
        setImportError('No valid URLs found in file');
        return;
      }

      const result = await importVideoUrls.mutateAsync(urls);
      setImportResult(result);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Failed to process file');
    }

    // Reset input
    event.target.value = '';
  };

  const isExporting = exportChannels.isPending || exportSavedVideos.isPending || exportAll.isPending;
  const isImporting = importChannels.isPending || importVideos.isPending || importVideoUrls.isPending;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-white">Import / Export</h2>

      {/* Export Section */}
      <div className="bg-gray-800 rounded-lg p-4 space-y-4">
        <h3 className="font-medium text-white">Export Data</h3>
        <p className="text-sm text-gray-400">
          Download your data as JSON files for backup or migration.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            onClick={() => exportChannels.mutate()}
            isLoading={exportChannels.isPending}
            disabled={isExporting}
          >
            Export Channels
          </Button>
          <Button
            variant="secondary"
            onClick={() => exportSavedVideos.mutate()}
            isLoading={exportSavedVideos.isPending}
            disabled={isExporting}
          >
            Export Saved Videos
          </Button>
          <Button
            variant="primary"
            onClick={() => exportAll.mutate()}
            isLoading={exportAll.isPending}
            disabled={isExporting}
          >
            Export All
          </Button>
        </div>
      </div>

      {/* Import Section */}
      <div className="bg-gray-800 rounded-lg p-4 space-y-4">
        <h3 className="font-medium text-white">Import Data</h3>
        <p className="text-sm text-gray-400">
          Import channels and videos from JSON files or YouTube URLs.
        </p>

        <div className="space-y-3">
          {/* JSON Import */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Import from JSON (channels, videos, or combined export)
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              onChange={(e) => handleFileUpload(e, 'all')}
              className="hidden"
            />
            <Button
              variant="secondary"
              onClick={() => fileInputRef.current?.click()}
              isLoading={importChannels.isPending || importVideos.isPending}
              disabled={isImporting}
            >
              Choose JSON File
            </Button>
          </div>

          {/* URL Import */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Import from URL list (text file with one URL per line)
            </label>
            <input
              ref={urlFileInputRef}
              type="file"
              accept=".txt"
              onChange={handleUrlFileUpload}
              className="hidden"
            />
            <Button
              variant="secondary"
              onClick={() => urlFileInputRef.current?.click()}
              isLoading={importVideoUrls.isPending}
              disabled={isImporting}
            >
              Choose URL File
            </Button>
          </div>
        </div>

        {/* Import Result */}
        {importResult && (
          <div className="mt-4 p-3 bg-gray-700 rounded">
            <p className="font-medium text-green-400">Import Complete</p>
            <p className="text-sm text-gray-300 mt-1">
              Imported: {importResult.imported} | Skipped: {importResult.skipped} | Total: {importResult.total}
            </p>
            {importResult.errors.length > 0 && (
              <div className="mt-2">
                <p className="text-sm text-red-400">Errors ({importResult.errors.length}):</p>
                <ul className="text-xs text-gray-400 mt-1 max-h-32 overflow-y-auto">
                  {importResult.errors.map((error, i) => (
                    <li key={i}>• {error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Import Error */}
        {importError && (
          <div className="mt-4 p-3 bg-red-900/50 rounded">
            <p className="text-red-400">{importError}</p>
          </div>
        )}
      </div>
    </div>
  );
}

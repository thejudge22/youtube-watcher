import { useState, useRef } from 'react';
import {
  useExportChannels,
  useExportSavedVideos,
  useExportAll,
  useImportChannels,
  useImportVideos,
  useImportVideoUrls,
  useImportPlaylist,
} from '../../hooks/useImportExport';
import { ExportData, ImportResult } from '../../api/client';
import { Button } from '../common/Button';

export default function ImportExportSection() {
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [importProgress, setImportProgress] = useState<{ current: number; total: number } | null>(null);
  const [playlistUrl, setPlaylistUrl] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const urlFileInputRef = useRef<HTMLInputElement>(null);

  const exportChannels = useExportChannels();
  const exportSavedVideos = useExportSavedVideos();
  const exportAll = useExportAll();
  const importChannels = useImportChannels();
  const importVideos = useImportVideos();
  const importVideoUrls = useImportVideoUrls();
  const importPlaylist = useImportPlaylist();

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
    type: 'channels' | 'videos' | 'all'
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setImportResult(null);
    setImportError(null);
    setImportProgress(null);

    try {
      const text = await file.text();
      const data: ExportData = JSON.parse(text);

      let result: ImportResult;
      let totalItems = 0;

      if (type === 'channels' || type === 'all') {
        totalItems += data.channels?.length || 0;
      }
      if (type === 'videos' || type === 'all') {
        totalItems += data.saved_videos?.length || 0;
      }

      let processedItems = 0;

      if (type === 'channels' || type === 'all') {
        if (data.channels && data.channels.length > 0) {
          setImportProgress({ current: processedItems, total: totalItems });
          result = await importChannels.mutateAsync(data.channels);
          processedItems += data.channels.length;
          setImportProgress({ current: processedItems, total: totalItems });
          setImportResult(result);
        }
      }

      if (type === 'videos' || type === 'all') {
        if (data.saved_videos && data.saved_videos.length > 0) {
          setImportProgress({ current: processedItems, total: totalItems });
          result = await importVideos.mutateAsync(data.saved_videos);
          processedItems += data.saved_videos.length;
          setImportProgress({ current: processedItems, total: totalItems });
          setImportResult(prev => prev ? {
            total: prev.total + result.total,
            imported: prev.imported + result.imported,
            skipped: prev.skipped + result.skipped,
            errors: [...prev.errors, ...result.errors],
          } : result);
        }
      }

      setImportProgress(null);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Failed to parse file');
      setImportProgress(null);
    }

    // Reset input
    event.target.value = '';
  };

  const handleUrlFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setImportResult(null);
    setImportError(null);
    setImportProgress(null);

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

      // Process in batches of 10 to avoid timeout issues
      const BATCH_SIZE = 10;
      const batches: string[][] = [];
      for (let i = 0; i < urls.length; i += BATCH_SIZE) {
        batches.push(urls.slice(i, i + BATCH_SIZE));
      }

      setImportProgress({ current: 0, total: urls.length });

      // Aggregate results across all batches
      const aggregatedResult: ImportResult = {
        total: 0,
        imported: 0,
        skipped: 0,
        errors: [],
      };

      let processedCount = 0;
      for (const batch of batches) {
        try {
          const batchResult = await importVideoUrls.mutateAsync(batch);
          aggregatedResult.total += batchResult.total;
          aggregatedResult.imported += batchResult.imported;
          aggregatedResult.skipped += batchResult.skipped;
          aggregatedResult.errors.push(...batchResult.errors);
          processedCount += batch.length;
          setImportProgress({ current: processedCount, total: urls.length });
        } catch (batchErr) {
          // If a batch fails, record the error but continue with remaining batches
          const errorMsg = batchErr instanceof Error ? batchErr.message : 'Batch import failed';
          aggregatedResult.errors.push(`Batch error (URLs ${processedCount + 1}-${processedCount + batch.length}): ${errorMsg}`);
          processedCount += batch.length;
          setImportProgress({ current: processedCount, total: urls.length });
        }
      }

      setImportProgress(null);
      setImportResult(aggregatedResult);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Failed to process file');
      setImportProgress(null);
    }

    // Reset input
    event.target.value = '';
  };

  const handlePlaylistImport = async () => {
    const url = playlistUrl.trim();
    if (!url) {
      setImportError('Please enter a playlist URL');
      return;
    }

    setImportResult(null);
    setImportError(null);
    setImportProgress({ current: 0, total: 1 });

    try {
      const result = await importPlaylist.mutateAsync(url);
      setImportProgress({ current: 1, total: 1 });
      setImportResult(result);
      setPlaylistUrl('');
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Failed to import playlist');
    } finally {
      setImportProgress(null);
    }
  };

  const isExporting = exportChannels.isPending || exportSavedVideos.isPending || exportAll.isPending;
  const isImporting = importChannels.isPending || importVideos.isPending || importVideoUrls.isPending || importPlaylist.isPending;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-text-primary">Import / Export</h2>

      {/* Export Section */}
      <div className="bg-bg-secondary rounded-lg p-4 space-y-4">
        <h3 className="font-medium text-text-primary">Export Data</h3>
        <p className="text-sm text-text-secondary">
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
      <div className="bg-bg-secondary rounded-lg p-4 space-y-4">
        <h3 className="font-medium text-text-primary">Import Data</h3>
        <p className="text-sm text-text-secondary">
          Import channels and videos from JSON files, YouTube URLs, or playlists.
        </p>

        <div className="space-y-3">
          {/* JSON Import */}
          <div>
            <label className="block text-sm text-text-secondary mb-2">
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
            <label className="block text-sm text-text-secondary mb-2">
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

          {/* Playlist Import */}
          <div>
            <label className="block text-sm text-text-secondary mb-2">
              Import from YouTube Playlist
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={playlistUrl}
                onChange={(e) => setPlaylistUrl(e.target.value)}
                placeholder="https://www.youtube.com/playlist?list=..."
                className="flex-1 bg-bg-tertiary text-text-primary px-3 py-2 rounded border border-border focus:outline-none focus:border-accent-blue disabled:opacity-50"
                disabled={isImporting}
              />
              <Button
                variant="secondary"
                onClick={handlePlaylistImport}
                isLoading={importPlaylist.isPending}
                disabled={isImporting || !playlistUrl.trim()}
              >
                Import Playlist
              </Button>
            </div>
          </div>
        </div>

        {/* Import Progress */}
        {importProgress && (
          <div className="mt-4 p-3 bg-accent-blue/10 border border-accent-blue/30 rounded">
            <p className="font-medium text-accent-blue">Importing...</p>
            <p className="text-sm text-text-secondary mt-1">
              Processing {importProgress.current} of {importProgress.total} items
            </p>
            <div className="mt-2 w-full bg-bg-tertiary rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(importProgress.current / importProgress.total) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Import Result */}
        {importResult && (
          <div className="mt-4 p-3 bg-bg-tertiary rounded">
            <p className="font-medium text-accent-green">Import Complete</p>
            <p className="text-sm text-text-secondary mt-1">
              Imported: {importResult.imported} | Skipped: {importResult.skipped} | Total: {importResult.total}
            </p>
            {importResult.errors.length > 0 && (
              <div className="mt-2">
                <p className="text-sm text-accent-red">Errors ({importResult.errors.length}):</p>
                <ul className="text-xs text-text-tertiary mt-1 max-h-32 overflow-y-auto">
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
          <div className="mt-4 p-3 bg-accent-red/10 rounded">
            <p className="text-accent-red">{importError}</p>
          </div>
        )}
      </div>
    </div>
  );
}

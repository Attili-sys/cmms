import { useState, useCallback } from 'react';
import downloadFile from 'downloadjs';
import api from 'src/utils/api';

interface UseExportReturn {
  exportEntity: (entity: ExportEntityType) => Promise<void>;
  loadingExport: Record<ExportEntityType, boolean>;
}

export type ExportEntityType =
  | 'work-orders'
  | 'assets'
  | 'locations'
  | 'parts'
  | 'meters'
  | 'preventive-maintenances'
  | 'costs-times'
  | 'part-transactions';

export const useExport = (): UseExportReturn => {
  const [loadingExport, setLoadingExport] = useState<
    Record<ExportEntityType, boolean>
  >({
    'work-orders': false,
    assets: false,
    locations: false,
    parts: false,
    meters: false,
    'preventive-maintenances': false,
    'costs-times': false,
    'part-transactions': false
  });

  const exportEntity = useCallback(
    async (entity: ExportEntityType): Promise<void> => {
      const uuid =
        typeof crypto !== 'undefined' && crypto.randomUUID
          ? crypto.randomUUID()
          : `${Date.now()}`;
      setLoadingExport((prev) => ({ ...prev, [entity]: true }));
      try {
        const res = await api.get<Response>(`export/${entity}?uuid=${uuid}`, {
          raw: true
        });
        const blob = await res.blob();
        downloadFile(blob, `${entity}.csv`);
      } finally {
        setLoadingExport((prev) => ({ ...prev, [entity]: false }));
      }
    },
    []
  );

  return {
    exportEntity,
    loadingExport
  };
};

export default useExport;

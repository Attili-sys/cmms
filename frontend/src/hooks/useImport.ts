import { useState, useCallback } from 'react';
import api from 'src/utils/api';

interface UseImportReturn {
  importEntity: (entity: EntityType, payload: any[]) => Promise<ImportResponse>;
  loadingImport: boolean;
}

export type EntityType =
  | 'work-orders'
  | 'assets'
  | 'locations'
  | 'parts'
  | 'meters'
  | 'preventive-maintenances';

export interface ImportResponse {
  success: boolean;
  created: number;
  updated: number;
  message?: string;
}

export const useImport = (): UseImportReturn => {
  const [loadingImport, setLoadingImport] = useState<boolean>(false);

  const importEntity = useCallback(
    async (entity: EntityType, payload: any[]): Promise<ImportResponse> => {
      const uuid =
        typeof crypto !== 'undefined' && crypto.randomUUID
          ? crypto.randomUUID()
          : `${Date.now()}`;
      setLoadingImport(true);
      try {
        const response = await api.post<ImportResponse>(
          `${basePath}/${entity}?uuid=${uuid}`,
          payload
        );
        return response;
      } finally {
        setLoadingImport(false);
      }
    },
    []
  );

  return {
    importEntity,
    loadingImport
  };
};

const basePath = 'import';

export default useImport;

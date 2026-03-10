import apiClient from './apiClient';

export interface IndexedFile {
    id: number;
    name: string;
    document_id: string;
    indexed_at: string;
    status: string;
}

export interface DriveStatus {
    connected: boolean;
    last_sync: string | null;
}

const driveService = {
    getStatus: async (): Promise<DriveStatus> => {
        const response = await apiClient.get('/drive/status');
        return response.data;
    },

    sync: async (folderId?: string) => {
        const response = await apiClient.post('/drive/sync', { folder_id: folderId });
        return response.data;
    },

    listFiles: async (): Promise<IndexedFile[]> => {
        const response = await apiClient.get('/drive/files');
        return response.data;
    }
};

export default driveService;

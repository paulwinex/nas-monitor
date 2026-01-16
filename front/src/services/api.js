/**
 * API client for NAS Monitor backend
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

class ApiClient {
    /**
     * Get device inventory (called once on page load)
     */
    async getInventory() {
        const response = await fetch(`${API_BASE}/api/inventory`);
        if (!response.ok) throw new Error('Failed to fetch inventory');
        return response.json();
    }

    /**
     * Get frontend configuration
     */
    async getConfig() {
        const response = await fetch(`${API_BASE}/api/config`);
        if (!response.ok) throw new Error('Failed to fetch config');
        return response.json();
    }

    /**
     * Get metrics with time range filtering
     * @param {Object} params - Query parameters
     * @param {string} params.history_type - 'raw', 'daily', or 'history'
     * @param {string[]} params.device_types - Optional device types filter
     * @param {number} params.hours - Get metrics for last N hours
     */
    async getMetrics(params) {
        const queryParams = new URLSearchParams();

        if (params.history_type) queryParams.append('history_type', params.history_type);
        if (params.device_types) {
            params.device_types.forEach(type => queryParams.append('device_types', type));
        }
        if (params.device_names) {
            params.device_names.forEach(name => queryParams.append('device_names', name));
        }
        if (params.hours !== undefined) queryParams.append('hours', params.hours);

        const response = await fetch(`${API_BASE}/api/metrics?${queryParams}`);
        if (!response.ok) throw new Error('Failed to fetch metrics');
        return response.json();
    }

    /**
     * Get latest metric values for current indicators
     * @param {string[]} device_types - Optional device types filter
     */
    async getLatest(device_types = null) {
        const queryParams = new URLSearchParams();
        if (device_types) {
            device_types.forEach(type => queryParams.append('device_types', type));
        }

        const response = await fetch(`${API_BASE}/api/latest?${queryParams}`);
        if (!response.ok) throw new Error('Failed to fetch latest metrics');
        return response.json();
    }

    /**
     * Get all registered devices
     */
    async listDevices() {
        const response = await fetch(`${API_BASE}/api/devices`);
        if (!response.ok) throw new Error('Failed to list devices');
        return response.json();
    }

    /**
     * Update device settings
     */
    async updateDevice(name, payload) {
        const response = await fetch(`${API_BASE}/api/devices/${name}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error('Failed to update device');
        return response.json();
    }

    /**
     * Get detailed system information
     */
    async getSystemInfo() {
        const response = await fetch(`${API_BASE}/api/system/info`);
        if (!response.ok) throw new Error('Failed to get system info');
        return response.json();
    }

    /**
     * Reboot the host
     */
    async restartHost() {
        const response = await fetch(`${API_BASE}/api/host/restart`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to restart host');
        return response.json();
    }

    /**
     * Power off the host
     */
    async poweroffHost() {
        const response = await fetch(`${API_BASE}/api/host/poweroff`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to power off host');
        return response.json();
    }
}

export const api = new ApiClient();

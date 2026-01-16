import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { api } from 'src/services/api';

export const useDeviceStore = defineStore('devices', () => {
    // State
    const inventory = ref(null);
    const configData = ref(null);
    const metrics = ref({});
    const detailMetrics = ref([]);
    const selectedDevice = ref(null);
    const allDevices = ref([]);
    const latestValues = ref({});
    const systemInfo = ref(null);
    const uptimeSeconds = ref(0);
    const isConnected = ref(true);
    const loading = ref(false);
    const error = ref(null);

    // Polling timers
    const pollingTimers = ref({});

    // Getters
    const zpools = computed(() => inventory.value?.data?.zpools || []);

    const systemDevices = computed(() => inventory.value?.data?.system_devices || {});

    const cpu = computed(() => systemDevices.value.cpu);
    const ram = computed(() => systemDevices.value.ram);
    const network = computed(() => systemDevices.value.network);
    const standaloneStorage = computed(() => systemDevices.value.storage || []);

    const updateIntervals = computed(() => configData.value?.data?.update_intervals || {});
    const smartStatusLevels = computed(() => configData.value?.data?.smart_status_levels || {});

    /**
     * Get metrics for a specific device
     */
    const getDeviceMetrics = (deviceName) => {
        return metrics.value[deviceName] || [];
    };

    /**
     * Get latest value for a device metric
     */
    const getLatestValue = (deviceName, label) => {
        return latestValues.value[deviceName]?.[label];
    };

    /**
     * Load inventory (called once on page load)
     */
    async function loadInventory() {
        try {
            loading.value = true;
            error.value = null;
            inventory.value = await api.getInventory();
            if (inventory.value?.data?.uptime_seconds) {
                uptimeSeconds.value = inventory.value.data.uptime_seconds;
            }
            isConnected.value = true;
        } catch (e) {
            isConnected.value = false;
            error.value = 'Failed to connect to server';
            console.error('Failed to load inventory:', e);
            startReconnectionLoop();
        } finally {
            loading.value = false;
        }
    }

    /**
     * Load configuration
     */
    async function loadConfig() {
        try {
            configData.value = await api.getConfig();
        } catch (e) {
            error.value = e.message;
            console.error('Failed to load config:', e);
        }
    }

    /**
     * Update metrics for specific device types
     */
    async function updateMetrics(deviceTypes = null, hours = 1) {
        try {
            const response = await api.getMetrics({
                history_type: 'raw',
                device_types: deviceTypes,
                hours: hours
            });

            // Group metrics by device
            const metricsByDevice = {};
            response.data.forEach(metric => {
                if (!metricsByDevice[metric.device_name]) {
                    metricsByDevice[metric.device_name] = [];
                }
                metricsByDevice[metric.device_name].push(metric);
            });

            // Merge with existing metrics
            metrics.value = { ...metrics.value, ...metricsByDevice };
        } catch (e) {
            console.error('Failed to update metrics:', e);
        }
    }

    /**
     * Update latest values for current indicators
     */
    async function updateLatestValues(deviceTypes = null) {
        if (!isConnected.value) return;
        try {
            const response = await api.getLatest(deviceTypes);
            latestValues.value = { ...latestValues.value, ...response.data };
            isConnected.value = true;
        } catch (e) {
            console.error('Failed to update latest values:', e);
            isConnected.value = false;
            startReconnectionLoop();
        }
    }

    /**
     * Fetch detailed metrics for a specific device and range
     */
    async function fetchDetailMetrics(deviceName, historyType = 'raw', hours = 24) {
        try {
            loading.value = true;
            const response = await api.getMetrics({
                history_type: historyType,
                device_names: [deviceName],
                hours: historyType === 'raw' ? hours : null
            });
            detailMetrics.value = response.data;
        } catch (e) {
            console.error('Failed to fetch detail metrics:', e);
        } finally {
            loading.value = false;
        }
    }

    /**
     * List all devices (for settings)
     */
    async function fetchAllDevices() {
        try {
            const response = await api.listDevices();
            allDevices.value = response.data;
        } catch (e) {
            console.error('Failed to fetch all devices:', e);
        }
    }

    /**
     * Update device enabled status
     */
    async function updateDeviceStatus(name, enabled) {
        try {
            await api.updateDevice(name, { enabled });
            await loadInventory(); // Refresh dashboard inventory
        } catch (e) {
            console.error('Failed to update device status:', e);
        }
    }

    /**
     * Get detailed system info
     */
    async function fetchSystemInfo() {
        try {
            const response = await api.getSystemInfo();
            systemInfo.value = response.data;
        } catch (e) {
            console.error('Failed to fetch system info:', e);
        }
    }

    /**
     * Trigger host reboot
     */
    async function rebootHost() {
        try {
            await api.restartHost();
        } catch (e) {
            console.error('Failed to reboot host:', e);
            throw e;
        }
    }

    /**
     * Trigger host shutdown
     */
    async function shutdownHost() {
        try {
            await api.poweroffHost();
        } catch (e) {
            console.error('Failed to shutdown host:', e);
            throw e;
        }
    }

    let reconnectionTimer = null;
    function startReconnectionLoop() {
        if (reconnectionTimer) return;

        console.log('Starting reconnection loop...');
        // Stop all polling to prevent flooding console with errors while offline
        stopAllPolling();

        reconnectionTimer = setInterval(async () => {
            if (isConnected.value) {
                clearInterval(reconnectionTimer);
                reconnectionTimer = null;
                return;
            }

            try {
                const data = await api.getInventory();
                // Check for successful response and required data structure
                if (data && data.status === 'success') {
                    console.log('Server is back! Performing full re-initialization...');

                    // Clear the timer first
                    clearInterval(reconnectionTimer);
                    reconnectionTimer = null;

                    // Reset error state
                    error.value = null;

                    // Perform full initialization (loads inventory, config, and starts polling)
                    await initialize();
                }
            } catch (e) {
                // Still down
            }
        }, 3000);
    }

    /**
     * Start polling for specific device types
     */
    function startPolling(deviceType) {
        if (!configData.value) {
            console.warn('Config not loaded, cannot start polling');
            return;
        }

        const interval = updateIntervals.value[deviceType];
        if (!interval) {
            console.warn(`No interval configured for device type: ${deviceType}`);
            return;
        }

        // Clear existing timer if any
        if (pollingTimers.value[deviceType]) {
            clearInterval(pollingTimers.value[deviceType]);
        }

        // Start new timer
        pollingTimers.value[deviceType] = setInterval(async () => {
            await updateMetrics([deviceType]);
            await updateLatestValues([deviceType]);
        }, interval * 1000);

        // Initial fetch
        updateMetrics([deviceType]);
        updateLatestValues([deviceType]);
    }

    /**
     * Start polling for all device types
     */
    function startAllPolling() {
        const deviceTypes = ['cpu', 'ram', 'network', 'storage', 'zfs_pool'];
        deviceTypes.forEach(type => startPolling(type));
    }

    /**
     * Stop polling for specific device type
     */
    function stopPolling(deviceType) {
        if (pollingTimers.value[deviceType]) {
            clearInterval(pollingTimers.value[deviceType]);
            delete pollingTimers.value[deviceType];
        }
    }

    /**
     * Stop all polling
     */
    function stopAllPolling() {
        Object.keys(pollingTimers.value).forEach(type => {
            clearInterval(pollingTimers.value[type]);
        });
        pollingTimers.value = {};
    }

    /**
     * Initialize store (load inventory and config, start polling)
     */
    async function initialize() {
        await loadInventory();
        await loadConfig();
        startAllPolling();
    }

    return {
        // State
        inventory,
        configData,
        metrics,
        detailMetrics,
        selectedDevice,
        allDevices,
        systemInfo,
        uptimeSeconds,
        isConnected,
        loading,
        error,

        // Getters
        zpools,
        systemDevices,
        cpu,
        ram,
        network,
        standaloneStorage,
        updateIntervals,
        smartStatusLevels,

        // Methods
        getDeviceMetrics,
        getLatestValue,
        loadInventory,
        loadConfig,
        updateMetrics,
        updateLatestValues,
        fetchDetailMetrics,
        fetchAllDevices,
        updateDeviceStatus,
        fetchSystemInfo,
        rebootHost,
        shutdownHost,
        startPolling,
        startAllPolling,
        stopPolling,
        stopAllPolling,
        initialize
    };
});

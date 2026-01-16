<template>
  <MetricsPanel :cols="2" min-col-width="200px">
    <template #title>
      <span class="text-subtitle2 text-weight-bolder text-blue-4 uppercase tracking-1">System</span>
    </template>

    <template #header-right>
      <div class="text-mono text-grey-5" style="font-size: 11px;">
        UPTIME: <span class="text-white q-ml-xs">{{ formattedUptime }}</span>
      </div>
      <q-btn icon="info" size="sm" class="q-ml-md" dense color="grey" flat />
    </template>

    <!-- CPU -->
    <MetricBaseWidget
      v-if="deviceStore.cpu"
      label="CPU"
      :value="cpuLoad + '%'"
      :temp="cpuTemp"
      :history="cpuHistory"
      min="0"
      max="100"
      color="#2E93FA"
      @click="handleWidgetClick"
    />

    <!-- RAM -->
    <MetricBaseWidget
      v-if="deviceStore.ram"
      label="RAM"
      :value="ramUsagePercent + '%'"
      :temp="ramTemp"
      :history="ramHistory"
      :extra-info="ramGbInfo"
      min="0"
      max="100"
      color="#00E396"
      @click="handleWidgetClick"
    />

    <!-- Network -->
    <NetworkWidget
      v-if="deviceStore.network"
      :upSpeed="netUpload + ' KB/s'"
      :downSpeed="netDownload + ' KB/s'"
      :upHistory="netUpHistory"
      :downHistory="netDownHistory"
      @click="handleWidgetClick"
    />

    <!-- Standalone Storage Devices -->
    <DiskUsageWidget
      v-for="disk in deviceStore.standaloneStorage"
      :key="disk.name"
      :path="disk.details?.path || disk.name"
      :temp="getDiskTemp(disk.name)"
      :used="getDiskMetric(disk.name, 'used_gb')"
      :total="getDiskMetric(disk.name, 'total_gb')"
      @click="handleWidgetClick"
    />

  </MetricsPanel>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue';
import { useDeviceStore } from 'src/stores/deviceStore';
import MetricBaseWidget from './MetricBaseWidget.vue';
import NetworkWidget from './NetworkWidget.vue';
import DiskUsageWidget from './DiskUsageWidget.vue';
import MetricsPanel from "./MetricsPanel.vue";

const deviceStore = useDeviceStore();

const handleWidgetClick = (id) => {
  console.log('Widget clicked:', id);
};

// Start initialization if not already started
onMounted(() => {
  if (!deviceStore.inventory) {
    deviceStore.initialize();
  }
});

// CPU metrics
const cpuLoad = computed(() => {
  const load = deviceStore.getLatestValue('cpu', 'load');
  return load !== undefined ? Math.round(load * 10) / 10 : 0;
});

const cpuTemp = computed(() => {
  const temp = deviceStore.getLatestValue('cpu', 'temp');
  return temp !== undefined ? Math.round(temp) : 0;
});

const cpuHistory = computed(() => {
  const metrics = deviceStore.getDeviceMetrics('cpu');
  return metrics
    .filter(m => m.label === 'load')
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    .slice(-40)
    .map(m => Math.round(m.value * 10) / 10);
});

// RAM metrics
const ramUsagePercent = computed(() => {
  const percent = deviceStore.getLatestValue('ram', 'usage_percent');
  return percent !== undefined ? Math.round(percent * 10) / 10 : 0;
});

const ramHistory = computed(() => {
  const metrics = deviceStore.getDeviceMetrics('ram');
  return metrics
    .filter(m => m.label === 'usage_percent')
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    .slice(-40)
    .map(m => Math.round(m.value * 10) / 10);
});

const ramTemp = computed(() => {
  const temp = deviceStore.getLatestValue('ram', 'temp');
  return temp !== undefined ? Math.round(temp) : 0;
});


const ramGbInfo = computed(() => {
  const used = deviceStore.getLatestValue('ram', 'used_gb');
  const total = deviceStore.ram?.details?.total_gb;
  if (used !== undefined && total !== undefined) {
    return `${used.toFixed(1)} / ${total.toFixed(0)} GB`;
  }
  return '';
});

// Network metrics
const netUpload = computed(() => {
  const upload = deviceStore.getLatestValue('net', 'upload');
  return upload !== undefined ? Math.round(upload * 10) / 10 : 0;
});

const netDownload = computed(() => {
  const download = deviceStore.getLatestValue('net', 'download');
  return download !== undefined ? Math.round(download * 10) / 10 : 0;
});

const netUpHistory = computed(() => {
  const metrics = deviceStore.getDeviceMetrics('net');
  return metrics
    .filter(m => m.label === 'upload')
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    .slice(-40)
    .map(m => Math.round(m.value * 10) / 10);
});

const netDownHistory = computed(() => {
  const metrics = deviceStore.getDeviceMetrics('net');
  return metrics
    .filter(m => m.label === 'download')
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    .slice(-40)
    .map(m => Math.round(m.value * 10) / 10);
});

// Helper for disk temperature
const getDiskTemp = (diskName) => {
  const temp = deviceStore.getLatestValue(diskName, 'temp');
  return temp !== undefined ? Math.round(temp) : 0;
};

// Helper for disk usage
const getDiskMetric = (diskName, label) => {
  const val = deviceStore.getLatestValue(diskName, label);
  return val !== undefined ? val : 0;
};


// Uptime (mock for now as it's not in the store yet)
const uptimeSeconds = ref(1052100);
const formattedUptime = computed(() => {
  const d = Math.floor(uptimeSeconds.value / 86400);
  const h = Math.floor((uptimeSeconds.value % 86400) / 3600);
  return `${d}d ${h}h`;
});
</script>




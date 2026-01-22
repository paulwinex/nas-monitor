<template>
  <q-dialog
    v-model="isOpen"
    maximized
    transition-show="slide-up"
    transition-show-duration="300"
    transition-hide="slide-down"
    transition-hide-duration="300"
  >
    <q-card class="bg-black text-white">
      <q-bar class="bg-header border-bottom-dark header-height">
        <div class="row items-center full-width no-wrap">
          <q-icon :name="getDeviceIcon(device?.type)" color="blue-4" size="20px" />
          <div class="text-subtitle2 q-ml-sm text-weight-bold uppercase tracking-1">
            {{ device?.name }} <span class="text-grey-6 text-weight-regular q-ml-xs">| {{ device?.type }}</span>
          </div>
          <q-space />
          <q-btn dense flat icon="close" v-close-popup>
            <q-tooltip class="bg-white text-primary">Close</q-tooltip>
          </q-btn>
        </div>
      </q-bar>

      <div class="q-pa-md">
        <!-- Range Selector -->
        <div class="row justify-center q-mb-md">
          <q-tabs
            v-model="selectedRange"
            dense
            class="text-grey-5 bg-grey-10 border-dark-thin rounded-borders"
            active-color="blue-4"
            indicator-color="blue-4"
            align="justify"
            narrow-indicator
            @update:model-value="loadDetailedMetrics"
          >
            <q-tab name="1h" label="1h" />
            <q-tab name="12h" label="12h" />
            <q-tab name="24h" label="24h" />
            <q-tab name="1w" label="1w" />
            <q-tab name="1m" label="1m" />
            <q-tab name="1y" label="1y" />
          </q-tabs>
        </div>

        <div class="row q-col-gutter-md">
          <!-- Left: Detailed Stats -->
          <div class="col-12 col-md-3">
            <q-card flat bordered class="bg-disk border-dark-thin full-height">
              <q-card-section>
                <div class="text-subtitle2 text-blue-4 q-mb-md">DEVICE DETAILS</div>
                <dl class="text-mono">
                  <div class="row justify-between no-wrap">
                    <dt class="text-grey-6 text-caption text-uppercase">NAME / SN</dt>
                    <dd class="text-blue-2 text-weight-bold text-mono" style="font-size: 11px;">{{ device?.name }}</dd>
                  </div>
                  <q-separator color="grey-9" class="q-my-xs" />
                  <template v-for="(val, key) in device?.details" :key="key">
                    <div class="row justify-between no-wrap">
                      <dt class="text-grey-6 text-caption text-uppercase">{{ key }}</dt>
                      <dd class="text-white text-weight-bold text-mono" style="font-size: 11px;">{{ val }}</dd>
                    </div>
                  </template>
                </dl>
              </q-card-section>
            </q-card>
          </div>

          <!-- Right: Main Chart -->
          <div class="col-12 col-md-9">
            <q-card flat bordered class="bg-disk border-dark-thin" style="min-height: 400px;">
              <q-card-section class="full-height flex flex-center" v-if="deviceStore.loading">
                <q-spinner color="blue-4" size="40px" />
              </q-card-section>
              <q-card-section v-else class="full-height">
                <apexchart
                  type="area"
                  height="400"
                  :options="chartOptions"
                  :series="chartSeries"
                />
              </q-card-section>
            </q-card>
          </div>
        </div>
      </div>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useDeviceStore } from 'src/stores/deviceStore';
import VueApexCharts from 'vue3-apexcharts';

const apexchart = VueApexCharts;
const deviceStore = useDeviceStore();

const isOpen = computed({
  get: () => !!deviceStore.selectedDevice,
  set: (val) => { if (!val) deviceStore.selectedDevice = null; }
});

const device = computed(() => deviceStore.selectedDevice);
const selectedRange = ref('1h');

const getDeviceIcon = (type) => {
  const icons = {
    cpu: 'memory',
    ram: 'subtitles',
    network: 'swap_vertical_circle',
    storage: 'storage',
    zfs_pool: 'titans'
  };
  return icons[type] || 'devices';
};

const CHART_COLORS = ['#2E93FA', '#00E396', '#FEB019', '#FF4560', '#775DD0', '#546E7A'];

const DEVICE_METRICS_FILTER = {
  cpu: ['load', 'temp'],
  ram: ['usage_percent', 'temp'],
  network: ['upload', 'download', 'upload_speed', 'download_speed'],
  storage: ['usage_percent', 'temp'],
  zfs_pool: ['usage_percent']
};

async function loadDetailedMetrics() {
  if (!device.value) return;
  
  let historyType = 'raw';
  let hours = 1;
  
  switch (selectedRange.value) {
    case '1h': hours = 1; break;
    case '12h': hours = 12; break;
    case '24h': hours = 24; break;
    case '1w': historyType = 'hourly'; hours = 24 * 7; break;
    case '1m': historyType = 'hourly'; hours = 24 * 30; break;
    case '1y': historyType = 'history'; hours = 24 * 365; break;
  }
  
  await deviceStore.fetchDetailMetrics(device.value.name, historyType, hours);
}

// Watch for device change to load metrics
watch(device, (newDev) => {
  if (newDev) {
    deviceStore.detailMetrics = [];
    selectedRange.value = '1h';
    loadDetailedMetrics();
  }
});

const chartSeries = computed(() => {
  const metrics = deviceStore.detailMetrics;
  if (!metrics || metrics.length === 0 || !device.value) return [];

  const allowedLabels = DEVICE_METRICS_FILTER[device.value.type] || [];

  // Group by label
  const groups = {};
  metrics.forEach(m => {
    // Safeguard: only show metrics for the selected device
    if (m.device_name !== device.value.name) return;
    
    if (allowedLabels.length > 0 && !allowedLabels.includes(m.label)) return;
    
    if (!groups[m.label]) groups[m.label] = [];
    groups[m.label].push({
      x: new Date(m.timestamp).getTime(),
      y: m.value
    });
  });

  return Object.keys(groups).map(label => ({
    name: label.toUpperCase(),
    data: groups[label].sort((a, b) => a.x - b.x)
  }));
});

const chartOptions = computed(() => ({
  chart: {
    type: 'area',
    background: 'transparent',
    foreColor: '#999',
    toolbar: { 
      show: true, 
      theme: 'dark',
      tools: {
        download: false,
        selection: true,
        zoom: true,
        zoomin: true,
        zoomout: true,
        pan: true,
        reset: true,
        menu: false,
        customIcons: []
      }
    },
    animations: { enabled: false }
  },
  dataLabels: { enabled: false },
  colors: CHART_COLORS,
  stroke: { curve: 'smooth', width: 2 },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.45,
      opacityTo: 0.05,
      stops: [20, 100]
    }
  },
  xaxis: {
    type: 'datetime',
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: {
    labels: {
      formatter: (val) => val.toFixed(1)
    }
  },
  grid: {
    borderColor: '#1f1f1f',
    strokeDashArray: 4
  },
  tooltip: {
    theme: 'dark',
    x: { format: 'dd MMM HH:mm:ss' }
  },
  legend: {
    position: 'bottom',
    horizontalAlign: 'center',
    offsetY: 8,
    itemMargin: {
      horizontal: 10,
      vertical: 5
    }
  }
}));
</script>

<style scoped>
.bg-header { background: #121212 !important; }
.bg-disk { background: #161616; }
.border-bottom-dark { border-bottom: 1px solid #1f1f1f; }
.border-dark-thin { border: 1px solid #1f1f1f; }
.header-height { height: 36px; }
.tracking-1 { letter-spacing: 1px; }
.rounded-borders { border-radius: 4px; }
dl, dd { margin: 0; }
</style>

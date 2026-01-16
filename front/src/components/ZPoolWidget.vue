<template>
  <MetricsPanel :cols="3" min-col-width="150px">
    <template #title>
      <span 
        class="text-subtitle2 text-weight-bolder text-blue-4 uppercase tracking-1 cursor-pointer" 
        @click="deviceStore.selectedDevice = pool"
      >{{ pool.name }}</span>
      <q-badge color="green-9" class="q-ml-sm text-weight-bold" label="ONLINE" size="10px" />
    </template>

    <template #header-right>
      <span class="text-grey-5 q-mr-sm" style="font-size: 11px;">{{ poolUsage }}</span>
      <div style="width: 50px"><q-linear-progress :value="usagePercent / 100" color="blue-6" track-color="grey-6" /></div>
      <q-btn icon="info" size="sm" class="q-ml-md" dense color="grey" flat />
    </template>

    <ZfsDiskWidget
      v-for="(disk, index) in pool.disks"
      :key="disk.name"
      :disk="disk"
      :accent-color="CHART_COLORS[index % CHART_COLORS.length]"
      @click="onDiskHandle"
    />
  </MetricsPanel>
</template>

<script setup>
import { computed } from 'vue';
import { useDeviceStore } from 'src/stores/deviceStore';
import ZfsDiskWidget from './ZfsDiskWidget.vue';
import MetricsPanel from "components/MetricsPanel.vue";

const props = defineProps({
  pool: {
    type: Object,
    required: true
  }
});

const deviceStore = useDeviceStore();

const CHART_COLORS = ['#2E93FA', '#00E396', '#FEB019', '#FF4560', '#775DD0', '#546E7A'];

// Get pool usage from latest metrics
const usedGb = computed(() => deviceStore.getLatestValue(props.pool.name, 'used_gb') || 0);
const totalGb = computed(() => {
  const latestTotal = deviceStore.getLatestValue(props.pool.name, 'total_gb');
  if (latestTotal) return latestTotal;
  // Fallback to inventory max_size parsing if metric not yet available
  const ms = props.pool.details?.max_size || '0';
  const val = parseFloat(ms);
  return ms.toUpperCase().includes('T') ? val * 1024 : val;
});

const usagePercent = computed(() => {
  const percent = deviceStore.getLatestValue(props.pool.name, 'usage_percent');
  if (percent !== undefined) return percent;
  return totalGb.value > 0 ? (usedGb.value / totalGb.value * 100) : 0;
});

const poolUsage = computed(() => {
  const used = usedGb.value;
  const total = totalGb.value;
  
  const formatSize = (gb) => {
    if (gb >= 1024) return `${(gb/1024).toFixed(1)} TB`;
    return `${gb.toFixed(1)} GB`;
  };

  return `${formatSize(used)} / ${formatSize(total)}`;
});


const onDiskHandle = (disk) => {
  deviceStore.selectedDevice = disk;
};
</script>

<style scoped>
.bg-dark-page { background: #0a0a0a; }
.bg-header { background: #121212; }
.border-bottom-dark { border-bottom: 1px solid #1f1f1f; }
.zfs-pool-widget { border: 1px solid #1f1f1f; border-radius: 4px; overflow: hidden; }

.disk-grid {
  display: grid;
  grid-template-rows: repeat(2, 48px);
  grid-auto-flow: column;
  grid-auto-columns: minmax(200px, 1fr);
  gap: 8px;
  padding: 4px;
  overflow-x: auto;
}
</style>


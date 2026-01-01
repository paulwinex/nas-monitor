<template>
  <MetricsPanel :cols="3" min-col-width="150px">
    <template #title>
      <span class="text-subtitle2 text-weight-bolder text-blue-4 uppercase tracking-1">{{ poolState.name }}</span>
      <q-badge color="green-9" class="q-ml-sm text-weight-bold" label="ONLINE" size="10px" />
    </template>

    <template #header-right>
      <span class="text-grey-5 q-mr-sm" style="font-size: 11px;">{{ poolState.usedSize }} / {{ poolState.totalSize }}</span>
      <div style="width: 50px"><q-linear-progress :value="0.6" color="blue-6" track-color="grey-6" /></div>
      <q-btn icon="info" size="sm" class="q-ml-md" dense color="grey" flat />
    </template>

    <ZfsDiskWidget
      v-for="(disk, index) in poolState.disks"
      :key="disk.sn"
      :disk="disk"
      :accent-color="CHART_COLORS[index % CHART_COLORS.length]"
      @click="onDiskHandle"
    />
  </MetricsPanel>
</template>

<script setup>
import { reactive, onMounted, onUnmounted } from 'vue';
import ZfsDiskWidget from './ZfsDiskWidget.vue';
import MetricsPanel from "components/MetricsPanel.vue";

const CHART_COLORS = ['#2E93FA', '#00E396', '#FEB019', '#FF4560', '#775DD0', '#546E7A'];

const poolState = reactive({
  name: 'STORE',
  usedSize: '4.2 TB',
  totalSize: '26.0 TB',
  disks: [
    { path: '/dev/sda', model: 'HGST Ultrastar', sn: 'K7G8L9P0', temp: 32, smart: 'OK', history: Array(21).fill(32) },
    { path: '/dev/sdb', model: 'HGST Ultrastar', sn: 'K7G8L9P1', temp: 33, smart: 'OK', history: Array(21).fill(33) },
    { path: '/dev/sdc', model: 'HGST Ultrastar', sn: 'K7G8L9P2', temp: 41, smart: 'OK', history: Array(21).fill(41) },
    { path: '/dev/sdd', model: 'HGST Ultrastar', sn: 'K7G8L9P3', temp: 34, smart: 'OK', history: Array(21).fill(34) },
    { path: '/dev/sde', model: 'Crucial MX500', sn: 'CT500MX1', temp: 29, smart: 'OK', history: Array(21).fill(29) },
    { path: '/dev/sdf', model: 'Crucial MX500', sn: 'CT500MX2', temp: 30, smart: 'OK', history: Array(21).fill(30) },
  ]
});

const fetchPoolData = () => {
  poolState.disks.forEach(disk => {
    const variation = Math.floor(Math.random() * 3) - 1;
    const newTemp = Math.max(20, Math.min(60, disk.temp + variation));
    disk.temp = newTemp;
    disk.history.push(newTemp);
    if (disk.history.length > 21) disk.history.shift();
  });
};

let pollingTimer = null;
onMounted(() => {
  fetchPoolData();
  pollingTimer = setInterval(fetchPoolData, 5000);
});

onUnmounted(() => {
  if (pollingTimer) clearInterval(pollingTimer);
});

const onDiskHandle = (disk) => {
  console.log('Action for disk:', disk.path);
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

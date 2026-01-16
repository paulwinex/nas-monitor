<template>
  <q-dialog v-model="isOpen" persistent @keydown.esc="isOpen = false">
    <q-card style="min-width: 350px;" class="bg-disk text-white border-dark-thin">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-subtitle1 text-weight-bold text-blue-4 uppercase tracking-1">Panel Settings</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section class="q-pt-md">
        <div class="text-caption text-grey-6 q-mb-sm">Select devices to display on this panel:</div>
        <q-list dense>
          <q-item v-for="device in localDevices" :key="device.name" tag="label" v-ripple class="q-px-none">
            <q-item-section avatar>
              <q-checkbox v-model="device.enabled" color="blue-4" dark />
            </q-item-section>
            <q-item-section>
              <q-item-label class="text-weight-medium">{{ device.name }}</q-item-label>
              <q-item-label caption class="text-grey-5">{{ device.type }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-card-section>

      <q-card-actions align="right" class="q-pb-md q-px-md">
        <q-btn flat label="Cancel" color="grey-6" v-close-popup />
        <q-btn unelevated label="Save" color="blue-7" @click="handleSave" :loading="saving" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useDeviceStore } from 'src/stores/deviceStore';

const props = defineProps({
  modelValue: Boolean,
  panelType: String, // 'system' or 'zfs_pool'
  poolName: String    // Required if panelType is 'zfs_pool'
});

const emit = defineEmits(['update:modelValue', 'save']);

const deviceStore = useDeviceStore();
const saving = ref(false);

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

// Local state for checkboxes
const localDevices = ref([]);

// Initialize local state when dialog opens
watch(isOpen, async (val) => {
  if (val) {
    await deviceStore.fetchAllDevices();
    const all = deviceStore.allDevices;
    
    if (props.panelType === 'zfs_pool') {
      // Find all disks that belong to this pool
      localDevices.value = all.filter(d => 
        d.type === 'storage' && d.details?.zfs_pool === props.poolName
      ).map(d => ({ ...d }));
    } else if (props.panelType === 'system') {
      // 1. Count members for each pool among all devices
      const poolCounts = {};
      all.forEach(d => {
        if (d.type === 'storage' && d.details?.zfs_pool) {
          const p = d.details.zfs_pool;
          poolCounts[p] = (poolCounts[p] || 0) + 1;
        }
      });

      // 2. CPU, RAM, Network, and standalone storage (no pool OR single-disk pool)
      localDevices.value = all.filter(d => {
        if (['cpu', 'ram', 'network'].includes(d.type)) return true;
        if (d.type === 'storage') {
          const p = d.details?.zfs_pool;
          if (!p || poolCounts[p] <= 1) return true;
        }
        return false;
      }).map(d => ({ ...d }));
    } else {
      localDevices.value = all.map(d => ({ ...d }));
    }
  }
});

const handleSave = async () => {
  saving.value = true;
  try {
    // Update each device that changed
    for (const localDev of localDevices.value) {
      const original = deviceStore.allDevices.find(d => d.name === localDev.name);
      if (original && original.enabled !== localDev.enabled) {
        await deviceStore.updateDeviceStatus(localDev.name, localDev.enabled);
      }
    }
    emit('save');
    isOpen.value = false;
  } catch (e) {
    console.error('Failed to save settings:', e);
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
.bg-disk { background: #161616; }
.border-dark-thin { border: 1px solid #1f1f1f; }
.tracking-1 { letter-spacing: 1px; }
</style>

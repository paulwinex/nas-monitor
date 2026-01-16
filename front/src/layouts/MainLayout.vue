<template>
  <q-layout view="lHh Lpr lFf" class="bg-black">
    <q-header elevated class="bg-dark border-bottom-dark">
      <q-toolbar>
        <q-toolbar-title class="text-weight-bold text-blue-4">
          NAS Monitor
        </q-toolbar-title>


        <q-space/>

        <q-btn icon="menu" flat dense rounded>
          <q-menu
            dark
            square
            transition-show="jump-down"
            transition-hide="jump-up"
          >
            <q-list style="min-width: 200px" class="menu-list-dark shadow-24">
              <q-item clickable v-close-popup @click="showSystemInfo = true">
                <q-item-section avatar><q-icon name="info" size="xs"/></q-item-section>
                <q-item-section>System Info</q-item-section>
              </q-item>

              <q-separator dark />
              <q-item clickable v-close-popup @click="confirmPowerAction('restart')">
                <q-item-section avatar><q-icon name="restart_alt" size="xs"/></q-item-section>
                <q-item-section>Restart</q-item-section>
              </q-item>

              <q-item clickable v-close-popup @click="confirmPowerAction('poweroff')">
                <q-item-section avatar><q-icon name="power_settings_new" size="xs"/></q-item-section>
                <q-item-section>Power Off</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>

    <SystemInfoDialog v-model="showSystemInfo" />
  </q-layout>
</template>

<style>
.menu-list-dark {
  background: #1a1a1a !important;
  border: 1px solid #333 !important;
  opacity: 1 !important;
}
.q-menu.q-dark {
  box-shadow: 0 10px 30px rgba(0,0,0,0.8) !important;
}
.bg-dark {
  background: #121212 !important;
}
.border-bottom-dark {
  border-bottom: 1px solid #1f1f1f;
}

.apexcharts-canvas {
  z-index: 1 !important;
}

.q-menu, .q-dialog__inner {
  z-index: 6000 !important;
}
.main-menu-custom, .menu-list-dark {
  background-color: #1a1a1a !important;
  opacity: 1 !important;
}
.apexcharts-canvas,
.q-card,
.metrics-panel {
  z-index: 1;
}
</style>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { useDeviceStore } from 'src/stores/deviceStore';
import SystemInfoDialog from 'src/components/SystemInfoDialog.vue';

const $q = useQuasar();
const deviceStore = useDeviceStore();
const showSystemInfo = ref(false);

const confirmPowerAction = (action: 'restart' | 'poweroff') => {
  const isRestart = action === 'restart';
  
  $q.dialog({
    title: isRestart ? 'Confirm Restart' : 'Confirm Power Off',
    message: isRestart 
      ? 'Are you sure you want to RESTART the host? The dashboard will be unavailable until it boots back up.' 
      : 'Are you sure you want to POWER OFF the host? This will shutdown the computer.',
    persistent: true,
    dark: true,
    ok: {
      flat: true,
      color: isRestart ? 'blue-4' : 'red-4',
      label: isRestart ? 'Restart' : 'Shut Down'
    },
    cancel: {
      flat: true,
      color: 'grey-5'
    }
  }).onOk(async () => {
    try {
      if (isRestart) {
        await deviceStore.rebootHost();
        $q.notify({
          type: 'positive',
          message: 'Reboot command sent successfully',
          color: 'blue-6',
          position: 'top'
        });
      } else {
        await deviceStore.shutdownHost();
        $q.notify({
          type: 'positive',
          message: 'Power off command sent successfully',
          color: 'red-6',
          position: 'top'
        });
      }
    } catch (e) {
      $q.notify({
        type: 'negative',
        message: `Failed to execute: ${e instanceof Error ? e.message : 'Unknown error'}`,
        color: 'red-8',
        position: 'top'
      });
    }
  });
};
</script>

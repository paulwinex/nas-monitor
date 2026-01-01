<template>
  <q-page class="flex flex-center">
    <div class="q-pa-md bg-black full-width" style="min-height: 100vh;">
      <div class="row q-col-gutter-md">
        <div class="col-12 col-md-6">
          <ZPoolWidget/>
        </div>
        <div class="col-12 col-md-6">
          <SystemMetricsWidget/>
        </div>

      </div>
    </div>
  </q-page>
</template>

<script setup>
import ZPoolWidget from "components/ZPoolWidget.vue";
import SystemMetricsWidget from "components/SystemMetricsWidget.vue";
</script>

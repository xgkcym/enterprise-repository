<template>
  <div ref="chartRef" class="echart-panel" :style="{ height }"></div>
</template>

<script setup>
import * as echarts from "echarts";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
  option: {
    type: Object,
    required: true,
  },
  height: {
    type: String,
    default: "280px",
  },
});

const chartRef = ref(null);
let chartInstance = null;
let resizeObserver = null;

const renderChart = () => {
  if (!chartRef.value) return;
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value);
  }
  chartInstance.setOption(props.option, true);
  chartInstance.resize();
};

const handleResize = () => {
  chartInstance?.resize();
};

onMounted(() => {
  renderChart();
  resizeObserver = new ResizeObserver(handleResize);
  if (chartRef.value) {
    resizeObserver.observe(chartRef.value);
  }
  window.addEventListener("resize", handleResize);
});

watch(
  () => props.option,
  () => {
    renderChart();
  },
  { deep: true }
);

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  window.removeEventListener("resize", handleResize);
  chartInstance?.dispose();
  chartInstance = null;
});
</script>

<style scoped>
.echart-panel {
  width: 100%;
}
</style>

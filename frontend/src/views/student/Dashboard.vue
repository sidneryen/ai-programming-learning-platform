<template>
  <div class="student-dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ completedCourses }}</div>
            <div class="stat-label">已完成课程</div>
          </div>
          <el-icon class="stat-icon"><Check /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ ongoingCourses }}</div>
            <div class="stat-label">进行中课程</div>
          </div>
          <el-icon class="stat-icon"><Clock /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ averageScore }}</div>
            <div class="stat-label">平均分数</div>
          </div>
          <el-icon class="stat-icon"><TrendCharts /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ attendanceRate }}</div>
            <div class="stat-label">出勤率</div>
          </div>
          <el-icon class="stat-icon"><PieChart /></el-icon>
        </el-card>
      </el-col>
    </el-row>

    <!-- 语言选择按钮 -->
    <div class="language-buttons" style="margin: 20px 0;">
      <el-button 
        v-for="lang in languages" 
        :key="lang.value"
        :type="selectedLanguage === lang.value ? 'primary' : 'default'"
        @click="selectLanguage(lang.value)"
      >
        {{ lang.label }}
      </el-button>
      <el-button type="primary" @click="loadKnowledgeMap" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>

    <!-- 知识图谱图表区域 -->
    <el-card class="chart-card" v-show="knowledgeData">
      <template #header>
        <div class="card-header">
          <span>知识点掌握图谱</span>
          <span style="margin-left: 20px; font-size: 12px; color: #666;">
            总提交次数: {{ knowledgeData.submission_count || 0 }} | 绿色:掌握良好 黄色:需巩固 红色:薄弱
          </span>
        </div>
      </template>
      
      <div class="chart-container" style="height: 400px; display: flex; gap: 20px;">
        <!-- 关系图 -->
        <div 
          id="knowledge-chart" 
          style="flex: 1.5; border: 1px solid #eee;"
        ></div>
        <!-- 饼图 -->
        <div 
          id="mastery-pie" 
          style="flex: 1; border: 1px solid #eee;"
        ></div>
      </div>
    </el-card>

    <!-- 柱状图：知识点掌握率对比 -->
    <el-card class="chart-card" v-show="knowledgeData">
      <template #header>
        <div class="card-header">
          <span>知识点掌握率对比</span>
          <span style="margin-left: 20px; font-size: 12px; color: #666;">诊断 vs 推荐后</span>
        </div>
      </template>
      <div id="mastery-bar" style="width: 100%; height: 300px;"></div>
    </el-card>

    <!-- 空状态 -->
    <div v-if="!knowledgeData" class="empty-state" style="text-align: center; padding: 100px 0;">
      <el-empty description="暂无数据" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Check, Clock, TrendCharts, PieChart, DataAnalysis, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import api from '../services/api'

// 统计数据
const completedCourses = ref(12)
const ongoingCourses = ref(3)
const averageScore = ref(85)
const attendanceRate = ref('96%')

// 知识图谱相关
const knowledgeData = ref(null)
const loading = ref(false)
const selectedLanguage = ref('Python')
let chartInstance = null
let pieChartInstance = null
let barChartInstance = null

// 图表是否已成功初始化
let chartInitialized = false

// 检查容器可见性的定时器
let visibilityCheckTimer = null

// 语言选项
const languages = [
  { label: 'Python', value: 'Python' },
  { label: 'C', value: 'C' },
  { label: 'C++', value: 'C++' },
  { label: 'Java', value: 'Java' },
  { label: 'Go', value: 'Go' }
]

// 根据选中的语言过滤节点
const filteredNodes = computed(() => {
  if (!knowledgeData.value) return []
  
  // 先过滤出符合条件的节点：只显示当前选中语言的知识点
  const candidates = knowledgeData.value.nodes.filter(node => {
    if (node.name.includes('-')) {
      const nodeLanguage = node.name.split('-')[0]
      return nodeLanguage === selectedLanguage.value
    }
    return false
  })
  
  // 去重：对于相同的知识点，只保留一个
  const uniqueNodes = []
  const seenKnowledge = new Set()
  
  for (const node of candidates) {
    let knowledgeName = node.name
    if (!seenKnowledge.has(knowledgeName)) {
      seenKnowledge.add(knowledgeName)
      uniqueNodes.push(node)
    }
  }
  
  return uniqueNodes
})

// 计算统计数据
const goodCount = computed(() => {
  if (!knowledgeData.value) return 0
  return filteredNodes.value.filter(node => node.value > 0.7).length
})

const mediumCount = computed(() => {
  if (!knowledgeData.value) return 0
  return filteredNodes.value.filter(node => node.value >= 0.4 && node.value <= 0.7).length
})

const poorCount = computed(() => {
  if (!knowledgeData.value) return 0
  return filteredNodes.value.filter(node => node.value < 0.4).length
})

// 语言选择方法
const selectLanguage = (lang) => {
  selectedLanguage.value = lang
  if (chartInstance && knowledgeData.value) {
    renderChart()
  }
}

// 初始化图表
const initChart = async () => {
  await nextTick()
  
  let chartDom = null
  let pieDom = null
  let barDom = null
  
  let containerAttempts = 0
  const maxContainerAttempts = 5
  
  while ((!chartDom || !pieDom || !barDom) && containerAttempts < maxContainerAttempts) {
    chartDom = document.getElementById('knowledge-chart')
    pieDom = document.getElementById('mastery-pie')
    barDom = document.getElementById('mastery-bar')
    
    if (!chartDom || !pieDom || !barDom) {
      containerAttempts++
      await new Promise(resolve => setTimeout(resolve, 200))
    }
  }
  
  if (!chartDom || !pieDom || !barDom) {
    console.error('图表容器不存在')
    return
  }
  
  console.log('容器尺寸:', chartDom.clientWidth, 'x', chartDom.clientHeight)
  
  // 确保容器有足够的尺寸
  let sizeAttempts = 0
  const maxSizeAttempts = 5
  
  while ((chartDom.clientWidth === 0 || chartDom.clientHeight === 0) && sizeAttempts < maxSizeAttempts) {
    console.log(`等待容器尺寸计算 (${sizeAttempts + 1}/${maxSizeAttempts})`)
    await new Promise(resolve => setTimeout(resolve, 200))
    sizeAttempts++
  }
  
  if (chartDom.clientWidth === 0 || chartDom.clientHeight === 0) {
    console.warn('⚠️ 图表容器尺寸为0，可能是隐藏状态，启动可见性检查')
    // 启动定时器定期检查容器可见性
    if (!visibilityCheckTimer) {
      visibilityCheckTimer = setInterval(() => {
        if (chartDom && chartDom.clientWidth > 0 && chartDom.clientHeight > 0 && !chartInitialized) {
          console.log(`📏 容器变为可见，尺寸: ${chartDom.clientWidth}x${chartDom.clientHeight}，尝试重新初始化图表`)
          clearInterval(visibilityCheckTimer)
          visibilityCheckTimer = null
          // 延迟一点时间再初始化，确保布局稳定
          setTimeout(async () => {
            await loadKnowledgeMap()
          }, 100)
        }
      }, 300)
      console.log('🔍 已启动容器可见性检查定时器')
    }
    return
  }
  
  // 确保图表实例已销毁，避免内存泄漏
  if (chartInstance) {
    chartInstance.dispose()
  }
  if (pieChartInstance) {
    pieChartInstance.dispose()
  }
  if (barChartInstance) {
    barChartInstance.dispose()
  }
  
  chartInstance = echarts.init(chartDom)
  pieChartInstance = echarts.init(pieDom)
  barChartInstance = echarts.init(barDom)
  chartInitialized = true
  console.log('✅ ECharts 实例创建成功')
  
  window.addEventListener('resize', () => {
    chartInstance?.resize()
    pieChartInstance?.resize()
    barChartInstance?.resize()
  })
}

// 处理推荐前后的掌握率数据
const getMasteryData = () => {
  const preData = {}
  const postData = {}
  let hasRecommendation = false
  
  // 从 pre_recommend_stats 构建掌握率数据
  if (knowledgeData.value?.pre_recommend_stats) {
    Object.entries(knowledgeData.value.pre_recommend_stats).forEach(([key, stats]) => {
      if (stats.total > 0) {
        preData[key] = stats.correct / stats.total
      } else {
        preData[key] = 0.5
      }
    })
  }
  
  const postKeys = knowledgeData.value?.post_recommend_stats ? Object.keys(knowledgeData.value.post_recommend_stats) : []
  if (postKeys.length > 0) {
    hasRecommendation = true
    Object.entries(knowledgeData.value.post_recommend_stats).forEach(([key, stats]) => {
      if (stats.total > 0) {
        postData[key] = stats.correct / stats.total
      } else {
        postData[key] = 0.5
      }
    })
  }
  
  // 从 nodes 数据中获取所有知识点（确保显示所有知识点的诊断柱状图）
  const knowledgeList = []
  const seenKnowledge = new Set()
  
  if (knowledgeData.value?.nodes) {
    knowledgeData.value.nodes.forEach(node => {
      const key = node.name
      if (key && !seenKnowledge.has(key)) {
        seenKnowledge.add(key)
        knowledgeList.push(key)
      }
    })
  }
  
  // 按语言过滤
  const filteredKnowledge = knowledgeList.filter(key => {
    if (key.includes('-')) {
      const nodeLanguage = key.split('-')[0]
      return nodeLanguage === selectedLanguage.value
    }
    // 如果没有语言前缀，也包含这个知识点（兼容旧数据）
    return true
  })
  
  // 去重（按核心知识点名称）
  const coreKnowledgeNames = new Set()
  const uniqueFilteredKnowledge = []
  
  filteredKnowledge.forEach(key => {
    let coreName = key
    if (key.includes('-')) {
      coreName = key.split('-')[1]
    }
    if (!coreKnowledgeNames.has(coreName)) {
      coreKnowledgeNames.add(coreName)
      uniqueFilteredKnowledge.push(key)
    }
  })
  
  const xAxisData = []
  const preMasteryData = []
  const postMasteryData = []
  
  uniqueFilteredKnowledge.forEach(key => {
    let coreName = key
    if (key.includes('-')) {
      coreName = key.split('-')[1]
    }
    xAxisData.push(coreName)
    // 从 preData 获取掌握率，如果没有则使用节点本身的 value
    let preValue = preData[key]
    if (preValue === undefined) {
      // 尝试从 nodes 中查找该节点的 value
      const node = knowledgeData.value?.nodes?.find(n => n.name === key)
      preValue = node?.value ?? 0.5
    }
    preMasteryData.push(preValue)
    
    // 只有该知识点有推荐后数据才显示推荐后掌握率，否则显示null（不显示）
    const hasPostData = postKeys.includes(key)
    postMasteryData.push(hasPostData ? postData[key] || 0.5 : null)
  })
  
  // 检查是否有任何知识点有推荐后数据
  const hasAnyRecommendation = postKeys.length > 0
  
  return { xAxisData, preMasteryData, postMasteryData, hasRecommendation: hasAnyRecommendation }
}

const hasRecommendation = computed(() => {
  const masteryData = getMasteryData()
  return masteryData.hasRecommendation
})

// 渲染图表
const renderChart = async () => {
  if (!knowledgeData.value || !chartInstance || !pieChartInstance) {
    console.error('渲染失败: 数据或实例为空')
    return
  }
  
  const chartDom = document.getElementById('knowledge-chart')
  const pieDom = document.getElementById('mastery-pie')
  const barDom = document.getElementById('mastery-bar')
  
  if (!chartDom || !pieDom || !barDom) {
    console.error('渲染失败: 图表容器不存在')
    return
  }
  
  // 确保容器有足够的尺寸
  let attempts = 0
  const maxAttempts = 5
  
  while ((chartDom.clientWidth === 0 || chartDom.clientHeight === 0) && attempts < maxAttempts) {
    console.error('渲染失败: 图表容器尺寸为0，等待重试...')
    await new Promise(resolve => setTimeout(resolve, 200))
    attempts++
  }
  
  if (chartDom.clientWidth === 0 || chartDom.clientHeight === 0) {
    console.error('渲染失败: 图表容器尺寸仍然为0')
    return
  }
  
  chartInstance.resize()
  pieChartInstance.resize()
  barChartInstance?.resize()
  
  const nodesWithColor = filteredNodes.value.map(node => {
    let itemStyle = {} 
    if (node.value >= 0.7) {
      itemStyle.color = '#52c41a'
    } else if (node.value >= 0.4) {
      itemStyle.color = '#faad14'
    } else {
      itemStyle.color = '#f5222d'
    }
    
    let displayName = node.name
    if (displayName.includes('-')) {
      displayName = displayName.split('-')[1]
    }
    
    return {
      ...node,
      name: displayName,
      itemStyle
    }
  })
  
  const categories = [...new Set(filteredNodes.value.map(n => n.category))]
  
  const graphOption = {
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        if (params.dataType === 'node') {
          const node = params.data
          const masteryPercent = (node.value * 100).toFixed(1)
          let status = '薄弱'
          if (node.value >= 0.7) status = '掌握良好'
          else if (node.value >= 0.4) status = '需巩固'
          
          let tooltip = `<strong>${node.name}</strong><br/>`
          tooltip += `掌握率: ${masteryPercent}%<br/>`
          tooltip += `状态: ${status}<br/>`
          tooltip += `类别: ${node.category}<br/>`
          if (node.total) {
            tooltip += `提交次数: ${node.total} | 正确: ${node.correct}`
          }
          return tooltip
        }
        return ''
      }
    },
    legend: {
      data: categories,
      bottom: 10
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodesWithColor,
      links: knowledgeData.value.links.filter(link => {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source
        const targetId = typeof link.target === 'object' ? link.target.id : link.target
        return nodesWithColor.some(node => node.id === sourceId || node.id === targetId)
      }),
      categories: categories.map(name => ({ name })),
      roam: true,
      label: { show: true, position: 'right', formatter: '{b}' },
      lineStyle: { color: 'source', curveness: 0.3 },
      emphasis: { focus: 'adjacency' },
      force: { repulsion: 500, edgeLength: 30, gravity: 0.3 }
    }]
  }
  
  const pieOption = {
    title: {
      text: '掌握状态分布',
      subtext: `掌握良好：${goodCount.value} 个 | 需要巩固：${mediumCount.value} 个 | 薄弱：${poorCount.value} 个`,
      left: 'center',
      top: 10,
      textStyle: { fontSize: 14 },
      subtextStyle: { fontSize: 11, color: '#666', padding: [5, 0, 15, 0] }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      data: ['掌握良好', '需巩固', '薄弱'],
      textStyle: { fontSize: 11 }
    },
    series: [{
      name: '掌握状态',
      type: 'pie',
      radius: '60%',
      center: ['60%', '60%'],
      data: [
        { value: goodCount.value, name: '掌握良好', itemStyle: { color: '#52c41a' } },
        { value: mediumCount.value, name: '需巩固', itemStyle: { color: '#faad14' } },
        { value: poorCount.value, name: '薄弱', itemStyle: { color: '#f5222d' } }
      ],
      label: {
        show: true,
        formatter: '{b}\n{c}个',
        fontSize: 11,
        overflow: 'break'
      },
      labelLine: {
        show: true,
        length: 10,
        length2: 20
      }
    }]
  }
  
  chartInstance.setOption(graphOption)
  pieChartInstance.setOption(pieOption)
  
  // 更新柱状图
  updateBarChart()
}

const updateBarChart = () => {
  if (!barChartInstance || !knowledgeData.value) return
  
  const { xAxisData, preMasteryData, postMasteryData, hasRecommendation } = getMasteryData()
  
  if (xAxisData.length === 0) {
    return
  }
  
  // 构建图例数据（如果有推荐后数据则显示推荐后图例）
  const legendData = ['诊断']
  if (hasRecommendation) {
    legendData.push('推荐后')
  }
  
  // 构建系列数据
  const series = [
    {
      name: '诊断',
      type: 'bar',
      data: preMasteryData.map(value => ({
        value: value,
        itemStyle: {
          color: value >= 0.7 ? '#52c41a' : (value >= 0.4 ? '#faad14' : '#f5222d')
        }
      })),
      barWidth: '35%'
    }
  ]
  
  // 如果有推荐后数据，添加推荐后系列
  if (hasRecommendation) {
    series.push({
      name: '推荐后',
      type: 'bar',
      data: postMasteryData.map(value => {
        if (value === null) {
          return null
        }
        return {
          value: value,
          itemStyle: {
            color: value >= 0.7 ? '#389e0d' : (value >= 0.4 ? '#fa8c16' : '#ff4d4f')
          }
        }
      }),
      barWidth: '35%'
    })
  }
  
  const barOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: function(params) {
        let result = `<strong>${params[0].axisValue}</strong><br/>`
        params.forEach(param => {
          if (param.value !== null && param.value !== undefined) {
            const percent = (param.value * 100).toFixed(1)
            result += `${param.marker} ${param.seriesName}: ${percent}%<br/>`
          }
        })
        return result
      }
    },
    legend: {
      data: legendData,
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLabel: { fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 1,
      axisLabel: {
        formatter: '{value}%',
        fontSize: 12
      },
      splitNumber: 5
    },
    series: series
  }
  
  barChartInstance.setOption(barOption)
  barChartInstance.resize()
}

// 加载知识图谱数据
const loadKnowledgeMap = async () => {
  loading.value = true
  try {
    const studentId = localStorage.getItem('userId')
    if (!studentId) {
      ElMessage.error('未找到学生信息')
      return
    }
    
    const response = await api.getKnowledgeMap(studentId)
    if (response.success) {
      knowledgeData.value = response
      // 等待DOM更新完成，确保图表容器可见
      await nextTick()
      await initChart()
      renderChart()
    } else {
      ElMessage.error(response.error || '获取知识图谱数据失败')
    }
  } catch (error) {
    console.error('加载知识图谱失败:', error)
    ElMessage.error('加载知识图谱数据失败')
  } finally {
    loading.value = false
  }
}

// 监听语言变化
watch(selectedLanguage, () => {
  if (knowledgeData.value) {
    renderChart()
  }
})

onMounted(() => {
  loadKnowledgeMap()
})
</script>

<style scoped>
.student-dashboard {
  padding: 20px;
}

.stat-card {
  height: 120px;
  position: relative;
  overflow: hidden;
}

.stat-content {
  position: relative;
  z-index: 2;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 5px;
}

.stat-icon {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 60px;
  color: #e6f2ff;
  z-index: 1;
}

.chart-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.language-buttons {
  display: flex;
  gap: 10px;
}
</style>
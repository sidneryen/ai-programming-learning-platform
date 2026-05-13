<template>
  <div class="knowledge-graph-panel">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="language-buttons">
            <el-button 
              v-for="lang in languages" 
              :key="lang.value"
              :type="selectedLanguage === lang.value ? 'primary' : 'default'"
              @click="selectLanguage(lang.value)"
            >
              {{ lang.label }}
            </el-button>
          </div>
          <el-button type="primary" @click="loadKnowledgeMap" :loading="loading">
            刷新数据
          </el-button>
        </div>
      </template>
      
      <!-- 图表容器始终存在，不依赖knowledgeData -->
      <div class="chart-container" style="max-height: 800px; overflow-y: auto; overflow-x: hidden; padding-right: 10px;">
        <div class="chart-wrapper" style="display: flex; align-items: stretch; gap: 20px;">
          <div 
            id="knowledge-chart" 
            style="flex: 1.5; border: 1px solid #eee; min-height: 500px;"
          ></div>
          <div 
            id="mastery-pie" 
            style="flex: 1.5; border: 1px solid #eee; min-height: 500px;"
          ></div>
        </div>
        
        <!-- 柱状图：知识点掌握率 -->
        <div class="bar-chart-container" style="margin-top: 40px; border: 1px solid #eee; min-height: 400px;">
          <div id="mastery-bar" style="width: 100%; height: 400px;"></div>
        </div>
        
        <!-- 空状态遮罩 -->
        <div v-if="!knowledgeData" class="empty-overlay">
          <el-empty description="暂无数据" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import api from '../services/api'

const knowledgeData = ref(null)
const loading = ref(false)
let chartInstance = null
let pieChartInstance = null
let barChartInstance = null
let visibilityCheckTimer = null
let intersectionObserver = null
let chartInitialized = false

// 保存初始的诊断数据（点击AI推荐前的数据）
const initialPreRecommendStats = ref(null)

// 语言选项
const languages = [
  { label: 'Python', value: 'Python' },
  { label: 'C', value: 'C' },
  { label: 'C++', value: 'C++' },
  { label: 'Java', value: 'Java' },
  { label: 'Go', value: 'Go' }
]

// 当前选中的语言
const selectedLanguage = ref('Python')

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

// 根据选中的语言过滤节点
const filteredNodes = computed(() => {
  if (!knowledgeData.value) return []
  
  // 先过滤出符合条件的节点：只显示当前选中语言的知识点
  const candidates = knowledgeData.value.nodes.filter(node => {
    // 提取知识点的语言部分
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
    // 提取知识点名称
    let knowledgeName = node.name
    
    // 如果这个知识点还没见过，就添加到结果中
    if (!seenKnowledge.has(knowledgeName)) {
      seenKnowledge.add(knowledgeName)
      uniqueNodes.push(node)
    }
  }
  
  return uniqueNodes
})

// 语言选择方法
const selectLanguage = (lang) => {
  selectedLanguage.value = lang
  // 重新渲染图表
  if (chartInstance && knowledgeData.value) {
    renderChart()
  }
}

// 初始化图表
const initChart = async () => {
  // 确保DOM元素已创建
  await nextTick()
  
  let chartDom = null
  let pieDom = null
  let barDom = null
  
  // 尝试获取容器，最多重试5次
  let containerAttempts = 0
  const maxContainerAttempts = 5
  
  while ((!chartDom || !pieDom || !barDom) && containerAttempts < maxContainerAttempts) {
    chartDom = document.getElementById('knowledge-chart')
    pieDom = document.getElementById('mastery-pie')
    barDom = document.getElementById('mastery-bar')
    
    if (!chartDom || !pieDom || !barDom) {
      console.log(`尝试获取图表容器 (${containerAttempts + 1}/${maxContainerAttempts})`)
      containerAttempts++
      await new Promise(resolve => setTimeout(resolve, 200))
    }
  }
  
  if (!chartDom || !pieDom || !barDom) {
    console.error('❌ 图表容器不存在')
    return
  }
  
  console.log('容器尺寸:', chartDom.clientWidth, 'x', chartDom.clientHeight)
  
  try {
    // 确保容器有足够的尺寸
    let sizeAttempts = 0
    const maxSizeAttempts = 5
    
    while ((chartDom.clientWidth === 0 || chartDom.clientHeight === 0) && sizeAttempts < maxSizeAttempts) {
      console.log(`等待容器尺寸计算 (${sizeAttempts + 1}/${maxSizeAttempts})`)
      // 等待容器尺寸计算完成
      await new Promise(resolve => setTimeout(resolve, 200))
      sizeAttempts++
    }
    
    if (chartDom.clientWidth === 0 || chartDom.clientHeight === 0) {
      console.warn('⚠️ 图表容器尺寸为0，可能是隐藏状态')
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
    
    // 重新添加 resize 事件监听器
    window.addEventListener('resize', () => {
      chartInstance?.resize()
      pieChartInstance?.resize()
      barChartInstance?.resize()
    })
  } catch (error) {
    console.error('ECharts 初始化失败:', error)
  }
}

// 渲染图表
const renderChart = async () => {
  if (!knowledgeData.value || !chartInstance || !pieChartInstance || !barChartInstance) {
    console.error('渲染失败: 数据或实例为空')
    return
  }
  
  // 确保DOM元素已创建且有尺寸
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
    // 等待容器尺寸计算完成
    await new Promise(resolve => setTimeout(resolve, 200))
    attempts++
  }
  
  if (chartDom.clientWidth === 0 || chartDom.clientHeight === 0) {
    console.error('渲染失败: 图表容器尺寸仍然为0')
    return
  }
  
  // 调整图表大小以适应容器
  chartInstance.resize()
  pieChartInstance.resize()
  barChartInstance.resize()
  
  console.log('开始渲染图表，节点数:', knowledgeData.value.nodes.length)
  
  // 处理节点颜色和名称
  const nodesWithColor = filteredNodes.value.map(node => {
    let itemStyle = {} 
    if (node.value >= 0.7) {
      itemStyle.color = '#52c41a' // 绿色 - 良好
    } else if (node.value >= 0.4) {
      itemStyle.color = '#faad14' // 黄色 - 需巩固
    } else {
      itemStyle.color = '#f5222d' // 红色 - 薄弱
    }
    
    // 只显示短横后面的内容
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
  
  // 关系图配置
  const graphOption = {
    title: {
      text: '知识点掌握图谱',
      subtext: `总提交次数: ${knowledgeData.value.submission_count || 0} | 绿色:掌握良好 黄色:需巩固 红色:薄弱`,
      left: 'center'
    },
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
    dataZoom: [{
      type: 'inside',
      start: 0,
      end: 12
    }],
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodesWithColor,
      // 过滤链接，只显示与过滤后节点相关的链接
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
  
  
  
  // 饼图配置
  const pieOption = {
    title: {
      text: '掌握状态分布',
      subtext: `掌握良好：${goodCount.value} 个 | 需要巩固：${mediumCount.value} 个 | 薄弱：${poorCount.value} 个`,
      left: 'center',
      top: 10,
      textStyle: {
        fontSize: 16
      },
      subtextStyle: {
        fontSize: 12,
        color: '#666',
        padding: [5, 0, 15, 0]
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      data: ['掌握良好', '需巩固', '薄弱'],
      textStyle: {
        fontSize: 12
      }
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
        fontSize: 12,
        overflow: 'break'
      },
      labelLine: {
        show: true,
        length: 10,
        length2: 20
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  // 处理推荐前后的掌握率数据
  const getMasteryData = () => {
    const preData = {}
    const postData = {}
    let hasRecommendation = false
    
    // 计算推荐后掌握率（先计算，以便知道哪些知识点有推荐后数据）
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
    
    // 计算推荐前掌握率
    // 规则：如果知识点有推荐后数据，使用初始诊断数据（冻结）；否则使用最新数据
    if (knowledgeData.value?.pre_recommend_stats) {
      Object.entries(knowledgeData.value.pre_recommend_stats).forEach(([key, stats]) => {
        // 检查该知识点是否有推荐后数据
        const hasPostData = postKeys.includes(key)
        
        if (hasPostData && initialPreRecommendStats.value && initialPreRecommendStats.value[key]) {
          // 如果有推荐后数据，使用初始诊断数据（冻结状态）
          const initialStats = initialPreRecommendStats.value[key]
          preData[key] = initialStats.total > 0 ? initialStats.correct / initialStats.total : 0.5
        } else {
          // 如果没有推荐后数据，使用最新诊断数据
          preData[key] = stats.total > 0 ? stats.correct / stats.total : 0.5
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
    
    // 提取核心知识点名称（去重）
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
    
    // 生成数据
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
  
  // 柱状图配置：知识点掌握率对比
  const barOption = {
    title: {
      text: '知识点掌握率对比',
      subtext: '诊断 vs 推荐后',
      left: 'center',
      top: '2%',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      },
      subtextStyle: {
        fontSize: 12,
        color: '#666'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: function(params) {
        let result = `<div style="font-weight:bold;margin-bottom:5px;">${params[0].axisValue}</div>`
        params.forEach(param => {
          const masteryPercent = (param.value * 100).toFixed(1)
          let status = '薄弱'
          if (param.value >= 0.7) status = '掌握良好'
          else if (param.value >= 0.4) status = '需巩固'
          result += `<div style="display:flex;align-items:center;margin:3px 0;">
            <span style="display:inline-block;width:10px;height:10px;background:${param.color};margin-right:8px;"></span>
            <span>${param.seriesName}: ${masteryPercent}% (${status})</span>
          </div>`
        })
        return result
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#ddd',
      borderWidth: 1,
      padding: 10,
      boxShadow: '0 2px 12px 0 rgba(0, 0, 0, 0.1)'
    },
    legend: {
      data: ['诊断', '推荐后'],
      bottom: 10,
      textStyle: {
        fontSize: 14,
        fontWeight: '500'
      },
      itemWidth: 16,
      itemHeight: 10,
      itemGap: 20
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '20%',
      top: '25%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: getMasteryData().xAxisData,
      axisLabel: {
        interval: 0,
        rotate: 45,
        fontSize: 12,
        fontWeight: '500'
      },
      axisLine: {
        lineStyle: {
          color: '#ddd'
        }
      },
      axisTick: {
        alignWithLabel: true
      }
    },
    yAxis: {
      type: 'value',
      name: '掌握率',
      min: 0,
      max: 1,
      interval: 0.2,
      axisLabel: {
        formatter: function(value) {
          return (value * 100).toFixed(0) + '%'
        },
        fontSize: 12
      },
      axisLine: {
        lineStyle: {
          color: '#ddd'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#f0f0f0',
          type: 'dashed'
        }
      }
    },
    series: [
      {
        name: '诊断',
        type: 'bar',
        data: getMasteryData().preMasteryData.map(value => ({
          value: value,
          itemStyle: {
            color: value >= 0.7 ? '#52c41a' : (value >= 0.4 ? '#faad14' : '#f5222d')
          }
        })),
        barWidth: getMasteryData().hasRecommendation ? '35%' : '60%',
        animationDuration: 1000,
        animationEasing: 'elasticOut'
      },
      ...(getMasteryData().hasRecommendation ? [{
        name: '推荐后',
        type: 'bar',
        data: getMasteryData().postMasteryData.map(value => {
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
        barWidth: '35%',
        animationDuration: 1000,
        animationEasing: 'elasticOut',
        animationDelay: 300
      }] : [])
    ]
  }
  
  try {
    chartInstance.setOption(graphOption, true)
    pieChartInstance.setOption(pieOption, true)
    barChartInstance.setOption(barOption, true)
    console.log('✅ 图表渲染完成')
  } catch (error) {
    console.error('图表渲染失败:', error)
  }

}

// 加载数据
const loadKnowledgeMap = async () => {
  loading.value = true
  try {
    const userId = localStorage.getItem('userId')
    if (!userId) {
      ElMessage.warning('请先登录')
      loading.value = false
      return
    }
    
    // 先确保DOM元素已创建
    await nextTick()
    
    // 尝试初始化图表，最多重试3次
    let chartInitAttempts = 0
    const maxChartInitAttempts = 3
    
    while (!chartInstance && chartInitAttempts < maxChartInitAttempts) {
      console.log(`尝试初始化图表 (${chartInitAttempts + 1}/${maxChartInitAttempts})`)
      await initChart()
      chartInitAttempts++
      if (!chartInstance) {
        await new Promise(resolve => setTimeout(resolve, 300))
      }
    }
    
    // 确保图表实例创建成功
    if (!chartInstance || !pieChartInstance || !barChartInstance) {
      console.error('图表实例创建失败，稍后重试')
      // 延迟重试
      setTimeout(async () => {
        console.log('重新尝试加载知识图谱')
        await loadKnowledgeMap()
      }, 1500)
      loading.value = false
      return
    }
    
    // 获取数据
    const result = await api.getKnowledgeMap(Number(userId))
    console.log('API返回数据:', result)
    
    if (result.success) {
      // 设置数据
      knowledgeData.value = result
      
      // 如果还没有保存初始诊断数据，保存当前的pre_recommend_stats
      // 这表示还没有点击过AI推荐按钮
      if (!initialPreRecommendStats.value && result.pre_recommend_stats) {
        initialPreRecommendStats.value = { ...result.pre_recommend_stats }
        console.log('保存初始诊断数据:', initialPreRecommendStats.value)
      }
      
      // 等待DOM更新
      await nextTick()
      
      // 尝试渲染图表，最多重试2次
      let renderAttempts = 0
      const maxRenderAttempts = 2
      let renderSuccess = false
      
      while (!renderSuccess && renderAttempts < maxRenderAttempts) {
        try {
          console.log(`尝试渲染图表 (${renderAttempts + 1}/${maxRenderAttempts})`)
          await renderChart()
          renderSuccess = true
        } catch (renderError) {
          console.error(`渲染尝试 ${renderAttempts + 1} 失败:`, renderError)
          renderAttempts++
          if (renderAttempts < maxRenderAttempts) {
            await new Promise(resolve => setTimeout(resolve, 500))
          }
        }
      }
      
      if (!renderSuccess) {
        console.error('图表渲染失败，稍后重试')
        // 延迟重试
        setTimeout(async () => {
          console.log('重新尝试渲染知识图谱')
          await renderChart()
        }, 1000)
      }
    } else {
      ElMessage.error(result.error || '加载失败')
    }
  } catch (error) {
    console.error('加载失败:', error)
    ElMessage.error('加载失败: ' + error.message)
    // 网络错误时延迟重试
    setTimeout(async () => {
      console.log('网络错误，重新尝试加载')
      await loadKnowledgeMap()
    }, 2000)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  console.log('组件挂载开始')
  try {
    // 等待DOM完全渲染
    await nextTick()
    
    // 创建IntersectionObserver，检测组件何时进入视口
    const panel = document.querySelector('.knowledge-graph-panel')
    if (panel) {
      intersectionObserver = new IntersectionObserver(
        async (entries) => {
          const entry = entries[0]
          if (entry.isIntersecting && !chartInitialized) {
            console.log('📊 知识图谱面板进入视口，开始初始化图表')
            intersectionObserver.disconnect()
            // 延迟初始化，确保布局稳定
            setTimeout(async () => {
              await loadKnowledgeMap()
            }, 300)
          }
        },
        { threshold: 0.1, rootMargin: '100px' }
      )
      intersectionObserver.observe(panel)
      console.log('👀 已启动IntersectionObserver监听')
    } else {
      // 如果找不到面板，降级为延迟初始化
      setTimeout(async () => {
        await loadKnowledgeMap()
      }, 1000)
    }
  } catch (error) {
    console.error('挂载时加载知识图谱失败:', error)
    // 延迟重试
    setTimeout(async () => {
      console.log('尝试重新加载知识图谱')
      await loadKnowledgeMap()
    }, 1000)
  }
})

// 组件卸载时清理资源
onUnmounted(() => {
  // 清理可见性检查定时器
  if (visibilityCheckTimer) {
    clearInterval(visibilityCheckTimer)
    visibilityCheckTimer = null
  }
  // 销毁图表实例
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  if (pieChartInstance) {
    pieChartInstance.dispose()
    pieChartInstance = null
  }
  if (barChartInstance) {
    barChartInstance.dispose()
    barChartInstance = null
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.language-buttons {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.language-buttons .el-button {
  font-size: 12px;
  padding: 4px 8px;
}

.chart-container {
  margin-top: 20px;
  position: relative;
}

.stats-summary {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 14px;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

.empty-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.9);
  z-index: 10;
}

.clearfix::after {
  content: '';
  display: table;
  clear: both;
}
</style>
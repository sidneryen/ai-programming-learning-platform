<!-- src/components/HistoryPanel.vue -->
<template>
  <div class="history-panel">
    <h3>提交历史记录</h3>
    <template v-if="historyList.length === 0 && !loading">
      <el-empty description="暂无提交记录" />
    </template>
    <el-skeleton v-else-if="loading" :rows="3" animated />
    <el-table v-else :data="historyList" style="width: 100%">
      <el-table-column prop="time" label="提交时间" width="200">
        <template #default="scope">
          {{ formatTime(scope.row.time) }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === '成功' ? 'success' : 'danger'">
            {{ scope.row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="code" label="代码内容">
        <template #default="scope">
          <el-popover
            placement="top"
            :width="400"
            trigger="click"
          >
            <template #reference>
              <span class="code-preview">{{ scope.row.code.substring(0, 50) }}...</span>
            </template>
            <pre><code>{{ scope.row.code }}</code></pre>
          </el-popover>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="scope">
          <el-button type="primary" size="small" @click="viewDetails(scope.row)">
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="提交详情"
      width="800px"
    >
      <el-descriptions :column="1" border>
        <el-descriptions-item label="提交时间">
          {{ formatTime(selectedSubmission?.time) }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="selectedSubmission?.status === '成功' ? 'success' : 'danger'">
            {{ selectedSubmission?.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="代码内容">
          <pre><code>{{ selectedSubmission?.code }}</code></pre>
        </el-descriptions-item>
        <el-descriptions-item label="AI反馈" v-if="selectedSubmission?.feedback">
          <div v-if="selectedSubmission.feedback.error_type" class="feedback-item">
            <strong>错误类型:</strong> {{ selectedSubmission.feedback.error_type }}
          </div>
          <div v-if="selectedSubmission.feedback.hint" class="feedback-item">
            <strong>修改提示:</strong> {{ selectedSubmission.feedback.hint }}
          </div>
          <div v-if="selectedSubmission.feedback.knowledge_tags" class="feedback-item">
            <strong>涉及知识点:</strong>
            <el-tag
              v-for="tag in selectedSubmission.feedback.knowledge_tags"
              :key="tag"
              type="info"
              size="small"
              style="margin-left: 5px"
            >
              {{ tag }}
            </el-tag>
          </div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../services/api'

const historyList = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const selectedSubmission = ref(null)

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 查看详情
const viewDetails = (submission) => {
  selectedSubmission.value = submission
  dialogVisible.value = true
}

// 获取提交历史
const fetchHistory = async () => {
  try {
    loading.value = true
    const userId = localStorage.getItem('userId')
    if (!userId) {
      ElMessage.warning('请先登录')
      return
    }
    
    const response = await api.getSubmissions(Number(userId))
    if (response.success) {
      // 解析 ai_feedback 字段为 JSON 对象
      historyList.value = response.submissions.map(item => {
        if (item.feedback) {
          try {
            item.feedback = JSON.parse(item.feedback)
          } catch (e) {
            // 如果解析失败，保持原始值
            console.warn('解析 feedback 失败:', e)
          }
        }
        return item
      })
    } else {
      ElMessage.error(response.error || '获取提交历史失败')
    }
  } catch (error) {
    ElMessage.error('获取提交历史失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 组件挂载时获取历史记录
onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.history-panel {
  padding: 16px;
  border: 1px solid #eee;
  border-radius: 4px;
}
</style>
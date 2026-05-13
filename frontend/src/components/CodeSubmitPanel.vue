<template>
  <div class="code-submit-panel">
    <!-- 题目列表 -->
    <el-card class="problem-list-card" style="margin-bottom: 20px;">
      <template #header>
        <div class="problem-list-header">
          <h3 class="problem-list-title">编程题目列表</h3>
          <div class="search-boxes">
            <el-input
              v-model="searchParams.problemNumber"
              placeholder="按题目号查找（精确）"
              style="width: 180px; margin-right: 10px"
              @keyup.enter="handleSearch"
            />
            <el-input
              v-model="searchParams.title"
              placeholder="按标题查找（模糊）"
              style="width: 180px; margin-right: 10px"
              @keyup.enter="handleSearch"
            />
            <el-input
              v-model="searchParams.category"
              placeholder="按分类查找（模糊）"
              style="width: 180px; margin-right: 10px"
              @keyup.enter="handleSearch"
            />
            <el-button type="primary" @click="handleSearch">
              搜索
            </el-button>
            <el-button @click="resetSearch">
              重置
            </el-button>
          </div>
        </div>
      </template>
      <el-table :data="problems" style="width: 100%">
        <el-table-column prop="problem_number" label="题目号" width="80" />
        <el-table-column prop="title" label="标题">
          <template #default="scope">
            <div class="title-with-status" style="display: flex; align-items: center;">
              <span class="problem-title" @click="selectProblem(scope.row)" style="cursor: pointer; font-weight: 500; color: #495057; font-size: 14px;">
                {{ scope.row.title }}
              </span>
              <el-tag v-if="scope.row.problem_number >= 10000" type="info" size="small" style="margin-left: 8px;">
                AI生成
              </el-tag>
              <el-tag v-if="completedProblemIds.includes(scope.row.id)" type="success" size="small" effect="plain" style="margin-left: 8px;">
                ✅
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="150">
          <template #default="scope">
            <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{{ scope.row.category }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="difficulty" label="难度" width="80">
          <template #default="scope">
            <el-tag :type="getDifficultyType(scope.row.difficulty)" size="small">
              {{ scope.row.difficulty || '入门' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button type="primary" size="small" @click="showSubmissionHistory(scope.row)">
              提交记录
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页组件 -->
      <div class="pagination-container" style="margin-top: 15px; text-align: center;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10]"
          layout="prev, pager, next"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 题目详情 -->
    <el-card v-if="selectedProblem" class="problem-detail-card" style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>题目详情 - {{ selectedProblem.problem_number }}. {{ selectedProblem.title }}</span>
        </div>
      </template>
      <div class="problem-detail">
        <div class="problem-section">
          <h4>题目描述</h4>
          <div v-html="selectedProblem.description" class="description-content"></div>
        </div>
        <div class="problem-section">
          <h4>输入</h4>
          <p>{{ selectedProblem.input_description }}</p>
        </div>
        <div class="problem-section">
          <h4>输出</h4>
          <p>{{ selectedProblem.output_description }}</p>
        </div>
        <div class="problem-section">
          <h4>样例输入</h4>
          <pre>{{ selectedProblem.sample_input }}</pre>
        </div>
        <div class="problem-section">
          <h4>样例输出</h4>
          <pre>{{ selectedProblem.sample_output }}</pre>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <div class="editor-header">
                <span>代码编辑器</span>
                <el-select v-model="selectedLanguage" placeholder="选择语言" style="width: 120px; margin-left: 15px" :disabled="true">
                  <el-option label="Python" value="python" />
                  <el-option label="C" value="c" />
                  <el-option label="C++" value="cpp" />
                  <el-option label="Java" value="java" />
                  <el-option label="Go" value="go" />
                </el-select>
              </div>
              <el-button type="primary" @click="submitCode" :loading="submitting">
                提交分析
              </el-button>
            </div>
          </template>
          
          <div class="code-editor-container">
            <div class="line-numbers" v-html="lineNumbers"></div>
            <textarea
              v-model="code"
              :rows="15"
              :placeholder="`请输入${getLanguagePlaceholder()}代码...`"
              class="code-textarea"
              @input="updateLineNumbers"
            ></textarea>
          </div>
          
          <div class="input-section" style="margin-top: 15px;">
            <h4>输入数据</h4>
            <el-input
              v-model="inputData"
              type="textarea"
              :rows="4"
              placeholder="请输入代码运行所需的输入数据..."
              resize="none"
            />
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="analysis-result">
          <template #header>
            <div class="card-header">
              <span>AI分析结果</span>
              <el-tag type="info" v-if="!analysisResult">
                未分析
              </el-tag>
              <el-tag :type="analysisResult.is_correct ? 'success' : 'danger'" v-else>
                {{ analysisResult.is_correct ? '正确' : '错误' }}
              </el-tag>
            </div>
          </template>
          
          <div v-if="analysisResult" class="analysis-content">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="错误类型">
                {{ analysisResult.error_type }}
              </el-descriptions-item>
              
              <el-descriptions-item label="修改提示">
                <div>
                  <div>{{ analysisResult.hint }}</div>
                  <div v-if="analysisResult.hint_en" class="hint-en" style="margin-top: 8px; font-size: 14px; color: #606266;">
                    {{ analysisResult.hint_en }}
                  </div>
                </div>
              </el-descriptions-item>
              
              <el-descriptions-item label="涉及知识点">
                <div class="knowledge-tags">
                  <el-tag
                    v-for="tag in analysisResult.knowledge_tags"
                    :key="tag"
                    type="info"
                    size="small"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
              </el-descriptions-item>
              
              <!-- 错误原因分析 -->
              <el-descriptions-item v-if="analysisResult.error_reason" label="错误原因">
                <div class="error-analysis" style="color: #e74c3c; font-weight: 500;">
                  {{ analysisResult.error_reason }}
                </div>
              </el-descriptions-item>
              
              <!-- 修改建议 -->
              <el-descriptions-item v-if="analysisResult.fix_suggestion" label="修改建议">
                <div class="fix-suggestion" style="color: #27ae60; font-weight: 500; background: #f0fdf4; padding: 10px; border-radius: 6px;">
                  {{ analysisResult.fix_suggestion }}
                </div>
              </el-descriptions-item>
              
              <el-descriptions-item v-if="analysisResult.is_correct && analysisResult.execution_result" label="运行结果">
                <pre class="execution-result">{{ analysisResult.execution_result }}</pre>
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <div v-else class="empty-analysis">
            <el-empty description="请选择题目并提交代码进行分析" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 提交历史对话框 -->
    <el-dialog
      v-model="submissionHistoryVisible"
      :title="`${selectedProblemForHistory?.problem_number}. ${selectedProblemForHistory?.title} - 提交历史`"
      width="70%"
    >
      <div>
        <template v-if="submissionHistoryList.length === 0 && !loadingSubmissions">
          <el-empty description="暂无提交记录" />
        </template>
        <el-skeleton v-else-if="loadingSubmissions" :rows="3" animated />
        <el-table v-else :data="submissionHistoryList" style="width: 100%">
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
                <span class="code-preview">{{ scope.row.code ? scope.row.code.substring(0, 50) + '...' : '' }}</span>
              </template>
              <pre><code>{{ scope.row.code }}</code></pre>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button type="primary" size="small" @click="viewSubmissionDetails(scope.row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      </div>

      <!-- 提交详情对话框 -->
      <el-dialog
        v-model="submissionDetailsVisible"
        title="提交详情"
        width="800px"
      >
        <el-descriptions :column="1" border v-if="selectedSubmission">
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
              <div v-if="selectedSubmission.feedback.hint_en" class="hint-en" style="margin-top: 8px; font-size: 14px; color: #606266;">
                {{ selectedSubmission.feedback.hint_en }}
              </div>
            </div>
            <!-- 错误原因 -->
            <div v-if="selectedSubmission.feedback.error_reason" class="feedback-item">
              <strong>错误原因:</strong> <span style="color: #e74c3c; font-weight: 500;">{{ selectedSubmission.feedback.error_reason }}</span>
            </div>
            <!-- 修改建议 -->
            <div v-if="selectedSubmission.feedback.fix_suggestion" class="feedback-item">
              <strong>修改建议:</strong> <span style="color: #27ae60; font-weight: 500;">{{ selectedSubmission.feedback.fix_suggestion }}</span>
            </div>
            <div v-if="selectedSubmission.feedback.knowledge_tags" class="feedback-item">
              <strong>涉及知识点:</strong>
              <el-tag
                v-for="tag in selectedSubmission.feedback.knowledge_tags"
                :key="tag"
                type="info"
                size="small"
                style="margin-left: 5px;"
              >
                {{ tag }}
              </el-tag>
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </el-dialog>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../services/api'

const code = ref('print("Hello, World!")\n\n# 在这里输入您的Python代码...')
const inputData = ref('')
const analysisResult = ref(null)
const submitting = ref(false)
const selectedLanguage = ref('python')

// 行号相关
const lineNumbers = ref('1\n2\n3')

const updateLineNumbers = () => {
  const lines = code.value.split('\n').length
  let numbers = ''
  for (let i = 1; i <= lines; i++) {
    numbers += i + '\n'
  }
  lineNumbers.value = numbers
}

// 题目相关
const problems = ref([])
const selectedProblem = ref(null)
const completedProblemIds = ref([])

// 分页相关
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const totalPages = ref(0)

// 搜索相关
const searchParams = ref({
  problemNumber: '',
  title: '',
  category: ''
})

// 提交历史相关
const submissionHistoryVisible = ref(false)
const submissionDetailsVisible = ref(false)
const submissionHistoryList = ref([])
const selectedProblemForHistory = ref(null)
const selectedSubmission = ref(null)
const loadingSubmissions = ref(false)

const loadProblems = async (page = 1) => {
  try {
    const response = await api.getProblems(page, pageSize.value, searchParams.value)
    if (response.success) {
      problems.value = response.problems || []
      total.value = response.total || 0
      totalPages.value = response.total_pages || 1
      currentPage.value = response.page || 1
    }
  } catch (error) {
    console.error('获取题目列表失败:', error)
    ElMessage.error('获取题目列表失败')
  }
}

// 搜索处理函数
const handleSearch = () => {
  currentPage.value = 1 // 搜索时重置到第一页
  loadProblems(1)
}

// 重置搜索
const resetSearch = () => {
  searchParams.value = {
    problemNumber: '',
    title: '',
    category: ''
  }
  currentPage.value = 1
  loadProblems(1)
}

const loadCompletedProblems = async () => {
  try {
    const userId = localStorage.getItem('userId')
    if (userId) {
      const response = await api.getCompletedProblems(Number(userId))
      if (response.success) {
        completedProblemIds.value = response.completed_problem_ids || []
      }
    }
  } catch (error) {
    console.error('获取已完成题目失败:', error)
  }
}

const selectProblem = async (problem) => {
  try {
    // 重置AI分析结果
    analysisResult.value = null
    code.value = ''
    inputData.value = ''
    
    const response = await api.getProblemDetail(problem.id)
    if (response.success) {
      selectedProblem.value = response.problem
      // 将样例输入设置为默认输入数据
      inputData.value = response.problem.sample_input || ''
      
      // 根据分类设置语言
      if (response.problem.category) {
        const category = response.problem.category
        // 提取短横前面的语言部分
        const languagePart = category.split('-')[0]
        // 映射到编辑器语言值
        const languageMap = {
          'Python': 'python',
          'C': 'c',
          'C++': 'cpp',
          'Java': 'java',
          'Go': 'go'
        }
        if (languageMap[languagePart]) {
          selectedLanguage.value = languageMap[languagePart]
          // 根据语言设置默认代码
            setDefaultCode(selectedLanguage.value)
            // 更新行号
            updateLineNumbers()
        }
      }
      
      // 检查是否有该题目的提交记录
      const userId = localStorage.getItem('userId')
      if (userId) {
        try {
          const submissionsResponse = await api.getSubmissions(Number(userId), problem.id)
          if (submissionsResponse.success && submissionsResponse.submissions && submissionsResponse.submissions.length > 0) {
            // 获取最新的提交记录
            const latestSubmission = submissionsResponse.submissions[0]
            // 加载代码和输入数据
            if (latestSubmission.code_content) {
              code.value = latestSubmission.code_content
              // 更新行号
              updateLineNumbers()
            }
            // 加载AI分析结果
            if (latestSubmission.ai_feedback) {
              try {
                const feedback = JSON.parse(latestSubmission.ai_feedback)
                analysisResult.value = feedback
              } catch (e) {
                console.warn('解析AI反馈失败:', e)
              }
            }
          }
        } catch (error) {
          console.error('获取提交记录失败:', error)
        }
      }
    }
  } catch (error) {
    console.error('获取题目详情失败:', error)
    ElMessage.error('获取题目详情失败')
  }
}

// 根据语言设置默认代码
const setDefaultCode = (language) => {
  code.value = ''
  // 更新行号
  updateLineNumbers()
}

const getLanguagePlaceholder = () => {
  const languageMap = {
    python: 'Python',
    c: 'C',
    cpp: 'C++',
    java: 'Java',
    go: 'Go'
  }
  return languageMap[selectedLanguage.value] || '代码'
}

const submitCode = async () => {
  if (!selectedProblem.value) {
    ElMessage.warning('请先选择一道题目')
    return
  }

  if (!code.value.trim()) {
    ElMessage.warning('请输入代码')
    return
  }

  submitting.value = true
  try {
    const userId = localStorage.getItem('userId')
    if (!userId) {
      ElMessage.warning('请先登录')
      return
    }
    const result = await api.submitCode(
      Number(userId), 
      code.value, 
      inputData.value,
      selectedProblem.value?.id,
      selectedLanguage.value
    )
    
    if (result.success) {
      analysisResult.value = result.analysis
      ElMessage.success('代码分析完成！')
      // 重新加载已完成题目列表
      await loadCompletedProblems()
    } else {
      ElMessage.error(result.error || '分析失败')
    }
  } catch (error) {
    ElMessage.error('提交失败: ' + error.message)
  } finally {
    submitting.value = false
  }
}

// 分页处理函数
const handleSizeChange = (size) => {
  pageSize.value = size
  loadProblems(1)
}

const handleCurrentChange = (current) => {
  loadProblems(current)
}

onMounted(async () => {
  await loadProblems()
  await loadCompletedProblems()
  
  // 检查是否有预选择的题目ID
  const selectedProblemId = localStorage.getItem('selectedProblemId')
  if (selectedProblemId) {
    // 查找对应的题目
    const problem = problems.value.find(p => p.id === Number(selectedProblemId))
    if (problem) {
      // 选择题目
      await selectProblem(problem)
    }
    // 清除localStorage中的selectedProblemId
    localStorage.removeItem('selectedProblemId')
  } else {
    // 初始更新行号
    updateLineNumbers()
  }
})

const getDifficultyType = (difficulty) => {
  if (!difficulty) return 'success'
  switch (difficulty) {
    case '入门': return 'success'
    case '基础': return 'warning'
    case '提高': return 'danger'
    default: return 'info'
  }
}

// 显示题目提交历史
const showSubmissionHistory = async (problem) => {
  try {
    selectedProblemForHistory.value = problem
    submissionHistoryVisible.value = true
    loadingSubmissions.value = true
    submissionHistoryList.value = []

    const userId = localStorage.getItem('userId')
    if (!userId) {
      ElMessage.warning('请先登录')
      return
    }

    const response = await api.getSubmissions(Number(userId), problem.id)
    if (response.success) {
      // 解析 ai_feedback 字段为 JSON 对象，并映射字段名
      submissionHistoryList.value = response.submissions.map(item => {
        const mappedItem = {
          id: item.id,
          time: item.submission_time,
          code: item.code_content,
          feedback: item.ai_feedback,
          status: item.ai_feedback ? '成功' : '失败'
        }
        
        if (mappedItem.feedback) {
          try {
            mappedItem.feedback = JSON.parse(mappedItem.feedback)
          } catch (e) {
            console.warn('解析 feedback 失败:', e)
          }
        }
        return mappedItem
      })
    } else {
      ElMessage.error(response.error || '获取提交历史失败')
    }
  } catch (error) {
    ElMessage.error('获取提交历史失败: ' + error.message)
  } finally {
    loadingSubmissions.value = false
  }
}

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

// 查看提交详情
const viewSubmissionDetails = (submission) => {
  selectedSubmission.value = submission
  submissionDetailsVisible.value = true
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: linear-gradient(135deg, #409eff, #667eea);
  color: white;
  border-radius: 8px 8px 0 0;
  margin: -20px -20px 20px -20px;
}

.card-header span {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.problem-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100vw;
  max-width: 100%;
  padding: 16px 20px;
  background: linear-gradient(135deg, #409eff, #667eea);
  border-radius: 8px 8px 0 0;
  margin: -20px -9999px 20px -9999px;
  box-sizing: border-box;
  position: relative;
  left: 9999px;
  right: 9999px;
}

.problem-list-title {
  font-size: 24px;
  font-weight: 700;
  color: white;
  margin: 0;
  letter-spacing: 1px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.search-boxes {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-right: 0;
  padding-right: 0;
}

.search-boxes .el-input {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.search-boxes .el-input:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.search-boxes .el-input input {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 14px;
  font-weight: 500;
  transition: border-color 0.3s ease;
}

.search-boxes .el-input input:focus {
  border-color: #667eea;
  outline: none;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.search-boxes .el-button {
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  padding: 10px 20px;
  transition: all 0.3s ease;
}

.search-boxes .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.search-boxes .el-button--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  font-weight: 600;
}

.editor-header {
  display: flex;
  align-items: center;
  gap: 15px;
}

.editor-header span {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.code-editor {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.code-editor:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.code-editor textarea {
  font-family: inherit;
  line-height: 1.6;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  transition: border-color 0.3s ease;
}

.code-editor textarea:focus {
  border-color: #667eea;
  outline: none;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

/* 带行号的代码编辑器 */
.code-editor-container {
  position: relative;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.code-editor-container:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.line-numbers {
  position: absolute;
  left: 0;
  top: 0;
  width: 50px;
  height: 100%;
  background-color: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  text-align: right;
  padding: 12px 8px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #909399;
  user-select: none;
  overflow: hidden;
  white-space: pre;
}

.code-textarea {
  width: 100%;
  min-height: 300px;
  padding: 12px 12px 12px 62px;
  border: none;
  resize: vertical;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  background-color: white;
  outline: none;
  transition: all 0.3s ease;
}

.code-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.analysis-result {
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.analysis-content {
  line-height: 1.7;
  padding: 0 20px 20px;
}

.knowledge-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.knowledge-tags .el-tag {
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 13px;
  background: #e6f7ff;
  border-color: #91d5ff;
  color: #1890ff;
}

.example-card {
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.code-examples {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 0 20px 20px;
}

.example-item h4 {
  margin-bottom: 12px;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.example-item h4::before {
  content: "📌";
  font-size: 14px;
}

.example-item pre {
  background-color: #2d3748;
  padding: 15px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 10px 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  color: #e2e8f0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.title-with-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.example-item code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  color: #e2e8f0;
}

.problem-list-card {
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  width: 100%;
  box-sizing: border-box;
  padding: 0;
  margin-left: -20px !important;
  margin-right: -20px !important;
  background: white;
}

.problem-detail-card {
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  width: 100%;
}

.problem-detail {
  line-height: 1.7;
  padding: 0 20px 20px;
}

.problem-section {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.problem-section h4 {
  margin-bottom: 12px;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.problem-section h4::before {
  content: "📌";
  font-size: 16px;
}

.problem-section p {
  margin: 0;
  color: #495057;
  font-size: 15px;
  line-height: 1.6;
}

.description-content {
  color: #495057;
  font-size: 15px;
  line-height: 1.6;
}

.description-content img {
  max-width: 100%;
  margin: 12px 0;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.problem-section pre {
  background-color: #2d3748;
  padding: 15px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 10px 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  color: #e2e8f0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.code-preview {
  cursor: pointer;
  color: #667eea;
  text-decoration: underline;
  font-weight: 500;
  transition: color 0.3s ease;
}

.code-preview:hover {
  color: #764ba2;
}

.input-section {
  margin-top: 20px;
}

.input-section h4 {
  margin-bottom: 10px;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-section h4::before {
  content: "📥";
  font-size: 14px;
}

.input-section .el-input {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.input-section .el-input:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.input-section .el-input textarea {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  transition: border-color 0.3s ease;
}

.input-section .el-input textarea:focus {
  border-color: #667eea;
  outline: none;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

/* 表格样式优化 */
.el-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e4e7ed;
}

.el-table th {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef) !important;
  font-weight: 600 !important;
  color: #2c3e50 !important;
  text-align: center !important;
  font-size: 15px;
  height: 48px;
  line-height: 48px;
  border-bottom: 2px solid #667eea !important;
}

.el-table td {
  text-align: center !important;
  vertical-align: middle !important;
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  height: 44px;
  line-height: 44px;
  border-bottom: 1px solid #f0f0f0 !important;
}

/* 表格行悬停效果 */
.el-table tr:hover td {
  background-color: #f5f7fa !important;
  color: #667eea !important;
  transition: all 0.3s ease;
}

/* 表格标题列样式 */
.el-table .title-with-status .el-button {
  font-size: 14px;
  font-weight: 600;
  color: #667eea;
  padding: 4px 8px;
  transition: all 0.3s ease;
}

.el-table .title-with-status .el-button:hover {
  color: #764ba2;
  text-decoration: underline;
  transform: translateY(-1px);
}

/* 标签样式优化 */
.el-table .el-tag {
  font-size: 12px;
  font-weight: 500;
  border-radius: 12px;
  padding: 2px 10px;
  transition: all 0.3s ease;
}

.el-table .el-tag:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

/* 容器样式调整，确保对齐 */
.code-submit-panel {
  padding: 0;
  margin: 0;
  width: 100%;
  box-sizing: border-box;
}

/* 确保 el-row 与卡片对齐 */
el-row {
  margin: 0 !important;
  width: 100%;
}

/* 确保 el-col 与卡片对齐 */
el-col {
  padding: 0 !important;
}

/* 确保所有卡片宽度一致 */
.problem-list-card,
.problem-detail-card,
.analysis-result,
el-card {
  width: 100% !important;
  box-sizing: border-box !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
  padding: 0 !important;
}

/* 移除 Element UI 卡片的默认内边距 */
el-card >>> .el-card__body {
  padding: 0 !important;
  margin: 0 !important;
  width: 100% !important;
}

/* 确保表格宽度一致 */
el-table {
  width: 100% !important;
  box-sizing: border-box !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* 分页样式 */
.pagination-container {
  margin-top: 20px;
  text-align: center;
}

.el-pagination .el-pager li.active {
  background: #667eea;
  color: white;
  border-radius: 4px;
}

.el-pagination button:hover {
  color: #667eea;
}

/* 按钮样式 */
.el-button {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.el-button--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.el-button--primary:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4392 100%);
}

/* 执行结果样式 */
.execution-result {
  margin-top: 10px;
}

.execution-result pre {
  background-color: #f0f9ff;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #bae7ff;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #0050b3;
  overflow-x: auto;
}

/* 反馈项样式 */
.feedback-item {
  margin-bottom: 12px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}

.feedback-item strong {
  color: #2c3e50;
  font-weight: 600;
}

.feedback-item p {
  margin: 5px 0 0 0;
  color: #495057;
  line-height: 1.5;
}

/* 提交历史样式 */
.submission-history {
  margin-top: 20px;
}

.submission-history .el-table {
  margin-top: 10px;
}

/* 提交详情样式 */
.submission-details {
  padding: 20px;
}

.submission-details h3 {
  margin-bottom: 15px;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
}

.submission-details pre {
  background-color: #2d3748;
  padding: 15px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 10px 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  color: #e2e8f0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.submission-details .el-divider {
  margin: 15px 0;
}

/* 题目列表样式 */
.problem-list {
  margin-top: 20px;
}

.problem-list .el-table {
  margin-top: 10px;
}

/* 已完成题目样式 */
.completed-problems {
  margin-top: 20px;
}

.completed-problems .el-table {
  margin-top: 10px;
}


.feedback-item {
  margin-bottom: 12px;
}
</style>
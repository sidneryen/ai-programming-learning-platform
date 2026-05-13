<template>
  <div class="homework-panel">
    <el-card class="homework-list-card">
      <template #header>
        <div class="card-header">
          <span>作业与测验列表</span>
        </div>
      </template>
      <el-table :data="homeworks" style="width: 100%">
        <el-table-column prop="id" label="编号" width="80" />
        <el-table-column prop="title" label="标题">
          <template #default="scope">
            <div class="title-with-status">
              <el-button link @click="selectHomework(scope.row)">{{ scope.row.title }}</el-button>
              <el-tag v-if="scope.row.status === 'ended'" type="danger" size="small" effect="plain" style="margin-left: 8px;">已结束</el-tag>
              <el-tag v-else-if="scope.row.status === 'completed'" type="success" size="small" effect="plain" style="margin-left: 8px;">已完成</el-tag>
              <el-tag v-else-if="scope.row.status === 'ongoing'" type="warning" size="small" effect="plain" style="margin-left: 8px;">进行中</el-tag>
              <el-tag v-else type="info" size="small" effect="plain" style="margin-left: 8px;">未开始</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.type === 'homework' ? 'primary' : 'danger'">{{ scope.row.type === 'homework' ? '作业' : '测验' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="deadline" label="截止时间" width="180" />
        <el-table-column prop="score" label="得分" width="80">
          <template #default="scope">
            <span v-if="scope.row.score !== null">{{ scope.row.score }}</span>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button type="primary" size="small" @click="selectHomework(scope.row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-container" style="margin-top: 15px; text-align: center;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          layout="prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-card v-if="selectedHomework" class="homework-detail-card">
      <template #header>
        <div class="card-header">
          <span>{{ selectedHomework.type === 'homework' ? '作业' : '测验' }}详情 - {{ selectedHomework.title }}</span>
        </div>
      </template>
      <div class="homework-detail">
        <div class="homework-section">
          <h4>题目列表</h4>
          <el-table :data="selectedHomework.problems" style="width: 100%">
            <el-table-column prop="problem_number" label="题目号" width="80" />
            <el-table-column label="标题">
              <template #default="scope">
                <div class="title-with-status">
                  <span>{{ scope.row.title }}</span>
                  <el-tag v-if="parseInt(scope.row.problem_number) >= 10000" type="info" size="small" style="margin-left: 8px;">
                    AI生成
                  </el-tag>
                  <el-tag v-if="scope.row.submissionStatus === true" type="success" size="small" style="margin-left: 8px;">
                    ✅
                  </el-tag>
                  <el-tag v-else-if="scope.row.submissionStatus === false" type="danger" size="small" style="margin-left: 8px;">
                    ❌
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="difficulty" label="难度" width="80">
              <template #default="scope">
                <el-tag :type="getDifficultyType(scope.row.difficulty)" size="small">
                  {{ scope.row.difficulty || '入门' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="分值" width="80" />
            <el-table-column label="操作" width="180">
              <template #default="scope">
                <div style="display: flex; gap: 10px;">
                  <el-button link @click="selectProblem(scope.row)" :disabled="selectedHomework?.status === 'ended'">{{ selectedHomework?.status === 'ended' ? '已结束' : '答题' }}</el-button>
                  <el-button link @click="showSubmissionHistory(scope.row)">提交记录</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
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

    <!-- 答题区域 -->
    <div v-if="selectedProblem" class="answer-container">
      <div class="left-panel">
        <el-card class="code-editor-card">
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
              <el-button type="primary" @click="submitAnswer" :loading="submitting" :disabled="selectedHomework?.status === 'ended'">
                {{ selectedHomework?.status === 'ended' ? '作业已结束，无法提交' : '提交答案' }}
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
          <div class="input-section">
            <h4>输入数据</h4>
            <el-input v-model="inputData" type="textarea" :rows="4" placeholder="请输入代码运行所需的输入数据..." resize="none" />
          </div>
        </el-card>
      </div>
      <div class="right-panel">
        <el-card class="analysis-result-card">
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
              <el-descriptions-item v-if="!(analysisResult.is_correct && analysisResult.score === 100)" label="得分">
                {{ analysisResult.score || 0 }}分
              </el-descriptions-item>
              
              <el-descriptions-item label="错误类型">
                {{ analysisResult.error_type || '无错误' }}
              </el-descriptions-item>
              
              <el-descriptions-item label="修改提示">
                <div>
                  <div>{{ analysisResult.hint || '代码语法正确' }}</div>
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
            <el-empty description="请提交代码进行分析" />
          </div>
        </el-card>
      </div>
    </div>

    <!-- 提交记录对话框 -->
    <el-dialog
      v-model="showSubmissionHistoryDialog"
      :title="`${currentHistoryProblem?.title || '题目'} - 提交记录`"
      width="800px"
    >
      <div v-if="submissionHistory.length > 0">
        <el-table :data="submissionHistory" style="width: 100%">
          <el-table-column prop="time" label="提交时间" width="200" />
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button type="primary" size="small" @click="viewSubmissionDetail(scope.row)">
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else class="no-data">
        <el-empty description="暂无提交记录" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../services/api'

const homeworks = ref([])
const selectedHomework = ref(null)
const selectedProblem = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const code = ref('print("Hello, World!")\n\n# 在这里输入您的Python代码...')
const inputData = ref('')
const submitting = ref(false)
const analysisResult = ref(null)
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
const showSubmissionHistoryDialog = ref(false)
const submissionHistory = ref([])
const currentHistoryProblem = ref(null)

const loadHomeworks = async (page = 1) => {
  try {
    // 获取学生ID，用于过滤作业
    const userId = localStorage.getItem('userId')
    const response = await api.getHomeworks(userId)
    if (response.success) {
      const problemsResponse = await api.getProblems(1, 500)
      // 直接使用getProblems返回的完整数据
      const detailedProblems = problemsResponse.problems || []
      let submissions = []
      if (userId) {
        try {
          const submissionsResponse = await api.getSubmissions(Number(userId))
          if (submissionsResponse.success) {
            submissions = submissionsResponse.submissions || []
          }
        } catch (error) {
          console.error('获取提交记录失败:', error)
        }
      }
      
      // 缓存通过编号获取的题目
      const problemCache = {}
      
      // 定义一个函数根据编号获取题目详情
      const getProblemByNumber = async (num) => {
        // 先从缓存查找
        if (problemCache[num]) {
          return problemCache[num]
        }
        // 先从已获取的题目列表查找
        const problem = detailedProblems.find(p => p.problem_number.toString() === num)
        if (problem) {
          problemCache[num] = problem
          return problem
        }
        // 如果找不到，尝试通过API获取
        try {
          const response = await api.getProblemByNumber(parseInt(num))
          if (response.success && response.problem) {
            problemCache[num] = response.problem
            return response.problem
          }
        } catch (error) {
          console.error(`获取题目 ${num} 详情失败:`, error)
        }
        return null
      }
      
      // 异步获取所有作业的题目详情
      const homeworksWithProblems = await Promise.all(response.homeworks.map(async homework => {
        const now = new Date()
        const startTime = homework.start_time ? new Date(homework.start_time) : null
        const endTime = homework.end_time ? new Date(homework.end_time) : null
        let status = 'pending'
        if (startTime && now >= startTime) {
          if (endTime && now > endTime) {
            status = 'ended'
          } else {
            status = 'ongoing'
          }
        }
        const formatTime = (dateString) => {
          if (!dateString) return ''
          const date = new Date(dateString)
          return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
          })
        }
        const getProblemsByNumbers = async (problemNumbers, problemScores) => {
          if (!problemNumbers) return []
          const numbers = problemNumbers.split(',').map(num => num.trim())
          const scores = problemScores ? problemScores.split(',').map(score => parseInt(score.trim())) : []
          
          // 计算平均分
          const avgScore = numbers.length > 0 ? Math.floor(100 / numbers.length) : 0
          const remainder = 100 - (avgScore * numbers.length)
          
          // 异步获取每个题目详情
          const problems = await Promise.all(numbers.map(async (num, index) => {
            const problem = await getProblemByNumber(num)
            // 获取分数，如果没有设置则使用平均分
            let score = scores[index] 
            // 只有在没有设置具体分数时才使用平均分和余数逻辑
            if (score === undefined || score === null) {
              score = avgScore
              // 处理余数，将余数分配给第一个题目
              if (index === 0 && remainder > 0) {
                score += remainder
              }
            }
            
            // 获取题目提交状态（只考虑作业与测验中的提交）
            let submissionStatus = null
            let submissionScore = 0
            if (problem && userId) {
              // 筛选出来自作业与测验的提交
              const homeworkSubmissions = submissions.filter(s => s.is_homework_submission === true)
              // 找到该题目的最新提交
              const submission = homeworkSubmissions.find(s => s.problem_id === problem.id)
              if (submission) {
                try {
                  const feedback = JSON.parse(submission.ai_feedback)
                  submissionStatus = feedback.is_correct
                  // 根据题目当前的分值和提交状态计算得分
                  submissionScore = submissionStatus ? score : 0
                } catch (error) {
                  console.error('解析提交反馈失败:', error)
                }
              }
            }
            
            return problem ? {
              ...problem,
              problem_number: num,
              score,
              submissionStatus,
              submissionScore
            } : {
              id: index + 1,
              problem_number: num,
              title: '题目 ' + num + ' (未找到)',
              score,
              submissionStatus: null,
              submissionScore: 0,
              description: '暂无描述',
              input_description: '暂无输入描述',
              output_description: '暂无输出描述',
              sample_input: '',
              sample_output: ''
            }
          }))
          
          return problems
        }
        // 计算作业当前得分
        const problems = await getProblemsByNumbers(homework.problem_numbers, homework.problem_scores)
        const currentScore = problems.reduce((total, problem) => {
          return total + (problem.submissionScore || 0)
        }, 0)
        
        return {
          ...homework,
          status,
          deadline: formatTime(homework.end_time),
          description: homework.description || '暂无描述',
          problems,
          score: currentScore
        }
      }))
      
      homeworks.value = homeworksWithProblems
      total.value = homeworks.value.length
    } else {
      ElMessage.error('获取作业列表失败')
    }
  } catch (error) {
    console.error('获取作业列表失败:', error)
    ElMessage.error('获取作业列表失败')
  }
}

const selectHomework = (homework) => {
  selectedHomework.value = homework
  selectedProblem.value = null
}

const selectProblem = async (problem) => {
  try {
    const response = await api.getProblemDetail(problem.id)
    if (response.success) {
      selectedProblem.value = response.problem
    } else {
      ElMessage.warning('获取题目详情失败，使用默认信息')
      selectedProblem.value = problem
    }
    inputData.value = selectedProblem.value.sample_input || ''
    // 设置默认代码为空
    code.value = ''
    // 重置AI分析结果
    analysisResult.value = null
    // 更新行号
    updateLineNumbers()
  } catch (error) {
    console.error('获取题目详情失败:', error)
    ElMessage.error('获取题目详情失败')
    selectedProblem.value = problem
    inputData.value = problem.sample_input || ''
    // 设置默认代码为空
    code.value = ''
    // 重置AI分析结果
    analysisResult.value = null
  }
}

const submitAnswer = async () => {
  if (!selectedProblem.value) {
    ElMessage.warning('请先选择一道题目')
    return
  }

  if (selectedHomework.value?.status === 'ended') {
    ElMessage.warning('作业已结束，无法提交')
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
      'python',
      true  // is_homework_submission: true，因为这是从作业与测验中提交的
    )
    if (result.success) {
      ElMessage.success('答案提交成功！')
      analysisResult.value = result.analysis
      // 重新加载作业列表，更新提交状态和得分
      await loadHomeworks()
      // 重新选择当前作业，保持页面状态
      if (selectedHomework.value) {
        const updatedHomework = homeworks.value.find(h => h.id === selectedHomework.value.id)
        if (updatedHomework) {
          selectedHomework.value = updatedHomework
        }
      }
    } else {
      ElMessage.error(result.error || '提交失败')
    }
  } catch (error) {
    ElMessage.error('提交失败: ' + error.message)
  } finally {
    submitting.value = false
  }
}

const handleSizeChange = (size) => {
  pageSize.value = size
  loadHomeworks(1)
}

const handleCurrentChange = (current) => {
  loadHomeworks(current)
}

const showSubmissionHistory = async (problem) => {
  currentHistoryProblem.value = problem
  try {
    const userId = localStorage.getItem('userId')
    if (!userId) {
      ElMessage.warning('请先登录')
      return
    }
    const response = await api.getSubmissions(Number(userId), problem.id)
    if (response.success) {
      // 映射字段名，确保前端使用正确的字段名
      submissionHistory.value = response.submissions.map(submission => ({
        time: submission.submission_time,
        code: submission.code_content,
        feedback: submission.ai_feedback
      }))
      showSubmissionHistoryDialog.value = true
    } else {
      ElMessage.error('获取提交记录失败')
    }
  } catch (error) {
    console.error('获取提交记录失败:', error)
    ElMessage.error('获取提交记录失败: ' + error.message)
  }
}

const viewSubmissionDetail = (submission) => {
  let feedbackHtml = '无反馈'
  if (submission.feedback) {
    try {
      const feedback = JSON.parse(submission.feedback)
      feedbackHtml = `
        <div style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow: auto; max-height: 300px;">
          ${feedback.is_correct !== undefined ? `<div style="margin-bottom: 8px;"><strong>是否正确:</strong> ${feedback.is_correct ? '是' : '否'}</div>` : ''}
          ${feedback.error_type ? `<div style="margin-bottom: 8px;"><strong>错误类型:</strong> ${feedback.error_type}</div>` : ''}
          ${feedback.hint ? `<div style="margin-bottom: 8px;"><strong>修改提示:</strong> ${feedback.hint}</div>` : ''}
          ${feedback.hint_en ? `<div style="margin-bottom: 8px; font-size: 14px; color: #606266;"><strong>Hint:</strong> ${feedback.hint_en}</div>` : ''}
          ${feedback.error_reason ? `<div style="margin-bottom: 8px;"><strong>错误原因:</strong> <span style="color: #e74c3c; font-weight: 500;">${feedback.error_reason}</span></div>` : ''}
          ${feedback.fix_suggestion ? `<div style="margin-bottom: 8px;"><strong>修改建议:</strong> <span style="color: #27ae60; font-weight: 500;">${feedback.fix_suggestion}</span></div>` : ''}
          ${feedback.execution_result ? `<div style="margin-bottom: 8px;"><strong>执行结果:</strong> ${feedback.execution_result.replace(/\n/g, '<br>')}</div>` : ''}
          ${feedback.knowledge_tags ? `<div style="margin-bottom: 8px;"><strong>涉及知识点:</strong> ${feedback.knowledge_tags.map(tag => `<span style="background: #e4e7ed; padding: 2px 8px; border-radius: 4px; margin-right: 8px; font-size: 14px;">${tag}</span>`).join('')}</div>` : ''}
        </div>
      `
    } catch (e) {
      feedbackHtml = submission.feedback
    }
  }
  
  ElMessageBox.alert(
    `<div style="padding: 20px;">
      <h4 style="margin-bottom: 10px;">提交时间: ${submission.time}</h4>
      <h4 style="margin-bottom: 10px;">代码内容:</h4>
      <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow: auto; max-height: 200px;">${submission.code || '无代码'}</pre>
      <h4 style="margin-bottom: 10px; margin-top: 20px;">AI反馈:</h4>
      ${feedbackHtml}
    </div>`,
    '提交详情',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '确定',
      width: '600px'
    }
  )
}

onMounted(() => {
  loadHomeworks()
  // 初始更新行号
  updateLineNumbers()
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

.title-with-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.homework-detail-card {
  margin-top: 20px;
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.homework-detail {
  line-height: 1.7;
  padding: 0 20px 20px;
}

.homework-section {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.homework-section h4 {
  margin-bottom: 12px;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.homework-section h4::before {
  content: "📌";
  font-size: 16px;
}

.homework-section p,
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

.homework-section pre,
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

.answer-container {
  display: flex;
  gap: 20px;
  margin-top: 20px;
  align-items: stretch;
}

.left-panel {
  flex: 1;
  min-width: 400px;
  display: flex;
  flex-direction: column;
}

.right-panel {
  flex: 1;
  min-width: 400px;
  display: flex;
  flex-direction: column;
}

.code-editor-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.analysis-result-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  margin-top: 0 !important;
}

.analysis-result-card .el-card__body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.analysis-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.empty-analysis {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.code-editor-container {
  position: relative;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  flex: 1;
  min-height: 200px;
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

.analysis-result-card {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.analysis-content {
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

/* 表格样式优化 */
.el-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.el-table th {
  background: #f8f9fa !important;
  font-weight: 600 !important;
  color: #2c3e50 !important;
  text-align: center !important;
}

.el-table td {
  text-align: center !important;
  vertical-align: middle !important;
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
  color: #606266;
}

.analysis-section {
  margin-bottom: 15px;
}

.analysis-section h4 {
  margin-bottom: 8px;
  color: #333;
  font-size: 16px;
  font-weight: bold;
}

.analysis-section p {
  margin: 0;
  color: #606266;
}

.analysis-section pre {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #333;
}

.knowledge-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hint-en {
  font-style: italic;
}

.execution-result pre {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #333;
}

/* 按钮样式 */
.card-header .el-button {
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  padding: 10px 20px;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.card-header .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.card-header .el-button:disabled {
  background: #ccc;
  transform: none;
  box-shadow: none;
  cursor: not-allowed;
}
</style>
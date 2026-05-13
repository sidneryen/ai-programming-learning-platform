<template>
  <div class="personal-recommendation">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>个性化学习推荐</span>
          <el-button type="primary" @click="refreshRecommendations" :loading="loading">
            刷新推荐
          </el-button>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <el-skeleton :rows="5" animated />
      </div>
      
      <!-- 推荐内容 -->
      <div v-else-if="recommendations.length > 0" class="recommend-list">
        <el-table :data="recommendations" style="width: 100%" v-loading="loading">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="title" label="推荐标题" min-width="150">
            <template #default="scope">
              <div class="title-with-status">
                <span>{{ scope.row.title }}</span>
                <el-tag v-if="scope.row.isCompleted" type="success" size="small" style="margin-left: 8px;">
                  ✅ 已完成
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="problem_count" label="题目数量" width="100" />
          <el-table-column prop="problem_number" label="题目编号" min-width="150" />
          <el-table-column prop="generated_at" label="生成时间" width="180" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="scope">
              <el-button 
                type="primary" 
                size="small" 
                @click="selectRecommendation(scope.row)"
              >
                查看题目
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <!-- 空状态 -->
      <div v-else class="empty-state" style="text-align: center; padding: 40px;">
        <el-empty description="暂无个性化推荐" />
        <p class="empty-hint" style="margin-top: 10px;">请先完成一些练习，系统会根据您的学习情况生成推荐</p>
        <el-button type="primary" @click="refreshRecommendations" style="margin-top: 10px;">
          重新加载
        </el-button>
      </div>
    </el-card>

    <!-- 推荐详情 -->
    <el-card v-if="selectedRecommendation" class="recommendation-detail-card">
      <template #header>
        <div class="card-header">
          <span>推荐详情 - {{ selectedRecommendation.title }}</span>
        </div>
      </template>
      <div class="recommendation-detail">
        <div class="recommendation-section">
          <h4>题目列表</h4>
          <el-table :data="selectedRecommendation.problems" style="width: 100%">
            <el-table-column prop="problem_number" label="题目号" width="80" />
            <el-table-column label="标题">
              <template #default="scope">
                <div class="title-with-status" style="display: flex; align-items: center;">
                  <span>{{ scope.row.title }}</span>
                  <el-tag v-if="scope.row.isAiGenerated" type="info" size="small" style="margin-left: 8px;">
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
            <el-table-column label="操作" width="180">
              <template #default="scope">
                <div style="display: flex; gap: 10px;">
                  <el-button link @click="selectProblem(scope.row)">答题</el-button>
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
        <div class="card-header" style="display: flex; align-items: center; gap: 10px;">
          <span>题目详情 - {{ selectedProblem.problem_number }}. {{ selectedProblem.title }}</span>
          <el-tag v-if="selectedProblem.isAiGenerated" type="info" size="small">
            AI生成
          </el-tag>
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
              <el-button type="primary" @click="submitAnswer" :loading="submitting">
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

const loading = ref(false)
const recommendations = ref([])
const currentStudentId = ref(null)
const selectedRecommendation = ref(null)
const selectedProblem = ref(null)
const code = ref('')
const inputData = ref('')
const submitting = ref(false)
const analysisResult = ref(null)
const selectedLanguage = ref('python')

// 行号相关
const lineNumbers = ref('1')

// 获取语言占位符
const getLanguagePlaceholder = () => {
  const languageMap = {
    'python': 'Python',
    'c': 'C',
    'cpp': 'C++',
    'java': 'Java',
    'go': 'Go'
  }
  return languageMap[selectedLanguage.value] || 'Python'
}

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

// 获取当前学生ID
const getCurrentStudentId = async () => {
    try {
        const userId = localStorage.getItem('userId')
        if (userId) {
            currentStudentId.value = userId
            return userId
        }
        return null
    } catch (error) {
        console.error('获取学生ID失败:', error)
        return null
    }
}

// 加载推荐数据
// 缓存题目数据，避免重复请求
let cachedProblems = []
let cacheTimestamp = 0
const CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存

const loadRecommendations = async () => {
    loading.value = true
    try {
        const studentId = await getCurrentStudentId()
        if (!studentId) {
            ElMessage.error('请先登录')
            loading.value = false
            return
        }
        
        // 调用API获取AI推荐作业列表
        const response = await fetch(`http://localhost:5002/api/ai-recommend/student-homework/${studentId}`)
        const data = await response.json()
        
        if (data.success) {
            // 先收集所有推荐中需要的题目编号
            const allRequiredProblemNumbers = new Set()
            data.homeworks.forEach(recommendation => {
                recommendation.problem_number.split(',').map(num => num.trim()).filter(Boolean).forEach(num => {
                    allRequiredProblemNumbers.add(parseInt(num))
                })
            })
            
            // 并行获取题目数据（智能缓存）和提交记录
            const [allProblems, submissions] = await Promise.all([
                loadProblemsSmartCache([...allRequiredProblemNumbers]),
                loadSubmissions(studentId)
            ])
            
            // 为每个推荐添加题目详情
            recommendations.value = data.homeworks.map(recommendation => {
                // 解析题目编号列表并去重
                const problemNumbers = [...new Set(recommendation.problem_number.split(',').map(num => num.trim()).filter(Boolean))]
                
                // 找到对应的题目详情
                const problems = problemNumbers.map(num => {
                    const numInt = parseInt(num)
                    const problem = allProblems.find(p => p.problem_number === numInt)
                    
                    // 获取题目提交状态
                    let submissionStatus = null
                    if (problem && studentId) {
                        const submission = submissions.find(s => s.problem_id === problem.id)
                        if (submission) {
                            try {
                                const feedback = JSON.parse(submission.ai_feedback)
                                submissionStatus = feedback.is_correct
                            } catch (error) {
                                console.error('解析提交反馈失败:', error)
                            }
                        }
                    }
                    
                    // 判断是否是AI生成的题目（编号 >= 10000）
                    const isAiGenerated = numInt >= 10000
                    
                    if (problem) {
                        return {
                            ...problem,
                            problem_number: num,
                            submissionStatus,
                            isAiGenerated
                        }
                    } else {
                        // 题目未找到，但如果是AI生成的题目，也显示AI生成标识
                        return {
                            id: 0,
                            problem_number: num,
                            title: '题目 ' + num + (isAiGenerated ? ' (AI生成)' : ' (未找到)'),
                            submissionStatus: null,
                            description: '暂无描述',
                            input_description: '暂无输入描述',
                            output_description: '暂无输出描述',
                            sample_input: '',
                            sample_output: '',
                            isAiGenerated,
                            difficulty: '入门'
                        }
                    }
                })
                
                // 计算推荐的完成状态（所有题目都已正确提交）
                const isCompleted = problems.every(problem => problem.submissionStatus === true)
                
                return {
                    ...recommendation,
                    problems,
                    isCompleted
                }
            })
        } else {
            ElMessage.error(data.error || '加载推荐失败')
        }
    } catch (error) {
        console.error('加载推荐失败:', error)
        ElMessage.error('加载推荐失败')
    } finally {
        loading.value = false
    }
}

// 带缓存的题目加载函数
const loadProblemsWithCache = async () => {
    const now = Date.now()
    // 如果缓存有效，直接返回缓存数据
    if (cachedProblems.length > 0 && now - cacheTimestamp < CACHE_DURATION) {
        console.log('使用缓存的题目数据')
        return cachedProblems
    }
    
    // 否则重新加载所有题目（使用并行请求）
    console.log('重新加载题目数据')
    let allProblems = []
    
    try {
        // 先获取第一页，获取总页数
        const firstResponse = await fetch('http://localhost:5002/api/problems?page=1')
        const firstData = await firstResponse.json()
        
        if (firstData.success && firstData.problems) {
            allProblems = allProblems.concat(firstData.problems)
            const totalPages = firstData.total_pages || 1
            
            // 如果有多页，并行请求所有剩余页面
            if (totalPages > 1) {
                const pageRequests = []
                for (let page = 2; page <= totalPages; page++) {
                    pageRequests.push(
                        fetch(`http://localhost:5002/api/problems?page=${page}`).then(res => res.json())
                    )
                }
                
                // 并行获取所有页面
                const results = await Promise.all(pageRequests)
                results.forEach(result => {
                    if (result.success && result.problems) {
                        allProblems = allProblems.concat(result.problems)
                    }
                })
            }
            
            // 更新缓存
            cachedProblems = allProblems
            cacheTimestamp = now
        }
    } catch (error) {
        console.error('加载题目数据失败:', error)
    }
    
    return allProblems
}

// 智能缓存加载题目数据 - 只获取需要的题目
const loadProblemsSmartCache = async (requiredNumbers) => {
    const now = Date.now()
    
    // 获取当前缓存中已有的题目编号
    const cachedNumbers = new Set(cachedProblems.map(p => p.problem_number))
    
    // 找出需要但缺失的题目编号
    const missingNumbers = requiredNumbers.filter(num => !cachedNumbers.has(num))
    
    // 如果有缺失的题目，或者缓存过期，重新加载全部
    if (missingNumbers.length > 0 || now - cacheTimestamp >= CACHE_DURATION) {
        if (missingNumbers.length > 0) {
            console.log(`🔍 需要获取 ${missingNumbers.length} 个缺失的题目: ${missingNumbers.join(', ')}，重新加载全部`)
        } else {
            console.log(`⏰ 缓存已过期，重新加载全部题目`)
        }
        const loadedProblems = await loadProblemsWithCache()
        console.log(`📥 加载完成，共 ${loadedProblems.length} 个题目`)
        
        // 检查是否获取到了缺失的题目
        const stillMissing = missingNumbers.filter(num => 
            !loadedProblems.find(p => p.problem_number === num)
        )
        if (stillMissing.length > 0) {
            console.warn(`⚠️ 以下题目仍未找到（可能是新生成的AI题目）: ${stillMissing.join(', ')}`)
        }
        
        return loadedProblems
    }
    
    // 所有题目都在缓存中且缓存有效，直接返回
    console.log('✓ 所有题目都在缓存中')
    return cachedProblems
}

// 获取学生提交记录
const loadSubmissions = async (studentId) => {
    if (!studentId) return []
    
    try {
        const response = await api.getSubmissions(Number(studentId))
        if (response.success) {
            return response.submissions || []
        }
    } catch (error) {
        console.error('获取提交记录失败:', error)
    }
    
    return []
}

// 选择推荐
const selectRecommendation = (recommendation) => {
    console.log('📋 选中推荐:', recommendation.title)
    console.log('📝 题目数量:', recommendation.problems?.length || 0)
    if (recommendation.problems) {
        console.log('📊 题目列表:', recommendation.problems.map(p => p.problem_number))
    }
    selectedRecommendation.value = recommendation
    selectedProblem.value = null
}

// 选择题目
const selectProblem = async (problem) => {
    try {
        // 检查题目ID是否有效（AI生成的题目可能没有有效的数据库ID）
        if (problem.id && problem.id > 0) {
            const response = await api.getProblemDetail(problem.id)
            if (response.success) {
                selectedProblem.value = response.problem
            } else {
                ElMessage.warning('获取题目详情失败，使用默认信息')
                selectedProblem.value = problem
            }
        } else {
            // 如果ID无效（如AI生成的题目），直接使用传入的problem数据
            selectedProblem.value = problem
        }
        inputData.value = selectedProblem.value.sample_input || ''
        // 设置默认代码为空
        code.value = ''
        // 重置AI分析结果为默认状态
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
    }
}

// 提交答案
const submitAnswer = async () => {
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
            selectedProblem.value?.id
        )
        if (result.success) {
            ElMessage.success('答案提交成功！')
            analysisResult.value = result.analysis
            // 重新加载推荐列表，更新提交状态
            await loadRecommendations()
            // 重新选择当前推荐，保持页面状态
            if (selectedRecommendation.value) {
                const updatedRecommendation = recommendations.value.find(r => r.id === selectedRecommendation.value.id)
                if (updatedRecommendation) {
                    selectedRecommendation.value = updatedRecommendation
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

// 显示提交记录
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

// 查看提交详情
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

// 刷新推荐
const refreshRecommendations = () => {
    // 强制清除题目缓存，因为新的推荐可能包含刚生成的AI题目
    // 这些题目是教师端刚刚通过DeepSeek API生成并添加到数据库的
    cachedProblems = []
    cacheTimestamp = 0
    console.log('🗑️ 已清除题目缓存，准备加载最新推荐')
    loadRecommendations()
}

onMounted(() => {
    loadRecommendations()
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
</script>

<style scoped>
.personal-recommendation {
  padding: 20px;
}

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

.loading {
  padding: 40px 0;
}

.recommend-card {
  margin-bottom: 20px;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.recommend-card .title {
  font-weight: bold;
  font-size: 16px;
  color: #2c3e50;
}

.recommend-card .description {
  color: #495057;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 15px;
}

.meta-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  color: #999;
  font-size: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.progress {
  margin-top: 15px;
}

.progress-text {
  display: block;
  margin-top: 5px;
  font-size: 12px;
  color: #666;
  text-align: center;
}

.card-footer {
  display: flex;
  justify-content: space-between;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

.empty-hint {
  margin-top: 10px;
  color: #999;
  font-size: 14px;
}

.recommendation-detail-card {
  margin-top: 20px;
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.recommendation-detail {
  line-height: 1.7;
  padding: 0 20px 20px;
}

.recommendation-section {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.recommendation-section h4 {
  margin-bottom: 12px;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.recommendation-section h4::before {
  content: "📌";
  font-size: 16px;
}

.title-with-status {
  display: flex;
  align-items: center;
  gap: 10px;
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

.code-editor-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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

.submit-section {
  margin-top: 20px;
  text-align: right;
}

.submit-section .el-button {
  padding: 10px 24px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.submit-section .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.problem-detail-card {
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.problem-detail {
  line-height: 1.7;
  padding: 0 20px 20px;
}

.analysis-result-card {
  margin-top: 20px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.analysis-content {
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

.analysis-section {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.analysis-section h4 {
  margin-bottom: 12px;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.analysis-section h4::before {
  content: "📌";
  font-size: 16px;
}

.analysis-section p {
  margin: 0;
  color: #495057;
  font-size: 15px;
  line-height: 1.6;
}

.analysis-section pre {
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

.hint-en {
  font-style: italic;
  color: #606266;
  margin-top: 8px;
  font-size: 14px;
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
  flex: 1;
  min-height: 200px;
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

/* 提交记录对话框样式 */
.submission-history {
  margin-top: 20px;
}

.submission-history .el-table {
  margin-top: 10px;
}

.no-data {
  padding: 40px 0;
  text-align: center;
}
</style>
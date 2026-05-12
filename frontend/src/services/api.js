// src/services/api.js
import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:5002/api', // 后端Flask地址（确保后端已启动）
  timeout: 30000, // 增加超时时间到30秒
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器（携带token）
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器（处理返回数据）
api.interceptors.response.use(
  response => {
    return response.data // 直接返回响应体的data字段
  },
  error => {
    console.error('API请求错误:', error)
    return Promise.reject(error)
  }
)

// API接口定义（默认导出）
export default {

  
  getKnowledgeMap(studentId) {
    return api.get(`/knowledge_map/${studentId}`)
  },
  
  getRecommendations(studentId) {
    return api.get(`/recommend/${studentId}`)
  },
  
  getSubmissions(studentId, problemId = null) {
    const url = problemId 
      ? `/submissions/${studentId}?problem_id=${problemId}` 
      : `/submissions/${studentId}`
    return api.get(url)
  },

  // 获取某个题目的所有提交记录
  getProblemSubmissions(problemId) {
    return api.get(`/problem_submissions/${problemId}`)
  },
  
  // 系统测试
  testConnection() {
    return api.get('/test')
  },
  
  // 数据初始化
  initTestData() {
    return api.post('/init_test_data')
  },

  // ✅ 新增：登录接口（用户名+密码）
  login(username, password) {
    return api.post('/login', { username, password })
  },

  // ✅ 新增：用户注册接口
  register(data) {
    return api.post('/register', data)
  },

  // ✅ 新增：批量导入学生花名册
  importStudents(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/students/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // ✅ 新增：获取所有学生列表
  getAllStudents() {
    return api.get('/students')
  },

  // ✅ 新增：获取题目列表（支持分页和搜索）
  getProblems(page = 1, perPage = 10, searchParams = {}) {
    let url = `/problems?page=${page}&per_page=${perPage}`
    
    // 添加搜索参数
    if (searchParams.problemNumber) {
      url += `&problem_number=${searchParams.problemNumber}`
    }
    if (searchParams.title) {
      url += `&title=${encodeURIComponent(searchParams.title)}`
    }
    if (searchParams.category) {
      url += `&category=${encodeURIComponent(searchParams.category)}`
    }
    if (searchParams.difficulty) {
      url += `&difficulty=${encodeURIComponent(searchParams.difficulty)}`
    }
    
    return api.get(url)
  },

  // ✅ 新增：获取所有题目分类
  getProblemCategories() {
    return api.get('/problems/categories')
  },

  // ✅ 新增：获取学生已完成的题目列表
  getCompletedProblems(studentId) {
    return api.get(`/students/${studentId}/completed-problems`)
  },

  // ✅ 新增：获取题目详情
  getProblemDetail(problemId) {
    return api.get(`/problems/${problemId}`)
  },

  // ✅ 新增：根据题目编号获取题目
  getProblemByNumber(problemNumber) {
    return api.get(`/problems/detail?number=${problemNumber}`)
  },

  // ✅ 新增：添加题目
  addProblem(problemData) {
    return api.post('/problems', problemData)
  },

  // ✅ 新增：通过AI生成题目
  generateProblems(topic, count, difficulty = '入门', require_custom_function = true, language = 'python') {
    return api.post('/problems/generate', { topic, count, difficulty, require_custom_function, language })
  },

  // ✅ 新增：删除题目
  deleteProblem(problemId) {
    return api.delete(`/problems/${problemId}`)
  },

  // ✅ 新增：导出题目
  exportProblems() {
    return api.get('/problems/export', { responseType: 'blob' })
  },

  // ✅ 新增：导入题目
  importProblems(formData) {
    return api.post('/problems/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // ✅ 新增：删除学生
  deleteStudent(studentId) {
    return api.delete(`/students/${studentId}`)
  },

  // ✅ 新增：更新题目
  updateProblem(problemId, problemData) {
    return api.put(`/problems/${problemId}`, problemData)
  },

  // ✅ 新增：测试题目
  testProblem(problemId, codeData) {
    return api.post(`/test-problem/${problemId}`, codeData)
  },

  // ✅ 新增：获取教师测试提交记录
  getTeacherSubmissions(teacherId) {
    return api.get(`/teacher/submissions?teacher_id=${teacherId}`)
  },

  // ✅ 新增：备份数据库
  backupDatabase() {
    return api.get('/backup/database', {
      responseType: 'blob'
    })
  },

  // ✅ 新增：获取备份历史
  getBackupHistory() {
    return api.get('/backup/history')
  },

  // ✅ 新增：提交代码分析
  submitCode(studentId, code, inputData, problemId, language = 'python', isHomeworkSubmission = false) {
    return api.post('/submit', {
      student_id: studentId,
      code: code,
      input_data: inputData,
      problem_id: problemId,
      language: language,
      is_homework_submission: isHomeworkSubmission
    })
  },

  // ✅ 新增：获取作业与测验列表
  getHomeworks(studentId = null) {
    if (studentId) {
      return api.get(`/homeworks?student_id=${studentId}`)
    }
    return api.get('/homeworks')
  },

  // ✅ 新增：添加作业与测验
  addHomework(homeworkData) {
    return api.post('/homeworks', homeworkData)
  },

  // ✅ 新增：更新作业与测验
  updateHomework(homeworkId, homeworkData) {
    return api.put(`/homeworks/${homeworkId}`, homeworkData)
  },

  // ✅ 新增：删除作业与测验
  deleteHomework(homeworkId) {
    return api.delete(`/homeworks/${homeworkId}`)
  },

  // ✅ 新增：获取作业成绩数据
  getHomeworkScores(homeworkId) {
    return api.get(`/homeworks/${homeworkId}/scores`)
  },

  // ✅ 新增：获取学生提交记录
  getStudentSubmissions(studentId) {
    return api.get(`/submissions/${studentId}`)
  },

  // ✅ 新增：获取班级知识图谱
  getClassKnowledgeMap(className) {
    return api.get(`/class_knowledge_map/${encodeURIComponent(className)}`)
  },

  // ✅ 新增：获取用户信息
  getUserInfo(userId) {
    return api.get(`/users/${userId}`)
  },

  // ✅ 新增：更新用户信息
  updateUserInfo(userId, userData) {
    return api.put(`/users/${userId}`, userData)
  },

  // ✅ 新增：获取今日提交数
  getTodaySubmissions() {
    return api.get('/submissions/today')
  },

  // ✅ 新增：教师修改密码
  changeTeacherPassword(teacherId, oldPassword, newPassword) {
    return api.post('/teacher/change-password', {
      teacher_id: teacherId,
      old_password: oldPassword,
      new_password: newPassword
    })
  },
}
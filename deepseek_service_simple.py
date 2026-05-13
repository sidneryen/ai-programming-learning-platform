"""
DeepSeek 代码分析器 - 简化版
用于高职Python编程学情诊断系统
"""

import json
import re
import requests

class DeepSeekAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
    
    def analyze_code(self, student_code):
        """分析学生代码"""
        # 先进行基本的语法检查
        syntax_result = self._check_syntax(student_code)
        
        # 如果语法错误，调用DeepSeek API获取详细的错误分析和修复建议
        if not syntax_result['is_correct']:
            try:
                # 调用DeepSeek API分析语法错误
                api_result = self._analyze_syntax_error(student_code, syntax_result["hint"])
                
                # 合并语法检查结果和API分析结果
                result = {
                    "is_correct": False,
                    "error_type": syntax_result["error_type"],
                    "hint": syntax_result["hint"],
                    "hint_en": syntax_result["hint_en"],
                    "knowledge_tags": api_result.get("knowledge_tags", syntax_result["knowledge_tags"])
                }
                
                # 添加错误原因和修复建议
                if 'error_reason' in api_result:
                    result['error_reason'] = api_result['error_reason']
                if 'fix_suggestion' in api_result:
                    result['fix_suggestion'] = api_result['fix_suggestion']
                
                return result
            except Exception as e:
                print(f"DeepSeek API调用失败: {e}")
                return syntax_result
        
        # 语法正确的情况下，检查代码是否包含input()函数
        if 'input(' in student_code:
            # 对于包含input()函数的代码，使用模拟分析
            # 但仍然调用DeepSeek API获取知识点分析
            mock_result = self._mock_analyze_code(student_code)
            
            # 调用DeepSeek API获取知识点分析
            try:
                api_result = self._real_analyze_code(student_code)
                mock_result['knowledge_tags'] = api_result.get('knowledge_tags', mock_result.get('knowledge_tags', []))
                
                # 如果API返回了更详细的分析，使用API结果
                if 'is_correct' in api_result:
                    mock_result['is_correct'] = api_result['is_correct']
                if 'error_type' in api_result:
                    mock_result['error_type'] = api_result['error_type']
                if 'hint' in api_result:
                    mock_result['hint'] = api_result['hint']
            except Exception as e:
                print(f"DeepSeek API调用失败: {e}")
            
            if "hint_en" not in mock_result:
                mock_result["hint_en"] = mock_result.get("hint", "")
            return mock_result
        
        # 如果语法正确且不包含input()，调用DeepSeek API进行深入分析
        try:
            result = self._real_analyze_code(student_code)
            # 确保返回格式正确
            if "hint_en" not in result:
                result["hint_en"] = result.get("hint", "")
            return result
        except Exception as e:
            print(f"DeepSeek API调用失败: {e}")
            # 失败时回退到模拟分析
            mock_result = self._mock_analyze_code(student_code)
            if "hint_en" not in mock_result:
                mock_result["hint_en"] = mock_result.get("hint", "")
            return mock_result
    
    def _analyze_syntax_error(self, student_code, error_message):
        """使用DeepSeek API分析语法错误，返回错误原因和修复建议"""
        if not self.api_key:
            return {"knowledge_tags": ["基础语法", "调试"]}
        
        prompt = f"""你是一位Python编程教师，请分析以下代码的语法错误并提供修复建议：

代码：
```python
{student_code}
```

错误信息：{error_message}

请按照以下JSON格式返回分析结果：
{{
  "error_reason": "错误原因的详细分析，解释为什么会出现这个语法错误",
  "fix_suggestion": "具体的修改建议，包括正确的代码示例",
  "knowledge_tags": ["涉及的知识点标签"]
}}

请只返回JSON格式，不要包含其他无关内容。"""
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 800
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # 提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    analysis = json.loads(json_match.group(0))
                    if isinstance(analysis, dict):
                        return analysis
                except json.JSONDecodeError:
                    pass
            
            # 如果解析失败，返回包含分析内容的结果
            return {
                "error_reason": content,
                "fix_suggestion": content,
                "knowledge_tags": ["基础语法", "调试"]
            }
        except Exception as e:
            print(f"DeepSeek API语法错误分析失败: {e}")
            return {"knowledge_tags": ["基础语法", "调试"]}
    
    def _check_syntax(self, student_code):
        """检查代码语法"""
        code = student_code.strip()
        
        if not code:
            return {
                "is_correct": False,
                "error_type": "空代码",
                "hint": "代码内容不能为空",
                "hint_en": "Code content cannot be empty",
                "knowledge_tags": ["基础语法"]
            }
        
        try:
            # 使用compile函数检查语法
            compile(code, '<string>', 'exec')
            return {
                "is_correct": True,
                "error_type": "无错误",
                "hint": "代码语法正确",
                "hint_en": "Code syntax is correct",
                "knowledge_tags": ["基础语法"]
            }
        except SyntaxError as e:
            return {
                "is_correct": False,
                "error_type": "语法错误",
                "hint": f"语法错误: {self._translate_error(e.msg)} (行 {e.lineno})",
                "hint_en": f"SyntaxError: {e.msg} (line {e.lineno})",
                "knowledge_tags": ["基础语法", "调试"]
            }
        except Exception as e:
            return {
                "is_correct": False,
                "error_type": "其他错误",
                "hint": f"代码执行错误: {str(e)}",
                "hint_en": f"Code execution error: {str(e)}",
                "knowledge_tags": ["基础语法", "调试"]
            }
    
    def _translate_error(self, error_msg):
        """翻译错误信息为中文"""
        error_translations = {
            "EOL while scanning string literal": "字符串的引号没有闭合",
            "unterminated string literal": "字符串的引号没有闭合",
            "invalid syntax": "无效的语法",
            "unexpected indent": "意外的缩进",
            "expected an indented block": "期望一个缩进块",
            "unexpected token": "意外的标记",
            "name '\\w+' is not defined": "名称未定义",
            "missing parentheses": "缺少括号",
            "unexpected EOF": "意外的文件结束",
        }
        
        for pattern, translation in error_translations.items():
            import re
            if re.match(pattern, error_msg):
                return translation
        
        return error_msg
    
    def _real_analyze_code(self, student_code):
        """使用DeepSeek API真实分析代码"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        prompt = f"""你是一位Python编程教师，请分析以下学生提交的代码：

```python
{student_code}
```

请按照以下格式返回分析结果：
1. is_correct: 布尔值，表示代码是否正确
2. error_type: 字符串，错误类型（如"语法错误"、"逻辑错误"、"无错误"等）
3. hint: 字符串，详细的错误提示或改进建议
4. knowledge_tags: 数组，涉及的知识点标签（如["基础语法", "函数", "循环"等）

请严格按照JSON格式返回，不要包含其他无关内容。"""
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # 提取JSON部分
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                analysis = json.loads(json_match.group(0))
                # 确保返回格式正确
                if isinstance(analysis, dict) and all(key in analysis for key in ['is_correct', 'error_type', 'hint', 'knowledge_tags']):
                    return analysis
            except json.JSONDecodeError:
                pass
        
        # 如果解析失败，返回默认分析结果
        return {
            "is_correct": False,
            "error_type": "分析失败",
            "hint": "DeepSeek API返回格式异常",
            "knowledge_tags": ["基础语法"]
        }
    
    def _mock_analyze_code(self, student_code):
        """模拟分析代码"""
        code = student_code.strip()
        
        if not code:
            return {
                "is_correct": False,
                "error_type": "语法错误",
                "hint": "代码为空，请编写有效的Python代码",
                "hint_en": "Code is empty, please write valid Python code",
                "knowledge_tags": ["基础语法"]
            }
        
        try:
            # 尝试编译代码
            compile(code, '<string>', 'exec')
            
            # 检查代码是否包含input()函数
            if 'input(' in code:
                # 对于包含input()函数的代码，不尝试执行
                # 直接返回语法正确的结果
                return {
                    "is_correct": True,
                    "error_type": "无错误",
                    "hint": "代码语法正确",
                    "hint_en": "Code syntax is correct",
                    "knowledge_tags": ["基础语法"]
                }
            
            # 尝试执行代码（仅对不包含input()函数的代码）
            exec(code)
            # 代码执行成功
            return {
                "is_correct": True,
                "error_type": "无错误",
                "hint": "代码语法正确，执行成功",
                "hint_en": "Code syntax is correct and executed successfully",
                "knowledge_tags": ["基础语法"]
            }
        except SyntaxError as e:
            error_msg = self._translate_error(e.msg)
            return {
                "is_correct": False,
                "error_type": "语法错误",
                "hint": f"语法错误: {error_msg} (行 {e.lineno})",
                "hint_en": f"SyntaxError: {e.msg} (line {e.lineno})",
                "knowledge_tags": ["基础语法", "调试"]
            }
        except IndexError as e:
            return {
                "is_correct": False,
                "error_type": "索引错误",
                "hint": "索引越界错误：尝试访问列表或元组中不存在的元素",
                "hint_en": "IndexError: list index out of range",
                "knowledge_tags": ["基础语法", "列表", "调试"]
            }
        except NameError as e:
            return {
                "is_correct": False,
                "error_type": "名称错误",
                "hint": "名称未定义：尝试使用未定义的变量或函数",
                "hint_en": f"NameError: {str(e)}",
                "knowledge_tags": ["基础语法", "变量", "调试"]
            }
        except TypeError as e:
            return {
                "is_correct": False,
                "error_type": "类型错误",
                "hint": "类型错误：操作或函数应用于不适当类型的对象",
                "hint_en": f"TypeError: {str(e)}",
                "knowledge_tags": ["基础语法", "数据类型", "调试"]
            }
        except ZeroDivisionError as e:
            return {
                "is_correct": False,
                "error_type": "除零错误",
                "hint": "除零错误：尝试除以零",
                "hint_en": "ZeroDivisionError: division by zero",
                "knowledge_tags": ["基础语法", "算术运算", "调试"]
            }
        except Exception as e:
            return {
                "is_correct": False,
                "error_type": "其他错误",
                "hint": f"代码执行错误: {str(e)}",
                "hint_en": f"Error: {str(e)}",
                "knowledge_tags": ["基础语法", "调试"]
            }
    
    def analyze_with_deepseek(self, prompt):
        """使用DeepSeek API分析特定问题"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 800
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # 提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    analysis = json.loads(json_match.group(0))
                    # 确保返回格式正确
                    if isinstance(analysis, dict):
                        return analysis
                except json.JSONDecodeError:
                    pass
            
            # 如果解析失败，返回包含分析内容的结果
            return {
                "hint": content,
                "hint_en": content
            }
        except Exception as e:
            print(f"DeepSeek API调用失败: {e}")
            return {
                "hint": "分析失败，请稍后重试",
                "hint_en": "Analysis failed, please try again later"
            }

    def generate_problems(self, topic, count, difficulty='入门', require_custom_function=True, language='python'):
        """使用DeepSeek API生成编程题目"""
        print(f"DEBUG: generate_problems called with topic={topic}, count={count}, difficulty={difficulty}, require_custom_function={require_custom_function}, language={language}")
        print(f"DEBUG: api_key length={len(self.api_key)}")
        
        if not self.api_key:
            print("DEBUG: API key is empty, returning empty list")
            return []
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 语言映射
        language_map = {
            'python': 'Python',
            'c': 'C',
            'cpp': 'C++',
            'java': 'Java',
            'javascript': 'JavaScript'
        }
        lang = language_map.get(language, 'Python')

        # 难度等级描述
        difficulty_desc = {
            '入门': '入门级，适合初学者，题目简单，主要考察基本概念和语法',
            '基础': '基础级，适合有一定基础的学生，题目有一定难度，需要综合运用知识',
            '提高': '提高级，适合进阶学习的学生，题目较难，需要深入理解和灵活运用'
        }

        # 自定义函数要求
        custom_func_requirement = "请在每道题目中明确要求学生定义特定的函数来解决问题，并在description中明确说明函数名" if require_custom_function else "题目可以不要求学生定义特定函数，可以直接编写代码解决问题"
        custom_func_required_note = "必须包含" if require_custom_function else "可以为空"

        prompt = f"""请生成{count}道关于{lang} {topic}的编程题目。

难度要求：{difficulty_desc.get(difficulty, '适中难度')}

函数要求：{custom_func_requirement}

要求：
1. 每道题目包含：题目标题(title)、题目描述(description)、输入描述(input_description)、输出描述(output_description)、样例输入(sample_input)、样例输出(sample_output)、测试输入(test_input)、测试输出(test_output)、必需函数(required_functions)
2. 题目难度符合指定的{difficulty}等级
3. 题目应该考察学生对{topic}的掌握程度
4. {custom_func_required_note}必需函数：如果要求学生定义特定函数，请在description中明确说明函数名，并在required_functions字段中列出这些函数名，用逗号分隔
5. 如果题目不要求特定函数，required_functions字段为空字符串
6. 样例输入和输出应该符合{lang}的语法规范，用于展示给学生
7. 测试输入和测试输出是额外的测试用例，用于验证学生代码的正确性，不显示给学生
8. 返回格式为JSON数组，每道题目的格式如下：
{{
  "title": "题目标题",
  "description": "题目描述（请明确要求学生定义的函数名称）",
  "input_description": "输入描述",
  "output_description": "输出描述",
  "sample_input": "样例输入",
  "sample_output": "样例输出",
  "test_input": "测试输入",
  "test_output": "测试输出",
  "required_functions": "函数1,函数2"
}}

请只返回JSON数组，不要包含其他文字说明。"""

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        try:
            print("DEBUG: Sending request to DeepSeek API")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            print(f"DEBUG: Response status code: {response.status_code}")
            response.raise_for_status()

            result = response.json()
            print(f"DEBUG: Response received: {result}")
            content = result['choices'][0]['message']['content'].strip()
            print(f"DEBUG: Content: {content}")

            # 尝试提取JSON数组
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                print(f"DEBUG: Found JSON match: {json_match.group(0)}")
                try:
                    problems = json.loads(json_match.group(0))
                    if isinstance(problems, list):
                        print(f"DEBUG: Successfully parsed {len(problems)} problems")
                        # 为每个题目添加language字段
                        for problem in problems:
                            problem['language'] = language
                        return problems
                except json.JSONDecodeError as e:
                    print(f"DEBUG: JSON decode error: {e}")
                    pass

            # 如果解析失败，返回空列表
            print("DEBUG: No valid JSON array found")
            return []
        except Exception as e:
            print(f"DeepSeek API调用失败: {e}")
            # 返回None表示API调用失败
            return None

    def generate_problems_with_errors(self, topic, count, language='python', error_summary="", difficulty="基础", require_custom_function=False):
        """使用DeepSeek API根据学生错误总结生成针对性的编程题目"""
        print(f"DEBUG: generate_problems_with_errors called with topic={topic}, count={count}, language={language}, error_summary={error_summary}, difficulty={difficulty}, require_custom_function={require_custom_function}")
        
        # 检查API密钥
        if not self.api_key:
            print("DEBUG: API key is empty or None")
            return None
        
        print(f"DEBUG: api_key length={len(self.api_key)}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # 语言映射
        language_map = {
            'python': 'Python',
            'c': 'C',
            'cpp': 'C++',
            'java': 'Java',
            'javascript': 'JavaScript'
        }
        lang = language_map.get(language, 'Python')

        # 根据传入的参数确定函数要求
        if require_custom_function:
            function_requirement = "每道题目都必须要求学生定义特定的函数来解决问题，并在description中明确说明函数名（如solve），在required_functions字段中列出这些函数名"
        else:
            function_requirement = "题目不需要学生定义特定函数，可以直接编写代码，required_functions字段为空字符串"

        # 构建提示词，包含学生的错误总结
        error_context = f"""
学生在该知识点上的错误总结：
{error_summary}

""" if error_summary and error_summary != "该学生在该知识点上暂无错误记录" else ""

        prompt = f"""请生成{count}道关于{lang} {topic}的编程题目。

{error_context}要求：
1. 每道题目包含：题目标题(title)、题目描述(description)、输入描述(input_description)、输出描述(output_description)、样例输入(sample_input)、样例输出(sample_output)、测试输入(test_input)、测试输出(test_output)、难度等级(difficulty)、必需函数(required_functions)
2. 根据学生的错误总结，生成针对性的练习题目，帮助学生克服薄弱环节
3. 所有题目的难度等级统一为：{difficulty}
4. 题目应该考察学生对{topic}的掌握程度，特别是针对学生常犯的错误类型
5. 函数要求：{function_requirement}
6. 如果需要学生定义特定函数，请在description中明确说明函数名（如solve），并在required_functions字段中列出这些函数名，用逗号分隔
7. 如果题目不要求特定函数，required_functions字段为空字符串
8. 样例输入和输出应该符合{lang}的语法规范，用于展示给学生
9. 测试输入和测试输出是额外的测试用例，用于验证学生代码的正确性，不显示给学生
10. 返回格式为JSON数组，每道题目的格式如下：
{{
  "title": "题目标题",
  "description": "题目描述",
  "input_description": "输入描述",
  "output_description": "输出描述",
  "sample_input": "样例输入",
  "sample_output": "样例输出",
  "test_input": "测试输入",
  "test_output": "测试输出",
  "difficulty": "{difficulty}",
  "required_functions": "函数1,函数2"
}}

请只返回JSON数组，不要包含其他文字说明。"""

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2500
        }

        try:
            print("DEBUG: Sending request to DeepSeek API with error context")
            print(f"DEBUG: Headers: {headers}")
            print(f"DEBUG: Payload length: {len(json.dumps(payload))}")
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            print(f"DEBUG: Response status code: {response.status_code}")
            
            # 检查响应内容
            try:
                result = response.json()
                print(f"DEBUG: Response received (keys): {list(result.keys())}")
                
                if 'error' in result:
                    print(f"DEBUG: API Error: {result['error']}")
                    return None
                    
                if 'choices' not in result or not result['choices']:
                    print("DEBUG: No choices in response")
                    return []
                    
                content = result['choices'][0]['message']['content'].strip()
                print(f"DEBUG: Content length: {len(content)}")
                print(f"DEBUG: Content preview (first 500 chars): {content[:500]}...")

                # 尝试提取JSON数组
                json_match = re.search(r'\[[\s\S]*\]', content)
                if json_match:
                    print(f"DEBUG: Found JSON match (length: {len(json_match.group(0))})")
                    try:
                        problems = json.loads(json_match.group(0))
                        if isinstance(problems, list):
                            print(f"DEBUG: Successfully parsed {len(problems)} problems")
                            # 为每个题目添加language字段，确保difficulty字段存在
                            for problem in problems:
                                problem['language'] = language
                                if 'difficulty' not in problem:
                                    problem['difficulty'] = '基础'  # 默认难度
                            return problems
                    except json.JSONDecodeError as e:
                        print(f"DEBUG: JSON decode error: {e}")
                        pass

                # 如果解析失败，返回空列表
                print("DEBUG: No valid JSON array found")
                return []
            except json.JSONDecodeError as e:
                print(f"DEBUG: Response is not valid JSON: {e}")
                print(f"DEBUG: Response text (first 1000 chars): {response.text[:1000]}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Request exception: {type(e).__name__}: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"DEBUG: Response status: {e.response.status_code}")
                print(f"DEBUG: Response text: {e.response.text[:1000]}")
            return None
        except Exception as e:
            print(f"DEBUG: Unexpected exception: {type(e).__name__}: {e}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return None
<template>
    <div class="rag-container">
        <!-- 标题 -->
        <h1 class="title">RAG智能问答系统</h1>

        <!-- 输入区域 -->
        <div class="input-section">
            <el-input v-model="question" placeholder="请输入您的问题，例如：什么是深度学习？" :disabled="isLoading" clearable
                @keyup.enter="handleSubmit">
                <template #append>
                    <el-button :loading="isLoading" type="primary" @click="handleSubmit">
                        <template #default>
                            <el-icon class="icon">
                                <Search />
                            </el-icon>
                            提问
                        </template>
                    </el-button>
                </template>
            </el-input>
        </div>

        <!-- 加载状态 -->
        <div v-if="isLoading" class="loading">
            <el-icon class="loading-icon" :size="40">
                <Loading />
            </el-icon>
            <span>正在为您生成答案...</span>
        </div>

        <!-- 结果展示 -->
        <template v-if="answerResult">
            <el-card class="result-card">
                <!-- 问题 -->
                <div class="question-section">
                    <h3>问题：</h3>
                    <p>{{ answerResult.question }}</p>
                </div>

                <!-- 答案 -->
                <div class="answer-section">
                    <h3>答案：</h3>
                    <p>{{ answerResult.answer }}</p>
                </div>

                <!-- 参考文档 -->
                <div class="sources-section">
                    <h3>参考来源：</h3>
                    <el-collapse>
                        <el-collapse-item v-for="(doc, index) in answerResult.source_docs" :key="index"
                            :title="`文档 ${index + 1}`">
                            <div class="doc-content">{{ doc }}</div>
                        </el-collapse-item>
                    </el-collapse>
                </div>
            </el-card>
        </template>

        <!-- 错误提示 -->
        <div v-if="errorMessage" class="error-message">
            <el-alert :title="errorMessage" type="error" :closable="false" />
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Search, Loading } from '@element-plus/icons-vue'

// API配置
const API_BASE_URL = 'https://898800-proxy-8000.dsw-gateway-cn-hangzhou.data.aliyun.com'  // 根据实际后端地址修改

// 响应式数据
const question = ref('')
const isLoading = ref(false)
const answerResult = ref(null)
const errorMessage = ref('')

// 提交问题
const handleSubmit = async () => {
    if (!question.value.trim()) {
        ElMessage.warning('请输入有效问题')
        return
    }

    try {
        isLoading.value = true
        errorMessage.value = ''

        const response = await axios.post(`${API_BASE_URL}/query`, {
            question: question.value.trim()
        }, { withCredentials: true })
        answerResult.value = response.data
    } catch (error) {
        errorMessage.value = `请求失败：${error.response?.data?.detail || error.message
            }`
        console.error('API Error:', error)
    } finally {
        isLoading.value = false
    }
}
</script>

<style scoped>
.rag-container {
    max-width: 800px;
    margin: 2rem auto;
    padding: 0 1rem;
}

.title {
    text-align: center;
    color: #2c3e50;
    margin-bottom: 2rem;
}

.input-section {
    margin-bottom: 2rem;
}

.loading {
    text-align: center;
    margin: 2rem 0;
    color: #666;
}

.loading-icon {
    animation: rotating 2s linear infinite;
    margin-right: 0.5rem;
}

.result-card {
    margin-top: 2rem;
    background-color: #f8f9fa;
}

.question-section h3,
.answer-section h3,
.sources-section h3 {
    color: #2c3e50;
    margin-bottom: 0.5rem;
}

.doc-content {
    white-space: pre-wrap;
    background: #fff;
    padding: 1rem;
    border-radius: 4px;
}

.error-message {
    margin-top: 2rem;
}

@keyframes rotating {
    from {
        transform: rotate(0deg);
    }

    to {
        transform: rotate(360deg);
    }
}
</style>
import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'

interface CorrectionResult {
  original_text: string
  corrected_text: string
  corrections: Array<{
    type: string
    original: string
    corrected: string
    explanation: string
  }>
  score: number
}

interface AIAnalysisResult {
  overall_score: number
  recognized_text: string
  grammar_corrections: Array<{
    type: string
    original: string
    corrected: string
    explanation: string
  }>
  pronunciation_feedback: Array<{
    type: string
    original: string
    corrected: string
    explanation: string
  }>
  scenario_suggestions: Array<{
    scenario_type: string
    difficulty_level: string
    reason: string
  }>
  personalized_tips: string[]
  difficulty_level: string
  next_scenario: string | null
  confidence_score: number
  detailed_analysis: string
}

interface Scenario {
  scenario_type: string
  difficulty_level: string
  display_name: string
}

interface ScenarioContext {
  scenario_type: string
  difficulty_level: string
  context_description: string
  sample_dialogues: string[]
  key_vocabulary: string[]
  grammar_focus: string[]
  pronunciation_targets: string[]
}

const PronunciationCorrection: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [result, setResult] = useState<CorrectionResult | null>(null)
  const [aiResult, setAiResult] = useState<AIAnalysisResult | null>(null)
  const [error, setError] = useState<string>('')
  const [referenceText, setReferenceText] = useState<string>('')
  const [analysisMode, setAnalysisMode] = useState<'basic' | 'ai'>('basic')
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [selectedScenario, setSelectedScenario] = useState<string>('')
  const [scenarioContext, setScenarioContext] = useState<ScenarioContext | null>(null)
  const [userId] = useState<string>('user_' + Date.now()) // 简单的用户ID生成
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement>(null)

  // 加载场景列表
  useEffect(() => {
    const loadScenarios = async () => {
      try {
        const response = await axios.get('/api/scenarios')
        setScenarios(response.data)
      } catch (err) {
        console.error('加载场景列表失败:', err)
      }
    }
    loadScenarios()
  }, [])

  // 加载场景上下文
  useEffect(() => {
    const loadScenarioContext = async () => {
      if (selectedScenario) {
        try {
          const [scenarioType, difficultyLevel] = selectedScenario.split('-')
          const response = await axios.get(`/api/scenarios/${scenarioType}/${difficultyLevel}`)
          setScenarioContext(response.data)
        } catch (err) {
          console.error('加载场景上下文失败:', err)
        }
      } else {
        setScenarioContext(null)
      }
    }
    loadScenarioContext()
  }, [selectedScenario])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
        setAudioBlob(audioBlob)
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
      setError('')
    } catch (err) {
      setError('マイクにアクセスできません。権限設定を確認してください。')
      console.error('録音失敗:', err)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const playRecording = () => {
    if (audioBlob && audioRef.current) {
      const audioUrl = URL.createObjectURL(audioBlob)
      audioRef.current.src = audioUrl
      audioRef.current.play().catch(console.error)
    }
  }

  const analyzeAudio = async () => {
    if (!audioBlob) {
      setError('先に音声を録音してください')
      return
    }

    if (!referenceText.trim()) {
      setError('お手本テキストを入力してください')
      return
    }

    setIsAnalyzing(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.wav')
      formData.append('reference_text', referenceText.trim())

      if (analysisMode === 'ai') {
        // AI分析模式
        if (selectedScenario) {
          formData.append('current_scenario', selectedScenario)
        }
        formData.append('user_id', userId)

        const response = await axios.post('/api/pronunciation/ai-analyze', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        setAiResult(response.data)
        setResult(null) // 清除基础分析结果
      } else {
        // 基础分析模式
        const response = await axios.post('/api/pronunciation/analyze', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        setResult(response.data)
        setAiResult(null) // 清除AI分析结果
      }
    } catch (err) {
      setError('分析に失敗しました。後でもう一度お試しください。')
      console.error('分析失败:', err)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const resetRecording = () => {
    setAudioBlob(null)
    setResult(null)
    setAiResult(null)
    setError('')
    setReferenceText('')
    setSelectedScenario('')
    setScenarioContext(null)
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return '#4CAF50'
    if (score >= 70) return '#FF9800'
    return '#F44336'
  }

  const getCorrectionTypeColor = (type: string) => {
    switch (type) {
      case 'grammar': return '#2196F3'
      case 'pronunciation': return '#9C27B0'
      case 'vocabulary': return '#FF5722'
      default: return '#607D8B'
    }
  }

  return (
    <div className="pronunciation-correction">
      <div className="correction-header">
        <h2>発音矯正</h2>
        <p>音声を録音してください。発音と文法のアドバイスを提供します。</p>
      </div>

      <div className="reference-text-section">
        <label htmlFor="reference-text">お手本テキスト</label>
        <textarea
          id="reference-text"
          value={referenceText}
          onChange={(e) => setReferenceText(e.target.value)}
          placeholder="練習したい日本語の文章を入力してください..."
          className="reference-text-input"
          rows={3}
          disabled={isAnalyzing}
        />
      </div>

      <div className="analysis-mode-section">
        <label>分析モード</label>
        <div className="mode-selector">
          <button
            className={`mode-button ${analysisMode === 'basic' ? 'active' : ''}`}
            onClick={() => setAnalysisMode('basic')}
            disabled={isAnalyzing}
          >
            基本分析
          </button>
          <button
            className={`mode-button ${analysisMode === 'ai' ? 'active' : ''}`}
            onClick={() => setAnalysisMode('ai')}
            disabled={isAnalyzing}
          >
            AIインテリジェント分析
          </button>
        </div>
      </div>

      {analysisMode === 'ai' && (
        <div className="scenario-section">
          <label htmlFor="scenario-select">練習シーン（任意）</label>
          <select
            id="scenario-select"
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className="scenario-select"
            disabled={isAnalyzing}
          >
            <option value="">練習シーンを選択...</option>
            {scenarios.map((scenario) => (
              <option key={`${scenario.scenario_type}-${scenario.difficulty_level}`} value={`${scenario.scenario_type}-${scenario.difficulty_level}`}>
                {scenario.display_name}
              </option>
            ))}
          </select>
          
          {scenarioContext && (
            <div className="scenario-context">
              <h4>シーンの説明</h4>
              <p>{scenarioContext.context_description}</p>
              
              {scenarioContext.sample_dialogues.length > 0 && (
                <div className="sample-dialogues">
                  <h5>例文</h5>
                  <ul>
                    {scenarioContext.sample_dialogues.map((dialogue, index) => (
                      <li key={index}>{dialogue}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {scenarioContext.key_vocabulary.length > 0 && (
                <div className="key-vocabulary">
                  <h5>重要キーワード</h5>
                  <div className="vocabulary-tags">
                    {scenarioContext.key_vocabulary.map((word, index) => (
                      <span key={index} className="vocabulary-tag">{word}</span>
                    ))}
                  </div>
                </div>
              )}
              
              {scenarioContext.pronunciation_targets.length > 0 && (
                <div className="pronunciation-targets">
                  <h5>発音のポイント</h5>
                  <ul>
                    {scenarioContext.pronunciation_targets.map((target, index) => (
                      <li key={index}>{target}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="recording-section">
        <div className="recording-controls">
          {!isRecording ? (
            <button 
              onClick={startRecording}
              className="record-button start"
              disabled={isAnalyzing}
            >
              🎤 録音開始
            </button>
          ) : (
            <button 
              onClick={stopRecording}
              className="record-button stop"
            >
              ⏹️ 停止
            </button>
          )}
          
          {audioBlob && (
            <>
              <button 
                onClick={playRecording}
                className="play-button"
                disabled={isAnalyzing}
              >
                ▶️ 録音を再生
              </button>
              <button 
                onClick={analyzeAudio}
                className="analyze-button"
                disabled={isAnalyzing}
              >
                {isAnalyzing ? '分析中...' : '🔍 音声を分析'}
              </button>
              <button 
                onClick={resetRecording}
                className="reset-button"
                disabled={isAnalyzing}
              >
                🔄 録り直し
              </button>
            </>
          )}
        </div>

        {isRecording && (
          <div className="recording-indicator">
            <div className="recording-dot"></div>
            <span>録音中...</span>
          </div>
        )}

        {error && (
          <div className="error-message">
            ❌ {error}
          </div>
        )}
      </div>

      {result && (
        <div className="analysis-results">
          <div className="score-section">
            <h3>総合スコア</h3>
            <div 
              className="score-circle"
              style={{ borderColor: getScoreColor(result.score) }}
            >
              <span style={{ color: getScoreColor(result.score) }}>
                {result.score}
              </span>
            </div>
          </div>

          <div className="text-comparison">
            <div className="text-section">
              <h4>認識されたテキスト</h4>
              <p className="original-text">{result.original_text}</p>
            </div>
            
            {result.corrected_text !== result.original_text && (
              <div className="text-section">
                <h4>修正の提案</h4>
                <p className="corrected-text">{result.corrected_text}</p>
              </div>
            )}
          </div>

          {result.corrections.length > 0 && (
            <div className="corrections-section">
              <h4>詳細なアドバイス</h4>
              <div className="corrections-list">
                {result.corrections.map((correction, index) => (
                  <div key={index} className="correction-item">
                    <div 
                      className="correction-type"
                      style={{ backgroundColor: getCorrectionTypeColor(correction.type) }}
                    >
                      {correction.type === 'grammar' ? '文法' : 
                       correction.type === 'pronunciation' ? '発音' : 
                       correction.type === 'vocabulary' ? '語彙' : 'その他'}
                    </div>
                    <div className="correction-content">
                      <div className="correction-change">
                        <span className="original">「{correction.original}」</span>
                        <span className="arrow">→</span>
                        <span className="corrected">「{correction.corrected}」</span>
                      </div>
                      <p className="correction-explanation">{correction.explanation}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {aiResult && (
        <div className="ai-analysis-results">
          <div className="ai-score-section">
            <h3>AIインテリジェントスコア</h3>
            <div className="score-grid">
              <div 
                className="score-circle"
                style={{ borderColor: getScoreColor(aiResult.overall_score) }}
              >
                <span style={{ color: getScoreColor(aiResult.overall_score) }}>
                  {aiResult.overall_score}
                </span>
                <small>総合スコア</small>
              </div>
              <div className="confidence-score">
                <span className="confidence-value">{aiResult.confidence_score}%</span>
                <small>信頼度</small>
              </div>
              <div className="difficulty-level">
                <span className="difficulty-value">{aiResult.difficulty_level}</span>
                <small>難易度</small>
              </div>
            </div>
          </div>

          <div className="ai-text-comparison">
            <div className="text-section">
              <h4>認識されたテキスト</h4>
              <p className="original-text">{aiResult.recognized_text}</p>
            </div>
          </div>

          {aiResult.grammar_corrections.length > 0 && (
            <div className="grammar-corrections-section">
              <h4>📝 文法修正</h4>
              <div className="corrections-list">
                {aiResult.grammar_corrections.map((correction, index) => (
                  <div key={index} className="correction-item">
                    <div 
                      className="correction-type"
                      style={{ backgroundColor: getCorrectionTypeColor('grammar') }}
                    >
                      文法
                    </div>
                    <div className="correction-content">
                      <div className="correction-change">
                        <span className="original">「{correction.original}」</span>
                        <span className="arrow">→</span>
                        <span className="corrected">「{correction.corrected}」</span>
                      </div>
                      <p className="correction-explanation">{correction.explanation}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {aiResult.pronunciation_feedback.length > 0 && (
            <div className="pronunciation-feedback-section">
              <h4>🎯 発音指導</h4>
              <div className="corrections-list">
                {aiResult.pronunciation_feedback.map((feedback, index) => (
                  <div key={index} className="correction-item">
                    <div 
                      className="correction-type"
                      style={{ backgroundColor: getCorrectionTypeColor('pronunciation') }}
                    >
                      発音
                    </div>
                    <div className="correction-content">
                      <div className="correction-change">
                        <span className="original">「{feedback.original}」</span>
                        <span className="arrow">→</span>
                        <span className="corrected">「{feedback.corrected}」</span>
                      </div>
                      <p className="correction-explanation">{feedback.explanation}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {aiResult.personalized_tips.length > 0 && (
            <div className="personalized-tips-section">
              <h4>💡 パーソナライズされたアドバイス</h4>
              <ul className="tips-list">
                {aiResult.personalized_tips.map((tip, index) => (
                  <li key={index} className="tip-item">{tip}</li>
                ))}
              </ul>
            </div>
          )}

          {aiResult.scenario_suggestions.length > 0 && (
            <div className="scenario-suggestions-section">
              <h4>🔄 シーンの提案</h4>
              <div className="scenario-suggestions">
                {aiResult.scenario_suggestions.map((suggestion, index) => (
                  <div key={index} className="scenario-suggestion">
                    <div className="scenario-info">
                      <span className="scenario-name">
                        {suggestion.scenario_type} - {suggestion.difficulty_level}
                      </span>
                      <p className="scenario-reason">{suggestion.reason}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {aiResult.next_scenario && (
            <div className="next-scenario-section">
              <h4>📈 次の練習の推奨</h4>
              <div className="next-scenario">
                <span className="next-scenario-name">{aiResult.next_scenario}</span>
                <button 
                  className="apply-scenario-button"
                  onClick={() => setSelectedScenario(aiResult.next_scenario!)}
                >
                  このシーンを適用
                </button>
              </div>
            </div>
          )}

          {aiResult.detailed_analysis && (
            <div className="detailed-analysis-section">
              <h4>📊 詳細分析</h4>
              <div className="detailed-analysis">
                <p>{aiResult.detailed_analysis}</p>
              </div>
            </div>
          )}
        </div>
      )}

      <audio ref={audioRef} />
    </div>
  )
}

export default PronunciationCorrection
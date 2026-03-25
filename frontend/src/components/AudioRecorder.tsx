import React, { useState, useRef } from 'react'

interface AudioRecorderProps {
  onAudioReady: (audioBlob: Blob) => void
  onError: (error: string) => void
  disabled?: boolean
  className?: string
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({
  onAudioReady,
  onError,
  disabled = false,
  className = ''
}) => {
  const [isRecording, setIsRecording] = useState(false)
  const [, setAudioBlob] = useState<Blob | null>(null)
  
  // const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  // const audioChunksRef = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement>(null)

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      // 使用Web Audio API录制原始音频数据
      const audioContext = new AudioContext({ sampleRate: 16000 })
      const source = audioContext.createMediaStreamSource(stream)
      
      // 创建ScriptProcessorNode来处理音频数据
      const processor = audioContext.createScriptProcessor(4096, 1, 1)
      const audioData: Float32Array[] = []
      
      processor.onaudioprocess = (event) => {
        const inputBuffer = event.inputBuffer.getChannelData(0)
        audioData.push(new Float32Array(inputBuffer))
      }
      
      source.connect(processor)
      processor.connect(audioContext.destination)
      
      // 保存引用以便停止时使用
      ;(window as any).currentRecording = {
        audioContext,
        processor,
        source,
        stream,
        audioData
      }
      
      setIsRecording(true)
    } catch (err) {
      onError('无法访问麦克风，请检查权限设置')
      console.error('录音失败:', err)
    }
  }

  const stopRecording = () => {
    if (isRecording && (window as any).currentRecording) {
      const { audioContext, processor, source, stream, audioData } = (window as any).currentRecording
      
      // 停止录音
      processor.disconnect()
      source.disconnect()
      audioContext.close()
      stream.getTracks().forEach((track: MediaStreamTrack) => track.stop())
      
      // 将Float32Array数据转换为WAV格式
      const wavBlob = createWavBlob(audioData, 16000)
      onAudioReady(wavBlob)
      
      // 清理
      delete (window as any).currentRecording
      setIsRecording(false)
      setAudioBlob(null) // 清除audioBlob，让录音按钮回到初始状态
    }
  }
  
  // 创建WAV格式的Blob
  const createWavBlob = (audioData: Float32Array[], sampleRate: number): Blob => {
    // 合并所有音频数据
    const totalLength = audioData.reduce((acc, chunk) => acc + chunk.length, 0)
    const mergedData = new Float32Array(totalLength)
    let offset = 0
    for (const chunk of audioData) {
      mergedData.set(chunk, offset)
      offset += chunk.length
    }
    
    // 转换为16位PCM
    const pcmData = new Int16Array(mergedData.length)
    for (let i = 0; i < mergedData.length; i++) {
      pcmData[i] = Math.max(-32768, Math.min(32767, mergedData[i] * 32767))
    }
    
    // 创建WAV文件头
    const buffer = new ArrayBuffer(44 + pcmData.length * 2)
    const view = new DataView(buffer)
    
    // WAV文件头
    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i))
      }
    }
    
    writeString(0, 'RIFF')
    view.setUint32(4, 36 + pcmData.length * 2, true)
    writeString(8, 'WAVE')
    writeString(12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, 1, true)
    view.setUint16(22, 1, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, sampleRate * 2, true)
    view.setUint16(32, 2, true)
    view.setUint16(34, 16, true)
    writeString(36, 'data')
    view.setUint32(40, pcmData.length * 2, true)
    
    // 写入PCM数据
    const pcmView = new Int16Array(buffer, 44)
    pcmView.set(pcmData)
    
    return new Blob([buffer], { type: 'audio/wav' })
  }

  // const playRecording = () => {
  //   if (audioBlob && audioRef.current) {
  //     const audioUrl = URL.createObjectURL(audioBlob)
  //     audioRef.current.src = audioUrl
  //     audioRef.current.play().catch(console.error)
  //   }
  // }

  // const clearRecording = () => {
  //   setAudioBlob(null)
  // }

  return (
    <div className={`audio-recorder ${className}`}>
      <div className="recording-controls">
        {!isRecording ? (
          <button 
            onClick={startRecording}
            className="record-button start"
            disabled={disabled}
            title="録音開始"
          >
            🎤
          </button>
        ) : (
          <button 
            onClick={stopRecording}
            className="record-button stop recording"
            title="停止"
          >
            ⏹️
          </button>
        )}
        
        {/* 移除播放和清除按钮，用户可以通过点击语音气泡播放录音 */}
      </div>

      {isRecording && (
        <div className="recording-indicator">
          <div className="recording-dot"></div>
          <span>録音中...</span>
        </div>
      )}

      <audio ref={audioRef} />
    </div>
  )
}

export default AudioRecorder
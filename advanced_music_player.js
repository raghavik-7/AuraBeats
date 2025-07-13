class AdvancedMusicPlayer {
    constructor() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.currentSource = null;
        this.isPlaying = false;
    }
    
    async loadAndPlaySegment(url, startTime = 0, duration = 30) {
        try {
            // Fetch audio file
            const response = await fetch(url);
            const arrayBuffer = await response.arrayBuffer();
            
            // Decode audio data
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
            
            // Create source
            this.currentSource = this.audioContext.createBufferSource();
            this.currentSource.buffer = audioBuffer;
            
            // Connect to destination
            this.currentSource.connect(this.audioContext.destination);
            
            // Play specific segment
            this.currentSource.start(0, startTime, duration);
            this.isPlaying = true;
            
            // Stop after duration
            setTimeout(() => {
                this.stop();
            }, duration * 1000);
            
        } catch (error) {
            console.error('Failed to load audio:', error);
        }
    }
    
    stop() {
        if (this.currentSource) {
            this.currentSource.stop();
            this.currentSource = null;
            this.isPlaying = false;
        }
    }
}

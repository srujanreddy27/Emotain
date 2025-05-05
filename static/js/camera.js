document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('videoPreview');
    const canvas = document.getElementById('canvasCapture');
    const captureBtn = document.getElementById('captureBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const emotionResult = document.getElementById('emotionResult');
    const detectedEmotion = document.getElementById('detectedEmotion');
    const confidenceValue = document.getElementById('confidenceValue');
    
    // Create permission prompt
    const permissionPrompt = document.createElement('div');
    permissionPrompt.className = 'permission-prompt hidden';
    permissionPrompt.innerHTML = `
        <p>Please allow camera access to use emotion detection</p>
        <button id="retryCamera">Allow Access</button>
    `;
    document.body.appendChild(permissionPrompt);
    
    let stream = null;

    async function initCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: 640, 
                    height: 480,
                    facingMode: 'user' 
                }, 
                audio: false 
            });
            video.srcObject = stream;
            permissionPrompt.classList.add('hidden');
        } catch (err) {
            console.error("Camera error:", err);
            permissionPrompt.classList.remove('hidden');
        }
    }

    // Retry camera access
    document.getElementById('retryCamera')?.addEventListener('click', initCamera);

    // Capture and analyze
    captureBtn.addEventListener('click', async function() {
        if (!stream) {
            alert("Camera not ready. Please allow camera access first.");
            return;
        }

        this.disabled = true;
        loadingIndicator.classList.remove('hidden');

        try {
            const context = canvas.getContext('2d');
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            const blob = await new Promise(resolve => {
                canvas.toBlob(resolve, 'image/jpeg', 0.95);
            });

            const formData = new FormData();
            formData.append('image', blob, 'emotion.jpg');

            const response = await fetch('/detect_emotion', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Please align your face properly`);
            }

            const result = await response.json();

            if (result.error) {
                throw new Error(result.error);
            }

            detectedEmotion.textContent = result.emotion;
            confidenceValue.textContent = (result.confidence * 100).toFixed(1);
            emotionResult.classList.remove('hidden');

        } catch (error) {
            console.error('Detection failed:', error);
            alert(`Error: ${error.message}`);
        } finally {
            captureBtn.disabled = false;
            loadingIndicator.classList.add('hidden');
        }
    });

    window.addEventListener('beforeunload', function() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });

    initCamera();
});
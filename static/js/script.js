document.addEventListener('DOMContentLoaded', function() {
    // Login page functionality
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // In a real app, you would validate and send to server
            window.location.href = '/camera';
        });
    }
    
    // Camera page functionality
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const captureBtn = document.getElementById('captureBtn');
    const emotionResult = document.getElementById('emotionResult');
    const detectedEmotion = document.getElementById('detectedEmotion');
    
    if (video && captureBtn) {
        let stream = null;
        
        // Access camera
        navigator.mediaDevices.getUserMedia({ video: true, audio: false })
            .then(function(s) {
                stream = s;
                video.srcObject = stream;
                video.play();
            })
            .catch(function(err) {
                console.error("Camera error:", err);
                alert("Could not access the camera. Please ensure you've granted permission.");
            });
        
        // Capture button click
        captureBtn.addEventListener('click', function() {
            if (!stream) {
                alert("Camera not ready. Please try again.");
                return;
            }
            
            // Draw video frame to canvas
            const context = canvas.getContext('2d');
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Convert canvas image to blob and send to server
            canvas.toBlob(function(blob) {
                const formData = new FormData();
                formData.append('image', blob, 'emotion.jpg');
                
                fetch('/detect_emotion', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        detectedEmotion.textContent = data.emotion;
                        emotionResult.classList.remove('hidden');
                        captureBtn.disabled = true;
                        
                        // Stop camera stream
                        if (stream) {
                            stream.getTracks().forEach(track => track.stop());
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error detecting emotion. Please try again.');
                });
            }, 'image/jpeg', 0.95);
        });
        
        // Clean up camera stream when leaving page
        window.addEventListener('beforeunload', function() {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        });
    }
});
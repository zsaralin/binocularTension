// Load the MoveNet body tracking model
async function loadModel() {
    const detector = await poseDetection.createDetector(poseDetection.SupportedModels.MoveNet);
    return detector;
}

// Function to perform body tracking on a given image and canvas
async function trackPoses(detector, imgId, canvasId) {
    const img = document.getElementById(imgId);
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');

    // Set canvas size based on image dimensions
    canvas.width = img.width;
    canvas.height = img.height;

    async function detect() {
        const poses = await detector.estimatePoses(img);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawStickFigure(poses, ctx);
        requestAnimationFrame(detect);  // Loop the detection
    }

    detect();
}

// Function to draw keypoints on the canvas
// Function to draw stick figure on the canvas
function drawStickFigure(poses, ctx) {
    poses.forEach(pose => {
        const keypoints = pose.keypoints;

        // Helper function to draw a line between two keypoints if confidence is high enough
        function drawLine(p1, p2, color = "black", thickness = 3) {
            if (p1.score > 0.5 && p2.score > 0.5) { // Only draw if both points have confidence > 0.5
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.strokeStyle = color;
                ctx.lineWidth = thickness;
                ctx.stroke();
            }
        }

        // Draw head
        const nose = keypoints.find(kp => kp.name === 'nose');
        const leftEye = keypoints.find(kp => kp.name === 'left_eye');
        const rightEye = keypoints.find(kp => kp.name === 'right_eye');

        if (nose && leftEye && rightEye) {
            const eyeDistance = Math.abs(leftEye.x - rightEye.x);
            const headRadius = eyeDistance * 1.5; // Approximate head radius based on eye distance
            if (nose.score > 0.5) {
                ctx.beginPath();
                ctx.arc(nose.x, nose.y, headRadius, 0, 2 * Math.PI);
                ctx.fillStyle = "black";
                ctx.fill();
                ctx.stroke();
            }
        }

        // Draw torso
        const leftShoulder = keypoints.find(kp => kp.name === 'left_shoulder');
        const rightShoulder = keypoints.find(kp => kp.name === 'right_shoulder');
        const leftHip = keypoints.find(kp => kp.name === 'left_hip');
        const rightHip = keypoints.find(kp => kp.name === 'right_hip');

        if (leftShoulder && rightShoulder && leftHip && rightHip) {
            // Draw lines between shoulders and hips (torso)
            drawLine(leftShoulder, rightShoulder);
            drawLine(leftShoulder, leftHip);
            drawLine(rightShoulder, rightHip);
            drawLine(leftHip, rightHip);
        }

        // Draw arms
        const leftElbow = keypoints.find(kp => kp.name === 'left_elbow');
        const rightElbow = keypoints.find(kp => kp.name === 'right_elbow');
        const leftWrist = keypoints.find(kp => kp.name === 'left_wrist');
        const rightWrist = keypoints.find(kp => kp.name === 'right_wrist');

        if (leftShoulder && leftElbow && leftWrist) {
            drawLine(leftShoulder, leftElbow);
            drawLine(leftElbow, leftWrist);
        }
        if (rightShoulder && rightElbow && rightWrist) {
            drawLine(rightShoulder, rightElbow);
            drawLine(rightElbow, rightWrist);
        }

        // Draw legs
        const leftKnee = keypoints.find(kp => kp.name === 'left_knee');
        const rightKnee = keypoints.find(kp => kp.name === 'right_knee');
        const leftAnkle = keypoints.find(kp => kp.name === 'left_ankle');
        const rightAnkle = keypoints.find(kp => kp.name === 'right_ankle');

        if (leftHip && leftKnee && leftAnkle) {
            drawLine(leftHip, leftKnee);
            drawLine(leftKnee, leftAnkle);
        }
        if (rightHip && rightKnee && rightAnkle) {
            drawLine(rightHip, rightKnee);
            drawLine(rightKnee, rightAnkle);
        }
    });
}


// Load model and start body tracking on the duplicate video feeds only
loadModel().then(detector => {
    // Track poses for the duplicate camera feeds
    trackPoses(detector, 'videoFeed0_duplicate', 'canvas0_duplicate');
    trackPoses(detector, 'videoFeed1_duplicate', 'canvas1_duplicate');
});
